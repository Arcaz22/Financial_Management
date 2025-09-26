from pydantic import BaseModel, Field
from typing import Optional, Any, List


class PhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class Chat(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    type: str


class Message(BaseModel):
    message_id: int
    from_: Optional[User] = Field(None, alias="from")
    chat: Chat
    date: int
    text: Optional[str] = None
    photo: Optional[List[PhotoSize]] = None
    document: Optional[Any] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda field_name: (
            "from" if field_name == "from_" else field_name
        )


class CallbackQuery(BaseModel):
    id: str
    from_: User = Field(..., alias="from")
    message: Optional[Message] = None
    inline_message_id: Optional[str] = None
    chat_instance: str
    data: Optional[str] = None

    class Config:
        populate_by_name = True


class Update(BaseModel):
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None


class WebhookResponse(BaseModel):
    status: str
    message: str
