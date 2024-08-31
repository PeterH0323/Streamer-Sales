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

from ...web_configs import WEB_CONFIGS
from ..models.product_model import ProductItem, ProductPageItem


async def get_db_product_info(user_id) -> List[ProductItem]:
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 过滤掉 其他 ID 商品，并进一步过滤被删除的商品
    filter_product_list = dict()
    for k, v in product_info_dict.items():

        # 过滤 ID
        if v.get("user_id") != user_id:
            continue

        # 去掉删掉的商品
        if v.get("delete", False) == True:
            continue

        filter_product_list.update({k: v})

    return filter_product_list


async def get_product_max_id():
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    max_id_key = max(product_info_dict, key=lambda x: product_info_dict[x]["product_id"])

    return product_info_dict[max_id_key]["product_id"]


def save_product_info(product_name: str, product_info_dict: ProductItem):
    """保存商品信息

    Args:
        product_info_dict (Dict[ProductItem]): 所有的商品信息
    """
    # 读取
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 更新对应字段
    product_info_dict.update({product_name: dict(product_info_dict)})

    # 保存
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(product_info_dict, f, allow_unicode=True)


async def get_product_list(user_id, product_name="", id=-1) -> Tuple[List[ProductItem], int]:
    """读取商品信息

    Args:
        product_name (str, optional): 用于模糊搜索商品名称. Defaults to "".
        id (int, optional): 商品 ID，查看特定 ID 商品的信息. Defaults to -1.

    Returns:
        list: 商品信息 list
        int: 所有商品的数量，用于分页计算和显示
    """
    # 读取数据库
    product_info_dict = await get_db_product_info(user_id)

    # 根据 ID 排序，避免乱序
    product_info_name_list = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["product_id"])).keys()
    product_list = []
    for key in product_info_name_list:
        info = product_info_dict[key]
        info.update({"product_name": key})

        # # 将 亮点 数组改为字符串
        # info["heighlights"] = "、".join(info["heighlights"])

        if product_name != "" and product_name not in key:
            # 如果有商品名则需要进行过滤处理，实现搜索功能
            continue

        if id > 0 and info["product_id"] == id:
            # 根据 ID 获取
            product_list = [info]
            break
        else:
            # 全部获取
            product_list.append(info)

    return product_list, len(product_info_dict)


async def get_prduct_by_page(user_id, currentPage, pageSize, productName="") -> ProductPageItem:
    product_list, db_product_size = await get_product_list(user_id, product_name=productName)
    product_total_size = len(product_list)

    # 根据页面大小返回
    # 前端传过来的 currentPage 最小 = 1
    end_index = currentPage * pageSize
    start_index = (currentPage - 1) * pageSize
    logger.info(f"start_index = {start_index}")
    logger.info(f"end_index = {end_index}")

    if start_index == 0 and end_index > len(product_list):
        # 单页数量超过商品数，直接返回
        pass
    elif end_index > db_product_size:
        product_list = product_list[start_index:]
    else:
        product_list = product_list[start_index:end_index]

    # 拼接服务器地址
    # for product in product_list:
    #     product["image_path"] = API_CONFIG.REQUEST_FILES_URL + product["image_path"]
    #     product["instruction"] =  API_CONFIG.REQUEST_FILES_URL + product["instruction"]

    logger.info(product_list)
    logger.info(f"len {len(product_list)}")

    return ProductPageItem(product_list=product_list, currentPage=currentPage, pageSize=pageSize, totalSize=product_total_size)
