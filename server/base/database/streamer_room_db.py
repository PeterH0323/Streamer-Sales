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

from ..models.streamer_room_model import OnAirRoomStatusItem, StreamRoomInfoDatabaseItem

from ...web_configs import WEB_CONFIGS


async def get_streaming_room_info(user_id, id=-1) -> List[StreamRoomInfoDatabaseItem] | StreamRoomInfoDatabaseItem:
    # 加载直播间数据
    with open(WEB_CONFIGS.STREAMING_ROOM_CONFIG_PATH, "r", encoding="utf-8") as f:
        streaming_room_info = yaml.safe_load(f)

    if streaming_room_info is None:
        empty_info = dict(StreamRoomInfoDatabaseItem(status=dict(OnAirRoomStatusItem())))
        if id == 0:
            return empty_info
        else:
            # 想获取所有，需要返回一个 list
            return [empty_info]

    filter_list = []
    for room in streaming_room_info:

        # 过滤 ID
        if room["user_id"] != user_id:
            continue

        if room["delete"]:
            continue

        if room["room_id"] == id:
            # 选择特定的直播间
            return room

        filter_list.append(room)

    if id <= 0:
        # 全部返回
        return filter_list

    return []


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
