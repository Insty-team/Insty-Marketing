from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, User
from app.core.db import get_db
from app.services.user.user_data_purge_service import UserDataPurgeService
from app.schemas.user import DeleteAIDataResponse
from app.docs.deco import op


router = APIRouter(prefix="/users", tags=["Users"])

@op("ai_user_read_me", tags=["users"])
@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
    }


@op("ai_user_delete_my_ai_data", tags=["users"])
@router.delete("/me/ai-data", response_model=DeleteAIDataResponse)
def delete_my_ai_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserDataPurgeService(db)
    try:
        deleted_counts = service.delete_all_ai_data_for_user(user_id=current_user.id)
        return {"success": True, "deleted_counts": deleted_counts}
    except Exception:
        return {"success": False, "deleted_counts": {}}