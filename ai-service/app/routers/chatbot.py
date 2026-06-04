from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import CurrentUser, get_current_user
from ..services import chatbot_service

router = APIRouter()


class ChatIn(BaseModel):
    message: str = ""


@router.post("/chatbot")
def chatbot(body: ChatIn, user: CurrentUser = Depends(get_current_user)):
    return chatbot_service.answer(body.message, user.id)
