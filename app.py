import copy
import time

import cv2
import streamlit as st
import yaml

from utils.infer.lmdeploy_infer import load_turbomind_model
from utils.infer.transformers_infer import load_hf_model
from utils.rag.feature_store import gen_vector_db


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

# ==================================================================
#                               页面配置
# ==================================================================
PRODUCT_IMAGE_HEIGHT = 400  # 商品图片高度
EACH_CARD_OFFSET = 100  # 每个商品卡片比图片高度多出的距离
EACH_ROW_COL = 2  # 商品页显示多少列

# ==================================================================
#                             配置文件路径
# ==================================================================
PRODUCT_INFO_YAML_PATH = r"./product_info/product_info.yaml"
CONVERSATION_CFG_YAML_PATH = r"./configs/conversation_cfg.yaml"

# ==================================================================
#                               RAG 配置
# ==================================================================
RAG_CONFIG_PATH = r"./config/rag_config.yaml"
RAG_SOURCE_DIR = r"./product_info/instructions"
RAG_VECTOR_DB_DIR = r"./work_dir/rag_vector_db"


def resize_image(image_path, max_height):
    # 读取图片
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # 计算新的宽度，保持纵横比
    new_width = int(width * max_height / height)

    # 缩放图片
    resized_image = cv2.resize(image, (new_width, max_height))

    return resized_image


@st.experimental_dialog("产品说明书")
def instruction_dialog(instruction_path):
    """产品说明书 popup 显示框

    Args:
        instruction_path (str): 说明书路径
    """
    with open(instruction_path, "r", encoding="utf-8") as f:
        instruct_lines = f.readlines()

    st.markdown(instruct_lines)
    if st.button("确定"):
        # st.rerun()
        pass


def on_btton_click(*args, **kwargs):
    # 按钮回调函数
    if kwargs["type"] == "check_manual":
        instruction_dialog(kwargs["instruction_path"])

    elif kwargs["type"] == "process_sales":
        st.session_state.page_switch = "pages/selling_page.py"

        st.session_state.hightlight = kwargs["heighlights"]
        product_info_struct = copy.deepcopy(st.session_state.product_info_struct_template)
        product_info_str = product_info_struct[0].replace("{name}", kwargs["product_name"])
        product_info_str += product_info_struct[1].replace("{highlights}", st.session_state.hightlight)

        st.session_state.first_input = copy.deepcopy(st.session_state.first_input_template).replace(
            "{product_info}", product_info_str
        )

        st.session_state.image_path = kwargs["image_path"]
        st.session_state.product_name = kwargs["product_name"]

        # 清空对话
        st.session_state.messages = []


def make_product_container(product_name, product_info, image_height, each_card_offset):
    with st.container(border=True, height=image_height + each_card_offset):
        st.header(product_name)
        image_col, info_col = st.columns([0.2, 0.8])

        with image_col:
            print(f"Loading {product_info['images']} ...")
            image = resize_image(product_info["images"], max_height=image_height)
            st.image(image, channels="bgr")

        with info_col:
            st.subheader("特点", divider="grey")

            heighlights_str = "、".join(product_info["heighlights"])
            st.text(heighlights_str)

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
    with open(CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    sales_info = dataset_yaml["role_type"][SALES_NAME]

    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    system_str = system.replace("{role_type}", SALES_NAME).replace("{character}", "、".join(sales_info))

    st.session_state.sales_info = system_str
    st.session_state.first_input_template = first_input
    st.session_state.product_info_struct_template = product_info_struct


def main(model_dir, using_lmdeploy, enable_rag):
    # --client.showSidebarNavigation=false
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

    # 初始化页面跳转
    if "page_switch" not in st.session_state:
        st.session_state.page_switch = "app.py"
    st.session_state.current_page = "app.py"

    # 判断是否需要跳转页面
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # 加载模型
    st.session_state.using_lmdeploy = using_lmdeploy
    if st.session_state.using_lmdeploy:
        load_model_func = load_turbomind_model
    else:
        load_model_func = load_hf_model

    print("load model begin.")
    st.session_state.model, st.session_state.tokenizer, st.session_state.rag_retriever = load_model_func(
        model_dir, enable_rag=enable_rag, rag_config=RAG_CONFIG_PATH, db_path=RAG_VECTOR_DB_DIR
    )
    print("load model end.")

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
        "这是主播后台，这里需要主播讲解的商品目录，选择一个商品，点击【开始讲解】即可跳转到主播讲解页面。如果需要加入更多商品，点击下方的添加按钮即可（开发中）",
        icon="ℹ️",
    )

    # 读取 yaml 文件
    with open(PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    product_name_list = list(product_info_dict.keys())

    # TODO 侧边栏显示产品概览，数量，入驻品牌方
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

    with st.form(key="add_product_form"):
        product_name_input = st.text_input(label="添加商品名称")
        heightlight_input = st.text_input(label="添加商品特性")
        product_image = st.file_uploader(label="上传商品图片")
        product_instruction = st.file_uploader(label="上传商品说明书")
        submit_button = st.form_submit_button(label="提交(后续开放)", disabled=True)

        if submit_button:
            update_product_info(product_name_input, heightlight_input, product_image, product_instruction)


def update_product_info(product_name_input, heightlight_input, product_image, product_instruction):

    if product_name_input == "" or heightlight_input == "":
        st.error("商品名称和特性不能为空")
        return

    if product_image is None or product_instruction is None:
        st.error("图片和说明书不能为空")
        return

    with st.status("正在上传商品...", expanded=True) as status:
        st.write("说明书上传中...")
        # 保存图片 & 说明书
        time.sleep(1)

        st.write("更新商品明细表...")
        # 更新 product_infor.yaml
        time.sleep(1)

        st.write("生成数据库...")
        # 重新生成 RAG 向量数据库
        time.sleep(1)

        # TODO 可以不输入图片和特性，大模型自动生成一版让用户自行选择

        status.update(label="添加商品成功!", state="complete", expanded=False)
        st.rerun()


@st.cache_resource
def gen_rag_db():
    # 生成向量数据库
    gen_vector_db(RAG_CONFIG_PATH, RAG_SOURCE_DIR, RAG_VECTOR_DB_DIR)


if __name__ == "__main__":

    print("Starting...")

    if ENABLE_RAG:
        # 每次启动生成向量数据库
        gen_rag_db()

    main(MODEL_DIR, USING_LMDEPLOY, ENABLE_RAG)
