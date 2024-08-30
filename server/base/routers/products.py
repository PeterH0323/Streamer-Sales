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

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from loguru import logger

from ...web_configs import WEB_CONFIGS
from ..database.product_db import get_db_product_info, get_prduct_by_page, get_product_list, get_product_max_id, save_product_info
from ..models.product_model import DeleteProductItem, ProductItem, ProductQueryItem
from ..modules.rag.rag_worker import rebuild_rag_db
from ..utils import ResultCode, delete_item_by_id, make_return_data
from .users import get_current_user_info

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.post("/list", summary="获取分页商品信息接口")
async def get_product_info_api(product_query_item: ProductQueryItem, user_id: int = Depends(get_current_user_info)):

    logger.info(f"Got product_query_item = {product_query_item}")
    res_data = await get_prduct_by_page(
        user_id, product_query_item.currentPage, product_query_item.pageSize, product_query_item.productName
    )
    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.get("/info", summary="获取特定商品 ID 的详细信息接口")
async def get_product_info_api(productId: str, user_id: int = Depends(get_current_user_info)):
    product_list, _ = await get_product_list(user_id, id=int(productId))

    logger.info(product_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", product_list[0])


@router.post("/upload/form", summary="新增 or 编辑商品接口")
async def upload_product_api(upload_product_item: ProductItem, user_id: int = Depends(get_current_user_info)):
    """新增 or 编辑商品

    Args:
        upload_product_item (UploadProductItem): _description_

    Returns:
        _type_: _description_
    """

    # TODO 后续直接插入到数据库就行，无需自行将 id + 1
    # 获取现有数据
    product_info_dict = await get_db_product_info(user_id)

    # 排序防止乱序
    product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["product_id"]))

    new_info_dict = ProductItem(
        user_id=user_id,
        product_name=upload_product_item.product_name,
        heighlights=upload_product_item.heighlights,
        image_path=str(upload_product_item.image_path),
        instruction=str(upload_product_item.instruction),
        departure_place=upload_product_item.departure_place,
        delivery_company=upload_product_item.delivery_company,
        selling_price=upload_product_item.selling_price,
        amount=upload_product_item.amount,
        upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        product_id=get_product_max_id() + 1,
        product_class=upload_product_item.product_class,
        delete=False,
    )

    if upload_product_item.product_name in product_info_dict:
        # 有则更新
        new_info_dict.product_id = product_info_dict[upload_product_item.product_name]["product_id"]  # 使用原来的 ID

    # 保存
    save_product_info(upload_product_item.product_name, dict(new_info_dict))

    if WEB_CONFIGS.ENABLE_RAG:
        # 重新生成 RAG 向量数据库
        rebuild_rag_db()

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.post("/instruction", summary="获取对应商品的说明书内容接口")
async def get_product_info_api(instruction_path: ProductQueryItem, user_id: int = Depends(get_current_user_info)):
    """获取对应商品的说明书

    Args:
        instruction_path (ProductInstructionItem): _description_

    """

    loacl_path = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(
        WEB_CONFIGS.PRODUCT_FILE_DIR, WEB_CONFIGS.INSTRUCTIONS_DIR, Path(instruction_path.instructionPath).name
    )
    if not loacl_path.exists():
        return make_return_data(False, ResultCode.FAIL, "文件不存在", "")

    # TODO 根据 user id 检查文件归属

    with open(loacl_path, "r") as f:
        instruction_content = f.read()

    return make_return_data(True, ResultCode.SUCCESS, "成功", instruction_content)


@router.post("/delete", summary="删除特定商品 ID 接口")
async def upload_product_api(delete_info: DeleteProductItem, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_item_by_id("product", delete_info.product_id, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")
