from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    requires_confirmation: bool = False
    confirmation_data: Optional[Dict] = None

class ConfirmationRequest(BaseModel):
    session_id: str
    confirmed: bool
    confirmation_data: Optional[Dict] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str