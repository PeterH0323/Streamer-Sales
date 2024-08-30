#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   streamer_info_model.py
@Time    :   2024/08/30
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   主播信息数据结构
"""

from typing import List

from pydantic import BaseModel


class StreamerInfoItem(BaseModel):
    user_id: int = 0

    id: int = 0
    name: str = ""
    character: List[str] = None
    value: str = ""
    avater: str = ""  # 头像

    tts_weight_tag: str = ""  # 艾丝妲
    tts_tag: str = ""
    tts_reference_sentence: str = ""
    tts_reference_audio: str = ""

    poster_image: str = ""
    base_mp4_path: str = ""

    delete: bool = False


class StreamerInfo(BaseModel):
    # 主播信息
    streamerId: int
