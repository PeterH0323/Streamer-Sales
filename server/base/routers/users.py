from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

class UserItem(BaseModel):
    username: str  # User 识别号，用于区分不用的用户调用
    password: str  # 请求 ID，用于生成 TTS & 数字人


@router.post("/login")
async def user_login(user_item: UserItem):
    logger.info(f"Got user info = {user_item}")
    return {"success": True, "message": "success", "state": 1, "content": {"access_token": "46541354846131"}}
