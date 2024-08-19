#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
# author: HinGwenWong
# github: https://github.com/PeterH0323/Streamer-Sales
# time: 2024/08/18
"""
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...web_configs import WEB_CONFIGS
from ..utils import ResultCode, get_all_streaming_room_info, make_return_data

router = APIRouter(
    prefix="/streaming-room",
    tags=["streaming-room"],
    responses={404: {"description": "Not found"}},
)

@router.post("/list")
async def get_streaming_room_api():
    """获取所有直播间信息"""
    # TODO 后续需要改造数据结构，目前先简单返回
    # 加载对话配置文件
    streaming_room_list = await get_all_streaming_room_info()

    logger.info(streaming_room_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streaming_room_list)
