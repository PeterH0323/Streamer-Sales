import requests
from loguru import logger

from ..web_configs import API_CONFIG, WEB_CONFIGS


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
