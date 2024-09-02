#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   digital_human.py
@Time    :   2024/09/02
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   数字人接口
"""


from pathlib import Path
import uuid
import requests
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..utils import ResultCode, make_return_data

router = APIRouter(
    prefix="/digital-human",
    tags=["digital-human"],
    responses={404: {"description": "Not found"}},
)


class GenDigitalHumanVideoItem(BaseModel):
    streamerId: int
    salesDoc: str


async def gen_tts_and_digital_human_video_app(streamer_id: int, sales_doc: str):
    logger.info(sales_doc)

    request_id = str(uuid.uuid1())
    sentence_id = 1  # 直接推理，所以设置成 1
    user_id = "123"

    # 生成 TTS wav
    tts_json = {
        "user_id": user_id,
        "request_id": request_id,
        "sentence": sales_doc,
        "chunk_id": sentence_id,
        # "wav_save_name": chat_item.request_id + f"{str(sentence_id).zfill(8)}.wav",
    }
    tts_save_path = Path(WEB_CONFIGS.TTS_WAV_GEN_PATH, request_id + f"-{str(1).zfill(8)}.wav")
    logger.info(f"waiting for wav generating done: {tts_save_path}")
    _ = requests.post(API_CONFIG.TTS_URL, json=tts_json)

    # 生成数字人视频
    digital_human_gen_info = {
        "user_id": user_id,
        "request_id": request_id,
        "chunk_id": 0,
        "tts_path": str(tts_save_path),
        "streamer_id": str(streamer_id),
    }
    video_path = Path(WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_OUTPUT_PATH).joinpath(request_id + ".mp4")
    logger.info(f"Generating digital human: {video_path}")
    _ = requests.post(API_CONFIG.DIGITAL_HUMAN_URL, json=digital_human_gen_info)

    # 删除过程文件
    tts_save_path.unlink()

    server_video_path = f"{API_CONFIG.REQUEST_FILES_URL}/{WEB_CONFIGS.STREAMER_FILE_DIR}/vid_output/{request_id}.mp4"
    logger.info(server_video_path)

    return server_video_path


@router.post("/gen")
async def get_digital_human_according_doc_api(gen_item: GenDigitalHumanVideoItem):
    """根据口播文案生成数字人介绍视频

    Args:
        gen_item (GenDigitalHumanVideoItem): _description_

    """
    server_video_path = await gen_tts_and_digital_human_video_app(gen_item.streamerId, gen_item.salesDoc)

    return make_return_data(True, ResultCode.SUCCESS, "成功", server_video_path)
