from pydantic import BaseModel
from .base import Session


class SessionCreated(BaseModel):
    session: Session


def session_created_handler(event: str) -> SessionCreated:
    return SessionCreated.model_validate(event)
