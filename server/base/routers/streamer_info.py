from datetime import datetime
from pathlib import Path
import yaml
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...web_configs import WEB_CONFIGS

router = APIRouter(
    prefix="/streamer",
    tags=["streamer"],
    responses={404: {"description": "Not found"}},
)


class StreamerInfoItem(BaseModel):
    id: int
    character: str
    imageUrl: str
    name: str
    videoUrl: str
    value: str


class StreamerInfo(BaseModel):
    # 主播信息
    streamer_name: str


async def get_all_streamer_info():
    # 加载对话配置文件
    with open(WEB_CONFIGS.CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    # 从配置中提取角色信息
    streamer_info = dataset_yaml["role_type"]  # [WEB_CONFIGS.streamer_NAME]

    return streamer_info


@router.post("/list")
async def get_streamer_info_api():
    # TODO 后续需要改造数据结构，目前先简单返回
    # 加载对话配置文件
    streamer_list = await get_all_streamer_info()

    streamer_info_dict = []
    id = 0
    for streamer_name, streamer_character in streamer_list.items():
        id += 1
        streamer_info_dict.append(
            {
                "id": id,
                "name": streamer_name,
                "character": ",".join(streamer_character),
                "value": f"{id}",
                "imageUrl": "https://fuss10.elemecdn.com/e/5d/4a731a90594a4af544c0c25941171jpeg.jpeg",
                "videoUrl": "https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4",
            }
        )

    logger.info(streamer_info_dict)
    return {
        "status": 0,
        "message": "success",
        "data": streamer_info_dict,
        "timestamp": datetime.now(),
    }


@router.get("/streamer_doc_template")
async def get_streamer_doc_template(streamer_info: StreamerInfo):
    """
    从配置文件中加载主播相关信息

    - streamer_info: 系统问候语，针对销售角色定制
    - first_input_template: 对话开始时的第一个输入模板
    - product_info_struct_template: 产品信息结构模板
    """
    # 加载对话配置文件
    dataset_yaml = await get_all_streamer_info()

    # 从配置中提取对话设置相关的信息
    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    # 将销售角色名和角色信息插入到 system prompt
    system_str = system.replace("{role_type}", WEB_CONFIGS.SALES_NAME).replace("{character}", "、".join(streamer_info))

    return {
        "status": "success",
        "streamer_info": system_str,
        "first_input_template": first_input,
        "product_info_struct_template": product_info_struct,
    }
