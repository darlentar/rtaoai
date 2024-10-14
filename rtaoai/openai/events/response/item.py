from pydantic import BaseModel


class OutputItem(BaseModel):
    id: str
    # TODO: Handle offer output than function
    name: str | None = None
    arguments: str | None = None
    call_id: str | None = None


class OutputItemDone(BaseModel):
    item: OutputItem
