#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   llm.py
@Time    :   2024/09/02
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   大模型接口
'''


from fastapi import APIRouter, Depends
from loguru import logger

from ..database.llm_db import get_llm_product_prompt_base_info
from ..database.streamer_info_db import get_streamers_info
from ..models.llm_model import GenProductItem, GenSalesDocItem
from ..modules.agent.agent_worker import get_agent_result
from ..server_info import SERVER_PLUGINS_INFO
from ..utils import LLM_MODEL_HANDLER, ResultCode, make_return_data
from .products import get_product_list
from .users import get_current_user_info

router = APIRouter(
    prefix="/llm",
    tags=["llm"],
    responses={404: {"description": "Not found"}},
)


def combine_history(prompt: list, history_msg: list):
    """生成对话历史 prompt

    Args:
        prompt (_type_): _description_
        history_msg (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    # 角色映射表
    role_map = {"streamer": "assistant", "user": "user"}

    # 生成历史对话信息
    for message in history_msg:
        prompt.append({"role": role_map[message["role"]], "content": message["message"]})

    return prompt


async def gen_poduct_base_prompt(user_id, streamer_id, product_id):
    """生成商品介绍的 prompt

    Args:
        streamer_id (_type_): _description_
        product_id (_type_): _description_

    Returns:
        _type_: _description_
    """

    # 加载对话配置文件
    dataset_yaml = await get_llm_product_prompt_base_info()

    # 从配置中提取对话设置相关的信息
    # system_str: 系统词，针对销售角色定制
    # first_input_template: 对话开始时的第一个输入模板
    # product_info_struct_template: 产品信息结构模板
    system = dataset_yaml["conversation_setting"]["system"]
    first_input_template = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct_template = dataset_yaml["product_info_struct"]

    # 根据 ID 获取主播信息
    streamer_info = await get_streamers_info(streamer_id)
    streamer_info = streamer_info[0]

    # 将销售角色名和角色信息插入到 system prompt
    system_str = system.replace("{role_type}", streamer_info["name"]).replace(
        "{character}", "、".join(streamer_info["character"])
    )

    # 根据 ID 获取商品信息
    product_list, _ = await get_product_list(user_id, id=product_id)
    product_info = product_list[0]

    product_info_str = product_info_struct_template[0].replace("{name}", product_info["product_name"])
    product_info_str += product_info_struct_template[1].replace("{highlights}", "、".join(product_info["heighlights"]))

    # 生成商品文案 prompt
    first_input = first_input_template.replace("{product_info}", product_info_str)

    prompt = [{"role": "system", "content": system_str}, {"role": "user", "content": first_input}]
    logger.info(prompt)

    return prompt


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


async def get_llm_res(prompt):

    logger.info(prompt)
    model_name = LLM_MODEL_HANDLER.available_models[0]

    res_data = ""
    for item in LLM_MODEL_HANDLER.chat_completions_v1(model=model_name, messages=prompt):
        res_data = item["choices"][0]["message"]["content"]

    return res_data


@router.post("/gen_product_info")
async def get_product_info_api(gen_product_item: GenProductItem, user_id: int = Depends(get_current_user_info)):
    """TODO 根据说明书内容生成商品信息

    Args:
        gen_product_item (GenProductItem): _description_
    """
    instruction_str = ""
    prompt = [{"system": "现在你是一个文档小助手，你可以从文档里面总结出我需要的信息", "input": ""}]

    res_data = ""
    model_name = LLM_MODEL_HANDLER.available_models[0]
    for item in LLM_MODEL_HANDLER.chat_completions_v1(model=model_name, messages=prompt):
        res_data += item


@router.post("/gen_sales_doc", summary="生成主播文案接口")
async def get_product_info_api(gen_sales_doc_item: GenSalesDocItem, user_id: int = Depends(get_current_user_info)):
    """生成口播文案

    Args:
        gen_sales_doc_item (GenSalesDocItem): _description_

    Returns:
        _type_: _description_
    """

    prompt = await gen_poduct_base_prompt(user_id, gen_sales_doc_item.streamerId, gen_sales_doc_item.productId)

    res_data = await get_llm_res(prompt)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)
