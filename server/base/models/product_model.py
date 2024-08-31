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

from typing import List
from pydantic import BaseModel
from fastapi import File


class ProductItem(BaseModel):
    """商品信息"""

    user_id: int = 0
    product_id: int = 0
    product_name: str = ""
    product_class: str
    heighlights: List[str]
    image_path: str
    instruction: str
    departure_place: str
    delivery_company: str
    selling_price: float
    amount: int
    upload_date: str = ""
    delete: bool = False


class PageItem(BaseModel):
    currentPage: int = 0  # 当前页数
    pageSize: int = 0  # 页面的组件数量
    totalSize: int = 0  # 总大小


class ProductPageItem(PageItem):
    product_list: List[ProductItem] = []


class ProductQueryItem(PageItem):
    productName: str = ""  # 商品名，用于指定查询
    productId: str = "-1"  # 商品ID，用于指定查询
    instructionPath: str = ""  # 商品说明书路径，用于获取说明书内容


class DeleteProductItem(BaseModel):
    product_id: int
