from pathlib import Path
import yaml
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel
import shutil

from ...web_configs import WEB_CONFIGS
from ..modules.rag.rag_worker import rebuild_rag_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


class UploadProductItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    name: str
    heightlight: str
    image_path: str
    instruction_path: str
    departure_place: str
    delivery_company: str


class ProductQueryItem(BaseModel):
    currentPage: int = 1  # 当前页号
    pageSize: int = 5  # 每页记录数


@router.post("/list")
def get_product_info_api(product_query_item: ProductQueryItem):

    logger.info(f"Got product_query_item = {product_query_item}")
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 根据 ID 排序，避免乱序
    product_info_name_list = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["product_id"])).keys()
    product_list = []
    for key in product_info_name_list:
        info = product_info_dict[key]
        info.update({"product_name": key})
        product_list.append(info)
    product_total_size = len(product_list)
    
    # 根据页面大小返回
    # 前端传过来的 currentPage 最小 = 1 
    end_index = product_query_item.currentPage * product_query_item.pageSize
    start_index = (product_query_item.currentPage - 1) * product_query_item.pageSize
    logger.info(f"start_index = {start_index}")
    logger.info(f"end_index = {end_index}")
    
    if start_index == 0 and end_index > len(product_list):
        # 单页数量超过商品数，直接返回
        pass
    elif end_index > len(product_info_dict):
        product_list = product_list[start_index : ]
    else:
        product_list = product_list[start_index : end_index]
    
    logger.info(product_list)
    logger.info(f"len {len(product_list)}")
    return {
        "success": True,
        "state": 0,
        "message": "success",
        "data": {
            "product": product_list,
            "current": product_query_item.currentPage,
            "pageSize": product_query_item.pageSize,
            "totalSize": product_total_size,
        },
    }


@router.post("/add")
async def upload_product_api(upload_product_item: UploadProductItem):
    # 上传商品

    # TODO 可以不输入商品名称和特性，大模型根据说明书自动生成一版让用户自行修改

    # 显示上传状态，并执行上传操作
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 排序防止乱序
    product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["id"]))
    max_id_key = max(product_info_dict, key=lambda x: product_info_dict[x]["id"])

    product_info_dict.update(
        {
            upload_product_item.name: {
                "heighlights": upload_product_item.heightlight.split("、"),
                "images": str(upload_product_item.image_path),
                "instruction": str(upload_product_item.instruction_path),
                "id": product_info_dict[max_id_key]["id"] + 1,
                "departure_place": upload_product_item.departure_place,
                "delivery_company_name": upload_product_item.delivery_company,
            }
        }
    )

    # 备份
    if Path(WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH).exists():
        Path(WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH).unlink()
    shutil.copy(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH)

    # 覆盖保存
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(product_info_dict, f, allow_unicode=True)

    if WEB_CONFIGS.ENABLE_RAG:
        # 重新生成 RAG 向量数据库
        rebuild_rag_db()

    return {
        "user_id": upload_product_item.user_id,
        "request_id": upload_product_item.request_id,
        "message": "success uploaded product",
        "status": "success",
    }
