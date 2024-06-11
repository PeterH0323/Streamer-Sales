from datetime import datetime
from pathlib import Path

import streamlit as st

# from utils.tts.sambert_hifigan.tts_sambert_hifigan import gen_tts_wav
from utils.model_loader import TTS_HANDLER
from utils.tts.gpt_sovits.inference_gpt_sovits import gen_tts_wav
from utils.web_configs import WEB_CONFIGS


def show_audio(tts_path):

    if tts_path is None:
        return

    with open(tts_path, "rb") as f_wav:
        audio_bytes = f_wav.read()
    st.audio(audio_bytes, format="audio/wav")


def gen_tts_in_spinner(cur_response):
    tts_save_path = None
    if TTS_HANDLER is not None and st.session_state.gen_tts_checkbox:
        with st.spinner("正在生成语音，请稍等... 如果觉得生成时间太久，可以将侧边栏的【生成语音】按钮取消选中，下次则不会生成"):
            save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".wav"
            tts_save_path = str(Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).joinpath(save_tag).absolute())
            # gen_tts_wav(st.session_state.tts_handler, cur_response, tts_save_path)

            # inp_ref = r"/root/hingwen_camp/utils/tts/gpt_sovits/weights/ref_wav/【开心】处理完之前的事情，这几天甚至都有空闲来车上转转了。.wav"
            text_language = "中英混合"
            gen_tts_wav(
                cur_response,
                text_language,
                TTS_HANDLER.bert_tokenizer,
                TTS_HANDLER.bert_model,
                TTS_HANDLER.ssl_model,
                TTS_HANDLER.vq_model,
                TTS_HANDLER.hps,
                TTS_HANDLER.max_sec,
                TTS_HANDLER.t2s_model,
                TTS_HANDLER.inp_ref,
                TTS_HANDLER.prompt_text,
                TTS_HANDLER.prompt,
                TTS_HANDLER.refer,
                TTS_HANDLER.bert1,
                TTS_HANDLER.phones1,
                TTS_HANDLER.zero_wav,
                tts_save_path,
            )

            show_audio(tts_save_path)
            st.toast("生成语音成功!")
    return tts_save_path
