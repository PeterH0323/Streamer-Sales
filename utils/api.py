import json
from pathlib import Path
from time import sleep
import uuid

import requests
import streamlit as st
from utils.tools import combine_history, show_audio, show_video
from server.web_configs import WEB_CONFIGS, API_CONFIG


def get_asr_api(wav_path, user_id="123"):
    # 获取 ASR 结果
    req_data = {
        "user_id": user_id,
        "request_id": str(uuid.uuid1()),
        "wav_path": wav_path,
    }

    print(req_data)

    res = requests.post(API_CONFIG.ASR_URL, json=req_data).json()
    return res["result"]


def get_chat_api(
    prompt,
    meta_instruction,
    session_messages,
    add_session_msg=True,
    first_input_str="",
    product_name="",
    departure_place="杭州",
    delivery_company_name="顺丰",
    enable_rag=True,
    enable_agent=True,
    enable_tts=True,
    enable_digital_human=True,
    user_id="123",
):
    request_id = str(uuid.uuid1())

    # ====================== 加上历史信息 ======================
    real_prompt = combine_history(
        prompt,
        meta_instruction,
        history_msg=session_messages,
        first_input_str=first_input_str,
    )  # 是否加上历史对话记录

    # Add user message to chat history
    if add_session_msg:
        session_messages.append({"role": "user", "content": prompt, "avatar": WEB_CONFIGS.USER_AVATOR})

    with st.chat_message("assistant", avatar=WEB_CONFIGS.ROBOT_AVATOR):
        message_placeholder = st.empty()
        cur_response = ""

        req_data = {
            "prompt": real_prompt,
            "user_id": user_id,
            "request_id": request_id,
            "product_info": {
                "name": product_name,
                "heighlights": "",
                "introduce": first_input_str,
                "image_path": "",
                "departure_place": departure_place,
                "delivery_company_name": delivery_company_name,
            },
            "chat_config": {"top_p": 0.8, "temperature": 0.7, "repetition_penalty": 1.005},
            "plugins": {
                "rag": enable_rag,
                "agent": enable_agent,
                "tts": enable_tts,
                "digital_human": enable_digital_human,
            },
        }

        print(req_data)

        res = requests.post(API_CONFIG.CHAT_URL, json=req_data, stream=True)
        for item in res.iter_lines(decode_unicode=True):
            print(item)

            item = item.replace("data: ", "")
            if item == "":
                continue
            try:
                item_json = json.loads(item)
                cur_response = item_json["data"]
                # step_name = item_json["step"]
                # end_flag = item_json["end_flag"]

            except Exception as e:
                print(f"Got error msg = {item}")

            message_placeholder.markdown(cur_response + "▌")
        message_placeholder.markdown(cur_response)

        wav_path = None
        if enable_tts:
            # 生成 TTS 文字转语音
            wav_path = str(Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).joinpath(request_id + ".wav"))
            show_audio(wav_path)
            st.toast("生成语音成功!")

        if enable_digital_human:
            # 生成 数字人视频
            dg_vid_path = str(Path(WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_OUTPUT_PATH).joinpath(request_id + ".mp4"))
            st.session_state.digital_human_video_path = dg_vid_path
            st.session_state.video_placeholder.empty()  # 清空
            with st.session_state.video_placeholder.container():
                show_video(st.session_state.digital_human_video_path)

            st.toast("生成数字人视频成功!")
        # Add robot response to chat history
        session_messages.append(
            {
                "role": "assistant",
                "content": cur_response,  # pylint: disable=undefined-loop-variable
                "avatar": WEB_CONFIGS.ROBOT_AVATOR,
                "wav": wav_path,
            }
        )


def upload_product_api(product_name, heightlight, image_path, instruction_path, departure_place, delivery_company, user_id="123"):
    # 获取 ASR 结果
    req_data = {
        "user_id": user_id,
        "request_id": str(uuid.uuid1()),
        "name": product_name,
        "heightlight": heightlight,
        "image_path": image_path,
        "instruction_path": instruction_path,
        "departure_place": departure_place,
        "delivery_company": delivery_company,
    }

    print(req_data)

    res = requests.post(API_CONFIG.UPLOAD_PRODUCT_URL, json=req_data).json()
    return res["status"]


def get_product_info_api():
    # 获取 商品信息 结果
    res = requests.get(API_CONFIG.GET_PRODUCT_INFO_URL).json()
    return res["product_info"]


def get_sales_info_api(sales_name: str):
    # 获取 主播信息 结果
    res = requests.get(API_CONFIG.GET_SALES_INFO_URL, json={"sales_name": sales_name}).json()
    return res["sales_info"], res["first_input_template"], res["product_info_struct_template"]


def get_server_plugins_info_api():
    # 获取 插件列表 结果
    res = requests.get(API_CONFIG.PLUGINS_INFO_URL).json()
    return res
