#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
# author: HinGwenWong
# github: https://github.com/PeterH0323/Streamer-Sales
# time: 2024/08/10
"""
from dataclasses import asdict, dataclass
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel
import yaml

from ...web_configs import WEB_CONFIGS
from ..utils import ResultCode, delete_item_by_id, get_all_streamer_info, get_streamer_info_by_id, make_return_data

router = APIRouter(
    prefix="/streamer",
    tags=["streamer"],
    responses={404: {"description": "Not found"}},
)


@dataclass
class StreamerInfoItem:
    id: int = 0
    name: str = ""
    character: str = ""
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


@router.post("/list")
async def get_streamer_info_api():
    """获取所有主播信息，用于用户进行主播的选择"""
    streamer_list = await get_all_streamer_info(True)

    logger.info(streamer_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_list)


@router.post("/info")
async def get_streamer_info_api(streamer_info: StreamerInfo):
    """用于获取特定主播的信息"""
    pick_info = await get_streamer_info_by_id(streamer_info.streamerId)

    if len(pick_info) == 0:
        # 没找到 or 主播 ID = 0，回复一个空的
        pick_info = [asdict(StreamerInfoItem())]

    logger.info(pick_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", pick_info)


@router.post("/edit")
async def edit_streamer_info_api(streamer_info: StreamerInfoItem):
    """新增 or 修改主播信息"""

    streamer_info.character = streamer_info.character.split("、")  # 将性格转为 list

    all_streamer_info_list = await get_all_streamer_info(need_to_formate_character=False)
    max_streamer_id = -1
    update_index = -1
    for idx, item in enumerate(all_streamer_info_list):

        if item["id"] == streamer_info.id:
            update_index = idx
            break

        max_streamer_id = max(item["id"], max_streamer_id)

    if update_index >= 0:
        # 修改
        logger.info("已有 ID，编辑模式，修改对应配置")
        all_streamer_info_list[update_index] = asdict(streamer_info)
    else:
        logger.info("新 ID，新增模式，新增对应配置")
        streamer_info.id = max_streamer_id + 1  # 直播间 ID
        all_streamer_info_list.append(asdict(streamer_info))

    logger.info(streamer_info)
    with open(WEB_CONFIGS.STREAMER_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(all_streamer_info_list, f, allow_unicode=True)

    return make_return_data(True, ResultCode.SUCCESS, "成功", streamer_info.id)



@router.post("/delete")
async def upload_product_api(delete_info: StreamerInfo):

    process_success_flag = await delete_item_by_id("streamer", delete_info.streamerId)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")
