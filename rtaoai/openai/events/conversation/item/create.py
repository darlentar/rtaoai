from pydantic import BaseModel
from .base import ConversationItem, ConversationItemContent
from rtaoai.utils import audio_to_item_create_event


class ConversationItemCreate(BaseModel):
    type: str = "conversation.item.create"
    item: ConversationItem


def make_conversation_item_create_event(audio: bytes) -> ConversationItemCreate:
    return ConversationItemCreate(
        item=ConversationItem(
            content=[ConversationItemContent(audio=audio_to_item_create_event(audio))],
        ),
    )
