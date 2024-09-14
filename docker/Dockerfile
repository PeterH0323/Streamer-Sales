FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel

LABEL MAINTAINER="HinGwen.Wong"

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo 'Asia/Shanghai' > /etc/timezone

# 切换阿里源并安装必须的系统库
RUN sed -i s/archive.ubuntu.com/mirrors.aliyun.com/g /etc/apt/sources.list \
    && sed -i s/security.ubuntu.com/mirrors.aliyun.com/g /etc/apt/sources.list \
    && apt-get update -y \ 
    && apt-get install -y --no-install-recommends wget git libgl1 libglib2.0-0 unzip libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /workspace/Streamer-Sales
WORKDIR /workspace/Streamer-Sales

ENV HF_ENDPOINT="https://hf-mirror.com"
ENV LANG="en_US.UTF-8"

# 安装必备依赖环境
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt
