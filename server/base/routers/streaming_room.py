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
from datetime import datetime
from pathlib import Path

import requests
from fastapi import APIRouter, Depends
from loguru import logger

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..database.product_db import get_db_product_info
from ..database.streamer_info_db import get_streamers_info
from ..database.streamer_room_db import (
    create_or_update_db_room_by_id,
    delete_room_id,
    get_conversation_list,
    get_db_streaming_room_info,
    update_conversation_message_info,
    update_streaming_room_info,
)
from ..database.user_db import get_db_user_info
from ..models.product_model import ProductInfo
from ..models.streamer_room_model import MessageItem, OnAirRoomStatusItem, RoomChatItem, SalesDocAndVideoInfo, StreamRoomInfo
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
            format_product_list.append(dict(db_product))
        streaming_room_list = dict(streaming_room_list[0])
        streaming_room_list["product_list"] = format_product_list
    else:
        streaming_room_list = []

    return make_return_data(True, ResultCode.SUCCESS, "成功", streaming_room_list)


@router.delete("/delete/{roomId}", summary="删除直播间接口")
async def delete_room_api(roomId: int, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_room_id(roomId, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.get("/product-edit-list/{roomId}", summary="获取直播间商品编辑列表，含有已选中的标识")
async def get_streaming_room_product_list_api(
    roomId: int, currentPage: int = 1, pageSize: int = 0, user_id: int = Depends(get_current_user_info)
):
    """获取直播间商品编辑列表，含有已选中的标识"""

    # 获取目前直播间商品列表
    if roomId == 0:
        # 新的直播间
        streaming_room_info = dict(StreamRoomInfo())
        streaming_room_info["product_list"] = []
    else:
        streaming_room_info = await get_db_streaming_room_info(user_id, roomId)

    if len(streaming_room_info) == 0:
        raise "401"

    # TODO 完成分页

    streaming_room_info = streaming_room_info[0]

    # 获取未被选中的商品
    exclude_list = [product.product_id for product in streaming_room_info.product_list]
    not_select_product_list, db_product_size = await get_db_product_info(user_id=user_id, exclude_list=exclude_list)

    # 合并商品信息
    merge_list = deepcopy(streaming_room_info.product_list)
    for not_select_product in not_select_product_list:
        merge_list.append(
            SalesDocAndVideoInfo(
                product_id=not_select_product.product_id,
                product_info=ProductInfo(**dict(not_select_product)),
                selected=False,
            )
        )

    # 格式化
    format_merge_list = []
    for product in merge_list:
        # 直接返回会导致字段丢失，需要转 dict 确保返回值里面有该字段
        dict_info = dict(product)
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
async def streaming_room_edit_api(edit_item: StreamRoomInfo, user_id: int = Depends(get_current_user_info)):
    pass


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


# ============================================================
#                          开播接口
# ============================================================


@router.post("/chat", summary="直播间开播对话接口")
async def get_on_air_live_room_api(room_chat: RoomChatItem, user_id: int = Depends(get_current_user_info)):
    streaming_room_info = await get_db_streaming_room_info(user_id, room_chat.roomId)

    # 获取直播间对话
    conversation_list = await get_conversation_list(streaming_room_info["status"]["conversation_id"])
    assert len(conversation_list) > 0

    # 获取用户信息
    user_info = await get_db_user_info(user_id)

    user_msg = MessageItem(
        role="user",
        userId=user_id,
        userName=user_info["username"],
        message=room_chat.message,
        avatar=user_info["avatar"],
        messageIndex=conversation_list[-1]["messageIndex"] + 1,
    )
    conversation_list.append(dict(user_msg))

    # 获取商品信息
    prodcut_index = streaming_room_info["status"]["current_product_index"]
    product_info = streaming_room_info["product_list"][prodcut_index]
    product_list, _ = await get_db_product_info(user_id, id=int(product_info["product_id"]))
    product_detail = product_list[0]

    # 根据对话记录生成 prompt
    prompt = await gen_poduct_base_prompt(
        user_id, streaming_room_info["streamer_id"], streaming_room_info["status"]["current_product_id"]
    )  # system + 获取商品文案prompt
    prompt = combine_history(prompt, conversation_list)

    # ====================== Agent ======================
    # 调取 Agent
    agent_response = await get_agent_res(prompt, product_detail["departure_place"], product_detail["delivery_company"])
    if agent_response != "":
        logger.info("Agent 执行成功，不执行 RAG")
        prompt[-1]["content"] = agent_response

    # ====================== RAG ======================
    # 调取 rag
    elif SERVER_PLUGINS_INFO.rag_enabled:
        logger.info("Agent 未执行 or 未开启")
        # agent 失败，调取 rag, chat_item.plugins.rag 为 True，则使用 RAG 查询数据库
        rag_res = build_rag_prompt(RAG_RETRIEVER, product_detail["product_name"], prompt[-1]["content"])
        if rag_res != "":
            prompt[-1]["content"] = rag_res

    # 调取 LLM
    streamer_res = await get_llm_res(prompt)

    # 生成数字人视频，并更新直播间数字人视频信息
    server_video_path = await gen_tts_and_digital_human_video_app(streaming_room_info["streamer_id"], streamer_res)
    streaming_room_info["status"]["streaming_video_path"] = server_video_path

    stream_info = conversation_list[0]
    streamer_msg = MessageItem(
        role="streamer",
        userId=stream_info["userId"],
        userName=stream_info["userName"],
        message=streamer_res,
        avatar=stream_info["avatar"],
        messageIndex=conversation_list[-1]["messageIndex"] + 1,
    )
    conversation_list.append(dict(streamer_msg))

    # 保存对话
    _ = await update_conversation_message_info(streaming_room_info["status"]["conversation_id"], conversation_list)

    # 保存直播间信息
    update_streaming_room_info(streaming_room_info)

    logger.info(streaming_room_info["status"]["conversation_id"])
    logger.info(conversation_list)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


async def get_or_init_conversation(user_id, room_id: int, next_product=False):
    # 根据直播间 ID 获取信息
    streaming_room_info = await get_db_streaming_room_info(user_id, room_id)
    logger.info(streaming_room_info)

    # 根据 ID 获取主播信息
    streamer_info = await get_streamers_info(streaming_room_info["streamer_id"])
    streamer_info = streamer_info[0]

    # 商品信息
    prodcut_index = streaming_room_info["status"]["current_product_index"]

    if next_product:
        # 如果是介绍下一个商品，则进行递增
        prodcut_index += 1

    assert prodcut_index >= 0
    product_info = streaming_room_info["product_list"][prodcut_index]
    product_list, _ = await get_db_product_info(user_id, id=int(product_info["product_id"]))

    # 是否为最后的商品
    if len(streaming_room_info["product_list"]) - 1 == prodcut_index:
        final_procut = True
    else:
        final_procut = False

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
            avatar=streamer_info["avatar"],
            messageIndex=0,
        )
        conversation_list.append(dict(streamer_msg))

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
    update_streaming_room_info(streaming_room_info)

    res_data = {
        "streamerInfo": streamer_info,
        "conversation": conversation_list,
        "currentProductInfo": product_list[0],
        "currentStreamerVideo": streaming_room_info["status"]["streaming_video_path"],
        "currentProductIndex": streaming_room_info["status"]["current_product_index"],
        "startTime": streaming_room_info["status"]["start_time"],
        "currentPoductStartTime": streaming_room_info["status"]["current_product_start_time"],
        "finalProduct": final_procut,
    }

    return res_data


@router.get("/live-info/{roomId}", summary="获取正在直播的直播间信息接口")
async def get_on_air_live_room_api(roomId: int, user_id: int = Depends(get_current_user_info)):
    """获取正在直播的直播间信息

    1. 主播视频地址
    2. 商品信息，显示在右下角的商品缩略图
    3. 对话记录 conversation_list

    Args:
        roomId (int): 直播间 ID
    """

    res_data = await get_or_init_conversation(user_id, roomId, next_product=False)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/next-product/{roomId}", summary="直播间进行下一个商品讲解接口")
async def on_air_live_room_next_product_api(roomId: int, user_id: int = Depends(get_current_user_info)):
    """直播间进行下一个商品讲解

    Args:
        roomId (int): 直播间 ID
    """

    res_data = await get_or_init_conversation(user_id, roomId, next_product=True)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/offline/{roomId}", summary="直播间下播接口")
async def offline_api(roomId: int, user_id: int = Depends(get_current_user_info)):
    # 根据直播间 ID 获取信息
    streaming_room_info = await get_db_streaming_room_info(user_id, roomId)
    logger.info(streaming_room_info)

    streaming_room_info["status"]["live_status"] = 2  # 标志为下播

    # 保存直播间信息
    update_streaming_room_info(streaming_room_info)

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
