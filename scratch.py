import time
import asyncio
import base64
import websockets
import io
import os
import json

from pydub import AudioSegment
from pydub.playback import play


def audio_to_item_create_event(audio_bytes: bytes) -> str:
    # Load the audio file from the byte stream
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

    # Resample to 24kHz mono pcm16
    pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2).raw_data

    # Encode to base64 string
    return base64.b64encode(pcm_audio).decode()


def base64_to_audio(base64_str: str):
    sound = AudioSegment(
        data=base64.b64decode(base64_str), sample_width=2, frame_rate=24_000, channels=1
    )
    play(sound)


url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    "OpenAI-Beta": "realtime=v1",
}

with open(os.getenv("INPUT_FILE"), "rb") as f:
    base64AudioData = audio_to_item_create_event(f.read())


class EventProcessors:
    def __init__(self):
        self.itemLookup = {}
        self.items = []
        self.queuedSpeechItems = {}
        self.queuedTranscriptItems = {}
        self.queuedInputAudio = None
        self.responseLookup = {}
        self.responses = []
        self.defaultFrequency = 24_000

    def conversation_item_created(self, event):
        item = event["item"]
        newItem = item.copy()  # Copie profonde de l'item
        if newItem["id"] not in self.itemLookup:
            self.itemLookup[newItem["id"]] = newItem
            self.items.append(newItem)

        newItem["formatted"] = {"audio": [], "text": "", "transcript": ""}

        # Gestion des éléments de type "speech"
        if newItem["id"] in self.queuedSpeechItems:
            newItem["formatted"]["audio"] = self.queuedSpeechItems[newItem["id"]][
                "audio"
            ]
            del self.queuedSpeechItems[newItem["id"]]

        # Population du texte si présent
        if "content" in newItem:
            textContent = [
                c for c in newItem["content"] if c["type"] in ["text", "input_text"]
            ]
            for content in textContent:
                newItem["formatted"]["text"] += content["text"]

        # Gestion des transcriptions
        if newItem["id"] in self.queuedTranscriptItems:
            newItem["formatted"]["transcript"] = self.queuedTranscriptItems[
                newItem["id"]
            ]["transcript"]
            del self.queuedTranscriptItems[newItem["id"]]

        if newItem["type"] == "message":
            newItem["status"] = (
                "completed" if newItem["role"] == "user" else "in_progress"
            )
            if newItem["role"] == "user" and self.queuedInputAudio:
                newItem["formatted"]["audio"] = self.queuedInputAudio
                self.queuedInputAudio = None
        elif newItem["type"] == "function_call":
            newItem["formatted"]["tool"] = {
                "type": "function",
                "name": newItem["name"],
                "call_id": newItem["call_id"],
                "arguments": "",
            }
            newItem["status"] = "in_progress"
        elif newItem["type"] == "function_call_output":
            newItem["status"] = "completed"
            newItem["formatted"]["output"] = newItem["output"]

        return {"item": newItem, "delta": None}

    def conversation_item_truncated(self, event):
        item_id = event["item_id"]
        audio_end_ms = event["audio_end_ms"]
        item = self.itemLookup.get(item_id)
        if not item:
            raise ValueError(f"item.truncated: Item '{item_id}' not found")

        endIndex = (audio_end_ms * self.defaultFrequency) // 1000
        item["formatted"]["transcript"] = ""
        item["formatted"]["audio"] = item["formatted"]["audio"][:endIndex]
        return {"item": item, "delta": None}

    def conversation_item_deleted(self, event):
        item_id = event["item_id"]
        item = self.itemLookup.get(item_id)
        if not item:
            raise ValueError(f"item.deleted: Item '{item_id}' not found")

        del self.itemLookup[item_id]
        if item in self.items:
            self.items.remove(item)

        return {"item": item, "delta": None}

    def conversation_item_input_audio_transcription_completed(self, event):
        item_id = event["item_id"]
        content_index = event["content_index"]
        transcript = event.get("transcript", " ")  # Espace pour transcript vide
        item = self.itemLookup.get(item_id)

        if not item:
            self.queuedTranscriptItems[item_id] = {"transcript": transcript}
            return {"item": None, "delta": None}
        else:
            item["content"][content_index]["transcript"] = transcript
            item["formatted"]["transcript"] = transcript
            return {"item": item, "delta": {"transcript": transcript}}

    def input_audio_buffer_speech_started(self, event):
        item_id = event["item_id"]
        audio_start_ms = event["audio_start_ms"]
        self.queuedSpeechItems[item_id] = {"audio_start_ms": audio_start_ms}
        return {"item": None, "delta": None}

    def input_audio_buffer_speech_stopped(self, event, inputAudioBuffer):
        item_id = event["item_id"]
        audio_end_ms = event["audio_end_ms"]
        speech = self.queuedSpeechItems.get(item_id)
        speech["audio_end_ms"] = audio_end_ms

        if inputAudioBuffer:
            startIndex = (speech["audio_start_ms"] * self.defaultFrequency) // 1000
            endIndex = (speech["audio_end_ms"] * self.defaultFrequency) // 1000
            speech["audio"] = inputAudioBuffer[startIndex:endIndex]

        return {"item": None, "delta": None}

    def response_created(self, event):
        response = event["response"]
        if response["id"] not in self.responseLookup:
            self.responseLookup[response["id"]] = response
            self.responses.append(response)
        return {"item": None, "delta": None}

    def response_output_item_added(self, event):
        response_id = event["response_id"]
        item = event["item"]
        response = self.responseLookup.get(response_id)
        if not response:
            raise ValueError(
                f'response.output_item.added: Response "{response_id}" not found'
            )

        response["output"].append(item["id"])
        return {"item": None, "delta": None}

    def response_output_item_done(self, event):
        item = event["item"]
        if not item:
            raise ValueError('response.output_item.done: Missing "item"')
        foundItem = self.itemLookup.get(item["id"])
        if not foundItem:
            raise ValueError(
                f'response.output_item.done: Item "{item["id"]}" not found'
            )

        foundItem["status"] = item["status"]
        return {"item": foundItem, "delta": None}

    def response_content_part_added(self, event):
        item_id = event["item_id"]
        part = event["part"]
        item = self.itemLookup.get(item_id)
        if not item:
            raise ValueError(f'response.content_part.added: Item "{item_id}" not found')

        item["content"].append(part)
        return {"item": item, "delta": None}

    def response_audio_transcript_delta(self, event):
        item_id = event["item_id"]
        content_index = event["content_index"]
        delta = event["delta"]
        item = self.itemLookup.get(item_id)
        if not item:
            raise ValueError(
                f'response.audio_transcript.delta: Item "{item_id}" not found'
            )

        item["content"][content_index]["transcript"] += delta
        item["formatted"]["transcript"] += delta
        return {"item": item, "delta": {"transcript": delta}}

    def response_audio_delta(self, event):
        item_id = event["item_id"]
        content_index = event["content_index"]
        delta = event["delta"]
        item = self.itemLookup.get(item_id)
        if not item:
            raise ValueError(f'response.audio.delta: Item "{item_id}" not found')

        item["formatted"]["audio"].extend(delta)
        return {"item": item, "delta": {"audio": delta}}

    def response_function_call_arguments_delta(self, event):
        item_id = event["item_id"]
        delta = event["delta"]
        item = self.itemLookup.get(item_id)
        if not item:
            raise ValueError(
                f'response.function_call_arguments.delta: Item "{item_id}" not found'
            )

        item["arguments"] += delta
        item["formatted"]["tool"]["arguments"] += delta
        return {"item": item, "delta": {"arguments": delta}}


create_input_audio = {
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_audio", "audio": base64AudioData}],
    },
}


async def connect_to_server():
    async with websockets.connect(url, extra_headers=headers) as ws:
        processor = EventProcessors()
        print("Connected to server.")

        # Sending a message to the server
        request = create_input_audio

        await ws.send(json.dumps(request))
        await ws.send(json.dumps({"type": "response.create"}))

        # Handling incoming messages
        async for message in ws:
            event = json.loads(message)
            with open(f"/tmp/{time.time()}.json", "w") as f:
                json.dump(event, fp=f, indent=4)
            match event["type"]:
                case "response.created":
                    processor.response_created(event)
                case "conversation.item.created":
                    processor.conversation_item_created(event)
                case "response.audio.delta":
                    processor.response_audio_delta(event)
                case "response.audio_transcript.delta":
                    r = processor.response_audio_transcript_delta(event)
                case "response.content_part.added":
                    processor.response_content_part_added(event)
                case "response.created":
                    processor.response_created(event)
                case "response.output_item.added":
                    processor.response_output_item_added(event)
                case "response.done":
                    for item in processor.items:
                        if formatted := item.get("formatted"):
                            if audio := formatted.get("audio"):
                                base64_to_audio("".join(audio))
                            if transcript := formatted.get("transcript"):
                                print(transcript)
                case "session.created":
                    print(event)
                case (
                    "response.output_item.done"
                    | "response.content_part.done"
                    | "session.created"
                    | "response.audio_transcript.done"
                    | "response.audio.done"
                ):
                    print(f"Unhandled event {event['type']}")


# Running the async function
asyncio.run(connect_to_server())
