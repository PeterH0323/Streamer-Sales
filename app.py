import torch
from transformers import AutoTokenizer, AutoModelForCausalLM  # isort: skip
import copy
import cv2
import streamlit as st
import yaml

def resize_image(image_path, max_height):
    # 读取图片
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # 计算新的宽度，保持纵横比
    new_width = int(width * max_height / height)

    # 缩放图片
    resized_image = cv2.resize(image, (new_width, max_height))

    return resized_image


def on_btton_click(*args, **kwargs):
    # 按钮回调函数
    if kwargs["type"] == "check_manual":
        pass
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
            image = resize_image(product_info["images"], max_height=image_height)
            st.image(image, channels="bgr")

        with info_col:
            st.subheader("特点", divider="grey")

            heighlights_str = "、".join(product_info["heighlights"])
            st.text(heighlights_str)

            st.subheader("说明书", divider="grey")
            st.button(
                "查看",
                key=f"check_manual_{product_name}",
                on_click=on_btton_click,
                kwargs={"type": "check_manual", "product_name": product_name},
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
    with open(r"./dataset/gen_dataset/conversation_cfg.yaml", "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    sales_name = "乐乐喵"
    sales_info = dataset_yaml["role_type"][sales_name]

    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    system_str = system.replace("{role_type}", sales_name).replace("{character}", "、".join(sales_info))

    st.session_state.sales_info = system_str
    st.session_state.first_input_template = first_input
    st.session_state.product_info_struct_template = product_info_struct



@st.cache_resource
def load_model(model_dir, using_modelscope):
    if using_modelscope:
        from modelscope import snapshot_download

        model_dir = snapshot_download(model_dir, revision="master")
    model = AutoModelForCausalLM.from_pretrained(model_dir, trust_remote_code=True).to(torch.bfloat16).cuda()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    return model, tokenizer


def main(model_dir, using_modelscope):
    # --client.showSidebarNavigation=false
    st.set_page_config(
        page_title="Streamer-Sales 销冠",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://www.extremelycoolapp.com/help",
            "Report a bug": "https://www.extremelycoolapp.com/bug",
            "About": "# This is a header. This is an *extremely* cool app!",
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
    print("load model begin.")
    st.session_state.model, st.session_state.tokenizer = load_model(model_dir, using_modelscope)
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
    st.info("这是主播后台，这里需要主播讲解的商品目录，如果需要加入更多商品，点击下方的添加按钮即可", icon="ℹ️")

    # 读取 yaml 文件
    with open("./product_info/product_info.yaml", "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 配置
    product_image_height = 400
    each_card_offset = 100
    each_row_col = 2

    product_name_list = list(product_info_dict.keys())

    # TODO 侧边栏显示产品概览，数量，入驻品牌方
    with st.sidebar:
        # 标题
        st.markdown("## 销冠 —— 卖货主播大模型")
        "[销冠 —— 卖货主播大模型 Github repo](https://github.com/PeterH0323/Streamer-Sales)"

        st.markdown(f"## 主播后台信息")
        st.markdown(f"共有商品：{len(product_name_list)} 件")
        st.markdown(f"共有品牌方：{len(product_name_list)} 个")

    # 生成商品信息
    for row_id in range(0, len(product_name_list), each_row_col):
        for col_id, col_handler in enumerate(st.columns(each_row_col)):
            with col_handler:
                if row_id + col_id >= len(product_name_list):
                    continue
                product_name = product_name_list[row_id + col_id]
                make_product_container(product_name, product_info_dict[product_name], product_image_height, each_card_offset)

    with st.form(key="add_product_form"):
        product_name_input = st.text_input(label="添加商品名称")
        heightlight_input = st.text_input(label="添加商品特性")
        product_image = st.file_uploader(label="上传商品图片")
        product_book = st.file_uploader(label="上传商品说明书")
        submit_button = st.form_submit_button(label="提交")


if __name__ == "__main__":

    USING_MODELSCOPE = True
    if USING_MODELSCOPE:
        MODEL_DIR = "HinGwenWoong/streamer-sales-lelemiao-7b"
    else:
        MODEL_DIR = "hingwen/streamer-sales-lelemiao-7b"

    main(MODEL_DIR, USING_MODELSCOPE)
