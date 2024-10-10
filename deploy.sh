#!/bin/bash

# 检查参数个数
if [ "$#" -ne 1 ]; then
    echo "Error: 必须且只能提供一个参数."
    echo "可用的选项为: tts, dg, asr, llm, base 或者 frontend."
    exit 1
fi

# 进入虚拟环境
# conda deactivate
conda activate streamer-sales

# 可选配置显卡 
# export CUDA_VISIBLE_DEVICES=1

# 配置 huggingface 国内镜像地址
export HF_ENDPOINT="https://hf-mirror.com"

case $1 in
    tts)
        echo "正在启动 TTS 服务..."
        uvicorn server.tts.tts_server:app --host 0.0.0.0 --port 8001
        ;;

    dg)
        echo "正在启动 数字人 服务..."
        uvicorn server.digital_human.digital_human_server:app --host 0.0.0.0 --port 8002
        ;;

    asr)
        echo "正在启动 ASR 服务..."
        export MODELSCOPE_CACHE="./weights/asr_weights"
        uvicorn server.asr.asr_server:app --host 0.0.0.0 --port 8003
        ;;

    llm)
        echo "正在启动 LLM 服务..."
        export LMDEPLOY_USE_MODELSCOPE=True
        export MODELSCOPE_CACHE="./weights/llm_weights"
        lmdeploy serve api_server HinGwenWoong/streamer-sales-lelemiao-7b \
                                  --server-port 23333 \
                                  --model-name internlm2 \
                                  --session-len 32768 \
                                  --cache-max-entry-count 0.1 \
                                  --model-format hf
        ;;

    llm-4bit)
        echo "正在启动 LLM-4bit 服务..."
        export LMDEPLOY_USE_MODELSCOPE=True
        export MODELSCOPE_CACHE="./weights/llm_weights"
        lmdeploy serve api_server HinGwenWoong/streamer-sales-lelemiao-7b-4bit \
                                  --server-port 23333 \
                                  --model-name internlm2 \
                                  --session-len 32768 \
                                  --cache-max-entry-count 0.1 \
                                  --model-format awq
        ;;

    base)
        echo "正在启动 中台 服务..."
        # Agent Key (如果有请配置，没有请忽略)
        # export DELIVERY_TIME_API_KEY="${快递 EBusinessID},${快递 api_key}"
        # export WEATHER_API_KEY="${天气 API key}"
        uvicorn server.base.base_server:app --host 0.0.0.0 --port 8000
        ;;

    frontend)
        echo "正在启动 前端 服务..."
        cd frontend
        # npm install
        npm run dev
        ;;

    *)
        echo "错误: 不支持的参数 '$1'."
        echo "可用的选项为: tts, dg, asr, llm, llm-4bit, base 或者 frontend."
        exit 1
        ;;
esac

exit 0



