#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   utils.py
@Time    :   2024/09/02
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   工具集合文件
"""


import asyncio
import json
import random
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import cv2
from lmdeploy.serve.openai.api_client import APIClient
from loguru import logger
from pydantic import BaseModel
from sqlmodel import Session
from tqdm import tqdm

from ..tts.tools import SYMBOL_SPLITS, make_text_chunk
from ..web_configs import API_CONFIG, WEB_CONFIGS
from .database.init_db import DB_ENGINE
from .database.product_db import get_db_product_info, save_product_info
from .database.streamer_info_db import get_streamers_info, save_streamer_info
from .database.streamer_room_db import get_streaming_room_info, update_streaming_room_info
from .models.product_model import ProductInfo
from .models.streamer_info_model import StreamerInfoItem
from .modules.agent.agent_worker import get_agent_result
from .modules.rag.rag_worker import RAG_RETRIEVER, build_rag_prompt
from .queue_thread import DIGITAL_HUMAN_QUENE, TTS_TEXT_QUENE
from .server_info import SERVER_PLUGINS_INFO


class ChatGenConfig(BaseModel):
    # LLM 推理配置
    top_p: float = 0.8
    temperature: float = 0.7
    repetition_penalty: float = 1.005


class ProductInfoItem(BaseModel):
    name: str
    heighlights: str
    introduce: str  # 生成商品文案 prompt

    image_path: str
    departure_place: str
    delivery_company_name: str


class PluginsInfo(BaseModel):
    rag: bool = True
    agent: bool = True
    tts: bool = True
    digital_human: bool = True


class ChatItem(BaseModel):
    user_id: str  # User 识别号，用于区分不用的用户调用
    request_id: str  # 请求 ID，用于生成 TTS & 数字人
    prompt: List[Dict[str, str]]  # 本次的 prompt
    product_info: ProductInfoItem  # 商品信息
    plugins: PluginsInfo = PluginsInfo()  # 插件信息
    chat_config: ChatGenConfig = ChatGenConfig()


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


def make_poster_by_video_first_frame(video_path: str, image_output_name: str):
    """根据视频第一帧生成缩略图

    Args:
        video_path (str): 视频文件路径

    Returns:
        str: 第一帧保存的图片路径
    """

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    # 读取第一帧
    ret, frame = cap.read()

    # 检查是否成功读取
    poster_save_path = str(Path(video_path).parent.joinpath(image_output_name))
    if ret:
        # 保存图像到文件
        cv2.imwrite(poster_save_path, frame)
        logger.info(f"第一帧已保存为 {poster_save_path}")
    else:
        logger.error("无法读取视频帧")

    # 释放视频捕获对象
    cap.release()

    return poster_save_path


async def delete_item_by_id(item_type: str, delete_id: int, user_id: int = 0):
    """根据类型删除某个ID的信息"""
    # TODO 删除
    logger.info(delete_id)

    assert item_type in ["product", "streamer", "room"]

    get_func_map = {
        "product": get_db_product_info,
        "streamer": get_streamers_info,
        "room": get_streaming_room_info,
    }

    save_func_map = {"product": save_product_info, "streamer": save_streamer_info, "room": update_streaming_room_info}

    id_name_map = {
        "product": "product_id",
        "streamer": "id",
        "room": "room_id",
    }

    item_list = await get_func_map[item_type](user_id)
    logger.info(item_list)

    process_success_flag = False

    save_info = None
    if item_type == "product":
        for product_name, product_info in item_list.items():
            if product_info[id_name_map[item_type]] != delete_id:
                continue

            item_list[product_name]["delete"] = True
            item_list[product_name].update({"product_name": product_name})
            save_info = item_list[product_name]
            process_success_flag = True
            break
    else:
        for idx, item in enumerate(item_list):
            if item[id_name_map[item_type]] != delete_id:
                continue

            item_list[idx]["delete"] = True
            save_info = item_list[idx]
            process_success_flag = True
            break

    # 保存
    save_func_map[item_type](save_info)

    return process_success_flag


@dataclass
class ResultCode:
    SUCCESS: int = 0000  # 成功
    FAIL: int = 1000  # 失败


def make_return_data(success_flag: bool, code: ResultCode, message: str, data: dict):
    return {
        "success": success_flag,
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def gen_default_data():
    """生成默认数据，包括：
    - 商品数据
    - 主播数据
    """

    def create_default_product_item():
        """生成商品默认数据库"""
        delivery_company_list = ["京东", "顺丰", "韵达", "圆通", "中通"]
        departure_place_list = ["广州", "北京", "武汉", "杭州", "上海", "深圳", "成都"]
        default_product_list = {
            "beef": {
                "product_name": "进口和牛羽下肉",
                "heighlights": "富含铁质;营养价值高;肌肉纤维好;红白相间纹理;适合烧烤炖煮;草食动物来源",
                "product_class": "食品",
            },
            "elec_toothblush": {
                "product_name": "声波电动牙刷",
                "heighlights": "高效清洁;减少手动压力;定时提醒;智能模式调节;无线充电;噪音低",
                "product_class": "电子",
            },
            "lip_stick": {
                "product_name": "唇膏",
                "heighlights": "丰富色号;滋润保湿;显色度高;持久不脱色;易于涂抹;便携包装",
                "product_class": "美妆",
            },
            "mask": {
                "product_name": "光感润颜面膜",
                "heighlights": "密集滋养;深层补水;急救修复;快速见效;定期护理;多种类型选择",
                "product_class": "美妆",
            },
            "oled_tv": {
                "product_name": "65英寸OLED电视",
                "heighlights": "色彩鲜艳;对比度极高;响应速度快;无背光眩光;厚度较薄;自发光无需额外照明",
                "product_class": "家电",
            },
            "pad": {
                "product_name": "14英寸平板电脑",
                "heighlights": "轻薄;触控操作;电池续航好;移动办公便利;娱乐性强;适合儿童学习",
                "product_class": "电子",
            },
            "pants": {
                "product_name": "速干运动裤",
                "heighlights": "快干;伸缩自如;吸湿排汗;防风保暖;高腰设计;多口袋实用",
                "product_class": "衣服",
            },
            "pen": {
                "product_name": "墨水钢笔",
                "heighlights": "耐用性;可书写性;不同颜色和类型;轻便设计;环保材料;易于携带",
                "product_class": "文具",
            },
            "perfume": {
                "product_name": "薰衣草淡香氛",
                "heighlights": "浪漫优雅;花香调为主;情感表达;适合各种年龄;瓶身设计精致;提升女性魅力",
                "product_class": "家居用品",
            },
            "shampoo": {
                "product_name": "本草精华洗发露",
                "heighlights": "温和配方;深层清洁;滋养头皮;丰富泡沫;易冲洗;适合各种发质",
                "product_class": "日用品",
            },
            "wok": {
                "product_name": "不粘煎炒锅",
                "heighlights": "不粘涂层;耐磨耐用;导热快;易清洗;多种烹饪方式;设计人性化",
                "product_class": "厨具",
            },
            "yoga_mat": {
                "product_name": "瑜伽垫",
                "heighlights": "防滑材质;吸湿排汗;厚度适中;耐用易清洁;各种瑜伽动作适用;轻巧便携",
                "product_class": "运动",
            },
        }

        with Session(DB_ENGINE) as session:
            for product_key, product_info in default_product_list.items():
                add_item = ProductInfo(
                    **product_info,
                    image_path=f"/{WEB_CONFIGS.PRODUCT_FILE_DIR}/{WEB_CONFIGS.IMAGES_DIR}/{product_key}.png",
                    instruction=f"/{WEB_CONFIGS.PRODUCT_FILE_DIR}/{WEB_CONFIGS.INSTRUCTIONS_DIR}/{product_key}.md",
                    departure_place=random.choice(departure_place_list),
                    delivery_company=random.choice(delivery_company_list),
                    selling_price=round(random.uniform(66.6, 1999.9), 2),
                    amount=random.randint(999, 9999),
                    user_id=1,
                )
                session.add(add_item)
            session.commit()

        logger.info("created default product info done!")

    def create_default_streamer():

        with Session(DB_ENGINE) as session:
            steamer_item = StreamerInfoItem(
                name="乐乐喵",
                character="甜美;可爱;熟练使用各种网络热门梗造句;称呼客户为[家人们]",
                avatar=f"/{WEB_CONFIGS.STREAMER_FILE_DIR}/{WEB_CONFIGS.STREAMER_INFO_FILES_DIR}/lelemiao.png",
                base_mp4_path=f"/{WEB_CONFIGS.STREAMER_FILE_DIR}/{WEB_CONFIGS.STREAMER_INFO_FILES_DIR}/lelemiao.mp4",
                poster_image=f"/{WEB_CONFIGS.STREAMER_FILE_DIR}/{WEB_CONFIGS.STREAMER_INFO_FILES_DIR}/lelemiao.png",
                tts_reference_audio=f"/{WEB_CONFIGS.STREAMER_FILE_DIR}/{WEB_CONFIGS.STREAMER_INFO_FILES_DIR}/lelemiao.wav",
                tts_reference_sentence="列车巡游银河，我不一定都能帮上忙，但只要是花钱能解决的事，尽管和我说吧。",
                tts_weight_tag="艾丝妲",
                user_id=1,
            )
            session.add(steamer_item)
            session.commit()

    create_default_product_item()  # 商品信息
    create_default_streamer()  # 主播信息
