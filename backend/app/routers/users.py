from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserOut
from app.services.i18n import get_message

router = APIRouter(prefix="/api/users", tags=["用户"])


class UpdateLanguageRequest(BaseModel):
    language: str


@router.patch("/preferences")
async def update_language_preference(
    data: UpdateLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """更新当前用户的语言偏好。

    接受 JSON 请求体 {"language": "zh"} 或 {"language": "en"}。
    """
    if data.language not in ("zh", "en"):
        raise HTTPException(
            status_code=400,
            detail=get_message("INVALID_LANGUAGE", current_user.language),
        )

    current_user.language = data.language
    db.commit()
    db.refresh(current_user)

    return {
        "code": 200,
        "message": get_message("LANGUAGE_UPDATED", data.language),
        "data": {
            "user": UserOut.model_validate(current_user),
        },
    }
