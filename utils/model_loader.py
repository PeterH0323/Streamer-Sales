from .web_configs import WEB_CONFIGS

from .rag.rag_worker import load_rag_model
from .asr.asr_worker import load_asr_model
from .digital_human.realtime_inference import digital_human_preprocess
from .infer.load_infer_model import load_turbomind_model
from .tts.gpt_sovits.inference_gpt_sovits import get_tts_model


# ==================================================================
#                             数字人 模型
# ==================================================================

if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
    DIGITAL_HUMAN_HANDLER = digital_human_preprocess(
        model_dir=WEB_CONFIGS.DIGITAL_HUMAN_MODEL_DIR,
        use_float16=False,
        video_path=WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH,
        work_dir=WEB_CONFIGS.DIGITAL_HUMAN_GEN_PATH,
        fps=WEB_CONFIGS.DIGITAL_HUMAN_FPS,
        bbox_shift=WEB_CONFIGS.DIGITAL_HUMAN_BBOX_SHIFT,
    )
else:
    DIGITAL_HUMAN_HANDLER = None


# ==================================================================
#                               RAG 模型
# ==================================================================

if WEB_CONFIGS.ENABLE_RAG:
    RAG_RETRIEVER = load_rag_model()
else:
    RAG_RETRIEVER = None


# ==================================================================
#                               TTS 模型
# ==================================================================

if WEB_CONFIGS.ENABLE_TTS:
    # samber
    # from utils.tts.sambert_hifigan.tts_sambert_hifigan import get_tts_model
    # TTS_HANDLER = get_tts_model()

    # gpt_sovits
    TTS_HANDLER = get_tts_model()
else:
    TTS_HANDLER = None


# ==================================================================
#                               ASR 模型
# ==================================================================

if WEB_CONFIGS.ENABLE_ASR:
    ASR_HANDLER = load_asr_model()
else:
    ASR_HANDLER = None


# ==================================================================
#                               LLM 模型
# ==================================================================

# 加载 LLM 模型
LLM_MODEL = load_turbomind_model(WEB_CONFIGS.LLM_MODEL_NAME)
