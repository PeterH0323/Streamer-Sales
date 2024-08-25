#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
# author: HinGwenWong
# github: https://github.com/PeterH0323/Streamer-Sales
# time: 2024/08/18
"""
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import yaml
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...web_configs import WEB_CONFIGS
from ..utils import (
    ResultCode,
    get_all_streamer_info,
    get_conversation_list,
    get_streamer_info_by_id,
    get_streaming_room_info,
    get_user_info,
    make_return_data,
    update_conversation_message_info,
    update_streaming_room_info,
)
from .products import get_prduct_by_page, get_product_list

router = APIRouter(
    prefix="/streaming-room",
    tags=["streaming-room"],
    responses={404: {"description": "Not found"}},
)


class RoomProductListItem(BaseModel):
    roomId: int
    currentPage: int = 1
    pageSize: int = 10


class RoomChatItem(BaseModel):
    roomId: int
    userId: str
    message: str


class RoomProductEdifItem(BaseModel):
    roomId: int
    name: str
    streamer_id: int
    product: list
    streamerInfo: dict
    room_poster: str | None
    background_image: str | None
    prohibited_words_id: str | None


@dataclass
class MessageItem:
    role: str
    userId: str
    userName: str
    message: str
    avater: str
    messageIndex: int
    datetime: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
        selected_id.update({room_item["product_id"]: room_item})

    product_list, _ = await get_product_list()

    filter_list = []
    for product in product_list:
        if product["product_id"] in selected_id.keys():

            # 更新信息详情
            for k, v in selected_id[product["product_id"]].items():
                if k == "product_id":
                    continue
                product.update({k: v})
            product.update({"selected": True})
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
        "roomId": room_info.roomId,
        "name": streaming_room_info["name"],
        "room_poster": streaming_room_info["room_poster"],
        "streamer_id": streaming_room_info["streamer_id"],
        "background_image": streaming_room_info["background_image"],
        "prohibited_words_id": streaming_room_info["prohibited_words_id"],
        "liveStatus": streaming_room_info["status"]["live_status"],
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
    selected_id = dict()
    for room_item in streaming_room_info["product_list"]:
        selected_id.update({room_item["product_id"]: room_item})

    logger.info(selected_id)

    # 根据选中情况更新 selected 的值，格式化返回的包
    product_all_list = []
    for product in page_info["product"]:

        if product["product_id"] in selected_id:
            sales_doc = selected_id[product["product_id"]]["sales_doc"]
            start_video = selected_id[product["product_id"]]["start_video"]
            start_time = selected_id[product["product_id"]]["start_time"]
        else:
            sales_doc = ""
            start_video = ""
            start_time = ""

        product_all_list.append(
            {
                "name": product["product_name"],
                "product_id": product["product_id"],
                "image": product["image_path"],
                "sales_doc": sales_doc,
                "start_video": start_video,
                "start_time": start_time,
                "selected": True if product["product_id"] in selected_id.keys() else False,
            }
        )

    page_info["product"] = product_all_list

    logger.info(page_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", page_info)


@router.post("/edit/form")
async def streaming_room_edit_api(edit_item: RoomProductEdifItem):
    """新增 or 编辑直播间接口

    Args:
        edit_item (RoomProductEdifItem): _description_
    """
    logger.info(f"get room id = {edit_item.roomId}")

    new_info = dict()

    # 直播间基本信息
    new_info.update({"name": edit_item.name})  # 直播间名字
    new_info.update({"room_poster": edit_item.room_poster})  # 直播间名字
    new_info.update({"background_image": edit_item.background_image})  # 直播间名字
    new_info.update({"prohibited_words_id": edit_item.prohibited_words_id})  # 直播间名字

    # 主播 ID
    new_info.update({"streamer_id": edit_item.streamer_id})

    # 商品 ID
    logger.info(edit_item.product)
    save_product_list = []
    for product in edit_item.product:
        if product.get("selected", False) is False:
            continue
        save_product_list.append(
            {
                "product_id": product["product_id"],
                "start_time": product["start_time"],
                "sales_doc": product["sales_doc"],
                "start_video": product["start_video"],
            }
        )
    new_info.update({"product_list": save_product_list})  # 直播间名字

    # 新建
    streaming_room_info = await get_streaming_room_info()
    max_room_id = -1
    update_index = -1
    for idx, item in enumerate(streaming_room_info):

        if item["room_id"] == edit_item.roomId:
            update_index = idx
            break

        max_room_id = max(item["room_id"], max_room_id)

    if update_index >= 0:
        # 修改
        new_info.update({"room_id": streaming_room_info[update_index]["room_id"]})
        streaming_room_info[update_index] = new_info
    else:
        new_info.update({"room_id": max_room_id + 1})  # 直播间 ID
        streaming_room_info.append(new_info)

    logger.info(new_info)

    # 覆盖保存
    with open(WEB_CONFIGS.STREAMING_ROOM_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(streaming_room_info, f, allow_unicode=True)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.post("/chat")
async def get_on_air_live_room_api(room_chat: RoomChatItem):
    streaming_room_info = await get_streaming_room_info(room_chat.roomId)

    # 获取直播间对话
    conversation_list = await get_conversation_list(streaming_room_info["status"]["conversation_id"])
    assert len(conversation_list) > 0

    # 获取用户信息
    user_info = await get_user_info(room_chat.userId)

    user_msg = MessageItem(
        role="user",
        userId=room_chat.userId,
        userName=user_info["userName"],
        message=room_chat.message,
        avater=user_info["avater"],
        messageIndex=conversation_list[-1]["messageIndex"] + 1,
    )
    conversation_list.append(asdict(user_msg))

    # 调取 LLM & 数字人生成视频
    streamer_res = "你好"  # TODO 改为真实数据

    stream_info = conversation_list[0]
    streamer_msg = MessageItem(
        role="streamer",
        userId=stream_info["userId"],
        userName=stream_info["userName"],
        message=streamer_res,
        avater=stream_info["avater"],
        messageIndex=conversation_list[-1]["messageIndex"] + 1,
    )
    conversation_list.append(asdict(streamer_msg))

    logger.info(streaming_room_info["status"]["conversation_id"])
    logger.info(conversation_list)

    # 保存对话
    _ = await update_conversation_message_info(streaming_room_info["status"]["conversation_id"], conversation_list)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


async def get_or_init_conversation(room_id: int, next_product=False):
    # 根据直播间 ID 获取信息
    streaming_room_info = await get_streaming_room_info(room_id)
    logger.info(streaming_room_info)

    # 根据 ID 获取主播信息
    streamer_info = await get_streamer_info_by_id(streaming_room_info["streamer_id"])
    streamer_info = streamer_info[0]

    # 商品信息
    prodcut_index = streaming_room_info["status"]["current_product_index"]

    if next_product:
        # 如果是介绍下一个商品，则进行递增
        prodcut_index += 1

    assert prodcut_index >= 0
    product_info = streaming_room_info["product_list"][prodcut_index]
    product_list, _ = await get_product_list(id=int(product_info["product_id"]))

    # 获取直播间对话
    if next_product:
        conversation_list = []
    else:
        conversation_list = await get_conversation_list(streaming_room_info["status"]["conversation_id"])

    if len(conversation_list) == 0:
        # 新直播间 or 新产品，需要新建对话
        streamer_msg = MessageItem(
            role="streamer",
            userId=str(streaming_room_info["streamer_id"]),
            userName=streamer_info["name"],
            message=product_info["sales_doc"],
            avater=streamer_info["avater"],
            messageIndex=0,
        )
        conversation_list.append(asdict(streamer_msg))

        #  基本信息完善
        streaming_room_info["status"]["conversation_id"] = str(uuid.uuid4().hex)
        streaming_room_info["status"]["current_product_id"] = product_info["product_id"]
        streaming_room_info["status"]["streaming_video_path"] = product_info["start_video"]
        streaming_room_info["status"]["current_product_index"] = prodcut_index
        streaming_room_info["status"]["start_time"] = (
            streaming_room_info["status"]["start_time"]
            if streaming_room_info["status"]["start_time"] != ""
            else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        streaming_room_info["status"]["current_product_start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        streaming_room_info["status"]["live_status"] = 1  # 0 未开播，1 正在直播，2 下播了

        # 更新商品开始信息
        if streaming_room_info["product_list"][prodcut_index]["start_time"] == "":
            streaming_room_info["product_list"][prodcut_index]["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(streaming_room_info["status"])
    logger.info(conversation_list)
    # 保存对话
    _ = await update_conversation_message_info(streaming_room_info["status"]["conversation_id"], conversation_list)

    # 保存直播间信息
    _ = await update_streaming_room_info(room_id, streaming_room_info)

    res_data = {
        "streamerInfo": streamer_info,
        "conversation": conversation_list,
        "currentProductInfo": product_list[0],
        "currentStreamerVideo": streaming_room_info["status"]["streaming_video_path"],
        "currentProductIndex": streaming_room_info["status"]["current_product_index"],
        "startTime": streaming_room_info["status"]["start_time"],
        "currentPoductStartTime": streaming_room_info["status"]["current_product_start_time"],
    }

    return res_data


@router.post("/live-info")
async def get_on_air_live_room_api(room_info: RoomProductListItem):
    """获取正在直播的直播间信息

    1. 主播视频地址
    2. 商品信息，显示在右下角的商品缩略图
    3. 对话记录 conversation_list

    Args:
        romm_info (RoomProductListItem): 直播间 ID
    """

    res_data = await get_or_init_conversation(room_info.roomId, next_product=False)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/next-product")
async def on_air_live_room_next_product_api(room_info: RoomProductListItem):
    """直播间进行下一个商品讲解

    Args:
        room_info (RoomProductListItem): 直播间 ID
    """

    res_data = await get_or_init_conversation(room_info.roomId, next_product=True)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)
