#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   product_db.py
@Time    :   2024/08/30
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   商品数据表文件读写
"""

from typing import List, Tuple

import yaml
from loguru import logger
from sqlalchemy import func
from sqlmodel import Session, and_, select

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..models.product_model import ProductInfo, ProductPageItem
from .init_db import DB_ENGINE


async def get_db_product_info(
    user_id: int,
    current_page: int = -1,
    page_size: int = 10,
    product_name: str | None = None,
    product_id: int | None = None,
) -> Tuple[List[ProductInfo], int]:
    """查询数据库中的商品信息

    Args:
        user_id (int): 用户 ID
        current_page (int, optional): 页数. Defaults to -1.
        page_size (int, optional): 每页的大小. Defaults to 10.
        product_name (str | None, optional): 商品名称，模糊搜索. Defaults to None.
        product_id (int | None, optional): 商品 ID，用户获取特定商品信息. Defaults to None.

    Returns:
         List[ProductInfo]: 商品信息
         int : 该用户持有的总商品数，已剔除删除的
    """

    assert current_page != 0
    assert page_size != 0

    # 查询条件
    query_condiction = and_(ProductInfo.user_id == user_id, ProductInfo.delete == False)

    # 获取总数
    with Session(DB_ENGINE) as session:
        # 获得该用户所有商品的总数
        total_product_num = session.scalar(select(func.count(ProductInfo.product_id)).where(query_condiction))

        if product_name is not None:
            # 查询条件更改为商品名称模糊搜索
            query_condiction = and_(
                ProductInfo.user_id == user_id, ProductInfo.delete == False, ProductInfo.product_name.ilike(f"%{product_name}%")
            )

        elif product_id is not None:
            # 查询条件更改为查找特定 ID
            query_condiction = and_(
                ProductInfo.user_id == user_id, ProductInfo.delete == False, ProductInfo.product_id == product_id
            )

        # 查询获取商品
        if current_page < 0:
            # 全部查询
            product_list = session.exec(select(ProductInfo).where(query_condiction)).all()
        else:
            # 分页查询
            offset_idx = (current_page - 1) * page_size
            product_list = session.exec(select(ProductInfo).where(query_condiction).offset(offset_idx).limit(page_size)).all()

    # 将路径换成服务器路径
    for product in product_list:
        product.image_path = API_CONFIG.REQUEST_FILES_URL + product.image_path
        product.instruction = API_CONFIG.REQUEST_FILES_URL + product.instruction

    return product_list, total_product_num


def save_product_info(new_product_info_dict: ProductInfo):
    """保存商品信息

    Args:
        product_info_dict (Dict[ProductInfo]): 所有的商品信息
    """
    # 读取
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 更新对应字段
    product_info_dict.update({new_product_info_dict["product_name"]: dict(new_product_info_dict)})

    # 保存
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(product_info_dict, f, allow_unicode=True)


def get_product_max_id():
    # TODO 删除
    raise NotImplemented("using get_db_product_info instead")


async def get_product_list(user_id, product_name="", id=-1) -> Tuple[List[ProductInfo], int]:
    # TODO 删除
    raise NotImplemented("using get_db_product_info instead")


async def get_prduct_by_page(user_id, currentPage, pageSize, productName: str | None = None) -> ProductPageItem:
    # TODO 删除
    raise NotImplemented("using get_db_product_info instead")
