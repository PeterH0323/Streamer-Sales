#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   streamer_info.py
@Time    :   2024/08/10
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   主播管理信息页面接口
"""

from typing import Tuple
import uuid
from pathlib import Path

import requests
from fastapi import APIRouter, Depends
from loguru import logger

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..database.streamer_info_db import create_or_update_db_streamer_by_id, delete_streamer_id, get_db_streamer_info
from ..models.streamer_info_model import StreamerInfo
from ..utils import ResultCode, make_poster_by_video_first_frame, make_return_data
from .users import get_current_user_info

router = APIRouter(
    prefix="/streamer",
    tags=["streamer"],
    responses={404: {"description": "Not found"}},
)


async def gen_digital_human(user_id, streamer_id: int, new_streamer_info: StreamerInfo) -> Tuple[str, str]:
    """生成数字人视频

    Args:
        user_id (int): 用户 ID
        streamer_id (int): 主播 ID
        new_streamer_info (StreamerInfo): 新的主播信息

    Returns:
        str: 数字人视频地址
        str: 数字人头像/海报地址
    """

    streamer_info_db = await get_db_streamer_info(user_id, streamer_id)
    streamer_info_db = streamer_info_db[0]

    new_base_mp4_path = new_streamer_info.base_mp4_path.replace(API_CONFIG.REQUEST_FILES_URL, "")
    if streamer_info_db.base_mp4_path.replace(API_CONFIG.REQUEST_FILES_URL, "") == new_base_mp4_path:
        # 数字人视频没更新，跳过
        return streamer_info_db.base_mp4_path, streamer_info_db.poster_image

    # 调取接口生成进行数字人预处理

    # new_streamer_info.base_mp4_path 是 服务器地址，需要进行转换
    video_local_dir = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(
        WEB_CONFIGS.STREAMER_FILE_DIR, WEB_CONFIGS.STREAMER_INFO_FILES_DIR
    )

    digital_human_gen_info = {
        "user_id": str(user_id),
        "request_id": str(uuid.uuid1()),
        "streamer_id": str(new_streamer_info.streamer_id),
        "video_path": str(video_local_dir.joinpath(Path(new_streamer_info.base_mp4_path).name)),
    }
    logger.info(f"Getting digital human preprocessing: {new_streamer_info.streamer_id}")
    _ = requests.post(API_CONFIG.DIGITAL_HUMAN_PREPROCESS_URL, json=digital_human_gen_info)

    # 根据视频第一帧生成头图
    poster_save_name = Path(new_streamer_info.base_mp4_path).stem + ".png"
    make_poster_by_video_first_frame(str(video_local_dir.joinpath(Path(new_streamer_info.base_mp4_path).name)), poster_save_name)

    # 生成头图服务器地址
    poster_server_url = str(Path(new_streamer_info.base_mp4_path).parent.joinpath(poster_save_name))
    if "http://" not in poster_server_url and "http:/" in poster_server_url:
        poster_server_url = poster_server_url.replace("http:/", "http://")

    return new_streamer_info.base_mp4_path, poster_server_url


@router.get("/list", summary="获取所有主播信息接口，用于用户进行主播的选择")
async def get_streamer_info_api(user_id: int = Depends(get_current_user_info)):
    """获取所有主播信息，用于用户进行主播的选择"""
    streamer_list = await get_db_streamer_info(user_id)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_list)


@router.get("/info/{streamerId}", summary="用于获取特定主播的信息接口")
async def get_streamer_info_api(streamerId: int, user_id: int = Depends(get_current_user_info)):
    """用于获取特定主播的信息"""

    streamer_list = await get_db_streamer_info(user_id, streamerId)
    if len(streamer_list) == 1:
        streamer_list = streamer_list[0]

    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_list)


@router.post("/create", summary="新增主播信息接口")
async def create_streamer_info_api(streamerItem: StreamerInfo, user_id: int = Depends(get_current_user_info)):
    """新增主播信息"""
    streamer_info = streamerItem
    streamer_info.user_id = user_id
    streamer_info.streamer_id = None

    poster_image = streamer_info.poster_image
    base_mp4_path = streamer_info.base_mp4_path

    streamer_info.poster_image = ""
    streamer_info.base_mp4_path = ""

    # 更新数据库，才能拿到 stream_id
    streamer_id = create_or_update_db_streamer_by_id(0, streamer_info, user_id)

    streamer_info.poster_image = poster_image
    streamer_info.base_mp4_path = base_mp4_path
    streamer_info.streamer_id = streamer_id

    # 数字人视频对其进行初始化，同时生成头图
    video_info = await gen_digital_human(user_id, streamer_id, streamer_info)

    streamer_info.base_mp4_path = video_info[0]
    streamer_info.poster_image = video_info[1]
    streamer_info.avatar = video_info[1]

    create_or_update_db_streamer_by_id(streamer_id, streamer_info, user_id)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_id)


@router.put("/edit/{streamer_id}", summary="修改主播信息接口")
async def edit_streamer_info_api(streamer_id: int, streamer_info: StreamerInfo, user_id: int = Depends(get_current_user_info)):
    """修改主播信息"""

    # 如果更新了数字人视频对其进行初始化，同时生成头图
    video_info = await gen_digital_human(user_id, streamer_id, streamer_info)

    streamer_info.base_mp4_path = video_info[0]
    streamer_info.poster_image = video_info[1]
    streamer_info.avatar = video_info[1]

    # 更新数据库
    create_or_update_db_streamer_by_id(streamer_id, streamer_info, user_id)

    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_id)


@router.delete("/delete/{streamerId}", summary="删除主播接口")
async def upload_product_api(streamerId: int, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_streamer_id(streamerId, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")
