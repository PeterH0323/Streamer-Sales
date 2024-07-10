from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel


from utils.digital_human.digital_human_worker import gen_digital_human_video_in_spinner


app = FastAPI()


class DigitalHumanItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    tts_path: str  # 文本
    chunk_id: int  # 句子 ID


@app.get("/digital_human")
async def get_digital_human(dg_item: DigitalHumanItem):
    # 语音转文字
    save_tag = dg_item.request_id + ".mp4" if dg_item.chunk_id == 0 else dg_item.request_id + f"-{str(dg_item.chunk_id).zfill(8)}.mp4"
    mp4_path = await gen_digital_human_video_in_spinner(dg_item.tts_path, save_tag)
    logger.info(f"digital human mp4 path = {mp4_path}")
    return {"user_id": dg_item.user_id, "request_id": dg_item.request_id, "digital_human_mp4_path": mp4_path}
