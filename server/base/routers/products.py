from datetime import datetime
import shutil
from pathlib import Path
import time
from typing import List
import uuid
import yaml
from fastapi import APIRouter, File, UploadFile
from loguru import logger
from pydantic import BaseModel

from ...web_configs import API_CONFIG, WEB_CONFIGS
from ..modules.rag.rag_worker import rebuild_rag_db
from ..utils import ResultCode, make_return_data

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


class UploadProductItem(BaseModel):
    user_id: str = ""  # User 识别号，用于区分不用的用户调用
    request_id: str = ""  # 请求 ID，用于生成 TTS & 数字人
    product_id: int = -1  # 8
    product_name: str
    product_class: str  # "衣服"
    heighlights: str  # [快干, 伸缩自如, 吸湿排汗, 防风保暖, 高腰设计, 多口袋实用]
    image_path: str  # "./product_info/images/pants.png"
    instruction: str  # "./product_info/instructions/pants.md"
    departure_place: str  # "广州"
    delivery_company: str  # "圆通"
    selling_price: float  # 66.9
    amount: int  # 12435
    upload_date: str = ""  # "1722944888"
    sales_doc: str = ""  # "速干运动裤"
    digital_human_video: str = ""  # "666"
    streamer_id: int


class UploadFileItem(BaseModel):
    file: bytes = File(...)


class ProductQueryItem(BaseModel):
    currentPage: int  # 当前页号
    pageSize: int  # 每页记录数
    productName: str = ""  # 商品名
    productId: str = "-1"  # 商品ID


class ProductInstructionItem(BaseModel):
    instructionPath: str


async def get_db_product_info(user_id: str = ""):
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    return product_info_dict


async def get_product_list(product_name="", id=-1):
    # 读取数据库
    product_info_dict = await get_db_product_info()

    # 根据 ID 排序，避免乱序
    product_info_name_list = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["product_id"])).keys()
    product_list = []
    for key in product_info_name_list:
        info = product_info_dict[key]
        info.update({"product_name": key})

        # TODO 先默认写入 lelemiao
        info.update({"streamer_id": 1})

        # 将 亮点 数组改为字符串
        info["heighlights"] = "、".join(info["heighlights"])

        if product_name != "" and product_name not in key:
            # 如果有商品名则需要进行过滤处理，实现搜索功能
            continue

        if id > 0 and info["product_id"] == id:
            # 根据 ID 获取
            product_list = [info]
            break
        else:
            # 全部获取
            product_list.append(info)

    return product_list, len(product_info_dict)


async def get_prduct_by_page(currentPage, pageSize, productName=""):
    product_list, db_product_size = await get_product_list(product_name=productName)
    product_total_size = len(product_list)

    # 根据页面大小返回
    # 前端传过来的 currentPage 最小 = 1
    end_index = currentPage * pageSize
    start_index = (currentPage - 1) * pageSize
    logger.info(f"start_index = {start_index}")
    logger.info(f"end_index = {end_index}")

    if start_index == 0 and end_index > len(product_list):
        # 单页数量超过商品数，直接返回
        pass
    elif end_index > db_product_size:
        product_list = product_list[start_index:]
    else:
        product_list = product_list[start_index:end_index]

    # 拼接服务器地址
    # for product in product_list:
    #     product["image_path"] = API_CONFIG.REQUEST_FILES_URL + product["image_path"]
    #     product["instruction"] =  API_CONFIG.REQUEST_FILES_URL + product["instruction"]

    logger.info(product_list)
    logger.info(f"len {len(product_list)}")

    res_data = {
        "product": product_list,
        "current": currentPage,
        "pageSize": pageSize,
        "totalSize": product_total_size,
    }

    return res_data


@router.post("/list")
async def get_product_info_api(product_query_item: ProductQueryItem):

    logger.info(f"Got product_query_item = {product_query_item}")
    res_data = await get_prduct_by_page(
        product_query_item.currentPage, product_query_item.pageSize, product_query_item.productName
    )
    return make_return_data(True, ResultCode.SUCCESS, "成功", res_data)


@router.get("/info")
async def get_product_info_api(productId: str):
    product_list, _ = await get_product_list(id=int(productId))

    logger.info(product_list)
    return make_return_data(True, ResultCode.SUCCESS, "成功", product_list[0])


@router.post("/upload/file")
async def upload_product_api(file: UploadFile = File(...)):

    file_type = file.filename.split(".")[-1]  # eg. image/png
    logger.info(f"upload file type = {file_type}")
    upload_time = str(int(time.time())) + "__" + str(uuid.uuid4().hex)
    sub_dir_name = WEB_CONFIGS.INSTRUCTIONS_DIR if file_type == "md" else WEB_CONFIGS.IMAGES_DIR
    save_path = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(
        WEB_CONFIGS.PRODUCT_FILE_DIR, sub_dir_name, upload_time + "." + file_type
    )
    save_path.parent.mkdir(exist_ok=True, parents=True)
    logger.info(f"save path = {save_path}")

    # 使用流式处理接收文件
    with open(save_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024 * 5):  # 每次读取 5MB 的数据块
            buffer.write(chunk)

    file_url = f"{API_CONFIG.REQUEST_FILES_URL}/{sub_dir_name}/{Path(save_path).name}"
    return make_return_data(True, ResultCode.SUCCESS, "成功", file_url)


@router.post("/upload/form")
async def upload_product_api(upload_product_item: UploadProductItem):
    """新增 or 编辑商品

    Args:
        upload_product_item (UploadProductItem): _description_

    Returns:
        _type_: _description_
    """

    # TODO 后续直接插入到数据库就行，无需自行将 id + 1
    # 获取现有数据
    product_info_dict = await get_db_product_info()

    # 排序防止乱序
    product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["product_id"]))
    max_id_key = max(product_info_dict, key=lambda x: product_info_dict[x]["product_id"])

    new_info_dict = {
        "heighlights": upload_product_item.heighlights.split("、"),
        "image_path": str(upload_product_item.image_path),
        "instruction": str(upload_product_item.instruction),
        "departure_place": upload_product_item.departure_place,
        "delivery_company": upload_product_item.delivery_company,
        "selling_price": upload_product_item.selling_price,
        "amount": upload_product_item.amount,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sales_doc": upload_product_item.sales_doc,
        "digital_human_video": upload_product_item.digital_human_video,
        "product_id": product_info_dict[max_id_key]["product_id"] + 1,
        "product_class": upload_product_item.product_class,
    }

    if upload_product_item.product_name not in product_info_dict:
        # 没有则加入
        product_info_dict.update({upload_product_item.product_name: new_info_dict})
    else:
        # 有则更新
        new_info_dict["product_id"] = product_info_dict[upload_product_item.product_name]["product_id"]  # 使用原来的 ID
        product_info_dict[upload_product_item.product_name] = new_info_dict

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

    return make_return_data(True, ResultCode.SUCCESS, "成功", "")


@router.post("/instruction")
async def get_product_info_api(instruction_path: ProductInstructionItem):

    loacl_path = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(
        WEB_CONFIGS.PRODUCT_FILE_DIR, WEB_CONFIGS.INSTRUCTIONS_DIR, Path(instruction_path.instructionPath).name
    )
    if not loacl_path.exists():
        return make_return_data(False, ResultCode.FAIL, "文件不存在", "")

    with open(loacl_path, "r") as f:
        instruction_content = f.read()

    logger.info(instruction_content)
    return make_return_data(True, ResultCode.SUCCESS, "成功", instruction_content)
