import asyncio
import json
import shutil
import wave
from pathlib import Path
from typing import Dict, List

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Response
from lmdeploy.serve.openai.api_client import APIClient
from loguru import logger
from sse_starlette import EventSourceResponse
from tqdm import tqdm

from ..tts.tools import SYMBOL_SPLITS, make_text_chunk
from ..web_configs import API_CONFIG, WEB_CONFIGS
from .modules.agent.agent_worker import get_agent_result
from .modules.rag.rag_worker import RAG_RETRIEVER, build_rag_prompt, rebuild_rag_db
from .queue_thread import DIGITAL_HUMAN_QUENE, TTS_TEXT_QUENE
from .utils import ChatItem, UploadProductItem, SERVER_PLUGINS_INFO

app = FastAPI()

# 加载 LLM 模型
LLM_MODEL_HANDLER = APIClient(API_CONFIG.LLM_URL)


async def streamer_sales_process(chat_item: ChatItem):

    # ====================== Agent ======================
    # 调取 Agent
    agent_response = ""
    if chat_item.plugins.agent and SERVER_PLUGINS_INFO.agent_enabled:
        GENERATE_AGENT_TEMPLATE = (
            "这是网上获取到的信息：“{}”\n 客户的问题：“{}” \n 请认真阅读信息并运用你的性格进行解答。"  # Agent prompt 模板
        )
        input_prompt = chat_item.prompt[-1]["content"]
        agent_response = get_agent_result(
            LLM_MODEL_HANDLER, input_prompt, chat_item.product_info.departure_place, chat_item.product_info.delivery_company_name
        )
        if agent_response != "":
            agent_response = GENERATE_AGENT_TEMPLATE.format(agent_response, input_prompt)
            print(f"Agent response: {agent_response}")
            chat_item.prompt[-1]["content"] = agent_response

    # ====================== RAG ======================
    # 调取 rag
    if chat_item.plugins.rag and agent_response == "":
        # 如果 Agent 没有执行，则使用 RAG 查询数据库
        rag_prompt = chat_item.prompt[-1]["content"]
        prompt_pro = build_rag_prompt(RAG_RETRIEVER, chat_item.product_info.name, rag_prompt)

        if prompt_pro != "":
            chat_item.prompt[-1]["content"] = prompt_pro

    # llm 推理流返回
    logger.info(chat_item.prompt)

    current_predict = ""
    idx = 0
    last_text_index = 0
    sentence_id = 0
    model_name = LLM_MODEL_HANDLER.available_models[0]
    for item in LLM_MODEL_HANDLER.chat_completions_v1(model=model_name, messages=chat_item.prompt, stream=True):
        logger.debug(f"LLM predict: {item}")
        if "content" not in item["choices"][0]["delta"]:
            continue
        current_res = item["choices"][0]["delta"]["content"]

        if "~" in current_res:
            current_res = current_res.replace("~", "。").replace("。。", "。")

        current_predict += current_res
        idx += 1

        if chat_item.plugins.tts and SERVER_PLUGINS_INFO.tts_server_enabled:
            # 切句子
            sentence = ""
            for symbol in SYMBOL_SPLITS:
                if symbol in current_res:
                    last_text_index, sentence = make_text_chunk(current_predict, last_text_index)
                    if len(sentence) <= 3:
                        # 文字太短的情况，不做生成
                        sentence = ""
                    break

            if sentence != "":
                sentence_id += 1
                logger.info(f"get sentence: {sentence}")
                tts_request_dict = {
                    "user_id": chat_item.user_id,
                    "request_id": chat_item.request_id,
                    "sentence": sentence,
                    "chunk_id": sentence_id,
                    # "wav_save_name": chat_item.request_id + f"{str(sentence_id).zfill(8)}.wav",
                }

                TTS_TEXT_QUENE.put(tts_request_dict)
                await asyncio.sleep(0.01)

        yield json.dumps(
            {
                "event": "message",
                "retry": 100,
                "id": idx,
                "data": current_predict,
                "step": "llm",
                "end_flag": False,
            },
            ensure_ascii=False,
        )
        await asyncio.sleep(0.01)  # 加个延时避免无法发出 event stream

    if chat_item.plugins.digital_human and SERVER_PLUGINS_INFO.digital_human_server_enabled:

        wav_list = [
            Path(WEB_CONFIGS.TTS_WAV_GEN_PATH, chat_item.request_id + f"-{str(i).zfill(8)}.wav")
            for i in range(1, sentence_id + 1)
        ]
        while True:
            # 等待 TTS 生成完成
            not_exist_count = 0
            for tts_wav in wav_list:
                if not tts_wav.exists():
                    not_exist_count += 1

            logger.info(f"still need to wait for {not_exist_count}/{sentence_id} wav generating...")
            if not_exist_count == 0:
                break

            yield json.dumps(
                {
                    "event": "message",
                    "retry": 100,
                    "id": idx,
                    "data": current_predict,
                    "step": "tts",
                    "end_flag": False,
                },
                ensure_ascii=False,
            )
            await asyncio.sleep(1)  # 加个延时避免无法发出 event stream

        # 合并 tts
        tts_save_path = Path(WEB_CONFIGS.TTS_WAV_GEN_PATH, chat_item.request_id + ".wav")
        all_tts_data = []

        for wav_file in tqdm(wav_list):
            logger.info(f"Reading wav file {wav_file}...")
            with wave.open(str(wav_file), "rb") as wf:
                all_tts_data.append([wf.getparams(), wf.readframes(wf.getnframes())])

        logger.info(f"Merging wav file to {tts_save_path}...")
        tts_params = max([tts_data[0] for tts_data in all_tts_data])
        with wave.open(str(tts_save_path), "wb") as wf:
            wf.setparams(tts_params)  # 使用第一个音频参数

            for wf_data in all_tts_data:
                wf.writeframes(wf_data[1])
        logger.info(f"Merged wav file to {tts_save_path} !")

        # 生成数字人视频
        tts_request_dict = {
            "user_id": chat_item.user_id,
            "request_id": chat_item.request_id,
            "chunk_id": 0,
            "tts_path": str(tts_save_path),
        }

        logger.info(f"Generating digital human...")
        DIGITAL_HUMAN_QUENE.put(tts_request_dict)
        while True:
            if (
                Path(WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_OUTPUT_PATH)
                .joinpath(Path(tts_save_path).stem + ".mp4")
                .with_suffix(".txt")
                .exists()
            ):
                break
            yield json.dumps(
                {
                    "event": "message",
                    "retry": 100,
                    "id": idx,
                    "data": current_predict,
                    "step": "dg",
                    "end_flag": False,
                },
                ensure_ascii=False,
            )
            await asyncio.sleep(1)  # 加个延时避免无法发出 event stream

        # 删除过程文件
        for wav_file in wav_list:
            wav_file.unlink()

    yield json.dumps(
        {
            "event": "message",
            "retry": 100,
            "id": idx,
            "data": current_predict,
            "step": "all",
            "end_flag": True,
        },
        ensure_ascii=False,
    )


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


@app.post("/streamer-sales/upload_product")
async def streamer_sales_chat(upload_product_item: UploadProductItem):
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
