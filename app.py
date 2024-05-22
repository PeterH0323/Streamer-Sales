#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024.4.16
# @Author  : HinGwenWong

import copy
import os
import shutil
from datetime import datetime
from pathlib import Path
import time

import streamlit as st
import yaml

from utils.infer.lmdeploy_infer import load_turbomind_model
from utils.infer.transformers_infer import load_hf_model
from utils.rag.feature_store import gen_vector_db
from utils.tools import resize_image

# ==================================================================
#                               模型配置
# ==================================================================
MODEL_DIR = "HinGwenWoong/streamer-sales-lelemiao-7b"
# MODEL_DIR = "HinGwenWoong/streamer-sales-lelemiao-7b-4bit"

SALES_NAME = "乐乐喵"  # 启动的角色名

# ==================================================================
#                               组件配置
# ==================================================================
USING_LMDEPLOY = True  # True 使用 LMDeploy 作为推理后端加速推理，False 使用原生 HF 进行推理用于初步验证模型
ENABLE_RAG = True  # True 启用 RAG 检索增强，False 不启用
DISABLE_UPLOAD = os.getenv("DISABLE_UPLOAD") == "true"

# ==================================================================
#                               页面配置
# ==================================================================
PRODUCT_IMAGE_HEIGHT = 400  # 商品图片高度
EACH_CARD_OFFSET = 100  # 每个商品卡片比图片高度多出的距离
EACH_ROW_COL = 2  # 商品页显示多少列

# ==================================================================
#                               商品配置
# ==================================================================
PRODUCT_INSTRUCTION_DIR = r"./product_info/instructions"
PRODUCT_IMAGES_DIR = r"./product_info/images"

# ==================================================================
#                             配置文件路径
# ==================================================================
PRODUCT_INFO_YAML_PATH = r"./product_info/product_info.yaml"
CONVERSATION_CFG_YAML_PATH = r"./configs/conversation_cfg.yaml"

PRODUCT_INFO_YAML_BACKUP_PATH = PRODUCT_INFO_YAML_PATH + ".bk"

# ==================================================================
#                               RAG 配置
# ==================================================================
RAG_CONFIG_PATH = r"./configs/rag_config.yaml"
RAG_VECTOR_DB_DIR = r"./work_dirs/instruction_db"


# 初始化 Streamlit 页面配置
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


@st.experimental_dialog("说明书", width="large")
def instruction_dialog(instruction_path):
    """
    显示产品说明书的popup窗口。

    通过给定的说明书路径，将文件内容以markdown格式在Streamlit应用中显示出来，并提供一个“确定”按钮供用户确认阅读。

    Args:
        instruction_path (str): 说明书的文件路径，该文件应为文本文件，并使用utf-8编码。
    """
    print(f"Show instruction : {instruction_path}")
    with open(instruction_path, "r", encoding="utf-8") as f:
        instruct_lines = "".join(f.readlines())

    st.warning("一定要点击下方的【确定】按钮离开该页面", icon="⚠️")
    st.markdown(instruct_lines)
    st.warning("一定要点击下方的【确定】按钮离开该页面", icon="⚠️")
    if st.button("确定"):
        st.rerun()


def on_btton_click(*args, **kwargs):
    """
    按钮点击事件的回调函数。
    """

    # 根据按钮类型执行相应操作
    if kwargs["type"] == "check_instruction":
        # 显示说明书
        st.session_state.show_instruction_path = kwargs["instruction_path"]

    elif kwargs["type"] == "process_sales":
        # 切换到主播卖货页面
        st.session_state.page_switch = "pages/selling_page.py"

        # 更新会话状态中的产品信息
        st.session_state.hightlight = kwargs["heighlights"]
        product_info_struct = copy.deepcopy(st.session_state.product_info_struct_template)
        product_info_str = product_info_struct[0].replace("{name}", kwargs["product_name"])
        product_info_str += product_info_struct[1].replace("{highlights}", st.session_state.hightlight)

        # 生成商品文案 prompt
        st.session_state.first_input = copy.deepcopy(st.session_state.first_input_template).replace(
            "{product_info}", product_info_str
        )

        # 更新图片路径和产品名称
        st.session_state.image_path = kwargs["image_path"]
        st.session_state.product_name = kwargs["product_name"]

        # 清空历史对话
        st.session_state.messages = []


def make_product_container(product_name, product_info, image_height, each_card_offset):
    """
    创建并展示产品信息容器。

    参数:
    - product_name: 产品名称。
    - product_info: 包含产品信息的字典，需包括图片路径、特点和说明书路径。
    - image_height: 图片展示区域的高度。
    - each_card_offset: 容器内各部分间距。
    """

    # 创建带边框的产品信息容器，设置高度
    with st.container(border=True, height=image_height + each_card_offset):

        # 页面标题
        st.header(product_name)

        # 划分左右两列，左侧为图片，右侧为商品信息
        image_col, info_col = st.columns([0.2, 0.8])

        # 图片展示区域
        with image_col:
            # print(f"Loading {product_info['images']} ...")
            image = resize_image(product_info["images"], max_height=image_height)
            st.image(image, channels="bgr")

        # 产品信息展示区域
        with info_col:

            # 亮点展示
            st.subheader("亮点", divider="grey")

            heighlights_str = "、".join(product_info["heighlights"])
            st.text(heighlights_str)

            # 说明书按钮
            st.subheader("说明书", divider="grey")
            st.button(
                "查看",
                key=f"check_instruction_{product_name}",
                on_click=on_btton_click,
                kwargs={
                    "type": "check_instruction",
                    "product_name": product_name,
                    "instruction_path": product_info["instruction"],
                },
            )
            # st.button("更新", key=f"update_manual_{product_name}")

            # 讲解按钮
            st.subheader("主播", divider="grey")
            st.button(
                "开始讲解",
                key=f"process_sales_{product_name}",
                on_click=on_btton_click,
                kwargs={
                    "type": "process_sales",
                    "product_name": product_name,
                    "heighlights": heighlights_str,
                    "image_path": product_info["images"],
                },
            )


def get_sales_info():
    """
    从配置文件中加载销售相关信息，并存储到session状态中。

    该函数不接受参数，也不直接返回任何值，但会更新全局的session状态，包括：
    - sales_info: 系统问候语，针对销售角色定制
    - first_input_template: 对话开始时的第一个输入模板
    - product_info_struct_template: 产品信息结构模板

    """

    # 加载对话配置文件
    with open(CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    # 从配置中提取角色信息
    sales_info = dataset_yaml["role_type"][SALES_NAME]

    # 从配置中提取对话设置相关的信息
    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    # 将销售角色名和角色信息插入到 system prompt
    system_str = system.replace("{role_type}", SALES_NAME).replace("{character}", "、".join(sales_info))

    # 更新session状态，存储销售相关信息
    st.session_state.sales_info = system_str
    st.session_state.first_input_template = first_input
    st.session_state.product_info_struct_template = product_info_struct


def main(model_dir, using_lmdeploy, enable_rag):
    """
    初始化页面配置，加载模型，处理页面跳转，并展示商品信息。

    参数:
    - model_dir: 模型目录路径，用于加载指定的模型。
    - using_lmdeploy: 布尔值，指示是否使用lmdeploy加载模型。
    - enable_rag: 布尔值，指示是否启用RAG（Retrieve And Generate）模型。

    返回值:
    无
    """
    print("Starting...")

    # 初始化页面跳转
    if "page_switch" not in st.session_state:
        st.session_state.page_switch = "app.py"
    st.session_state.current_page = "app.py"

    # 显示商品说明书
    if "show_instruction_path" not in st.session_state:
        st.session_state.show_instruction_path = "X-X"
    if st.session_state.show_instruction_path != "X-X":
        instruction_dialog(st.session_state.show_instruction_path)
        st.session_state.show_instruction_path = "X-X"

    # 判断是否需要跳转页面
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # 加载模型
    st.session_state.using_lmdeploy = using_lmdeploy
    if st.session_state.using_lmdeploy:
        load_model_func = load_turbomind_model
    else:
        load_model_func = load_hf_model

    st.session_state.model, st.session_state.tokenizer, st.session_state.rag_retriever = load_model_func(
        model_dir, enable_rag=enable_rag, rag_config=RAG_CONFIG_PATH, db_path=RAG_VECTOR_DB_DIR
    )

    # 获取销售信息
    if "sales_info" not in st.session_state:
        get_sales_info()

    # 添加页面导航页
    # st.sidebar.page_link("app.py", label="商品页", disabled=True)
    # st.sidebar.page_link("./pages/selling_page.py", label="主播卖货")

    # 主页标题
    st.title("Streamer-Sales 销冠 —— 卖货主播大模型")
    st.header("商品页")

    # 说明
    st.info(
        "这是主播后台，这里需要主播讲解的商品目录，选择一个商品，点击【开始讲解】即可跳转到主播讲解页面。如果需要加入更多商品，点击下方的添加按钮即可",
        icon="ℹ️",
    )

    # 读取 yaml 文件
    with open(PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    product_name_list = list(product_info_dict.keys())

    # 侧边栏显示产品数量，入驻品牌方
    with st.sidebar:
        # 标题
        st.markdown("## 销冠 —— 卖货主播大模型")
        "[销冠 —— 卖货主播大模型 Github repo](https://github.com/PeterH0323/Streamer-Sales)"

        st.markdown(f"## 主播后台信息")
        st.markdown(f"共有商品：{len(product_name_list)} 件")
        st.markdown(f"共有品牌方：{len(product_name_list)} 个")

        # TODO 单品成交量
        # st.markdown(f"共有品牌方：{len(product_name_list)} 个")

    # 生成商品信息
    for row_id in range(0, len(product_name_list), EACH_ROW_COL):
        for col_id, col_handler in enumerate(st.columns(EACH_ROW_COL)):
            with col_handler:
                if row_id + col_id >= len(product_name_list):
                    continue
                product_name = product_name_list[row_id + col_id]
                make_product_container(product_name, product_info_dict[product_name], PRODUCT_IMAGE_HEIGHT, EACH_CARD_OFFSET)

    # 添加新商品上传表单
    with st.form(key="add_product_form"):
        product_name_input = st.text_input(label="添加商品名称")
        heightlight_input = st.text_input(label="添加商品特性，以'、'隔开")
        product_image = st.file_uploader(label="上传商品图片", type=["png", "jpg", "jpeg", "bmp"])
        product_instruction = st.file_uploader(label="上传商品说明书", type=["md"])
        submit_button = st.form_submit_button(label="提交", disabled=DISABLE_UPLOAD)

        if DISABLE_UPLOAD:
            st.info(
                "Github 上面的代码已支持上传新商品逻辑。\n但因开放性的 Web APP 没有新增商品审核机制，暂不在此开放上传商品。\n您可以 clone 本项目到您的机器启动即可使能上传按钮",
                icon="ℹ️",
            )

        if submit_button:
            update_product_info(product_name_input, heightlight_input, product_image, product_instruction)


def update_product_info(product_name_input, heightlight_input, product_image, product_instruction):
    """
    更新产品信息的函数。

    参数:
    - product_name_input: 商品名称输入，字符串类型。
    - heightlight_input: 商品特性输入，字符串类型。
    - product_image: 商品图片，图像类型。
    - product_instruction: 商品说明书，文本类型。

    返回值:
    无。该函数直接操作UI状态，不返回任何值。
    """

    # TODO 可以不输入图片和特性，大模型自动生成一版让用户自行选择

    # 检查入参
    if product_name_input == "" or heightlight_input == "":
        st.error("商品名称和特性不能为空")
        return

    if product_image is None or product_instruction is None:
        st.error("图片和说明书不能为空")
        return

    # 显示上传状态，并执行上传操作
    with st.status("正在上传商品...", expanded=True) as status:

        save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        image_save_path = Path(PRODUCT_IMAGES_DIR).joinpath(f"{save_tag}{Path(product_image.name).suffix}")
        instruct_save_path = Path(PRODUCT_INSTRUCTION_DIR).joinpath(f"{save_tag}{Path(product_instruction.name).suffix}")

        st.write("图片保存中...")
        with open(image_save_path, "wb") as file:
            file.write(product_image.getvalue())

        st.write("说明书保存中...")
        with open(instruct_save_path, "wb") as file:
            file.write(product_instruction.getvalue())

        st.write("生成数据库...")
        if ENABLE_RAG:
            # 重新生成 RAG 向量数据库
            gen_vector_db(RAG_CONFIG_PATH, PRODUCT_INSTRUCTION_DIR, RAG_VECTOR_DB_DIR)

            # 重新加载 retriever
            st.session_state.rag_retriever.pop("default")
            st.session_state.rag_retriever.get(fs_id="default", config_path=RAG_CONFIG_PATH, work_dir=RAG_VECTOR_DB_DIR)

        st.write("更新商品明细表...")
        with open(PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
            product_info_dict = yaml.safe_load(f)

        product_info_dict.update(
            {
                product_name_input: {
                    "heighlights": heightlight_input.split("、"),
                    "images": str(image_save_path),
                    "instruction": str(instruct_save_path),
                }
            }
        )

        # 备份
        if Path(PRODUCT_INFO_YAML_BACKUP_PATH).exists():
            Path(PRODUCT_INFO_YAML_BACKUP_PATH).unlink()
        shutil.copy(PRODUCT_INFO_YAML_PATH, PRODUCT_INFO_YAML_BACKUP_PATH)

        # 覆盖保存
        with open(PRODUCT_INFO_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(product_info_dict, f, allow_unicode=True)

        # 更新状态
        status.update(label="添加商品成功!", state="complete", expanded=False)

        st.toast("添加商品成功!", icon="🎉")

        with st.spinner("准备刷新页面..."):
            time.sleep(3)

        # 刷新页面
        st.rerun()


@st.cache_resource
def gen_rag_db(force_gen=False):
    """
    生成向量数据库。

    参数:
    force_gen - 布尔值，当设置为 True 时，即使数据库已存在也会重新生成数据库。
    """

    # 检查数据库目录是否存在，如果存在且force_gen为False，则不执行生成操作
    if Path(RAG_VECTOR_DB_DIR).exists() and not force_gen:
        return

    print("Generating rag database, pls wait ...")
    # 调用函数生成向量数据库
    gen_vector_db(RAG_CONFIG_PATH, PRODUCT_INSTRUCTION_DIR, RAG_VECTOR_DB_DIR)


if __name__ == "__main__":
    # streamlit run app.py --server.address=0.0.0.0 --server.port 7860

    # print("Starting...")
    if ENABLE_RAG:
        # 生成向量数据库
        gen_rag_db()

    main(MODEL_DIR, USING_LMDEPLOY, ENABLE_RAG)
