#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   queue_thread.py
@Time    :   2024/09/02
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   队列调取相关逻辑(半废弃状态)
"""


from loguru import logger
import requests
import multiprocessing

from ..web_configs import API_CONFIG
from .server_info import SERVER_PLUGINS_INFO


def process_tts(tts_text_queue):

    while True:
        try:
            text_chunk = tts_text_queue.get(block=True, timeout=1)
        except Exception as e:
            # logger.info(f"### {e}")
            continue
        logger.info(f"Get tts quene: {type(text_chunk)} , {text_chunk}")
        res = requests.post(API_CONFIG.TTS_URL, json=text_chunk)

        # # tts 推理成功，放入数字人队列进行推理
        # res_json = res.json()
        # tts_request_dict = {
        #     "user_id": "123",
        #     "request_id": text_chunk["request_id"],
        #     "chunk_id": text_chunk["chunk_id"],
        #     "tts_path": res_json["wav_path"],
        # }

        # DIGITAL_HUMAN_QUENE.put(tts_request_dict)

        logger.info(f"tts res = {res}")


def process_digital_human(digital_human_queue):

    while True:
        try:
            text_chunk = digital_human_queue.get(block=True, timeout=1)
        except Exception as e:
            # logger.info(f"### {e}")
            continue
        logger.info(f"Get digital human quene: {type(text_chunk)} , {text_chunk}")
        res = requests.post(API_CONFIG.DIGITAL_HUMAN_URL, json=text_chunk)
        logger.info(f"digital human res = {res}")


if SERVER_PLUGINS_INFO.tts_server_enabled:
    TTS_TEXT_QUENE = multiprocessing.Queue(maxsize=100)
    tts_thread = multiprocessing.Process(target=process_tts, args=(TTS_TEXT_QUENE,), name="tts_processer")
    tts_thread.start()
else:
    TTS_TEXT_QUENE = None

if SERVER_PLUGINS_INFO.digital_human_server_enabled:
    DIGITAL_HUMAN_QUENE = multiprocessing.Queue(maxsize=100)
    digital_human_thread = multiprocessing.Process(
        target=process_digital_human, args=(DIGITAL_HUMAN_QUENE,), name="digital_human_processer"
    )
    digital_human_thread.start()
else:
    DIGITAL_HUMAN_QUENE = None
