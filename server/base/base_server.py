import shutil
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Response
from sse_starlette import EventSourceResponse

from ..web_configs import WEB_CONFIGS
from .server_info import SERVER_PLUGINS_INFO
from .utils import ChatItem, streamer_sales_process
from .routers import users, products, llm, streamer_info

app = FastAPI()

# 注册路由
app.include_router(users.router)
app.include_router(products.router)
app.include_router(llm.router)
app.include_router(streamer_info.router)


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



# 执行
# uvicorn server.main:app --reload

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
