#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   product_model.py
@Time    :   2024/08/30
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   商品数据类型定义
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


# =======================================================
#                      数据库模型
# =======================================================
class ProductInfo(SQLModel, table=True):
    """商品信息"""

    product_id: int | None = Field(default=None, primary_key=True, unique=True)
    product_name: str = Field(index=True, unique=True)
    product_class: str
    heighlights: str
    image_path: str
    instruction: str
    departure_place: str
    delivery_company: str
    selling_price: float
    amount: int
    upload_date: datetime = datetime.now()
    delete: bool = False

    user_id: int | None = Field(default=None, foreign_key="userinfo.user_id")


# =======================================================
#                      基本模型
# =======================================================
class PageItem(BaseModel):
    currentPage: int = 0  # 当前页数
    pageSize: int = 0  # 页面的组件数量
    totalSize: int = 0  # 总大小


class ProductPageItem(PageItem):
    product_list: List[ProductInfo] = []


class ProductQueryItem(PageItem):
    productName: str = ""  # 商品名，用于指定查询
    productId: str = "-1"  # 商品ID，用于指定查询
    instructionPath: str = ""  # 商品说明书路径，用于获取说明书内容
