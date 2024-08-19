#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
# author: HinGwenWong
# github: https://github.com/PeterH0323/Streamer-Sales
# time: 2024/08/10
"""
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...web_configs import WEB_CONFIGS
from ..utils import ResultCode, get_all_streamer_info, make_return_data

router = APIRouter(
    prefix="/streamer",
    tags=["streamer"],
    responses={404: {"description": "Not found"}},
)


class StreamerInfoItem(BaseModel):
    id: int
    name: str
    character: str
    value: str
    imageUrl: str
    videoUrl: str


class StreamerInfo(BaseModel):
    # 主播信息
    streamerId: int


@router.post("/list")
async def get_streamer_info_api():
    """获取所有主播信息，用于用户进行主播的选择"""
    # TODO 后续需要改造数据结构，目前先简单返回
    # 加载对话配置文件
    streamer_list = await get_all_streamer_info()

    logger.info(streamer_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_list)


@router.post("/info")
async def get_streamer_info_api(streamer_info: StreamerInfo):
    """获取所有主播信息，用于获取特定主播的信息"""
    # TODO 后续需要改造数据结构，目前先简单返回
    # 加载对话配置文件
    streamer_list = await get_all_streamer_info()

    pick_info = []
    for i in streamer_list:
        if i["id"] == streamer_info.streamerId:
            pick_info = [i]
            break

    logger.info(pick_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", pick_info)
