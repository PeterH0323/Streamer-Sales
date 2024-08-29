from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from loguru import logger
from pydantic import BaseModel

from ..utils import ResultCode, make_return_data

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


class TokenItem(BaseModel):
    access_token: str
    token_type: str


class UserItem(BaseModel):
    username: str  # User 识别号，用于区分不用的用户调用
    password: str  # 请求 ID，用于生成 TTS & 数字人


# Token 秘钥
SECURITY_KEY = "zljvcliwehrlnsdkjwfpqwiefjpwemf"


def check_username(username, password):
    return username


@router.post("/login")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
async def login(form_data: UserItem):

    username = check_username(form_data.username, form_data.password)

    if not username:
        raise HTTPException(status_code=404, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})

    # 过期时间
    token_expires = datetime.now(timezone.utc) + timedelta(days=7)

    # token 生成包含内容，记录 IP 的原因是防止被其他人拿到用户的 token 进行假冒访问
    token_data = {
        "username": username,
        "exp": int(token_expires.timestamp()),
        "ip": "127.0.0.1",
        "login_time": int(datetime.now(timezone.utc).timestamp()),
    }
    logger.info(f"token_data = {token_data}")

    # 生成 token
    token = jwt.encode(token_data, SECURITY_KEY, algorithm="HS256")

    # 返回
    content = TokenItem(access_token=token, token_type="bearer")
    logger.info(f"Got token info = {content}")
    return make_return_data(True, ResultCode.SUCCESS, "成功", content)
