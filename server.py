import asyncio
import json
import os
from collections import defaultdict
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from rtaoai.openai.processors import EventHandler
from rtaoai.openai.runner import OpenAIRunner
from rtaoai.openai.events import (
    AudioTranscriptDone,
    AudioDelta,
    OutputItemDone,
    AudioDone,
    InputAudioTranscriptionCompleted,
)


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    def get_product_remmaining_stock(product_id: int) -> int:
        """Get product remaining stock given a product id."""
        try:
            return [1, 23, 244, 344, 123][product_id]
        except IndexError:
            return 0

    def list_all_products() -> list[int]:
        """List all available products. Returns a list of int."""
        return list(range(20))

    async def on_transcript_delta_done(audio_transcript: AudioTranscriptDone):
        await websocket.send_json(
            {
                "type": "new.server.transcript",
                "data": audio_transcript.transcript,
            }
        )

    items = defaultdict(list)

    async def on_event(event: str):
        await websocket.send_json({"type": "event", "data": event})

    async def on_audio_delta(audio_delta: AudioDelta):
        items[audio_delta.item_id].append(audio_delta.delta)
        await websocket.send_json({"type": "new.audio", "data": audio_delta.delta})

    async def on_audio_done(audio_done: AudioDone):
        item = items[audio_done.item_id]
        #await websocket.send_json({"type": "new.audio", "data": item})

    async def on_input_audio_transcription_completed(
        item: InputAudioTranscriptionCompleted,
    ):
        await websocket.send_json(
            {"type": "new.client.transcript", "data": item.transcript}
        )

    openai_runner = OpenAIRunner(
        api_key=os.getenv("OPENAI_API_KEY"),
        tools=[get_product_remmaining_stock, list_all_products],
    )

    async def on_output_item_done(output_item: OutputItemDone):
        # TODO: make it dynamic
        if output_item.item.name == "get_product_remmaining_stock":
            if output_item.item.arguments is None:
                raise ValueError("arguments can't be None")
            params = json.loads(output_item.item.arguments)
            result = get_product_remmaining_stock(**params)
            send_json = json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "call_id": output_item.item.call_id,
                        "type": "function_call_output",
                        # "role": "system",
                        "output": str(result),
                    },
                }
            )
            await openai_runner.ws.send(send_json)
            await openai_runner.ws.send(json.dumps({"type": "response.create"}))
        elif output_item.item.name == "list_all_products":
            list_products_result = list_all_products()
            send_json = json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "call_id": output_item.item.call_id,
                        "type": "function_call_output",
                        # "role": "system",
                        "output": str(list_products_result),
                    },
                }
            )
            await openai_runner.ws.send(send_json)
            await openai_runner.ws.send(json.dumps({"type": "response.create"}))

    event_handler = EventHandler(
        on_transcript_delta_done=on_transcript_delta_done,
        on_output_item_done=on_output_item_done,
        on_audio_delta=on_audio_delta,
        on_audio_done=on_audio_done,
        on_input_audio_transcription_completed=on_input_audio_transcription_completed,
        on_event=on_event,
    )
    # TODO: add a setter
    openai_runner.event_handler = event_handler
    await websocket.accept()

    async def client_websocket():
        while True:
            data = await websocket.receive()
            await openai_runner.send_audio(data["bytes"])

    await asyncio.gather(openai_runner.run(), client_websocket())
