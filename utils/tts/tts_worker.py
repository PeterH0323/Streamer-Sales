from datetime import datetime
from pathlib import Path
import streamlit as st
# from utils.tts.sambert_hifigan.tts_sambert_hifigan import gen_tts_wav
from utils.tts.gpt_sovits.inference_gpt_sovits import gen_tts_wav


def show_audio(tts_save_path):
    with open(tts_save_path, "rb") as f_wav:
        audio_bytes = f_wav.read()
    st.audio(audio_bytes, format="audio/wav")


def gen_tts_in_spinner(cur_response):
    tts_save_path = None
    if (st.session_state.tts_model is not None or st.session_state.bert_tokenizer is not None) and st.session_state.gen_tts_checkbox:
        with st.spinner("正在生成语音，请稍等... 如果觉得生成时间太久，可以将侧边栏的【生成语音】按钮取消选中，下次则不会生成"):
            save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".wav"
            tts_save_path = str(Path(st.session_state.tts_wav_root).joinpath(save_tag).absolute())
            # gen_tts_wav(st.session_state.tts_model, cur_response, tts_save_path)

            # inp_ref = r"/root/hingwen_camp/utils/tts/gpt_sovits/weights/ref_wav/【开心】处理完之前的事情，这几天甚至都有空闲来车上转转了。.wav"
            text_language = "中英混合"
            gen_tts_wav(
                cur_response,
                text_language,
                st.session_state.bert_tokenizer,
                st.session_state.bert_model,
                st.session_state.ssl_model,
                st.session_state.vq_model,
                st.session_state.hps,
                st.session_state.max_sec,
                st.session_state.t2s_model,
                st.session_state.inp_ref,
                st.session_state.prompt_text,
                tts_save_path,
            )

            show_audio(tts_save_path)
            st.toast("生成语音成功!")
    return tts_save_path
