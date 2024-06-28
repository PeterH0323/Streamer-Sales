from pathlib import Path

import streamlit as st
from lmdeploy import TurbomindEngineConfig, pipeline
from modelscope import snapshot_download

from utils.web_configs import WEB_CONFIGS


@st.cache_resource
def load_turbomind_model(model_dir):  # hf awq

    print("load model begin.")

    model_format = "hf"
    if Path(model_dir).stem.endswith("-4bit"):
        model_format = "awq"

    model_dir = snapshot_download(model_dir, revision="master", cache_dir=WEB_CONFIGS.LLM_MODEL_DIR)

    backend_config = TurbomindEngineConfig(
        model_format=model_format, session_len=32768, cache_max_entry_count=WEB_CONFIGS.CACHE_MAX_ENTRY_COUNT
    )
    pipe = pipeline(model_dir, backend_config=backend_config, log_level="INFO", model_name="internlm2")

    print("load model end.")

    return pipe
    
