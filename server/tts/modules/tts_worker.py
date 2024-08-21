from pathlib import Path


from ...web_configs import WEB_CONFIGS
from .gpt_sovits.inference_gpt_sovits import gen_tts_wav, get_tts_model

if WEB_CONFIGS.ENABLE_TTS:
    # samber
    # from utils.tts.sambert_hifigan.tts_sambert_hifigan import get_tts_model
    # TTS_HANDLER = get_tts_model()

    # gpt_sovits
    TTS_HANDLER = get_tts_model()
else:
    TTS_HANDLER = None


async def gen_tts_wav_app(cur_response, save_tag):
    # if save_tag == "":
    #     save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".wav"

    tts_save_path = str(Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).joinpath(save_tag).absolute())
    if not Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).exists():
        Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).mkdir(parents=True, exist_ok=True)

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

    return tts_save_path
