from pydantic import BaseModel


class InputAudioBufferAppend(BaseModel):
    audio: str
    type: str = "input_audio_buffer.append"


class InputAudioBufferCommit(BaseModel):
    type: str = "input_audio_buffer.commit"
