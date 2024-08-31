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
from datetime import datetime
from typing import List

import yaml
from fastapi import APIRouter, Depends
from loguru import logger

from ...web_configs import WEB_CONFIGS
from ..database.streamer_info_db import get_streamers_info
from ..database.streamer_room_db import (
    get_conversation_list,
    get_streaming_room_info,
    update_conversation_message_info,
    update_streaming_room_info,
)
from ..database.user_db import get_user_info
from ..models.product_model import ProductPageItem
from ..models.streamer_room_model import (
    MessageItem,
    OnAirRoomStatusItem,
    RoomChatItem,
    RoomProductListItem,
    StreamRoomDetailItem,
    StreamRoomInfoDatabaseItem,
    StreamRoomInfoReponseItem,
    StreamRoomProductDatabaseItem,
    StreamRoomProductItem,
)
from ..modules.agent.agent_worker import get_agent_result
from ..modules.rag.rag_worker import RAG_RETRIEVER, build_rag_prompt
from ..routers.users import get_current_user_info
from ..server_info import SERVER_PLUGINS_INFO
from ..utils import LLM_MODEL_HANDLER, ResultCode, combine_history, delete_item_by_id, make_return_data
from .digital_human import gen_tts_and_digital_human_video_app
from .llm import gen_poduct_base_prompt, get_llm_res
from .products import get_prduct_by_page, get_product_list

router = APIRouter(
    prefix="/streaming-room",
    tags=["streaming-room"],
    responses={404: {"description": "Not found"}},
)


@router.post("/list", summary="获取所有直播间信息接口")
async def get_streaming_room_api(user_id: int = Depends(get_current_user_info)):
    """获取所有直播间信息"""
    # 加载直播间数据
    streaming_room_list = await get_streaming_room_info(user_id)
    logger.info(streaming_room_list)

    # 加载到返回数据格式
    res_room_list = [StreamRoomInfoReponseItem(**(info.model_dump())) for info in streaming_room_list]

    for room in res_room_list:
        # 因为数据库中保存的是 主播 ID ，需要查库拿到 主播信息
        streamer_info = await get_streamers_info(user_id, room.streamer_id)
        room.streamer_info = streamer_info[0]

    logger.info(res_room_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", res_room_list)


@router.post("/detail", summary="获取特定直播间信息接口")
async def get_streaming_room_api(room_info: RoomProductListItem, user_id: int = Depends(get_current_user_info)):
    """获取特定直播间信息"""
    # 加载直播间配置文件
    streaming_room_info = await get_streaming_room_info(user_id, room_info.roomId)

    # 将直播间的商品 ID 进行提取，后续作为 选中 id
    selected_id = dict()
    for room_item in streaming_room_info["product_list"]:
        selected_id.update({room_item["product_id"]: room_item})

    product_list, _ = await get_product_list(user_id)

    filter_list = []
    for product in product_list:
        if product["product_id"] not in selected_id.keys():
            continue

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
    streamer_list = await get_streamers_info(user_id)
    streamer_info = dict()
    for i in streamer_list:
        if i["id"] == streaming_room_info["streamer_id"]:
            streamer_info = i
            break

    res_data = StreamRoomDetailItem(
        streamer_info=streamer_info,
        product_list=filter_list,
        currentPage=room_info.currentPage,
        pageSize=room_info.pageSize,
        totalSize=total_size,
        room_id=room_info.roomId,
        name=streaming_room_info["name"],
        room_poster=streaming_room_info["room_poster"],
        streamer_id=streaming_room_info["streamer_id"],
        background_image=streaming_room_info["background_image"],
        prohibited_words_id=streaming_room_info["prohibited_words_id"],
        status=streaming_room_info["status"],
    )

    logger.info(res_data)
    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/product-add", summary="直播间编辑or添加商品接口")
async def get_streaming_room_api(room_info: RoomProductListItem, user_id: int = Depends(get_current_user_info)):
    """直播间编辑or添加商品"""

    logger.info(room_info)
    # 加载对话配置文件
    if room_info.roomId == 0:
        # 新的直播间
        streaming_room_info = dict(StreamRoomInfoDatabaseItem())
        streaming_room_info["product_list"] = []
    else:
        streaming_room_info = await get_streaming_room_info(user_id, room_info.roomId)

    if room_info.pageSize > 0:
        # 按页返回
        page_info = await get_prduct_by_page(user_id, room_info.currentPage, room_info.pageSize)
    else:
        # 全部返回
        product_list, db_product_size = await get_product_list(user_id)
        page_info = dict(
            ProductPageItem(
                product_list=product_list,
                current=room_info.currentPage,
                pageSize=db_product_size,
                totalSize=db_product_size,
            )
        )

    logger.info(streaming_room_info)

    # 将直播间的商品 ID 进行提取，后续作为 选中 id
    selected_id = dict()
    for room_item in streaming_room_info["product_list"]:
        selected_id.update({room_item["product_id"]: room_item})

    logger.info(selected_id)

    # 根据选中情况更新 selected 的值，格式化返回的包
    product_all_list = []
    for product in page_info["product_list"]:

        product = dict(product)
        if product["product_id"] in selected_id:
            sales_doc = selected_id[product["product_id"]]["sales_doc"]
            start_video = selected_id[product["product_id"]]["start_video"]
            start_time = selected_id[product["product_id"]]["start_time"]
        else:
            sales_doc = ""
            start_video = ""
            start_time = ""

        product_item_info = StreamRoomProductItem(
            **product,
            sales_doc=sales_doc,
            start_video=start_video,
            start_time=start_time,
            selected=True if product["product_id"] in selected_id.keys() else False,
        )
        product_all_list.append(product_item_info)

    page_info["product_list"] = product_all_list

    logger.info(page_info)
    return make_return_data(True, ResultCode.SUCCESS, "成功", page_info)


@router.post("/edit/form", summary="新增 or 编辑直播间接口")
async def streaming_room_edit_api(edit_item: StreamRoomInfoReponseItem, user_id: int = Depends(get_current_user_info)):
    """新增 or 编辑直播间接口

    Args:
        edit_item (StreamRoomInfoReponseItem): _description_
    """
    logger.info(f"get room id = {edit_item.room_id}")

    new_info = StreamRoomInfoDatabaseItem(
        user_id=user_id,
        streamer_id=edit_item.streamer_id,
        name=edit_item.name,
        product_list=[],
        status=OnAirRoomStatusItem(),
        room_poster=edit_item.room_poster,
        background_image=edit_item.background_image,
        prohibited_words_id=edit_item.prohibited_words_id,
        delete=False,
    )

    # 商品 ID
    logger.info(edit_item.product_list)
    save_product_list = []
    for product in edit_item.product_list:
        product = dict(product)
        if product.get("selected", False) is False:
            continue
        save_product_list.append(dict(StreamRoomProductDatabaseItem(**product)))
    new_info.product_list = save_product_list

    # 更新 直播间状态
    if edit_item.status is None:
        new_status = OnAirRoomStatusItem(current_product_id=save_product_list[0]["product_id"])
        new_info.status = new_status
    else:
        new_info.status = edit_item.status  # 直播间状态

    # 新建
    streaming_room_info = await get_streaming_room_info(user_id)
    max_room_id = -1
    update_index = -1
    for idx, item in enumerate(streaming_room_info):

        if item["room_id"] == edit_item.room_id:
            update_index = idx
            break

        max_room_id = max(item["room_id"], max_room_id)

    if update_index >= 0:
        # 修改
        logger.info("已有 ID，编辑模式，修改对应配置")
        new_info.room_id = streaming_room_info[update_index]["room_id"]
        streaming_room_info[update_index] = new_info
    else:
        logger.info("新 ID，新增模式，新增对应配置")
        new_info.room_id = max_room_id + 1  # 直播间 ID
        new_info.delete = False
        streaming_room_info.append(new_info)

    logger.info(new_info)
    new_info.status = dict(new_info.status)
    _ = await update_streaming_room_info(new_info.room_id, new_info)

    return make_return_data(True, ResultCode.SUCCESS, "成功", new_info.room_id)


async def get_agent_res(prompt, departure_place, delivery_company):
    """调用 Agent 能力"""
    agent_response = ""

    if not SERVER_PLUGINS_INFO.agent_enabled:
        # 如果不开启则直接返回空
        return ""

    GENERATE_AGENT_TEMPLATE = (
        "这是网上获取到的信息：“{}”\n 客户的问题：“{}” \n 请认真阅读信息并运用你的性格进行解答。"  # Agent prompt 模板
    )
    input_prompt = prompt[-1]["content"]
    agent_response = get_agent_result(LLM_MODEL_HANDLER, input_prompt, departure_place, delivery_company)
    if agent_response != "":
        agent_response = GENERATE_AGENT_TEMPLATE.format(agent_response, input_prompt)
        logger.info(f"Agent response: {agent_response}")

    return agent_response


@router.post("/chat", summary="直播间开播对话接口")
async def get_on_air_live_room_api(room_chat: RoomChatItem, user_id: int = Depends(get_current_user_info)):
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
    conversation_list.append(dict(user_msg))

    # 获取商品信息
    prodcut_index = streaming_room_info["status"]["current_product_index"]
    product_info = streaming_room_info["product_list"][prodcut_index]
    product_list, _ = await get_product_list(id=int(product_info["product_id"]))
    product_detail = product_list[0]

    # 根据对话记录生成 prompt
    prompt = await gen_poduct_base_prompt(
        streaming_room_info["streamer_id"], streaming_room_info["status"]["current_product_id"]
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

    # 调取 LLM & 数字人生成视频
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
        avater=stream_info["avater"],
        messageIndex=conversation_list[-1]["messageIndex"] + 1,
    )
    conversation_list.append(dict(streamer_msg))

    # 保存对话
    _ = await update_conversation_message_info(streaming_room_info["status"]["conversation_id"], conversation_list)

    # 保存直播间信息
    _ = await update_streaming_room_info(room_chat.roomId, streaming_room_info)

    logger.info(streaming_room_info["status"]["conversation_id"])
    logger.info(conversation_list)

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


async def get_or_init_conversation(room_id: int, next_product=False):
    # 根据直播间 ID 获取信息
    streaming_room_info = await get_streaming_room_info(room_id)
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
    product_list, _ = await get_product_list(id=int(product_info["product_id"]))

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
            avater=streamer_info["avater"],
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
    _ = await update_streaming_room_info(room_id, streaming_room_info)

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


@router.post("/live-info", summary="获取正在直播的直播间信息接口")
async def get_on_air_live_room_api(room_info: RoomProductListItem, user_id: int = Depends(get_current_user_info)):
    """获取正在直播的直播间信息

    1. 主播视频地址
    2. 商品信息，显示在右下角的商品缩略图
    3. 对话记录 conversation_list

    Args:
        room_info (RoomProductListItem): 直播间 ID
    """

    res_data = await get_or_init_conversation(room_info.roomId, next_product=False)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/next-product", summary="直播间进行下一个商品讲解接口")
async def on_air_live_room_next_product_api(room_info: RoomProductListItem, user_id: int = Depends(get_current_user_info)):
    """直播间进行下一个商品讲解

    Args:
        room_info (RoomProductListItem): 直播间 ID
    """

    res_data = await get_or_init_conversation(room_info.roomId, next_product=True)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.post("/delete", summary="删除直播间接口")
async def upload_product_api(delete_info: RoomProductListItem, user_id: int = Depends(get_current_user_info)):

    process_success_flag = await delete_item_by_id("room", delete_info.roomId, user_id)

    if not process_success_flag:
        return make_return_data(False, ResultCode.FAIL, "失败", "")

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")
