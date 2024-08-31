#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   streamer_room_model.py
@Time    :   2024/08/31
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   直播间信息数据结构定义
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.product_model import ProductItem, ProductPageItem

from ..models.streamer_info_model import StreamerInfoItem


class RoomProductListItem(BaseModel):
    roomId: int
    currentPage: int = 1
    pageSize: int = 10


class RoomChatItem(BaseModel):
    roomId: int
    userId: str
    message: str = ""
    asrFileUrl: str = ""


class MessageItem(BaseModel):
    role: str
    userId: str
    userName: str
    message: str
    avater: str
    messageIndex: int
    datetime: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class OnAirRoomStatusItem(BaseModel):
    """直播间状态信息"""

    conversation_id: str = ""  # 现阶段的对话 ID
    current_product_id: int = 1  # 目前介绍的商品 ID
    current_product_index: int = 0  # 商品列表索引
    current_product_start_time: str = ""  # 该商品开始时间
    streaming_video_path: str = ""  # 目前介绍使用的视频

    live_status: int = 0  # 直播间状态 0 未开播，1 正在直播，2 下播了
    start_time: str = ""  # 直播开始时间


class StreamRoomProductDatabaseItem(BaseModel):
    """直播间商品信息，数据库保存时的数据结构"""

    product_id: int = 0
    sales_doc: str = ""
    start_time: str = ""
    start_video: str = ""
    selected: bool = True


class StreamRoomInfoDatabaseItem(BaseModel):
    """直播间信息，数据库保存时的数据结构"""

    user_id: int = 0  # 用户ID
    room_id: int = 0  # 直播间 ID
    streamer_id: int = 0  # 主播 ID
    name: str = ""  # 直播间名字

    product_list: List[StreamRoomProductDatabaseItem] = []  # 商品列表
    status: OnAirRoomStatusItem | None = None  # 直播状态

    prohibited_words_id: int = 0  # 违禁词表 ID
    room_poster: str = ""  # 海报图
    background_image: str = ""  # 主播背景图

    delete: bool = False  # 是否删除


class StreamRoomInfoReponseItem(StreamRoomInfoDatabaseItem):
    """直播间接口返回的数据结构，继承自 StreamRoomInfoDatabaseItem"""

    streamer_info: StreamerInfoItem = {}


class StreamRoomProductItem(StreamRoomProductDatabaseItem, ProductItem):
    """直播间商品信息，内含商品基本信息 ProductPageItem 和 文案数字人信息 StreamRoomProductDatabaseItem"""

    ...


class StreamRoomDetailItem(ProductPageItem, StreamRoomInfoReponseItem):
    product_list: List[StreamRoomProductItem] = []
