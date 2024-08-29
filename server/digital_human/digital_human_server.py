from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from loguru import logger
from pydantic import BaseModel


from .modules.digital_human_worker import gen_digital_human_video_app, preprocess_digital_human_app


app = FastAPI()


class DigitalHumanItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    streamer_id: str  # 数字人 ID
    tts_path: str = ""  # 文本
    chunk_id: int = 0  # 句子 ID


class DigitalHumanPreprocessItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    streamer_id: str  # 数字人 ID
    video_path: str  # 数字人视频


@app.post("/digital_human/gen")
async def get_digital_human(dg_item: DigitalHumanItem):
    """生成数字人视频"""
    save_tag = (
        dg_item.request_id + ".mp4" if dg_item.chunk_id == 0 else dg_item.request_id + f"-{str(dg_item.chunk_id).zfill(8)}.mp4"
    )
    mp4_path = await gen_digital_human_video_app(dg_item.streamer_id, dg_item.tts_path, save_tag)
    logger.info(f"digital human mp4 path = {mp4_path}")
    return {"user_id": dg_item.user_id, "request_id": dg_item.request_id, "digital_human_mp4_path": mp4_path}


@app.post("/digital_human/preprocess")
async def preprocess_digital_human(preprocess_item: DigitalHumanPreprocessItem):
    """数字人视频预处理，用于新增数字人"""

    _ = await preprocess_digital_human_app(str(preprocess_item.streamer_id), preprocess_item.video_path)

    logger.info(f"digital human process for {preprocess_item.streamer_id} done")
    return {"user_id": preprocess_item.user_id, "request_id": preprocess_item.request_id}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """调 API 入参错误的回调接口

    Args:
        request (_type_): _description_
        exc (_type_): _description_

    Returns:
        _type_: _description_
    """
    logger.info(request)
    logger.info(exc)
    return PlainTextResponse(str(exc), status_code=400)


@app.get("/digital_human/check")
async def check_server():
    return {"message": "server enabled"}
