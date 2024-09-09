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

from typing import List
from pydantic import BaseModel
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from ..models.product_model import ProductInfo, ProductPageItem, ProductStreamRoomLink

from ..models.streamer_info_model import StreamerInfo


class RoomProductListItem(BaseModel):
    roomId: int
    currentPage: int = 1
    pageSize: int = 10


class RoomChatItem(BaseModel):
    roomId: int
    message: str = ""
    asrFileUrl: str = ""


class MessageItem(BaseModel):
    """直播页面对话数据结构"""

    role: str
    userId: int
    userName: str
    message: str
    avatar: str
    messageIndex: int
    datetime: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class StreamRoomProductDatabaseItem(BaseModel):
    """直播间商品信息，数据库保存时的数据结构"""

    product_id: int = 0
    sales_doc: str = ""
    start_time: str = ""
    start_video: str = ""
    selected: bool = True


# =======================================================
#                      数据库模型
# =======================================================


class StreamRoomInfo(SQLModel, table=True):
    """直播间信息，数据库保存时的数据结构"""

    __tablename__ = "stream_room_info"

    room_id: int | None = Field(default=None, primary_key=True, unique=True)  # 直播间 ID

    name: str = ""  # 直播间名字
    product_list: list[ProductInfo] = Relationship(back_populates="stream_room", link_model=ProductStreamRoomLink)  # 商品列表

    prohibited_words_id: int = 0  # 违禁词表 ID
    room_poster: str = ""  # 海报图
    background_image: str = ""  # 主播背景图

    delete: bool = False  # 是否删除

    status_id: int | None = Field(default=None, foreign_key="on_air_room_status_item.status_id")
    user_id: int | None = Field(default=None, foreign_key="user_info.user_id")
    streamer_id: int | None = Field(default=None, foreign_key="streamer_info.streamer_id")  # 主播 ID


class OnAirRoomStatusItem(SQLModel, table=True):
    """直播间状态信息"""

    __tablename__ = "on_air_room_status_item"

    status_id: int | None = Field(default=None, primary_key=True, unique=True)  # 直播间 ID

    conversation_id: str = ""  # 现阶段的对话 ID
    current_product_id: int = 0  # 目前介绍的商品 ID
    current_product_index: int = 0  # 商品列表索引
    current_product_start_time: datetime | None = None  # 该商品开始时间
    streaming_video_path: str = ""  # 目前介绍使用的视频

    live_status: int = 0  # 直播间状态 0 未开播，1 正在直播，2 下播了
    start_time: datetime | None = None  # 直播开始时间

    user_id: int | None = Field(default=None, foreign_key="user_info.user_id")


class StreamRoomInfoReponseItem(BaseModel):  # StreamRoomInfo):
    """直播间接口返回的数据结构，继承自 StreamRoomInfo"""

    streamer_info: StreamerInfo = {}


class StreamRoomProductItem(BaseModel):  # StreamRoomInfo, ProductInfo):
    """直播间商品信息，内含商品基本信息 ProductPageItem 和 文案数字人信息 StreamRoomInfo"""

    ...


class StreamRoomDetailItem(BaseModel):  # ProductPageItem, StreamRoomInfoReponseItem):
    product_list: List[StreamRoomProductItem] = []
