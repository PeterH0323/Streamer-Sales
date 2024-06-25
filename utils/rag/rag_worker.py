import shutil
from pathlib import Path

import streamlit as st
import torch
import yaml

from utils.rag.feature_store import gen_vector_db
from utils.rag.retriever import CacheRetriever
from utils.web_configs import WEB_CONFIGS

# 基础配置
CONTEXT_MAX_LENGTH = 3000  # 上下文最大长度
GENERATE_TEMPLATE = "这是说明书：“{}”\n 客户的问题：“{}” \n 请阅读说明并运用你的性格进行解答。"  # RAG prompt 模板


def build_rag_prompt(rag_retriever: CacheRetriever, product_name, prompt):

    real_retriever = rag_retriever.get(fs_id="default")

    if isinstance(real_retriever, tuple):
        print(f" @@@ GOT real_retriever == tuple : {real_retriever}")
        return ""

    chunk, db_context, references = real_retriever.query(
        f"商品名：{product_name}。{prompt}", context_max_length=CONTEXT_MAX_LENGTH - 2 * len(GENERATE_TEMPLATE)
    )
    print(f"db_context = {db_context}")

    if db_context is not None and len(db_context) > 1:
        prompt_rag = GENERATE_TEMPLATE.format(db_context, prompt)
    else:
        print("db_context get error")
        prompt_rag = prompt

    print(f"RAG reference = {references}")
    print("=" * 20)

    return prompt_rag


def init_rag_retriever(rag_config: str, db_path: str):
    torch.cuda.empty_cache()

    retriever = CacheRetriever(config_path=rag_config)

    # 初始化
    retriever.get(fs_id="default", config_path=rag_config, work_dir=db_path)

    return retriever


def gen_rag_db(force_gen=False):
    """
    生成向量数据库。

    参数:
    force_gen - 布尔值，当设置为 True 时，即使数据库已存在也会重新生成数据库。
    """

    # 检查数据库目录是否存在，如果存在且force_gen为False，则不执行生成操作
    if Path(WEB_CONFIGS.RAG_VECTOR_DB_DIR).exists() and not force_gen:
        return

    if force_gen and Path(WEB_CONFIGS.RAG_VECTOR_DB_DIR).exists():
        shutil.rmtree(WEB_CONFIGS.RAG_VECTOR_DB_DIR)

    # 仅仅遍历 instructions 字段里面的文件
    if Path(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP).exists():
        shutil.rmtree(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP)
    Path(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP).mkdir(exist_ok=True, parents=True)

    # 读取 yaml 文件，获取所有说明书路径，并移动到 tmp 目录
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)
    for _, info in product_info_dict.items():
        shutil.copyfile(
            info["instruction"], Path(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP).joinpath(Path(info["instruction"]).name)
        )

    print("Generating rag database, pls wait ...")
    # 调用函数生成向量数据库
    gen_vector_db(
        WEB_CONFIGS.RAG_CONFIG_PATH,
        str(Path(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP).absolute()),
        WEB_CONFIGS.RAG_VECTOR_DB_DIR,
    )

    # 删除过程文件
    shutil.rmtree(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP)


@st.cache_resource
def load_rag_model():
    # 生成 rag 数据库
    gen_rag_db()

    # 加载 rag 模型
    retriever = init_rag_retriever(rag_config=WEB_CONFIGS.RAG_CONFIG_PATH, db_path=WEB_CONFIGS.RAG_VECTOR_DB_DIR)

    return retriever
