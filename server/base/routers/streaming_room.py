#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
# author: HinGwenWong
# github: https://github.com/PeterH0323/Streamer-Sales
# time: 2024/08/18
"""
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...web_configs import WEB_CONFIGS
from ..utils import ResultCode, get_all_streamer_info, get_streaming_room_info, make_return_data
from .products import get_product_list, get_prduct_by_page

router = APIRouter(
    prefix="/streaming-room",
    tags=["streaming-room"],
    responses={404: {"description": "Not found"}},
)


class RoomProductListItem(BaseModel):
    roomId: int
    currentPage: int
    pageSize: int


@router.post("/list")
async def get_streaming_room_api():
    """获取所有直播间信息"""
    # 加载直播间配置文件
    streaming_room_list = await get_streaming_room_info()

    logger.info(streaming_room_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", streaming_room_list)


@router.post("/detail")
async def get_streaming_room_api(room_info: RoomProductListItem):
    """获取特定直播间信息"""
    # 加载直播间配置文件
    streaming_room_info = await get_streaming_room_info(room_info.roomId)
    # 将直播间的商品 ID 进行提取，后续作为 选中 id
    selected_id = dict()
    for room_item in streaming_room_info["product_list"]:
        selected_id.update({room_item["id"]: room_item})

    product_list, _ = await get_product_list()

    filter_list = []
    for product in product_list:
        if product["product_id"] in selected_id.keys():

            # 更新信息详情
            for k, v in selected_id[product["product_id"]].items():
                if k == "id":
                    continue
                product.update({k: v})

            filter_list.append(product)

    total_size = len(filter_list)

    # 分页
    end_index = room_info.currentPage * room_info.pageSize
    start_index = (room_info.currentPage - 1) * room_info.pageSize
    logger.info(f"start_index = {start_index}")
    logger.info(f"end_index = {end_index}")

    if start_index == 0 and end_index > len(filter_list):
        # 单页数量超过商品数，直接返回
        pass
    elif end_index > total_size:
        filter_list = filter_list[start_index:]
    else:
        filter_list = filter_list[start_index:end_index]

    # 主播信息
    streamer_list = await get_all_streamer_info()
    streamer_info = dict()
    for i in streamer_list:
        if i["id"] == streaming_room_info["streamer_id"]:
            streamer_info = i
            break

    res_data = {
        "streamerInfo": streamer_info,
        "product": filter_list,
        "currentPage": room_info.currentPage,
        "pageSize": room_info.pageSize,
        "totalSize": total_size,
    }

    logger.info(res_data)
    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/product-add")
async def get_streaming_room_api(romm_info: RoomProductListItem):
    """直播间编辑中添加商品"""
    # 加载对话配置文件
    streaming_room_info = await get_streaming_room_info(romm_info.roomId)

    if romm_info.pageSize > 0:
        # 按页返回
        page_info = await get_prduct_by_page(romm_info.currentPage, romm_info.pageSize)
    else:
        # 全部返回
        product_list, db_product_size = await get_product_list()
        page_info = {
            "product": product_list,
            "current": romm_info.currentPage,
            "pageSize": db_product_size,
            "totalSize": db_product_size,
        }

    logger.info(streaming_room_info)

    # 将直播间的商品 ID 进行提取，后续作为 选中 id
    selected_id = []
    for room_item in streaming_room_info["product_list"]:
        selected_id.append(room_item["id"])

    # 根据选中情况更新 selected 的值，格式化返回的包
    product_all_list = []
    for product in page_info["product"]:
        product_all_list.append(
            {
                "name": product["product_name"],
                "id": product["product_id"],
                "image": product["image_path"],
                "selected": True if product["product_id"] in selected_id else False,
            }
        )

    page_info["product"] = product_all_list

    logger.info(page_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", page_info)
