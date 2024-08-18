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
    streamer_name: str


@router.post("/list")
async def get_streamer_info_api():
    """获取所有主播信息，用于用户进行主播的选择

    Returns:
        data: [
            {
                "id": id,
                "name": streamer_name,
                "character": ",".join(streamer_character),
                "value": "str(id)",
                "imageUrl": "xxx.jpeg",
                "videoUrl": "xxx.mp4",
            },
            ...
        ]
    """
    # TODO 后续需要改造数据结构，目前先简单返回
    # 加载对话配置文件
    streamer_list = await get_all_streamer_info()

    streamer_info_dict = []
    for streamer_info in streamer_list:
        streamer_info_dict.append(
            {
                "id": streamer_info['id'],
                "name": streamer_info['name'],
                "character": ",".join(streamer_info['character']),
                "value": streamer_info['value'],
                "imageUrl": streamer_info['digital_human_setting']['base_mp4_path'],
                "videoUrl": streamer_info['digital_human_setting']['poster'],
            }
        )

    logger.info(streamer_info_dict)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_info_dict)
