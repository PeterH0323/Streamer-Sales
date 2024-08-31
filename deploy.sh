# 进入虚拟环境
conda activate streamer-sales

# CUDA_VISIBLE_DEVICES
export HF_ENDPOINT="https://hf-mirror.com"

# ========================== 后端 =============================

# TTS
uvicorn server.tts.tts_server:app --host 0.0.0.0 --port 8001

# Digital Human
uvicorn server.digital_human.digital_human_server:app --host 0.0.0.0 --port 8002

# ASR
export MODELSCOPE_CACHE="./weights/asr_weights"
uvicorn server.asr.asr_server:app --host 0.0.0.0 --port 8003

# LLM
export LMDEPLOY_USE_MODELSCOPE=True
export MODELSCOPE_CACHE="./weights/llm_weights"
lmdeploy serve api_server HinGwenWoong/streamer-sales-lelemiao-7b \
                          --server-port 23333 \
                          --model-name internlm2 \
                          --session-len 32768 \
                          --cache-max-entry-count 0.1 \
                          --model-format hf

# 中台  llm + rag + agent
# Agent Key (如果没有请忽略)
export DELIVERY_TIME_API_KEY="${快递 EBusinessID},${快递 api_key}"
export WEATHER_API_KEY="${天气 API key}"
uvicorn server.base.base_server:app --host 0.0.0.0 --port 8000


# ========================== 前端 =============================
# 前端
streamlit run app.py --server.address=0.0.0.0 --server.port 7860 
