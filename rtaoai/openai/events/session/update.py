from typing import Callable
from .base import (
    Session,
    Tools,
    SessionParameters,
    SessionParametersProperties,
)
from pydantic import BaseModel
import inspect
from typing import Literal, get_origin, get_args


class InputAudioTranscription(BaseModel):
    model: str = "whisper-1"


class SessionUpdatePayload(Session):
    input_audio_transcription: InputAudioTranscription | None = None


class SessionUpdate(BaseModel):
    type: str
    session: SessionUpdatePayload


def make_session_update_event(tools=list[Callable]) -> SessionUpdate:
    session_tools = []
    for tool in tools:
        description = tool.__doc__
        name = tool.__name__
        properties = {}
        required = []
        for p in inspect.signature(tool).parameters.values():
            if p.annotation is str:
                property = SessionParametersProperties(type="string")
            elif p.annotation is int:
                property = SessionParametersProperties(type="integer")
            elif get_origin(p.annotation) is Literal:
                property = SessionParametersProperties(
                    type="string",
                    enum=list(get_args(p.annotation)),
                )
            else:
                raise NotImplementedError(f"annotation: {p.annotation}")
            properties[p.name] = property
            # TODO: Support optional args
            required.append(p.name)

        parameters = SessionParameters(
            type="object",
            properties=properties,
            required=required,
        )
        session_tools.append(
            Tools(
                type="function",
                name=name,
                description=description,
                parameters=parameters,
            )
        )
    return SessionUpdate(
        type="session.update",
        session=SessionUpdatePayload(
            tools=session_tools,
            input_audio_transcription=InputAudioTranscription(model="whisper-1"),
            turn_detection=None,
            voice="alloy",
        ),
    )
