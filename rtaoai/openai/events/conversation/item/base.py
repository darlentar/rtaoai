from pydantic import BaseModel


# TODO: Support other types than audio
class ConversationItemContent(BaseModel):
    type: str = "input_audio"
    audio: str | None = None
    transcript: str | None = None


class ConversationItem(BaseModel):
    id: str | None = None  # TODO: Should make a separate type
    type: str = "message"
    role: str = "user"
    content: list[ConversationItemContent] | None = None


class InputAudioTranscriptionCompleted(BaseModel):
    item_id: str
    transcript: str
