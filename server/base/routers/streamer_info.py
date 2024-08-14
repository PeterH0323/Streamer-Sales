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
    id = 0
    for streamer_name, streamer_character in streamer_list.items():
        id += 1
        streamer_info_dict.append(
            {
                "id": id,
                "name": streamer_name,
                "character": ",".join(streamer_character),
                "value": f"{id}",
                "imageUrl": "https://fuss10.elemecdn.com/e/5d/4a731a90594a4af544c0c25941171jpeg.jpeg",
                "videoUrl": "https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4",
            }
        )

    logger.info(streamer_info_dict)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_info_dict)
