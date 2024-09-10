#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   streamer_room_db.py
@Time    :   2024/08/31
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   直播间信息数据库操作
"""


from typing import List

import yaml
from loguru import logger
from sqlmodel import Session, and_, select

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..models.streamer_room_model import StreamRoomInfo
from .init_db import DB_ENGINE


async def get_db_streaming_room_info(user_id: int, room_id: int | None = None) -> List[StreamRoomInfo] | None:
    """查询数据库中的商品信息

    Args:
        user_id (int): 用户 ID
        streamer_id (int | None, optional): 主播 ID，用户获取特定主播信息. Defaults to None.

    Returns:
        List[StreamRoomInfo] | None: 直播间信息
    """

    # 查询条件
    query_condiction = and_(StreamRoomInfo.user_id == user_id, StreamRoomInfo.delete == False)

    # 获取总数
    with Session(DB_ENGINE) as session:
        if room_id is not None:
            # 查询条件更改为查找特定 ID
            query_condiction = and_(
                StreamRoomInfo.user_id == user_id, StreamRoomInfo.delete == False, StreamRoomInfo.room_id == room_id
            )

        # 查询获取直播间信息
        stream_room_list = session.exec(select(StreamRoomInfo).where(query_condiction).order_by(StreamRoomInfo.room_id)).all()

    if stream_room_list is None:
        logger.warning("nothing to find in db...")
        stream_room_list = []

    # 将路径换成服务器路径
    for stream_room in stream_room_list:
        # 主播信息
        stream_room.streamer_info.avatar = API_CONFIG.REQUEST_FILES_URL + stream_room.streamer_info.avatar
        stream_room.streamer_info.tts_reference_audio = (
            API_CONFIG.REQUEST_FILES_URL + stream_room.streamer_info.tts_reference_audio
        )
        stream_room.streamer_info.poster_image = API_CONFIG.REQUEST_FILES_URL + stream_room.streamer_info.poster_image
        stream_room.streamer_info.base_mp4_path = API_CONFIG.REQUEST_FILES_URL + stream_room.streamer_info.base_mp4_path

        # 商品信息
        for idx, product in enumerate(stream_room.product_list):
            stream_room.product_list[idx].product_info.image_path = API_CONFIG.REQUEST_FILES_URL + product.product_info.image_path
            stream_room.product_list[idx].product_info.instruction = (
                API_CONFIG.REQUEST_FILES_URL + product.product_info.instruction
            )

    logger.info(stream_room_list)
    logger.info(f"len {len(stream_room_list)}")

    return stream_room_list


async def delete_room_id(room_id: int, user_id: int) -> bool:
    """删除特定的主播间 ID

    Args:
        room_id (int): 直播间 ID
        user_id (int): 用户 ID，用于防止其他用户恶意删除

    Returns:
        bool: 是否删除成功
    """

    delete_success = True

    try:
        # 获取总数
        with Session(DB_ENGINE) as session:
            # 查找特定 ID
            room_info = session.exec(
                select(StreamRoomInfo).where(and_(StreamRoomInfo.room_id == room_id, StreamRoomInfo.user_id == user_id))
            ).one()

            if room_info is None:
                logger.error("Delete by other ID !!!")
                return False

            room_info.delete = True  # 设置为删除
            session.add(room_info)
            session.commit()  # 提交
    except Exception:
        delete_success = False

    return delete_success


def update_streaming_room_info(new_info):

    new_info = dict(new_info)

    # 加载直播间文件
    with open(WEB_CONFIGS.STREAMING_ROOM_CONFIG_PATH, "r", encoding="utf-8") as f:
        streaming_room_info = yaml.safe_load(f)

    if streaming_room_info is None:
        streaming_room_info = []

    # 选择特定的直播间
    new_room = True
    for idx, room_info in enumerate(streaming_room_info):
        if room_info["room_id"] == new_info["room_id"]:
            streaming_room_info[idx] = new_info
            new_room = False

    if new_room:
        streaming_room_info.append(new_info)

    # 保存
    with open(WEB_CONFIGS.STREAMING_ROOM_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(streaming_room_info, f, allow_unicode=True)


async def get_conversation_list(conversion_id: str):

    if conversion_id == "":
        return []

    # 获取对应的 conversion ID 信息
    with open(WEB_CONFIGS.CONVERSATION_MESSAGE_STORE_CONFIG_PATH, "r", encoding="utf-8") as f:
        conversation_all = yaml.safe_load(f)

    if conversation_all is None:
        return []

    conversation_list = conversation_all[conversion_id]

    # 根据 message index 排序
    conversation_list_sorted = sorted(conversation_list, key=lambda item: item["messageIndex"])

    return conversation_list_sorted


async def update_conversation_message_info(id, new_info):

    with open(WEB_CONFIGS.CONVERSATION_MESSAGE_STORE_CONFIG_PATH, "r", encoding="utf-8") as f:
        streaming_room_info = yaml.safe_load(f)

    if streaming_room_info is None:
        # 初始化文件内容
        streaming_room_info = dict()

    streaming_room_info[id] = new_info

    with open(WEB_CONFIGS.CONVERSATION_MESSAGE_STORE_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(streaming_room_info, f, allow_unicode=True)
