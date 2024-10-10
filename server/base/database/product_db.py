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

from loguru import logger
from sqlalchemy import func
from sqlmodel import Session, and_, not_, select

from ...web_configs import API_CONFIG
from ..models.product_model import ProductInfo
from .init_db import DB_ENGINE


async def get_db_product_info(
    user_id: int,
    current_page: int = -1,
    page_size: int = 10,
    product_name: str | None = None,
    product_id: int | None = None,
    exclude_list: List[int] | None = None,
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

        elif exclude_list is not None:
            # 排除查询
            query_condiction = and_(
                ProductInfo.user_id == user_id, ProductInfo.delete == False, not_(ProductInfo.product_id.in_(exclude_list))
            )

        # 查询获取商品
        if current_page < 0:
            # 全部查询
            product_list = session.exec(select(ProductInfo).where(query_condiction).order_by(ProductInfo.product_id)).all()
        else:
            # 分页查询
            offset_idx = (current_page - 1) * page_size
            product_list = session.exec(
                select(ProductInfo).where(query_condiction).offset(offset_idx).limit(page_size).order_by(ProductInfo.product_id)
            ).all()

    if product_list is None:
        logger.warning("nothing to find in db...")
        product_list = []

    # 将路径换成服务器路径
    for product in product_list:
        product.image_path = API_CONFIG.REQUEST_FILES_URL + product.image_path
        product.instruction = API_CONFIG.REQUEST_FILES_URL + product.instruction

    logger.info(product_list)
    logger.info(f"len {len(product_list)}")

    return product_list, total_product_num


async def delete_product_id(product_id: int, user_id: int) -> bool:
    """删除特定的商品 ID

    Args:
        product_id (int): 商品 ID
        user_id (int): 用户 ID，用于防止其他用户恶意删除

    Returns:
        bool: 是否删除成功
    """

    delete_success = True

    try:
        # 获取总数
        with Session(DB_ENGINE) as session:
            # 查找特定 ID
            product_info = session.exec(
                select(ProductInfo).where(and_(ProductInfo.product_id == product_id, ProductInfo.user_id == user_id))
            ).one()

            if product_info is None:
                logger.error("Delete by other ID !!!")
                return False

            product_info.delete = True  # 设置为删除
            session.add(product_info)
            session.commit()  # 提交
    except Exception:
        delete_success = False

    return delete_success


def create_or_update_db_product_by_id(product_id: int, new_info: ProductInfo, user_id: int) -> bool:
    """新增 or 编辑商品信息

    Args:
        product_id (int): 商品 ID
        new_info (ProductInfo): 新的信息
        user_id (int): 用户 ID，用于防止其他用户恶意修改

    Returns:
        bool: 说明书是否变化
    """

    instruction_updated = False

    # 去掉服务器地址
    new_info.image_path = new_info.image_path.replace(API_CONFIG.REQUEST_FILES_URL, "")
    new_info.instruction = new_info.instruction.replace(API_CONFIG.REQUEST_FILES_URL, "")

    with Session(DB_ENGINE) as session:

        if product_id > 0:
            # 更新特定 ID
            product_info = session.exec(
                select(ProductInfo).where(and_(ProductInfo.product_id == product_id, ProductInfo.user_id == user_id))
            ).one()

            if product_info is None:
                logger.error("Edit by other ID !!!")
                return False

            if product_info.instruction != new_info.instruction:
                # 判断说明书是否变化了
                instruction_updated = True

            # 更新对应的值
            product_info.product_name = new_info.product_name
            product_info.product_class = new_info.product_class
            product_info.heighlights = new_info.heighlights
            product_info.image_path = new_info.image_path
            product_info.instruction = new_info.instruction
            product_info.departure_place = new_info.departure_place
            product_info.delivery_company = new_info.delivery_company
            product_info.selling_price = new_info.selling_price
            product_info.amount = new_info.amount

            session.add(product_info)
        else:
            # 新增，直接添加即可
            session.add(new_info)
            instruction_updated = True

        session.commit()  # 提交
    return instruction_updated
