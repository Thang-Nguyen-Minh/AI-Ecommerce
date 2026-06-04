import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db, graph
from ..auth import CurrentUser, get_current_user
from ..config import VALID_ACTIONS

router = APIRouter()


class EventIn(BaseModel):
    product_id: int
    action: str


@router.post("/events", status_code=201)
def create_event(body: EventIn, user: CurrentUser = Depends(get_current_user)):
    # BR: chỉ nhận view/click/add_to_cart (TC-02)
    if body.action not in VALID_ACTIONS:
        raise HTTPException(status_code=400, detail="action phải là view/click/add_to_cart")

    ts = time.time()
    db.add_event(user.id, body.product_id, body.action, ts)        # behavior store
    graph.record_event(user.id, body.product_id, body.action)      # cạnh live (bỏ qua nếu Neo4j chết)
    return {"status": "recorded", "user_id": user.id, "product_id": body.product_id, "action": body.action}
