from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ..database.streamer_info_db import get_streamers_info
from ..utils import LLM_MODEL_HANDLER, ResultCode, get_llm_product_prompt_base_info, make_return_data
from .products import get_product_list

router = APIRouter(
    prefix="/llm",
    tags=["llm"],
    responses={404: {"description": "Not found"}},
)


class GenProductItem(BaseModel):
    gen_type: str
    instruction: str


class GenSalesDocItem(BaseModel):
    streamerId: int
    productId: int


async def gen_poduct_base_prompt(streamer_id, product_id):
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
    product_list, _ = await get_product_list(id=product_id)
    product_info = product_list[0]

    product_info_str = product_info_struct_template[0].replace("{name}", product_info["product_name"])
    product_info_str += product_info_struct_template[1].replace("{highlights}", "、".join(product_info["heighlights"]))

    # 生成商品文案 prompt
    first_input = first_input_template.replace("{product_info}", product_info_str)

    prompt = [{"role": "system", "content": system_str}, {"role": "user", "content": first_input}]
    logger.info(prompt)

    return prompt


async def get_llm_res(prompt):

    logger.info(prompt)
    model_name = LLM_MODEL_HANDLER.available_models[0]

    res_data = ""
    for item in LLM_MODEL_HANDLER.chat_completions_v1(model=model_name, messages=prompt):
        res_data = item["choices"][0]["message"]["content"]

    return res_data


@router.post("/gen_product_info")
async def get_product_info_api(gen_product_item: GenProductItem):
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


@router.post("/gen_sales_doc")
async def get_product_info_api(gen_sales_doc_item: GenSalesDocItem):
    """生成口播文案

    Args:
        gen_sales_doc_item (GenSalesDocItem): _description_

    Returns:
        _type_: _description_
    """

    prompt = await gen_poduct_base_prompt(gen_sales_doc_item.streamerId, gen_sales_doc_item.productId)

    res_data = await get_llm_res(prompt)

    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)
