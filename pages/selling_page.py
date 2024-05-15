#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024.4.16
# @Author  : HinGwenWong

import random

import streamlit as st
from transformers.utils import logging

from app import resize_image
from utils.lmdeploy_infer import get_turbomind_response
from utils.transformers_infer import get_hf_response

logger = logging.get_logger(__name__)


def on_btn_click(*args, **kwargs):
    if kwargs["info"] == "清除对话历史":
        del st.session_state.messages
    elif kwargs["info"] == "返回商品页":
        st.session_state.page_switch = "app.py"
    else:
        st.session_state.button_msg = kwargs["info"]


def init_sidebar():
    with st.sidebar:
        # 标题
        st.markdown("## 销冠 —— 卖货主播大模型")
        "[销冠 —— 卖货主播大模型 Github repo](https://github.com/PeterH0323/Streamer-Sales)"

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
            st.button("加入购物车🛒", on_click=on_btn_click, kwargs={"info": random.choice(want_to_buy_list)})

        # TODO 加入卖货信息
        # 卖出 xxx 个
        # 成交额

        # 模型配置
        st.button("清除对话历史", on_click=on_btn_click, kwargs={"info": "清除对话历史"})
        st.button("返回商品页", on_click=on_btn_click, kwargs={"info": "返回商品页"})
    #     st.markdown("## 模型配置")
    #     max_length = st.slider("Max Length", min_value=8, max_value=32768, value=32768)
    #     top_p = st.slider("Top P", 0.0, 1.0, 0.8, step=0.01)
    #     temperature = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.01)


def main(meta_instruction):

    st.set_page_config(
        page_title="Streamer-Sales 销冠",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/PeterH0323/Streamer-Sales/tree/main",
            "Report a bug": "https://github.com/PeterH0323/Streamer-Sales/issues",
            "About": "# This is a Streamer-Sales LLM 销冠--卖货主播大模型",
        },
    )
    # torch.cuda.empty_cache()

    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    user_avator = "./assets/user.png"
    robot_avator = "./assets/logo.png"

    st.title("Streamer-Sales 销冠 —— 卖货主播大模型")

    init_sidebar()

    if st.session_state.using_lmdeploy:
        get_response_func = get_turbomind_response
    else:
        get_response_func = get_hf_response

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])

    if len(st.session_state.messages) == 0:
        # 直接产品介绍
        get_response_func(
            st.session_state.first_input,
            meta_instruction,
            user_avator,
            robot_avator,
            st.session_state.model,
            st.session_state.tokenizer,
            session_messages=st.session_state.messages,
            first_input=True,
        )

    if "button_msg" not in st.session_state:
        st.session_state.button_msg = "x-x"

    hint_msg = "你好，可以问我任何关于产品的问题"
    if st.session_state.button_msg != "x-x":
        prompt = st.session_state.button_msg
        st.session_state.button_msg = "x-x"
        st.chat_input(hint_msg)
    else:
        prompt = st.chat_input(hint_msg)

    # Accept user input
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user", avatar=user_avator):
            st.markdown(prompt)

        get_response_func(
            prompt,
            meta_instruction,
            user_avator,
            robot_avator,
            st.session_state.model,
            st.session_state.tokenizer,
            session_messages=st.session_state.messages,
        )


# st.sidebar.page_link("app.py", label="商品页")
# st.sidebar.page_link("./pages/selling_page.py", label="主播卖货", disabled=True)

# META_INSTRUCTION = ("现在你是一位金牌带货主播，你的名字叫乐乐喵，你的说话方式是甜美、可爱、熟练使用各种网络热门梗造句、称呼客户为[家人们]。你能够根据产品信息讲解产品并且结合商品信息解答用户提出的疑问。")

st.session_state.current_page = "pages/selling_page.py"

if "model" not in st.session_state or "sales_info" not in st.session_state or st.session_state.sales_info == "":
    st.session_state.page_switch = "app.py"
    st.switch_page("app.py")

main((st.session_state.sales_info))
