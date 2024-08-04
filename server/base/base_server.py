import shutil
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Response
from sse_starlette import EventSourceResponse

from ..web_configs import WEB_CONFIGS
from .modules.rag.rag_worker import rebuild_rag_db
from .server_info import SERVER_PLUGINS_INFO
from .utils import ChatItem, UploadProductItem, SalesInfo, streamer_sales_process
from .routers import users

app = FastAPI()

# 注册路由
app.include_router(users.router)

@app.get("/")
async def hello():
    return {"message": "Hello Streamer-Sales"}


@app.get("/streamer-sales/plugins_info")
async def get_plugins_info():
    return {
        "rag": True,
        "asr": SERVER_PLUGINS_INFO.asr_server_enabled,
        "tts": SERVER_PLUGINS_INFO.tts_server_enabled,
        "digital_human": SERVER_PLUGINS_INFO.digital_human_server_enabled,
        "agent": SERVER_PLUGINS_INFO.agent_enabled,
    }


@app.post("/streamer-sales/chat")
async def streamer_sales_chat(chat_item: ChatItem, response: Response):
    # 对话总接口
    response.headers["Content-Type"] = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    return EventSourceResponse(streamer_sales_process(chat_item))


@app.get("/streamer-sales/get_product_info")
def get_product_info_api():
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 根据 ID 排序，避免乱序
    product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["id"]))

    return {"status": "success", "product_info": product_info_dict}


@app.get("/streamer-sales/get_sales_info")
def get_sales_info_api(sales_info: SalesInfo):
    """
    从配置文件中加载销售相关信息

    - sales_info: 系统问候语，针对销售角色定制
    - first_input_template: 对话开始时的第一个输入模板
    - product_info_struct_template: 产品信息结构模板
    """

    # 加载对话配置文件
    with open(WEB_CONFIGS.CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    # 从配置中提取角色信息
    sales_info = dataset_yaml["role_type"][sales_info.sales_name]  # [WEB_CONFIGS.SALES_NAME]

    # 从配置中提取对话设置相关的信息
    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    # 将销售角色名和角色信息插入到 system prompt
    system_str = system.replace("{role_type}", WEB_CONFIGS.SALES_NAME).replace("{character}", "、".join(sales_info))

    return {
        "status": "success",
        "sales_info": system_str,
        "first_input_template": first_input,
        "product_info_struct_template": product_info_struct,
    }


@app.post("/streamer-sales/upload_product")
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


# 执行
# uvicorn server.main:app --reload

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
