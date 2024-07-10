# 进入虚拟环境
conda activate streamer-sales

# LLM
lmdeploy serve api_server /root/.cache/modelscope/hub/HinGwenWoong/streamer-sales-lelemiao-7b \
                          --server-port 23333 \
                          --model-name internlm2 \
                          --session-len 32768 \
                          --cache-max-entry-count 0.1 \
                          --model-format hf

# 后端

# Agent Key (如果没有请忽略)
export DELIVERY_TIME_API_KEY="${快递 EBusinessID},${快递 api_key}"
export WEATHER_API_KEY="${天气 API key}"

uvicorn server.base.base_server:app --host 0.0.0.0 --port 8000 # base: llm + rag + agent

uvicorn server.tts_server.tts_server:app --host 0.0.0.0 --port 8001 # tts
uvicorn server.digital_human_server.digital_human_server:app --host 0.0.0.0 --port 8002 # digital human
uvicorn server.asr_server.asr_server:app --host 0.0.0.0 --port 8003 # asr

# 前端
streamlit run app.py --server.address=0.0.0.0 --server.port 7860 
