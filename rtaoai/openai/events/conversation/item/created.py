from pydantic import BaseModel
from .base import ConversationItem


class ConversationItemCreated(BaseModel):
    event_id: str
    item: ConversationItem


def conversation_item_created_event_handler(event: str) -> ConversationItemCreated:
    return ConversationItemCreated.model_validate(event)
