from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

from ..web_configs import WEB_CONFIGS
from .asr_worker import load_asr_model, process_asr

# router = APIRouter(
#     prefix="/asr",
#     tags=["asr"],
#     responses={404: {"description": "Not found"}},
# )

app = FastAPI()

if WEB_CONFIGS.ENABLE_ASR:
    ASR_HANDLER = load_asr_model()
else:
    ASR_HANDLER = None


class ASRItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    wav_path: str  # wav 文件路径


@app.get("/asr")
async def get_asr(asr_item: ASRItem):
    # 语音转文字
    result = ""
    status = "success"
    if ASR_HANDLER is None:
        result = "ASR not enable in sever"
        status = "fail"
        logger.error(f"ASR not enable...")
    else:
        result = process_asr(ASR_HANDLER, asr_item.wav_path)
    logger.info(f"ASR res for id {asr_item.request_id}, res = {result}")

    return {"user_id": asr_item.user_id, "request_id": asr_item.request_id, "status": status, "result": result}
