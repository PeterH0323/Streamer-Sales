#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   base_server.py
@Time    :   2024/09/02
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   中台服务入口文件
"""

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from ..web_configs import API_CONFIG, WEB_CONFIGS
from .database.init_db import create_db_and_tables
from .routers import digital_human, llm, products, streamer_info, streaming_room, users
from .server_info import SERVER_PLUGINS_INFO
from .utils import ChatItem, ResultCode, gen_default_data, make_return_data, streamer_sales_process

swagger_description = """

## 项目地址

[销冠 —— 卖货主播大模型 && 后台管理系统](https://github.com/PeterH0323/Streamer-Sales)

## 功能点

1. 📜 **主播文案一键生成**
2. 🚀 KV cache + Turbomind **推理加速**
3. 📚 RAG **检索增强生成**
4. 🔊 TTS **文字转语音**
5. 🦸 **数字人生成**
6. 🌐 **Agent 网络查询**
7. 🎙️ **ASR 语音转文字**
8. 🍍 **Vue + pinia + element-plus **搭建的前端，可自由扩展快速开发
9. 🗝️ 后端采用 FastAPI + Uvicorn + PostgreSQL，**高性能，高效编码，生产可用，同时具有 JWT 身份验证**
10. 🐋 采用 Docker-compose 部署，**一键实现分布式部署**

"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务生命周期函数"""
    # 启动
    create_db_and_tables()  # 创建数据库和数据表

    # 新服务，生成默认数据，可以自行注释 or 修改
    gen_default_data()

    if WEB_CONFIGS.ENABLE_RAG:
        from .modules.rag.rag_worker import load_rag_model

        # 生成 rag 数据库
        await load_rag_model(user_id=1)

    yield

    # 结束
    logger.info("Base server stopped.")


app = FastAPI(
    title="销冠 —— 卖货主播大模型 && 后台管理系统",
    description=swagger_description,
    summary="一个能够根据给定的商品特点从激发用户购买意愿角度出发进行商品解说的卖货主播大模型。",
    version="1.0.0",
    license_info={
        "name": "AGPL-3.0 license",
        "url": "https://github.com/PeterH0323/Streamer-Sales/blob/main/LICENSE",
    },
    root_path=API_CONFIG.API_V1_STR,
    lifespan=lifespan,
)

# 注册路由
app.include_router(users.router)
app.include_router(products.router)
app.include_router(llm.router)
app.include_router(streamer_info.router)
app.include_router(streaming_room.router)
app.include_router(digital_human.router)


# 挂载静态文件目录，以便访问上传的文件
WEB_CONFIGS.SERVER_FILE_ROOT = str(Path(WEB_CONFIGS.SERVER_FILE_ROOT).absolute())
Path(WEB_CONFIGS.SERVER_FILE_ROOT).mkdir(parents=True, exist_ok=True)
logger.info(f"上传文件挂载路径: {WEB_CONFIGS.SERVER_FILE_ROOT}")
logger.info(f"上传文件访问 URL: {API_CONFIG.REQUEST_FILES_URL}")
app.mount(
    f"/{API_CONFIG.REQUEST_FILES_URL.split('/')[-1]}",
    StaticFiles(directory=WEB_CONFIGS.SERVER_FILE_ROOT),
    name=API_CONFIG.REQUEST_FILES_URL.split("/")[-1],
)


@app.get("/")
async def hello():
    return {"message": "Hello Streamer-Sales"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """调 API 入参错误的回调接口

    Args:
        request (_type_): _description_
        exc (_type_): _description_

    Returns:
        _type_: _description_
    """
    logger.info(request.headers)
    logger.info(exc)
    return PlainTextResponse(str(exc), status_code=400)


@app.get("/dashboard", tags=["base"], summary="获取主页信息接口")
async def get_dashboard_info():
    """首页展示数据"""
    fake_dashboard_data = {
        "registeredBrandNum": 98431,  # 入驻品牌方
        "productNum": 49132,  # 商品数
        "dailyActivity": 68431,  # 日活
        "todayOrder": 8461321,  # 订单量
        "totalSales": 245578131857,  # 销售额
        "conversionRate": 90.0,  # 转化率
        # 折线图
        "orderNumList": [46813, 68461, 99561, 138131, 233812, 84613, 846122],  # 订单量
        "totalSalesList": [46813, 68461, 99561, 138131, 23383, 84613, 841213],  # 销售额
        "newUserList": [3215, 65131, 6513, 6815, 2338, 84614, 84213],  # 新增用户
        "activityUserList": [132, 684, 59431, 4618, 31354, 68431, 88431],  # 活跃用户
        # 柱状图
        "knowledgeBasesNum": 12,  # 知识库数量
        "digitalHumanNum": 3,  # 数字人数量
        "LiveRoomNum": 5,  # 直播间数量
    }

    return make_return_data(True, ResultCode.SUCCESS, "成功", fake_dashboard_data)


@app.get("/plugins_info", tags=["base"], summary="获取组件信息接口")
async def get_plugins_info():

    plugins_info = SERVER_PLUGINS_INFO.get_status()
    return make_return_data(True, ResultCode.SUCCESS, "成功", plugins_info)


@app.post("/upload/file", tags=["base"], summary="上传文件接口")
async def upload_product_api(file: UploadFile = File(...), user_id: int = Depends(users.get_current_user_info)):

    file_type = file.filename.split(".")[-1]  # eg. png
    logger.info(f"upload file type = {file_type}")

    sub_dir_name_map = {
        "md": WEB_CONFIGS.INSTRUCTIONS_DIR,
        "png": WEB_CONFIGS.IMAGES_DIR,
        "jpg": WEB_CONFIGS.IMAGES_DIR,
        "mp4": WEB_CONFIGS.STREAMER_INFO_FILES_DIR,
        "wav": WEB_CONFIGS.STREAMER_INFO_FILES_DIR,
        "webm": WEB_CONFIGS.ASR_FILE_DIR,
    }
    if file_type in ["wav", "mp4"]:
        save_root = WEB_CONFIGS.STREAMER_FILE_DIR
    elif file_type in ["webm"]:
        save_root = ""
    else:
        save_root = WEB_CONFIGS.PRODUCT_FILE_DIR

    upload_time = str(int(time.time())) + "__" + str(uuid.uuid4().hex)

    sub_dir_name = sub_dir_name_map[file_type]
    save_path = Path(WEB_CONFIGS.SERVER_FILE_ROOT).joinpath(save_root, sub_dir_name, upload_time + "." + file_type)
    save_path.parent.mkdir(exist_ok=True, parents=True)
    logger.info(f"save path = {save_path}")

    # 使用流式处理接收文件
    with open(save_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024 * 5):  # 每次读取 5MB 的数据块
            buffer.write(chunk)

    split_dir_name = Path(WEB_CONFIGS.SERVER_FILE_ROOT).name  # 保存文件夹根目录名字
    file_url = f"{API_CONFIG.REQUEST_FILES_URL}{str(save_path).split(split_dir_name)[-1]}"

    # TODO 文件归属记录表

    return make_return_data(True, ResultCode.SUCCESS, "成功", file_url)


@app.post("/streamer-sales/chat", tags=["base"], summary="对话接口", deprecated=True)
async def streamer_sales_chat(chat_item: ChatItem, response: Response):
    from sse_starlette import EventSourceResponse

    # 对话总接口
    response.headers["Content-Type"] = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    return EventSourceResponse(streamer_sales_process(chat_item))
