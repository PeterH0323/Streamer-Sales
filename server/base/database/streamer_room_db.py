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


from datetime import datetime
from typing import List

from loguru import logger
from sqlmodel import Session, and_, not_, select

from ...web_configs import API_CONFIG
from ..models.streamer_room_model import ChatMessageInfo, OnAirRoomStatusItem, SalesDocAndVideoInfo, StreamRoomInfo
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


def create_or_update_db_room_by_id(room_id: int, new_info: StreamRoomInfo, user_id: int):
    """新增 or 编辑直播间信息

    Args:
        room_id (int): 直播间 ID
        new_info (StreamRoomInfo): 新的信息
        user_id (int): 用户 ID，用于防止其他用户恶意修改
    """

    with Session(DB_ENGINE) as session:

        # 更新 status 内容
        if new_info.status_id is not None:
            status_info = session.exec(
                select(OnAirRoomStatusItem).where(OnAirRoomStatusItem.status_id == new_info.status_id)
            ).one()
        else:
            status_info = OnAirRoomStatusItem()

        status_info.streaming_video_path = new_info.status.streaming_video_path.replace(API_CONFIG.REQUEST_FILES_URL, "")
        status_info.live_status = new_info.status.live_status
        session.add(status_info)
        session.commit()
        session.refresh(status_info)

        if room_id > 0:

            # 更新主播间其他信息
            room_info = session.exec(
                select(StreamRoomInfo).where(and_(StreamRoomInfo.room_id == room_id, StreamRoomInfo.user_id == user_id))
            ).one()

            if room_info is None:
                logger.error("Edit by other ID !!!")
                return

        else:
            room_info = StreamRoomInfo(status_id=status_info.status_id, user_id=user_id)

        # 更新直播间基础信息
        room_info.name = new_info.name
        room_info.prohibited_words_id = new_info.prohibited_words_id
        room_info.room_poster = new_info.room_poster.replace(API_CONFIG.REQUEST_FILES_URL, "")
        room_info.background_image = new_info.background_image.replace(API_CONFIG.REQUEST_FILES_URL, "")
        room_info.streamer_id = new_info.streamer_id

        session.add(room_info)
        session.commit()  # 提交
        session.refresh(room_info)

        # 更新商品信息
        if len(new_info.product_list) > 0:
            selected_id_list = [product.product_id for product in new_info.product_list]
            for product in new_info.product_list:
                if product.sales_info_id is not None:
                    # 更新
                    sales_info = session.exec(
                        select(SalesDocAndVideoInfo).where(
                            and_(
                                SalesDocAndVideoInfo.room_id == room_info.room_id,
                                SalesDocAndVideoInfo.product_id == product.product_id,
                                SalesDocAndVideoInfo.sales_info_id == product.sales_info_id,
                            )
                        )
                    ).one()
                else:
                    # 新建
                    sales_info = SalesDocAndVideoInfo()

                sales_info.product_id = product.product_id
                sales_info.sales_doc = product.sales_doc
                sales_info.start_time = product.start_time
                sales_info.start_video = product.start_video.replace(API_CONFIG.REQUEST_FILES_URL, "")
                sales_info.selected = True
                sales_info.room_id = room_info.room_id
                session.add(sales_info)
                session.commit()

            # 删除没选上的
            if len(selected_id_list) > 0:
                cancel_select_sales_info = session.exec(
                    select(SalesDocAndVideoInfo).where(
                        and_(
                            SalesDocAndVideoInfo.room_id == room_info.room_id,
                            not_(SalesDocAndVideoInfo.product_id.in_(selected_id_list)),
                        )
                    )
                ).all()

                if cancel_select_sales_info is not None:
                    for cancel_select in cancel_select_sales_info:
                        session.delete(cancel_select)
                        session.commit()

        return room_info.room_id


def init_conversation(db_session, sales_info_id: int, streamer_id: int, sales_doc: str):
    """新建直播间对话，一般触发于点击 开始直播 or 下一个商品

    Args:
        db_session (it): 数据库句柄
        sales_info_id (int): 销售 ID
        streamer_id (int): 主播 ID
        sales_doc (str): 主播文案
    """
    message_info = ChatMessageInfo(
        sales_info_id=sales_info_id, streamer_id=streamer_id, role="streamer", message=sales_doc, send_time=datetime.now()
    )
    db_session.add(message_info)


def update_message_info(sales_info_id: int, role_id: int, role: str, message: str):
    """新增对话记录

    Args:
        sales_info_id (int): 销售 ID
        role_id (int): 角色 ID
        role (str): 角色类型："streamer", "user"
        message (str): 插入的消息
    """

    assert role in ["streamer", "user"]

    with Session(DB_ENGINE) as session:

        role_key = "streamer_id" if role == "streamer" else "user_id"
        role_id_info = {role_key: role_id}

        message_info = ChatMessageInfo(
            **role_id_info, sales_info_id=sales_info_id, role=role, message=message, send_time=datetime.now()
        )
        session.add(message_info)
        session.commit()


def update_db_room_status(room_id: int, user_id: int, process_type: str):
    """编辑直播间状态信息

    Args:
        room_id (int): 直播间 ID
        new_status_info (OnAirRoomStatusItem): 新的信息
        user_id (int): 用户 ID，用于防止其他用户恶意修改
    """

    with Session(DB_ENGINE) as session:

        # 更新主播间其他信息
        room_info = session.exec(
            select(StreamRoomInfo).where(and_(StreamRoomInfo.room_id == room_id, StreamRoomInfo.user_id == user_id))
        ).one()

        if room_info is None:
            logger.error("Edit by other ID !!!")
            return

        # 更新 status 内容
        if room_info.status_id is not None:
            status_info = session.exec(
                select(OnAirRoomStatusItem).where(OnAirRoomStatusItem.status_id == room_info.status_id)
            ).one()

        if status_info is None:
            logger.error("status_info is None !!!")
            return

        if process_type in ["online", "next-product"]:

            if process_type == "online":
                status_info.live_status = 1
                status_info.start_time = datetime.now()
                status_info.end_time = None
                status_info.current_product_index = 0

            elif process_type == "next-product":
                status_info.current_product_index += 1

            current_idx = status_info.current_product_index

            status_info.streaming_video_path = room_info.product_list[current_idx].start_video
            status_info.sales_info_id = room_info.product_list[current_idx].sales_info_id

            sales_info = session.exec(
                select(SalesDocAndVideoInfo).where(
                    SalesDocAndVideoInfo.sales_info_id == room_info.product_list[current_idx].sales_info_id
                )
            ).one()

            sales_info.start_time = datetime.now()
            session.add(sales_info)

            # 新建对话
            init_conversation(
                session, status_info.sales_info_id, room_info.streamer_id, room_info.product_list[current_idx].sales_doc
            )

        elif process_type == "offline":
            status_info.streaming_video_path = ""
            status_info.live_status = 2
            status_info.end_time = datetime.now()

        else:
            raise NotImplemented("process type error !!")

        session.add(status_info)
        session.commit()


def get_message_list(sales_info_id: int) -> List[ChatMessageInfo]:
    """根据销售 ID 获取全部对话

    Args:
        sales_info_id (int): 销售 ID

    Returns:
        List[ChatMessageInfo]: 对话列表
    """
    with Session(DB_ENGINE) as session:

        message_info = session.exec(
            select(ChatMessageInfo)
            .where(and_(ChatMessageInfo.sales_info_id == sales_info_id))
            .order_by(ChatMessageInfo.message_id)
        ).all()

        if message_info is None:
            return []

    formate_message_list = []
    for message_ in message_info:
        chat_item = {
            "role": message_.role,
            "avatar": message_.user_info.avatar if message_.role == "user" else message_.streamer_info.avatar,
            "userName": message_.user_info.username if message_.role == "user" else message_.streamer_info.name,
            "message": message_.message,
            "datetime": message_.send_time,
        }

        chat_item["avatar"] = API_CONFIG.REQUEST_FILES_URL + chat_item["avatar"]
        formate_message_list.append(chat_item)

    return formate_message_list


def update_room_video_path(status_id: int, news_video_server_path: str):
    """数据库更新 status 主播视频

    Args:
        status_id (int): 主播间 status ID
        news_video_server_path (str): 需要更新的主播视频 服务器地址

    """
    with Session(DB_ENGINE) as session:
        # 更新 status 内容
        status_info = session.exec(select(OnAirRoomStatusItem).where(OnAirRoomStatusItem.status_id == status_id)).one()

        status_info.streaming_video_path = news_video_server_path.replace(API_CONFIG.REQUEST_FILES_URL, "")
        session.add(status_info)
        session.commit()


async def get_live_room_info(user_id: int, room_id: int):
    """获取直播间的开播实时信息

    Args:
        user_id (int): 用户 ID
        room_id (int): 直播间 ID

    Returns:
        dict: 直播间实时信息
    """

    # 根据直播间 ID 获取信息
    streaming_room_info = await get_db_streaming_room_info(user_id, room_id)
    streaming_room_info = streaming_room_info[0]

    # 主播信息
    streamer_info = streaming_room_info.streamer_info

    # 商品索引
    prodcut_index = streaming_room_info.status.current_product_index

    # 是否为最后的商品
    final_procut = True if len(streaming_room_info.product_list) - 1 == prodcut_index else False

    # 对话信息
    conversation_list = get_message_list(streaming_room_info.status.sales_info_id)

    # 视频转换为服务器地址
    video_path = API_CONFIG.REQUEST_FILES_URL + streaming_room_info.status.streaming_video_path

    # 返回报文
    res_data = {
        "streamerInfo": streamer_info,
        "conversation": conversation_list,
        "currentProductInfo": streaming_room_info.product_list[prodcut_index].product_info,
        "currentStreamerVideo": video_path,
        "currentProductIndex": streaming_room_info.status.current_product_index,
        "startTime": streaming_room_info.status.start_time,
        "currentPoductStartTime": streaming_room_info.product_list[prodcut_index].start_time,
        "finalProduct": final_procut,
    }

    logger.info(res_data)

    return res_data
