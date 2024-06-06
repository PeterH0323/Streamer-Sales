from pathlib import Path

import streamlit as st
import torch
from lmdeploy import TurbomindEngineConfig, pipeline
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

from utils.tools import init_rag_retriever
from utils.web_configs import WEB_CONFIGS


@st.cache_resource
def load_turbomind_model(model_dir, enable_rag=True, rag_config=None, db_path=None):  # hf awq

    print("load model begin.")

    retriever = None
    if enable_rag:
        # 加载 rag 模型
        retriever = init_rag_retriever(rag_config=rag_config, db_path=db_path)

    model_format = "hf"
    if Path(model_dir).stem.endswith("-4bit"):
        model_format = "awq"

    model_dir = snapshot_download(model_dir, revision="master")
    backend_config = TurbomindEngineConfig(
        model_format=model_format, session_len=32768, cache_max_entry_count=WEB_CONFIGS.CACHE_MAX_ENTRY_COUNT
    )
    pipe = pipeline(model_dir, backend_config=backend_config, log_level="INFO", model_name="internlm2")

    print("load model end.")
    return pipe, None, retriever


@st.cache_resource
def load_hf_model(model_dir, enable_rag=True, rag_config=None, db_path=None):
    print("load model begin.")

    retriever = None
    if enable_rag:
        # 加载 rag 模型
        retriever = init_rag_retriever(rag_config=rag_config, db_path=db_path)

    model_dir = snapshot_download(model_dir, revision="master")
    model = AutoModelForCausalLM.from_pretrained(model_dir, trust_remote_code=True).to(torch.bfloat16).cuda()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)

    print("load model end.")
    return model, tokenizer, retriever
