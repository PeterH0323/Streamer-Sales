from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel


from .modules.tts_worker import gen_tts_wav_app


app = FastAPI()


class TextToSpeechItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    sentence: str  # 文本
    chunk_id: int  # 句子 ID


@app.post("/tts")
async def get_tts(tts_item: TextToSpeechItem):
    # 语音转文字
    wav_path = await gen_tts_wav_app(tts_item.sentence, tts_item.request_id + f"-{str(tts_item.chunk_id).zfill(8)}.wav")
    logger.info(f"tts wav path = {wav_path}")
    return {"user_id": tts_item.user_id, "request_id": tts_item.request_id, "wav_path": wav_path}


@app.get("/tts/check")
async def check_server():
    return {"message": "server enabled"}
