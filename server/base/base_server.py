from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sse_starlette import EventSourceResponse

from ..web_configs import API_CONFIG, WEB_CONFIGS
from .routers import digital_human, llm, products, streamer_info, streaming_room, users
from .server_info import SERVER_PLUGINS_INFO
from .utils import ChatItem, ResultCode, make_return_data, streamer_sales_process

app = FastAPI()

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


@app.post("/dashboard")
async def get_dashboard_info():
    """首页展示数据"""
    dashboard_data = {
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

    return make_return_data(True, ResultCode.SUCCESS, "成功", dashboard_data)


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """调 API 入参错误的回调接口

    Args:
        request (_type_): _description_
        exc (_type_): _description_

    Returns:
        _type_: _description_
    """
    logger.info(request)
    logger.info(exc)
    return PlainTextResponse(str(exc), status_code=400)


# 执行
# uvicorn server.main:app --reload

# if __name__ == "__main__":
#     # for debug
#     uvicorn.run(app, host="0.0.0.0", port=8000)
