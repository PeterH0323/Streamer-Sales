#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   streaming_room.py
@Time    :   2024/08/31
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   主播间信息交互接口
"""

import uuid
from copy import deepcopy
from pathlib import Path

import requests
from fastapi import APIRouter, Depends
from loguru import logger

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..database.product_db import get_db_product_info
from ..database.streamer_room_db import (
    create_or_update_db_room_by_id,
    get_live_room_info,
    get_message_list,
    update_db_room_status,
    delete_room_id,
    get_db_streaming_room_info,
    update_message_info,
    update_room_video_path,
)
from ..models.product_model import ProductInfo
from ..models.streamer_room_model import OnAirRoomStatusItem, RoomChatItem, SalesDocAndVideoInfo, StreamRoomInfo
from ..modules.rag.rag_worker import RAG_RETRIEVER, build_rag_prompt
from ..routers.users import get_current_user_info
from ..server_info import SERVER_PLUGINS_INFO
from ..utils import ResultCode, make_return_data
from .digital_human import gen_tts_and_digital_human_video_app
from .llm import combine_history, gen_poduct_base_prompt, get_agent_res, get_llm_res

router = APIRouter(
    prefix="/streaming-room",
    tags=["streaming-room"],
    responses={404: {"description": "Not found"}},
)


@router.get("/list", summary="获取所有直播间信息接口")
async def get_streaming_room_api(user_id: int = Depends(get_current_user_info)):
    """获取所有直播间信息"""
    # 加载直播间数据
    streaming_room_list = await get_db_streaming_room_info(user_id)

    for i in range(len(streaming_room_list)):
        # 直接返回会导致字段丢失，需要转 dict 确保返回值里面有该字段
        streaming_room_list[i] = dict(streaming_room_list[i])

    return make_return_data(True, ResultCode.SUCCESS, "成功", streaming_room_list)


@router.get("/info/{roomId}", summary="获取特定直播间信息接口")
async def get_streaming_room_id_api(
    roomId: int, currentPage: int = 1, pageSize: int = 5, user_id: int = Depends(get_current_user_info)
):
    """获取特定直播间信息"""
    # 加载直播间配置文件
    assert roomId != 0

    # TODO 加入分页

    # 加载直播间数据
    streaming_room_list = await get_db_streaming_room_info(user_id, room_id=roomId)

    if len(streaming_room_list) == 1:
        # 直接返回会导致字段丢失，需要转 dict 确保返回值里面有该字段
        format_product_list = []
        for db_product in streaming_room_list[0].product_list:

            product_dict = dict(db_product)
            # 将 start_video 改为服务器地址
            if product_dict["start_video"] != "":
                product_dict["start_video"] = API_CONFIG.REQUEST_FILES_URL + product_dict["start_video"]

            format_product_list.append(product_dict)
        streaming_room_list = dict(streaming_room_list[0])
        streaming_room_list["product_list"] = format_product_list
    else:
        streaming_room_list = []

    return make_return_data(True, ResultCode.SUCCESS, "成功", streaming_room_list)


@router.get("/product-edit-list/{roomId}", summary="获取直播间商品编辑列表，含有已选中的标识")
async def get_streaming_room_product_list_api(
    roomId: int, currentPage: int = 1, pageSize: int = 0, user_id: int = Depends(get_current_user_info)
):
    """获取直播间商品编辑列表，含有已选中的标识"""

    # 获取目前直播间商品列表
    if roomId == 0:
        # 新的直播间
        merge_list = []
        exclude_list = []
    else:
        streaming_room_info = await get_db_streaming_room_info(user_id, roomId)

        if len(streaming_room_info) == 0:
            raise "401"

        streaming_room_info = streaming_room_info[0]
        # 获取未被选中的商品
        exclude_list = [product.product_id for product in streaming_room_info.product_list]
        merge_list = deepcopy(streaming_room_info.product_list)

    # 获取未选中的商品信息
    not_select_product_list, db_product_size = await get_db_product_info(user_id=user_id, exclude_list=exclude_list)

    # 合并商品信息
    for not_select_product in not_select_product_list:
        merge_list.append(
            SalesDocAndVideoInfo(
                product_id=not_select_product.product_id,
                product_info=ProductInfo(**dict(not_select_product)),
                selected=False,
            )
        )

    # TODO 懒加载分页

    # 格式化
    format_merge_list = []
    for product in merge_list:
        # 直接返回会导致字段丢失，需要转 dict 确保返回值里面有该字段
        dict_info = dict(product)
        if "stream_room" in dict_info:
            dict_info.pop("stream_room")
        format_merge_list.append(dict_info)

    page_info = dict(
        product_list=format_merge_list,
        current=currentPage,
        pageSize=db_product_size,
        totalSize=db_product_size,
    )
    logger.info(page_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", page_info)


@router.post("/create", summary="新增直播间接口")
async def streaming_room_edit_api(edit_item: dict, user_id: int = Depends(get_current_user_info)):
    product_list = edit_item.pop("product_list")
    status = edit_item.pop("status")
    edit_item.pop("streamer_info")
    edit_item.pop("room_id")

    if "status_id" in edit_item:
        edit_item.pop("status_id")

    formate_product_list = []
    for product in product_list:
        if not product["selected"]:
            continue
        product.pop("product_info")
        product_item = SalesDocAndVideoInfo(**product)
        formate_product_list.append(product_item)

    edit_item["user_id"] = user_id
    formate_info = StreamRoomInfo(**edit_item, product_list=formate_product_list, status=OnAirRoomStatusItem(**status))
    room_id = create_or_update_db_room_by_id(0, formate_info, user_id)
    return make_return_data(True, ResultCode.SUCCESS, "成功", room_id)


@router.put("/edit/{room_id}", summary="编辑直播间接口")
async def streaming_room_edit_api(room_id: int, edit_item: dict, user_id: int = Depends(get_current_user_info)):
    """编辑直播间接口

    Args:
        edit_item (StreamRoomInfo): _description_
    """

    product_list = edit_item.pop("product_list")
    status = edit_item.pop("status")
    edit_item.pop("streamer_info")

    formate_product_list = []
    for product in product_list:
        if not product["selected"]:
            continue
        product.pop("product_info")
        product_item = SalesDocAndVideoInfo(**product)
        formate_product_list.append(product_item)

    formate_info = StreamRoomInfo(**edit_item, product_list=formate_product_list, status=OnAirRoomStatusItem(**status))
    create_or_update_db_room_by_id(room_id, formate_info, user_id)
    return make_return_data(True, ResultCode.SUCCESS, "成功", room_id)


@router.delete("/delete/{roomId}", summary="删除直播间接口")
async def delete_room_api(roomId: int, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_room_id(roomId, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


# ============================================================
#                          开播接口
# ============================================================


@router.post("/online/{roomId}", summary="直播间开播接口")
async def offline_api(roomId: int, user_id: int = Depends(get_current_user_info)):

    update_db_room_status(roomId, user_id, "online")
    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.put("/offline/{roomId}", summary="直播间下播接口")
async def offline_api(roomId: int, user_id: int = Depends(get_current_user_info)):

    update_db_room_status(roomId, user_id, "offline")
    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.post("/next-product/{roomId}", summary="直播间进行下一个商品讲解接口")
async def on_air_live_room_next_product_api(roomId: int, user_id: int = Depends(get_current_user_info)):
    """直播间进行下一个商品讲解

    Args:
        roomId (int): 直播间 ID
    """

    update_db_room_status(roomId, user_id, "next-product")
    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.get("/live-info/{roomId}", summary="获取正在直播的直播间信息接口")
async def get_on_air_live_room_api(roomId: int, user_id: int = Depends(get_current_user_info)):
    """获取正在直播的直播间信息

    1. 主播视频地址
    2. 商品信息，显示在右下角的商品缩略图
    3. 对话记录 conversation_list

    Args:
        roomId (int): 直播间 ID
    """

    res_data = await get_live_room_info(user_id, roomId)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.put("/chat", summary="直播间对话接口")
async def get_on_air_live_room_api(room_chat: RoomChatItem, user_id: int = Depends(get_current_user_info)):
    # 根据直播间 ID 获取信息
    streaming_room_info = await get_db_streaming_room_info(user_id, room_chat.roomId)
    streaming_room_info = streaming_room_info[0]

    # 商品索引
    product_detail = streaming_room_info.product_list[streaming_room_info.status.current_product_index].product_info

    # 销售 ID
    sales_info_id = streaming_room_info.product_list[streaming_room_info.status.current_product_index].sales_info_id

    # 更新对话记录
    update_message_info(sales_info_id, user_id, role="user", message=room_chat.message)

    # 获取最新的对话记录
    conversation_list = get_message_list(sales_info_id)

    # 根据对话记录生成 prompt
    prompt = await gen_poduct_base_prompt(
        user_id,
        streamer_info=streaming_room_info.streamer_info,
        product_info=product_detail,
    )  # system + 获取商品文案prompt

    prompt = combine_history(prompt, conversation_list)

    # ====================== Agent ======================
    # 调取 Agent
    agent_response = await get_agent_res(prompt, product_detail.departure_place, product_detail.delivery_company)
    if agent_response != "":
        logger.info("Agent 执行成功，不执行 RAG")
        prompt[-1]["content"] = agent_response

    # ====================== RAG ======================
    # 调取 rag
    elif SERVER_PLUGINS_INFO.rag_enabled:
        logger.info("Agent 未执行 or 未开启，调用 RAG")
        # agent 失败，调取 rag, chat_item.plugins.rag 为 True，则使用 RAG 查询数据库
        rag_res = build_rag_prompt(RAG_RETRIEVER, product_detail.product_name, prompt[-1]["content"])
        if rag_res != "":
            prompt[-1]["content"] = rag_res

    # 调取 LLM
    streamer_res = await get_llm_res(prompt)

    # 生成数字人视频
    server_video_path = await gen_tts_and_digital_human_video_app(streaming_room_info.streamer_info.streamer_id, streamer_res)

    # 更新直播间数字人视频信息
    update_room_video_path(streaming_room_info.status_id, server_video_path)

    # 更新对话记录
    update_message_info(sales_info_id, streaming_room_info.streamer_info.streamer_id, role="streamer", message=streamer_res)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.post("/asr", summary="直播间调取 ASR 语音转文字 接口")
async def get_on_air_live_room_api(room_chat: RoomChatItem, user_id: int = Depends(get_current_user_info)):

    # room_chat.asr_file 是 服务器地址，需要进行转换
    asr_local_path = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(WEB_CONFIGS.ASR_FILE_DIR, Path(room_chat.asrFileUrl).name)

    # 获取 ASR 结果
    req_data = {
        "user_id": user_id,
        "request_id": str(uuid.uuid1()),
        "wav_path": str(asr_local_path),
    }
    logger.info(req_data)

    res = requests.post(API_CONFIG.ASR_URL, json=req_data).json()
    asr_str = res["result"]
    logger.info(f"ASR res = {asr_str}")

    # 删除过程文件
    asr_local_path.unlink()
    return make_return_data(True, ResultCode.SUCCESS, "成功", asr_str)
