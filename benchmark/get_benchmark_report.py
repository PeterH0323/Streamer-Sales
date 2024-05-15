import datetime
from pathlib import Path

import torch
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline
from prettytable import PrettyTable
from transformers import AutoModelForCausalLM, AutoTokenizer
from modelscope import snapshot_download


def get_lmdeploy_benchmark(mode_name, model_format="hf", tag="LMDeploy (Turbomind)"):
    print(f"Processing {mode_name}")

    model_path = snapshot_download(mode_name, revision="master")

    backend_config = TurbomindEngineConfig(model_format=model_format, session_len=32768)
    gen_config = GenerationConfig(
        top_p=0.8,
        top_k=40,
        temperature=0.7,
        # max_new_tokens=4096
    )
    pipe = pipeline(model_path, backend_config=backend_config)

    # warmup
    inp = "你好！"
    for i in range(5):
        print(f"Warm up...[{i+1}/5]")
        pipe([inp])

    # test speed
    times = 10
    total_words = 0
    start_time = datetime.datetime.now()
    for i in range(times):
        response = pipe(["请介绍一下你自己。"], gen_config=gen_config)
        total_words += len(response[0].text)
    end_time = datetime.datetime.now()

    delta_time = end_time - start_time
    delta_time = delta_time.seconds + delta_time.microseconds / 1000000.0
    speed = total_words / delta_time

    print(f"{Path(model_path).name:<10}, {speed:.3f}")
    return [Path(model_path).name, tag, round(speed, 4)]


def get_hf_benchmark(model_name, tag="transformer"):

    print(f"Processing {model_name}")

    model_path = snapshot_download(model_name, revision="master")

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    # Set `torch_dtype=torch.float16` to load model in float16, otherwise it will be loaded as float32 and cause OOM Error.
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True).cuda()
    model = model.eval()

    # warmup
    inp = "你好！"
    for i in range(5):
        print(f"Warm up...[{i + 1}/5]")
        response, history = model.chat(tokenizer, inp, history=[])

    # test speed
    inp = "请介绍一下你自己。"
    times = 10
    total_words = 0
    start_time = datetime.datetime.now()
    for i in range(times):
        response, history = model.chat(tokenizer, inp, history=history)
        total_words += len(response)
    end_time = datetime.datetime.now()

    delta_time = end_time - start_time
    delta_time = delta_time.seconds + delta_time.microseconds / 1000000.0
    speed = total_words / delta_time
    print(f"{Path(model_path).name:<10}, {speed:.3f}")
    return [Path(model_path).name, tag, round(speed, 4)]


if __name__ == "__main__":

    table = PrettyTable()
    table.field_names = ["Model", "Toolkit", "Speed (words/s)"]
    table.add_row(get_hf_benchmark("HinGwenWoong/streamer-sales-lelemiao-7b"))
    table.add_row(get_lmdeploy_benchmark("HinGwenWoong/streamer-sales-lelemiao-7b", model_format="hf"))
    table.add_row(get_lmdeploy_benchmark("HinGwenWoong/streamer-sales-lelemiao-7b-4bit", model_format="awq"))
    print(table)
