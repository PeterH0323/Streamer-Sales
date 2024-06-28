import datetime
from funasr import AutoModel
import streamlit as st
from utils.web_configs import WEB_CONFIGS
from modelscope import snapshot_download
from modelscope.utils.constant import Invoke, ThirdParty
from funasr.download.name_maps_from_hub import name_maps_ms as NAME_MAPS_MS


@st.cache_resource
def load_asr_model():

    # 模型下载
    model_path_info = dict()
    for model_name in ["paraformer-zh", "fsmn-vad", "ct-punc"]:
        print(f"downloading asr model : {NAME_MAPS_MS[model_name]}")
        mode_dir = snapshot_download(
            NAME_MAPS_MS[model_name],
            revision="master",
            user_agent={Invoke.KEY: Invoke.PIPELINE, ThirdParty.KEY: "funasr"},
            cache_dir=WEB_CONFIGS.ASR_MODEL_DIR,
        )
        model_path_info[model_name] = mode_dir
        NAME_MAPS_MS[model_name] = mode_dir # 更新

    print(f"ASR model path info = {model_path_info}")
    # paraformer-zh is a multi-functional asr model
    # use vad, punc, spk or not as you need
    model = AutoModel(
        model="paraformer-zh",  # 语音识别，带时间戳输出，非实时
        vad_model="fsmn-vad",  # 语音端点检测，实时
        punc_model="ct-punc",  # 标点恢复
        # spk_model="cam++" # 说话人确认/分割
        model_path=model_path_info["paraformer-zh"],
        vad_kwargs={"model_path": model_path_info["fsmn-vad"]},
        punc_kwargs={"model_path": model_path_info["ct-punc"]},
    )
    return model


def process_asr(model: AutoModel, wav_path):
    # https://github.com/modelscope/FunASR/blob/main/README_zh.md#%E5%AE%9E%E6%97%B6%E8%AF%AD%E9%9F%B3%E8%AF%86%E5%88%AB
    f_start_time = datetime.datetime.now()
    res = model.generate(input=wav_path, batch_size_s=50, hotword="魔搭")
    delta_time = datetime.datetime.now() - f_start_time

    try:
        print(f"ASR using time {delta_time}s, text: ", res[0]["text"])
        res_str = res[0]["text"]
    except Exception as e:
        print("ASR 解析失败，无法获取到文字")
        return ""

    return res_str
