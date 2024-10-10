#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   llm.py
@Time    :   2024/09/02
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   大模型接口
"""


from typing import Dict, List

from fastapi import APIRouter, Depends
from loguru import logger

from ..database.llm_db import get_llm_product_prompt_base_info
from ..database.product_db import get_db_product_info
from ..database.streamer_info_db import get_db_streamer_info
from ..models.product_model import ProductInfo
from ..models.streamer_info_model import StreamerInfo
from ..modules.agent.agent_worker import get_agent_result
from ..server_info import SERVER_PLUGINS_INFO
from ..utils import LLM_MODEL_HANDLER, ResultCode, make_return_data
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
        history_msg (_type_): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    # 角色映射表
    role_map = {"streamer": "assistant", "user": "user"}

    # 生成历史对话信息
    for message in history_msg:
        prompt.append({"role": role_map[message["role"]], "content": message["message"]})

    return prompt


async def gen_poduct_base_prompt(
    user_id: int,
    streamer_id: int = -1,
    product_id: int = -1,
    streamer_info: StreamerInfo | None = None,
    product_info: ProductInfo | None = None,
) -> List[Dict[str, str]]:
    """生成商品介绍的 prompt

    Args:
        user_id (int): 用户 ID
        streamer_id (int): 主播 ID
        product_id (int): 商品 ID
        streamer_info (StreamerInfo, optional): 主播信息，如果为空则根据 streamer_id 查表
        product_info (ProductInfo, optional): 商品信息，如果为空则根据 product_id 查表

    Returns:
        List[Dict[str,str]]: 生成的 promot
    """

    assert (streamer_id == -1 and streamer_info is not None) or (streamer_id != -1 and streamer_info is None)
    assert (product_id == -1 and product_info is not None) or (product_id != -1 and product_info is None)

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
    if streamer_info is None:
        streamer_info = await get_db_streamer_info(user_id, streamer_id)
        streamer_info = streamer_info[0]

    # 将销售角色名和角色信息插入到 system prompt
    character_str = streamer_info.character.replace(";", "、")
    system_str = system.replace("{role_type}", streamer_info.name).replace("{character}", character_str)

    # 根据 ID 获取商品信息
    if product_info is None:
        product_list, _ = await get_db_product_info(user_id, product_id=product_id)
        product_info = product_list[0]

    heighlights_str = product_info.heighlights.replace(";", "、")
    product_info_str = product_info_struct_template[0].replace("{name}", product_info.product_name)
    product_info_str += product_info_struct_template[1].replace("{highlights}", heighlights_str)

    # 生成商品文案 prompt
    sales_doc_prompt = first_input_template.replace("{product_info}", product_info_str)

    prompt = [{"role": "system", "content": system_str}, {"role": "user", "content": sales_doc_prompt}]
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
    """获取 LLM 推理返回

    Args:
        prompt (str): _description_

    Returns:
        _type_: _description_
    """

    logger.info(prompt)
    model_name = LLM_MODEL_HANDLER.available_models[0]

    res_data = ""
    for item in LLM_MODEL_HANDLER.chat_completions_v1(model=model_name, messages=prompt):
        res_data = item["choices"][0]["message"]["content"]

    return res_data


@router.get("/gen_sales_doc", summary="生成主播文案接口")
async def get_product_info_api(streamer_id: int, product_id: int, user_id: int = Depends(get_current_user_info)):
    """生成口播文案

    Args:
        streamer_id (int): 主播 ID，用于获取性格等信息
        product_id (int): 商品 ID
    """

    prompt = await gen_poduct_base_prompt(user_id, streamer_id, product_id)

    res_data = await get_llm_res(prompt)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.get("/gen_product_info")
async def get_product_info_api(product_id: int, user_id: int = Depends(get_current_user_info)):
    """TODO 根据说明书内容生成商品信息

    Args:
        gen_product_item (GenProductItem): _description_
    """

    raise NotImplemented()
    instruction_str = ""
    prompt = [{"system": "现在你是一个文档小助手，你可以从文档里面总结出我需要的信息", "input": ""}]

    res_data = ""
    model_name = LLM_MODEL_HANDLER.available_models[0]
    for item in LLM_MODEL_HANDLER.chat_completions_v1(model=model_name, messages=prompt):
        res_data += item
