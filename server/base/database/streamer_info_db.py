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

from loguru import logger
from sqlmodel import Session, and_, select

from ...web_configs import API_CONFIG
from ..models.streamer_info_model import StreamerInfo
from .init_db import DB_ENGINE


async def get_db_streamer_info(user_id: int, streamer_id: int | None = None) -> List[StreamerInfo] | None:
    """查询数据库中的主播信息

    Args:
        user_id (int): 用户 ID
        streamer_id (int | None, optional): 主播 ID，用户获取特定主播信息. Defaults to None.

    Returns:
        List[StreamerInfo] | StreamerInfo | None: 主播信息，如果获取全部则返回 list，如果获取单个则返回单个，如果查不到返回 None
    """

    # 查询条件
    query_condiction = and_(StreamerInfo.user_id == user_id, StreamerInfo.delete == False)

    # 获取总数
    with Session(DB_ENGINE) as session:
        # 获得该用户所有主播的总数
        # total_product_num = session.scalar(select(func.count(StreamerInfo.product_id)).where(query_condiction))

        if streamer_id is not None:
            # 查询条件更改为查找特定 ID
            query_condiction = and_(
                StreamerInfo.user_id == user_id, StreamerInfo.delete == False, StreamerInfo.streamer_id == streamer_id
            )

        # 查询主播商品，并根据 ID 进行排序
        try:
            streamer_list = session.exec(select(StreamerInfo).where(query_condiction).order_by(StreamerInfo.streamer_id)).all()
        except Exception as e:
            streamer_list = None

    if streamer_list is None:
        logger.warning("nothing to find in db...")
        streamer_list = []

    # 将路径换成服务器路径
    for streamer in streamer_list:
        streamer.avatar = API_CONFIG.REQUEST_FILES_URL + streamer.avatar
        streamer.tts_reference_audio = API_CONFIG.REQUEST_FILES_URL + streamer.tts_reference_audio
        streamer.poster_image = API_CONFIG.REQUEST_FILES_URL + streamer.poster_image
        streamer.base_mp4_path = API_CONFIG.REQUEST_FILES_URL + streamer.base_mp4_path

    logger.info(streamer_list)
    logger.info(f"len {len(streamer_list)}")

    return streamer_list


async def delete_streamer_id(streamer_id: int, user_id: int) -> bool:
    """删除特定的主播 ID

    Args:
        streamer_id (int): 主播 ID
        user_id (int): 用户 ID，用于防止其他用户恶意删除

    Returns:
        bool: 是否删除成功
    """

    delete_success = True

    try:
        # 获取总数
        with Session(DB_ENGINE) as session:
            # 查找特定 ID
            streamer_info = session.exec(
                select(StreamerInfo).where(and_(StreamerInfo.streamer_id == streamer_id, StreamerInfo.user_id == user_id))
            ).one()

            if streamer_info is None:
                logger.error("Delete by other ID !!!")
                return False

            streamer_info.delete = True  # 设置为删除
            session.add(streamer_info)
            session.commit()  # 提交
    except Exception:
        delete_success = False

    return delete_success


def create_or_update_db_streamer_by_id(streamer_id: int, new_info: StreamerInfo, user_id: int) -> int:
    """新增 or 编辑主播信息

    Args:
        product_id (int): 商品 ID
        new_info (ProductInfo): 新的信息
        user_id (int): 用户 ID，用于防止其他用户恶意修改

    Returns:
        int: 主播 ID
    """

    # 去掉服务器地址
    new_info.avatar = new_info.avatar.replace(API_CONFIG.REQUEST_FILES_URL, "")
    new_info.tts_reference_audio = new_info.tts_reference_audio.replace(API_CONFIG.REQUEST_FILES_URL, "")
    new_info.poster_image = new_info.poster_image.replace(API_CONFIG.REQUEST_FILES_URL, "")
    new_info.base_mp4_path = new_info.base_mp4_path.replace(API_CONFIG.REQUEST_FILES_URL, "")

    with Session(DB_ENGINE) as session:

        if streamer_id > 0:
            # 更新特定 ID
            streamer_info = session.exec(
                select(StreamerInfo).where(and_(StreamerInfo.streamer_id == streamer_id, StreamerInfo.user_id == user_id))
            ).one()

            if streamer_info is None:
                logger.error("Edit by other ID !!!")
                return -1
        else:
            # 新增，直接添加即可
            streamer_info = StreamerInfo(user_id=user_id)

        # 更新对应的值
        streamer_info.name = new_info.name
        streamer_info.character = new_info.character
        streamer_info.avatar = new_info.avatar
        streamer_info.tts_weight_tag = new_info.tts_weight_tag
        streamer_info.tts_reference_sentence = new_info.tts_reference_sentence
        streamer_info.tts_reference_audio = new_info.tts_reference_audio
        streamer_info.poster_image = new_info.poster_image
        streamer_info.base_mp4_path = new_info.base_mp4_path

        session.add(streamer_info)
        session.commit()  # 提交
        session.refresh(streamer_info)

        return int(streamer_info.streamer_id)
