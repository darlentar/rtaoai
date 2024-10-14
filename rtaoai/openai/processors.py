from collections.abc import Awaitable, Callable
from .events import (
    conversation_item_created_event_handler,
    ConversationItem,
    AudioDelta,
    AudioDone,
    AudioTranscriptDelta,
    AudioTranscriptDone,
    OutputItemDone,
    InputAudioTranscriptionCompleted,
)


class EventHandler:
    def __init__(
        self,
        on_item_created: Callable[[ConversationItem], Awaitable[None]] | None = None,
        on_transcript_delta: Callable[[AudioTranscriptDelta], Awaitable[None]]
        | None = None,
        on_transcript_delta_done: Callable[[AudioTranscriptDone], Awaitable[None]]
        | None = None,
        on_audio_delta: Callable[[AudioDelta], Awaitable[None]] | None = None,
        on_audio_done: Callable[[AudioDone], Awaitable[None]] | None = None,
        on_output_item_done: Callable[[OutputItemDone], Awaitable[None]] | None = None,
        on_input_audio_transcription_completed: Callable[
            [InputAudioTranscriptionCompleted], Awaitable[None]
        ]
        | None = None,
        on_event: Callable[[str], Awaitable[None]] | None = None,
    ):
        self.on_item_created = on_item_created
        self.on_transcript_delta = on_transcript_delta
        self.on_transcript_delta_done = on_transcript_delta_done
        self.on_audio_delta = on_audio_delta
        self.on_audio_done = on_audio_done
        self.on_output_item_done = on_output_item_done
        self.on_input_audio_transcription_completed = (
            on_input_audio_transcription_completed
        )
        self.on_event = on_event

    async def handle_event(self, event):
        handlers = {
            "conversation.item.created": (
                conversation_item_created_event_handler,
                self.on_item_created,
            ),
            "response.audio_transcript.delta": (
                AudioTranscriptDelta.model_validate,
                self.on_transcript_delta,
            ),
            "response.audio_transcript.done": (
                AudioTranscriptDone.model_validate,
                self.on_transcript_delta_done,
            ),
            "response.audio.delta": (
                AudioDelta.model_validate,
                self.on_audio_delta,
            ),
            "response.audio.done": (
                AudioDone.model_validate,
                self.on_audio_done,
            ),
            "response.output_item.done": (
                OutputItemDone.model_validate,
                self.on_output_item_done,
            ),
            "conversation.item.input_audio_transcription.completed": (
                InputAudioTranscriptionCompleted.model_validate,
                self.on_input_audio_transcription_completed,
            ),
        }
        (create_model_handler, callback) = handlers.get(event["type"], (None, None))
        if callback:
            item = create_model_handler(event)
            await callback(item)
        if self.on_event:
            await self.on_event(event)


class FakeOpenAI:
    def __init__(
        self,
        events: list[str],
        event_handler: EventHandler,
    ):
        self.events = events
        self.event_handler = event_handler

    async def run(self):
        for event in self.events:
            await self.event_handler.handle_event(event)
