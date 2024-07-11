from typing import Dict, List
import requests
from loguru import logger
from pydantic import BaseModel

from ..web_configs import API_CONFIG, WEB_CONFIGS


class ChatGenConfig(BaseModel):
    # LLM 推理配置
    top_p: float = 0.8
    temperature: float = 0.7
    repetition_penalty: float = 1.005


class ProductInfo(BaseModel):
    name: str
    heighlights: str
    introduce: str  # 生成商品文案 prompt

    image_path: str
    departure_place: str
    delivery_company_name: str


class PluginsInfo(BaseModel):
    rag: bool = True
    agent: bool = True
    tts: bool = True
    digital_human: bool = True


class ChatItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    prompt: List[Dict[str, str]]  # 本次的 prompt
    product_info: ProductInfo  # 商品信息
    plugins: PluginsInfo = PluginsInfo()  # 插件信息
    chat_config: ChatGenConfig = ChatGenConfig()


class UploadProductItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    name: str
    heightlight: str
    image_path: str
    instruction_path: str
    departure_place: str
    delivery_company: str


class ServerPluginsInfo:

    def __init__(self) -> None:
        self.tts_server_enabled = self.check_server(API_CONFIG.TTS_URL + "/check")
        self.digital_human_server_enabled = self.check_server(API_CONFIG.DIGITAL_HUMAN_URL + "/check")
        self.asr_server_enabled = self.check_server(API_CONFIG.ASR_URL + "/check")

        if WEB_CONFIGS.AGENT_DELIVERY_TIME_API_KEY is None or WEB_CONFIGS.AGENT_WEATHER_API_KEY is None:
            self.agent_enabled = False
        else:
            self.agent_enabled = True

        logger.info(
            "self check plugins info : \n"
            f"tts {self.tts_server_enabled}\n"
            f"digital hunam {self.digital_human_server_enabled}\n"
            f"asr {self.asr_server_enabled}\n"
            f"agent {self.agent_enabled}\n"
        )

    def check_server(self, url):
        res = requests.get(url)
        if res.status_code == 200:
            return True
        else:
            return False


SERVER_PLUGINS_INFO = ServerPluginsInfo()
