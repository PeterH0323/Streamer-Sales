#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024.4.16
# @Author  : HinGwenWong

import random

import streamlit as st

# 设置页面配置，包括标题、图标、布局和菜单项
st.set_page_config(
    page_title="Streamer-Sales 销冠",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/PeterH0323/Streamer-Sales/tree/main",
        "Report a bug": "https://github.com/PeterH0323/Streamer-Sales/issues",
        "About": "# Streamer-Sales LLM 销冠--卖货主播大模型",
    },
)

from utils.digital_human.digital_human_worker import show_video
from utils.infer.lmdeploy_infer import get_turbomind_response
from utils.infer.transformers_infer import get_hf_response
from utils.model_loader import LLM_MODEL, LLM_TOKENIZER, RAG_RETRIEVER
from utils.tools import resize_image
from utils.web_configs import WEB_CONFIGS


def on_btn_click(*args, **kwargs):
    """
    处理按钮点击事件的函数。
    """
    if kwargs["info"] == "清除对话历史":
        st.session_state.messages = []
    elif kwargs["info"] == "返回商品页":
        st.session_state.page_switch = "app.py"
    else:
        st.session_state.button_msg = kwargs["info"]


def init_sidebar():
    """
    初始化侧边栏界面，展示商品信息，并提供操作按钮。
    """
    with st.sidebar:
        # 标题
        st.markdown("## 销冠 —— 卖货主播大模型")
        st.markdown("[销冠 —— 卖货主播大模型 Github repo](https://github.com/PeterH0323/Streamer-Sales)")
        st.subheader("功能点：", divider="grey")
        st.markdown(
            "1. 📜 **主播文案一键生成**\n2. 🚀 KV cache + Turbomind **推理加速**\n3. 📚 RAG **检索增强生成**\n4. 🔊 TTS **文字转语音**\n5. 🦸 **数字人生成**"
        )

        st.subheader("目前讲解")
        with st.container(height=400, border=True):
            st.subheader(st.session_state.product_name)

            image = resize_image(st.session_state.image_path, max_height=100)
            st.image(image, channels="bgr")

            st.subheader("产品特点", divider="grey")
            st.markdown(st.session_state.hightlight)

            want_to_buy_list = [
                "我打算买了。",
                "我准备入手了。",
                "我决定要买了。",
                "我准备下单了。",
                "我将要购买这款产品。",
                "我准备买下来了。",
                "我准备将这个买下。",
                "我准备要购买了。",
                "我决定买下它。",
                "我准备将其买下。",
            ]
            buy_flag = st.button("加入购物车🛒", on_click=on_btn_click, kwargs={"info": random.choice(want_to_buy_list)})

        # TODO 加入卖货信息
        # 卖出 xxx 个
        # 成交额

        # 是否生成 TTS
        if WEB_CONFIGS.ENABLE_TTS:
            st.subheader("TTS 配置", divider="grey")
            st.session_state.gen_tts_checkbox = st.toggle("生成语音", value=st.session_state.gen_tts_checkbox)

        if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
            # 是否生成 数字人
            st.subheader(f"数字人 配置", divider="grey")
            st.session_state.gen_digital_human_checkbox = st.toggle(
                "生成数字人视频", value=st.session_state.gen_digital_human_checkbox
            )

        st.subheader("页面切换", divider="grey")
        st.button("返回商品页", on_click=on_btn_click, kwargs={"info": "返回商品页"})

        st.subheader("对话设置", divider="grey")
        st.button("清除对话历史", on_click=on_btn_click, kwargs={"info": "清除对话历史"})

        # 模型配置
        # st.markdown("## 模型配置")
        # max_length = st.slider("Max Length", min_value=8, max_value=32768, value=32768)
        # top_p = st.slider("Top P", 0.0, 1.0, 0.8, step=0.01)
        # temperature = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.01)


def init_message_block(meta_instruction, get_response_func, user_avator, robot_avator):

    # 在应用重新运行时显示聊天历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])

            if message.get("wav") is not None:
                # 展示语音
                print(f"Load wav {message['wav']}")
                with open(message["wav"], "rb") as f_wav:
                    audio_bytes = f_wav.read()
                st.audio(audio_bytes, format="audio/wav")

    # 如果聊天历史为空，则显示产品介绍
    if len(st.session_state.messages) == 0:
        # 直接产品介绍
        get_response_func(
            st.session_state.first_input,
            meta_instruction,
            user_avator,
            robot_avator,
            LLM_MODEL,
            LLM_TOKENIZER,
            session_messages=st.session_state.messages,
            add_session_msg=False,
            first_input_str="",
        )

    # 初始化按钮消息状态
    if "button_msg" not in st.session_state:
        st.session_state.button_msg = "x-x"


def process_message(get_response_func, user_avator, prompt, meta_instruction, robot_avator):
    # Display user message in chat message container
    with st.chat_message("user", avatar=user_avator):
        st.markdown(prompt)

    get_response_func(
        prompt,
        meta_instruction,
        user_avator,
        robot_avator,
        LLM_MODEL,
        LLM_TOKENIZER,
        session_messages=st.session_state.messages,
        add_session_msg=True,
        first_input_str=st.session_state.first_input,
        rag_retriever=RAG_RETRIEVER,
        product_name=st.session_state.product_name,
    )


def main(meta_instruction):

    # 检查页面切换状态并进行切换
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # 页面标题
    st.title("Streamer-Sales 销冠 —— 卖货主播大模型⭐🛒🏆")

    # 说明
    st.warning(
        "本项目基于人工智能的文字、语音、视频生成领域搭建的卖货主播大模型。用户被授予使用此工具创建文字、语音、视频的自由，但用户在使用过程中应该遵守当地法律，并负责任地使用。开发人员不对用户可能的不当使用承担任何责任。",
        icon="❗",
    )
    # 初始化侧边栏
    init_sidebar()

    # 根据是否使用lmdeploy选择响应函数
    if WEB_CONFIGS.USING_LMDEPLOY:
        get_response_func = get_turbomind_response
    else:
        get_response_func = get_hf_response

    # 初始化聊天历史记录
    if "messages" not in st.session_state:
        st.session_state.messages = []

    message_col = None
    if st.session_state.gen_digital_human_checkbox and WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:

        with st.container():
            message_col, video_col = st.columns([0.6, 0.4])

            with video_col:
                # 创建 empty 控件
                st.session_state.video_placeholder = st.empty()
                with st.session_state.video_placeholder.container():
                    show_video(st.session_state.digital_human_video_path, autoplay=True, loop=True, muted=True)

            with message_col:
                init_message_block(meta_instruction, get_response_func, WEB_CONFIGS.USER_AVATOR, WEB_CONFIGS.ROBOT_AVATOR)
    else:
        init_message_block(meta_instruction, get_response_func, WEB_CONFIGS.USER_AVATOR, WEB_CONFIGS.ROBOT_AVATOR)

    # 输入框显示提示信息
    hint_msg = "你好，可以问我任何关于产品的问题"
    if st.session_state.button_msg != "x-x":
        prompt = st.session_state.button_msg
        st.session_state.button_msg = "x-x"
        st.chat_input(hint_msg)
    else:
        prompt = st.chat_input(hint_msg)

    # 接收用户输入
    if prompt:

        if message_col is None:
            process_message(get_response_func, WEB_CONFIGS.USER_AVATOR, prompt, meta_instruction, WEB_CONFIGS.ROBOT_AVATOR)
        else:
            with message_col:
                process_message(get_response_func, WEB_CONFIGS.USER_AVATOR, prompt, meta_instruction, WEB_CONFIGS.ROBOT_AVATOR)


# st.sidebar.page_link("app.py", label="商品页")
# st.sidebar.page_link("./pages/selling_page.py", label="主播卖货", disabled=True)

# META_INSTRUCTION = ("现在你是一位金牌带货主播，你的名字叫乐乐喵，你的说话方式是甜美、可爱、熟练使用各种网络热门梗造句、称呼客户为[家人们]。你能够根据产品信息讲解产品并且结合商品信息解答用户提出的疑问。")

print("into sales page")
st.session_state.current_page = "pages/selling_page.py"

if "sales_info" not in st.session_state or st.session_state.sales_info == "":
    st.session_state.page_switch = "app.py"
    st.switch_page("app.py")

main((st.session_state.sales_info))
