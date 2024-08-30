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
    product_id: int = -1
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


class ProductQueryItem(BaseModel):
    currentPage: int = 1  # 当前页号
    pageSize: int = 10  # 每页记录数
    productName: str = ""  # 商品名，用于指定查询
    productId: str = "-1"  # 商品ID，用于指定查询
    instructionPath: str = ""  # 商品说明书路径，用于获取说明书内容


class DeleteProductItem(BaseModel):
    product_id: int
