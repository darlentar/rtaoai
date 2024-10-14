from pydantic import BaseModel


class AudioTranscriptDelta(BaseModel):
    item_id: str
    delta: str


class AudioTranscriptDone(BaseModel):
    item_id: str
    transcript: str
