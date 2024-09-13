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

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from ..models.user_model import UserInfo
from ..models.product_model import ProductInfo
from ..models.streamer_info_model import StreamerInfo


class RoomChatItem(BaseModel):
    roomId: int
    message: str = ""
    asrFileUrl: str = ""


# =======================================================
#                      直播间数据库模型
# =======================================================


class SalesDocAndVideoInfo(SQLModel, table=True):
    """直播间 文案 和 数字人介绍视频数据结构"""

    __tablename__ = "sales_doc_and_video_info"

    sales_info_id: int | None = Field(default=None, primary_key=True, unique=True)

    sales_doc: str = ""  # 讲解文案
    start_video: str = ""  # 开播时候第一个讲解视频
    start_time: datetime | None = None  # 当前商品开始时间
    selected: bool = True

    product_id: int | None = Field(default=None, foreign_key="product_info.product_id")
    product_info: ProductInfo | None = Relationship(back_populates="sales_info", sa_relationship_kwargs={"lazy": "selectin"})

    room_id: int | None = Field(default=None, foreign_key="stream_room_info.room_id")
    stream_room: Optional["StreamRoomInfo"] | None = Relationship(back_populates="product_list")


class OnAirRoomStatusItem(SQLModel, table=True):
    """直播间状态信息"""

    __tablename__ = "on_air_room_status_item"

    status_id: int | None = Field(default=None, primary_key=True, unique=True)  # 直播间 ID

    sales_info_id: int | None = Field(default=None, foreign_key="sales_doc_and_video_info.sales_info_id")

    current_product_index: int = 0  # 目前讲解的商品列表索引
    streaming_video_path: str = ""  # 目前介绍使用的视频

    live_status: int = 0  # 直播间状态 0 未开播，1 正在直播，2 下播了
    start_time: datetime | None = None  # 直播开始时间
    end_time: datetime | None = None  # 直播下播时间

    room_info: Optional["StreamRoomInfo"] | None = Relationship(
        back_populates="status", sa_relationship_kwargs={"lazy": "selectin"}
    )

    """直播间信息，数据库保存时的数据结构"""


class StreamRoomInfo(SQLModel, table=True):

    __tablename__ = "stream_room_info"

    room_id: int | None = Field(default=None, primary_key=True, unique=True)  # 直播间 ID

    name: str = ""  # 直播间名字

    product_list: list[SalesDocAndVideoInfo] = Relationship(
        back_populates="stream_room",
        sa_relationship_kwargs={"lazy": "selectin", "order_by": "asc(SalesDocAndVideoInfo.product_id)"},
    )  # 商品列表，查找的时候加上 order_by 自动排序，desc -> 降序; asc -> 升序

    prohibited_words_id: int = 0  # 违禁词表 ID
    room_poster: str = ""  # 海报图
    background_image: str = ""  # 主播背景图

    delete: bool = False  # 是否删除

    status_id: int | None = Field(default=None, foreign_key="on_air_room_status_item.status_id")
    status: OnAirRoomStatusItem | None = Relationship(back_populates="room_info", sa_relationship_kwargs={"lazy": "selectin"})

    streamer_id: int | None = Field(default=None, foreign_key="streamer_info.streamer_id")  # 主播 ID
    streamer_info: StreamerInfo | None = Relationship(back_populates="room_info", sa_relationship_kwargs={"lazy": "selectin"})

    user_id: int | None = Field(default=None, foreign_key="user_info.user_id")


# =======================================================
#                    直播对话数据库模型
# =======================================================


class ChatMessageInfo(SQLModel, table=True):
    """直播页面对话数据结构"""

    __tablename__ = "chat_message_info"

    message_id: int | None = Field(default=None, primary_key=True, unique=True)  # 消息 ID

    sales_info_id: int | None = Field(default=None, foreign_key="sales_doc_and_video_info.sales_info_id")
    sales_info: SalesDocAndVideoInfo | None = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    user_id: int | None = Field(default=None, foreign_key="user_info.user_id")
    user_info: UserInfo | None = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    streamer_id: int | None = Field(default=None, foreign_key="streamer_info.streamer_id")
    streamer_info: StreamerInfo | None = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    role: str
    message: str
    send_time: datetime | None = None
