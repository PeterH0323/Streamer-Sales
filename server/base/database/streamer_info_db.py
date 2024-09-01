#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   streamer_info_db.py
@Time    :   2024/08/30
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   主播信息数据库操作
"""


from typing import List
import yaml

from ..models.streamer_info_model import StreamerInfoItem
from ...web_configs import WEB_CONFIGS


async def get_streamers_info(user_id: int, stream_id: int = -1) -> List[StreamerInfoItem]:
    # 加载数据库文件
    with open(WEB_CONFIGS.STREAMER_CONFIG_PATH, "r", encoding="utf-8") as f:
        streamer_info = yaml.safe_load(f)

    # 过滤掉 其他 ID 主播，并进一步过滤被删除的主播
    filter_streamer_list = []
    for streamer in streamer_info:

        # 过滤 ID
        if streamer["user_id"] != user_id:
            continue

        # 过滤删除的
        if streamer["delete"]:
            continue

        if stream_id > 0 and streamer["id"] == stream_id:
            # 根据 ID 获取，直接返回
            return [streamer]
        else:
            # 全部获取
            filter_streamer_list.append(streamer)

    return filter_streamer_list


def get_max_streamer_id() -> int:
    """获取目前数据库中最大的 ID

    Returns:
        int: 最大 ID
    """

    with open(WEB_CONFIGS.STREAMER_CONFIG_PATH, "r", encoding="utf-8") as f:
        streamer_info = yaml.safe_load(f)

    max_streamer_id = -1
    for item in streamer_info:
        max_streamer_id = max(item["id"], max_streamer_id)

    return max_streamer_id


def save_streamer_info(new_streamer_info: StreamerInfoItem):
    """更新 or 新增数据库信息

    Args:
        new_streamer_info (StreamerInfoItem): 新的主播信息，如果 ID 匹配则更新，如果不匹配现有的则更新
    """

    new_streamer_info = dict(new_streamer_info)

    with open(WEB_CONFIGS.STREAMER_CONFIG_PATH, "r", encoding="utf-8") as f:
        all_streamer_info_list = yaml.safe_load(f)

    # 根据 ID 进行匹配
    match_indx = -1
    for idx, sreamer in enumerate(all_streamer_info_list):

        if sreamer["id"] == new_streamer_info["id"]:
            # 匹配成功则更新
            all_streamer_info_list[idx] = dict(new_streamer_info)
            match_indx = idx
            break

    # 匹配不成功，直接加入
    if match_indx < 0:
        all_streamer_info_list.append(dict(new_streamer_info))

    # 保存
    with open(WEB_CONFIGS.STREAMER_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(all_streamer_info_list, f, allow_unicode=True)
