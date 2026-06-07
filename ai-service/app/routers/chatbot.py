from fastapi import APIRouter, Header
from pydantic import BaseModel

from ..auth import decode_jwt
from ..services import chatbot_service

router = APIRouter()


class ChatIn(BaseModel):
    message: str = ""


@router.post("/chatbot")
def chatbot(body: ChatIn, authorization: str = Header(default="")):
    user_id = 0
    if authorization.startswith("Bearer "):
        try:
            payload = decode_jwt(authorization[7:].strip())
            user_id = payload.get("user_id", 0) or 0
        except Exception:
            pass
    return chatbot_service.answer(body.message, user_id)
