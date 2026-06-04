from fastapi import APIRouter, Depends

from ..auth import CurrentUser, get_current_user
from ..services import recommend_service

router = APIRouter()


@router.get("/recommend")
def recommend(n: int = 5, user: CurrentUser = Depends(get_current_user)):
    n = max(1, min(n, 50))
    items = recommend_service.recommend(user.id, n)
    return {"items": items}
