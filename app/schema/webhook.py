from pydantic import BaseModel
from typing import Optional, Dict, Any

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
    from_: Optional[User] = None
    chat: Chat
    date: int
    text: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda field_name: 'from' if field_name == 'from_' else field_name

class Update(BaseModel):
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    callback_query: Optional[Dict[str, Any]] = None

class WebhookResponse(BaseModel):
    status: str
    message: str
