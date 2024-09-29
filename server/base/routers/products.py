#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   products.py
@Time    :   2024/08/30
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   商品信息接口
"""

from pathlib import Path

from fastapi import APIRouter, Depends

from ...web_configs import WEB_CONFIGS
from ..database.product_db import (
    create_or_update_db_product_by_id,
    delete_product_id,
    get_db_product_info,
)
from ..models.product_model import ProductInfo, ProductPageItem, ProductQueryItem
from ..modules.rag.rag_worker import rebuild_rag_db
from ..utils import ResultCode, make_return_data
from .users import get_current_user_info

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.get("/list", summary="获取分页商品信息接口")
async def get_product_info_api(
    currentPage: int = 1, pageSize: int = 5, productName: str | None = None, user_id: int = Depends(get_current_user_info)
):
    product_list, db_product_size = await get_db_product_info(
        user_id=user_id,
        current_page=currentPage,
        page_size=pageSize,
        product_name=productName,
    )

    res_data = ProductPageItem(product_list=product_list, currentPage=currentPage, pageSize=pageSize, totalSize=db_product_size)
    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.get("/info/{productId}", summary="获取特定商品 ID 的详细信息接口")
async def get_product_id_info_api(productId: int, user_id: int = Depends(get_current_user_info)):
    product_list, _ = await get_db_product_info(user_id=user_id, product_id=productId)

    if len(product_list) == 1:
        product_list = product_list[0]

    return make_return_data(True, ResultCode.SUCCESS, "成功", product_list)


@router.post("/create", summary="新增商品接口")
async def upload_product_api(upload_product_item: ProductInfo, user_id: int = Depends(get_current_user_info)):

    upload_product_item.user_id = user_id
    upload_product_item.product_id = None

    rebuild_rag_db_flag = create_or_update_db_product_by_id(0, upload_product_item)

    if WEB_CONFIGS.ENABLE_RAG and rebuild_rag_db_flag:
        # 重新生成 RAG 向量数据库
        await rebuild_rag_db(user_id)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.put("/edit/{product_id}", summary="编辑商品接口")
async def upload_product_api(product_id: int, upload_product_item: ProductInfo, user_id: int = Depends(get_current_user_info)):

    rebuild_rag_db_flag = create_or_update_db_product_by_id(product_id, upload_product_item, user_id)

    if WEB_CONFIGS.ENABLE_RAG and rebuild_rag_db_flag:
        # 重新生成 RAG 向量数据库
        await rebuild_rag_db(user_id)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.delete("/delete/{productId}", summary="删除特定商品 ID 接口")
async def upload_product_api(productId: int, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_product_id(productId, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    if WEB_CONFIGS.ENABLE_RAG:
        # 重新生成 RAG 向量数据库
        await rebuild_rag_db(user_id)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.post("/instruction", summary="获取对应商品的说明书内容接口", dependencies=[Depends(get_current_user_info)])
async def get_product_instruction_info_api(instruction_path: ProductQueryItem):
    """获取对应商品的说明书

    Args:
        instruction_path (ProductInstructionItem): 说明书路径

    """
    # TODO 后续改为前端 axios 直接获取
    loacl_path = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(
        WEB_CONFIGS.PRODUCT_FILE_DIR, WEB_CONFIGS.INSTRUCTIONS_DIR, Path(instruction_path.instructionPath).name
    )
    if not loacl_path.exists():
        return make_return_data(False, ResultCode.FAIL, "文件不存在", "")

    with open(loacl_path, "r") as f:
        instruction_content = f.read()

    return make_return_data(True, ResultCode.SUCCESS, "成功", instruction_content)
