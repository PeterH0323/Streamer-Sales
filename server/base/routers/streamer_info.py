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

import uuid
from pathlib import Path

import requests
from fastapi import APIRouter, Depends
from loguru import logger

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..database.streamer_info_db import get_max_streamer_id, get_streamers_info, save_streamer_info
from ..models.streamer_info_model import StreamerInfo, StreamerInfoItem
from ..utils import ResultCode, delete_item_by_id, make_poster_by_video_first_frame, make_return_data
from .users import get_current_user_info

router = APIRouter(
    prefix="/streamer",
    tags=["streamer"],
    responses={404: {"description": "Not found"}},
)


@router.post("/list", summary="获取所有主播信息接口，用于用户进行主播的选择")
async def get_streamer_info_api(user_id: int = Depends(get_current_user_info)):
    """获取所有主播信息，用于用户进行主播的选择"""
    streamer_list = await get_streamers_info(user_id)

    logger.info(streamer_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_list)


@router.get("/info", summary="用于获取特定主播的信息接口")
async def get_streamer_info_api(streamerId: int, user_id: int = Depends(get_current_user_info)):
    """用于获取特定主播的信息"""

    pick_info = []
    if streamerId > 0:
        pick_info = await get_streamers_info(user_id, streamerId)

    if len(pick_info) == 0:
        # 没找到 or 主播 ID = 0，回复一个空的
        new_info = StreamerInfoItem(character=[""])
        pick_info = [dict(new_info)]

    logger.info(pick_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", pick_info)


@router.post("/edit", summary="新增 or 修改主播信息接口")
async def edit_streamer_info_api(streamer_info: StreamerInfoItem, user_id: int = Depends(get_current_user_info)):
    """新增 or 修改主播信息"""

    all_streamer_info_list = await get_streamers_info(user_id)
    max_streamer_id = get_max_streamer_id()

    update_index = -1
    for idx, item in enumerate(all_streamer_info_list):

        if item["id"] == streamer_info.id:
            update_index = idx
            break

    need_to_preprocess_digital_human = False
    if update_index >= 0:
        # 修改
        logger.info("已有 ID，编辑模式，修改对应配置")

        if all_streamer_info_list[update_index]["base_mp4_path"] != streamer_info.base_mp4_path:
            need_to_preprocess_digital_human = True

    else:
        logger.info("新 ID，新增模式，新增对应配置")
        streamer_info.id = max_streamer_id + 1  #  主播 ID
        streamer_info.user_id = user_id
        need_to_preprocess_digital_human = True
        update_index += 1

    if need_to_preprocess_digital_human:
        # 调取接口生成进行数字人预处理

        # streamer_info.base_mp4_path 是 服务器地址，需要进行转换
        video_local_dir = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(
            WEB_CONFIGS.STREAMER_FILE_DIR, WEB_CONFIGS.STREAMER_INFO_FILES_DIR
        )

        digital_human_gen_info = {
            "user_id": "123",
            "request_id": str(uuid.uuid1()),
            "streamer_id": str(streamer_info.id),
            "video_path": str(video_local_dir.joinpath(Path(streamer_info.base_mp4_path).name)),
        }
        logger.info(f"Getting digital human preprocessing: {streamer_info.id}")
        _ = requests.post(API_CONFIG.DIGITAL_HUMAN_PREPROCESS_URL, json=digital_human_gen_info)

        poster_save_name = Path(streamer_info.base_mp4_path).stem + ".png"
        make_poster_by_video_first_frame(str(video_local_dir.joinpath(Path(streamer_info.base_mp4_path).name)), poster_save_name)
        all_streamer_info_list[update_index]["poster_image"] = str(
            Path(streamer_info.base_mp4_path).parent.joinpath(poster_save_name)
        )
        streamer_info.poster_image = all_streamer_info_list[update_index]["poster_image"]

    logger.info(streamer_info)
    save_streamer_info(streamer_info)

    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_info.id)


@router.post("/delete", summary="删除主播接口")
async def upload_product_api(delete_info: StreamerInfo, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_item_by_id("streamer", delete_info.streamerId, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")
