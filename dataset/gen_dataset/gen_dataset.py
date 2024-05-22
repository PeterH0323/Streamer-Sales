import argparse
from copy import deepcopy
import json
import random
import re
from http import HTTPStatus
from pathlib import Path

import dashscope
import requests
import yaml
from tqdm import tqdm


def set_api_key(api_type, api_yaml_path):
    """设置 api key

    Args:
        api_type (str): api 类型
        api_yaml_path (str): api yaml 文件路径
    """
    # 读取 yaml 文件
    with open(api_yaml_path, "r", encoding="utf-8") as f:
        api_yaml = yaml.safe_load(f)

    # 设置 api key
    if api_type == "qwen":
        api_key = api_yaml["ali_qwen_api_key"]
        dashscope.api_key = api_key
    elif api_type == "ernie":
        api_key = api_yaml["baidu_ernie_api_key"]
    else:
        raise ValueError("api_type must be qwen or ernie")

    return api_key


def call_qwen_message(content_str, model_type=dashscope.Generation.Models.qwen_turbo):

    try:
        response = dashscope.Generation.call(model_type, prompt=content_str)
    except Exception as e:
        print(f"Maybe connect error , try again : {e}")
        response = dashscope.Generation.call(model_type, prompt=content_str)

    if response.status_code == HTTPStatus.OK:
        print("Used token: ", response.usage)
        response_str = response.output.text
    else:
        print(
            "Request id: %s, Status code: %s, error code: %s, error message: %s"
            % (
                response.request_id,
                response.status_code,
                response.code,
                response.message,
            )
        )
        response_str = "Error"

    return response_str


def call_ernie_message(content_str, access_token):
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"

    payload = json.dumps(
        {
            "messages": [
                {"role": "user", "content": content_str},
            ],
            "disable_search": False,
            "enable_citation": False,
        }
    )
    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == HTTPStatus.OK:

        # 获取 body 中的数据
        response_json = response.json()

        print("Used token: ", response_json["usage"])
        response_str = response_json["result"]
    else:
        response_str = "Error"

    return response_str


def format_json_from_response(func, content_str, func_args, model_name):
    response = func(content_str, func_args)

    if "```json" in response:
        response = re.findall(r"```json(.*)```", response, flags=re.DOTALL)[0]

    # 去掉导致 json 格式化失败的字符
    response = response.replace("\\", "\\\\").replace("\n\n", "\n").replace("”", '"').replace("“", '"')

    if model_name == "qwen":
        # qwen 需要检查文案中是否有 " ，并替换为单引号 '

        # 查找第一个 output 的字符串
        output_start = response.find('"output": "')
        if output_start != -1:
            # 查找第二个 output 的字符位置
            output_end = response.find("}", output_start + 1)
            if output_end != -1:
                response = list(response)
                # 截取第二个 output 的字符串
                check_len = len(response[output_start + len('"output": "') : output_end - 10])
                for idx in range(check_len):
                    str_idx = output_start + len('"output": "') + idx
                    if response[str_idx] == '"':
                        response[str_idx] = "'"

                response = "".join(response)

    # 加上 strict=False 解决 decode Invalid control character
    format_json = json.loads(response, strict=False)

    return format_json, response


def process_request(func, content_str, func_args, model_name):
    """_summary_

    Args:
        func (_type_): _description_
        content_str (_type_): _description_
        func_args (str):
            qwen: model_type
            ernie: api_key
    Returns:
        _type_: _description_
    """

    try:
        format_json, response = format_json_from_response(func, content_str, func_args, model_name)
    except Exception as e:
        try:
            # 再试一次
            print(f"\n Got error, try again <== {e} \n")
            if isinstance(e, json.decoder.JSONDecodeError):
                print(f"JSONDecodeError doc 1: {str(e.doc)} \n")
            format_json, response = format_json_from_response(func, content_str, func_args, model_name)
        except Exception as e:
            print(f"\n Got error <== {e} \n")
            if isinstance(e, json.decoder.JSONDecodeError):
                print(f"JSONDecodeError doc 2: {str(e.doc)} \n")
            with open(f"error-{model_name}.log", "a+", encoding="utf-8") as f_error:
                if isinstance(e, json.decoder.JSONDecodeError):
                    f_error.write(f"JSONDecodeError doc: {str(e.doc)} \n")
                f_error.write(str(e))
                f_error.flush()

            format_json = {"Error": "Error"}

    return format_json


def gen_product_highlights(dastset_yaml_path, api_yaml_path):
    """根据产品的 yaml 文件生成每个产品的特点描述

    Args:
        dastset_yaml_path (str): 数据集的 yaml 文件路径
        api_yaml_path (_type_): api 的 yaml 文件路径
    """

    # 读取 yaml 文件
    with open(dastset_yaml_path, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    set_api_key("qwen", api_yaml_path)

    for _, products in dataset_yaml["product_list"].items():
        for product_class, product in products.items():
            product_str = str(product).replace("'", "")
            print(f"Process: {product_str}")

            product_highlights = call_qwen_message(
                content_str=product_str,
                system_str="现在你精通任何产品，你可以帮我举例每个产品的6个亮点或特点，, 然后用python dict形式输出：{类名：[特点1, 特点2] ...} ，去掉特点12的字样，除python字典外的其他都不要输出，不要有任何的警告信息",
                model_type=dashscope.Generation.Models.qwen_turbo,
            )

            code_block = re.findall(r"```python(.*)```", product_highlights, flags=re.DOTALL)[0]
            if " = " in code_block[:20]:
                code_block = code_block.split(" = ")[1]

            products[product_class] = eval(re.findall(r"```python(.*)```", product_highlights, flags=re.DOTALL)[0])

    # 保存 yaml 文件
    with open(f"{dastset_yaml_path}", "w", encoding="utf-8") as f:
        yaml.dump(dataset_yaml, f, allow_unicode=True)


def gen_dataset(dastset_yaml_path: str, api_yaml_path: str, save_json_root: Path, model_name: str, specific_name=""):

    # 确保文件夹存在
    save_json_root.mkdir(parents=True, exist_ok=True)

    # 读取 yaml 文件
    with open(dastset_yaml_path, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    if specific_name != "":
        assert (
            specific_name in dataset_yaml["role_type"]
        ), f"{specific_name} not in dataset_yaml['role_type'] ({dataset_yaml['role_type']}), pls check dataset yaml!"

    # 设置 api key
    api_key = set_api_key(model_name, api_yaml_path)

    data_gen_setting = dataset_yaml["data_generation_setting"]
    gen_num = data_gen_setting["each_product_gen"]
    each_pick_hightlight = data_gen_setting["each_pick_hightlight"]
    each_pick_question = data_gen_setting["each_pick_question"]

    # qwen 配置调取的模型种类，确保有个一是最强模型
    # gen_model_type = [dashscope.Generation.Models.qwen_plus] * (gen_num - 2)
    # gen_model_type += [dashscope.Generation.Models.qwen_max] * 2
    qwen_model_type = [dashscope.Generation.Models.qwen_max] * gen_num

    for role_type, role_character in dataset_yaml["role_type"].items():

        if specific_name != "" and role_type != specific_name:
            # 只生成特定人物的
            print(f"specific_name = {specific_name}, skipping for {role_type}")
            continue

        gen_json = dict()

        save_json_path = save_json_root.joinpath(f"{model_name}_{role_type}_train.json")
        bk_json_path = save_json_root.joinpath(f"{model_name}_{role_type}_train.json.bk")

        # 加载之前已经有的 json
        if save_json_path.exists():
            with open(save_json_path, "r", encoding="utf-8") as f:
                gen_json = json.load(f)

        # 加载成功的话，再删除备份的 json
        if bk_json_path.exists():
            bk_json_path.unlink()

        # 遍历所有产品，方便进度条显示
        list_product = [
            product_name
            for _, products in dataset_yaml["product_list"].items()
            for _, product_name_list in products.items()
            for product_name in product_name_list.keys()
        ]

        # 生成人物性格
        character = "、".join(role_character)

        pbar = tqdm(total=len(list_product))

        # 遍历产品
        for _, products in dataset_yaml["product_list"].items():
            for _, product_name_list in products.items():
                for product, hightlights in product_name_list.items():
                    pbar.set_description(product)

                    if product in gen_json:
                        # 跳过已经有的
                        pbar.update(1)
                        continue

                    gen_json.update({product: []})

                    # 生成数据
                    for idx in range(gen_num):

                        # 随机抽取 ${each_pick_hightlight} 个产品特性
                        if each_pick_hightlight >= len(hightlights):
                            # 超过打乱，增加随机性
                            hightlights_list = random.shuffle(hightlights)
                        else:
                            hightlights_list = random.sample(hightlights, each_pick_hightlight)
                        hightlight_str = "、".join(hightlights_list)

                        # 随机抽取 ${each_pick_question} 个提问角度
                        if each_pick_question >= len(dataset_yaml["customer_question_type"]):
                            # 超过打乱，增加随机性
                            customer_question_type = random.shuffle(dataset_yaml["customer_question_type"])
                        else:
                            customer_question_type = random.sample(dataset_yaml["customer_question_type"], each_pick_question)
                        customer_question_str = "、".join(customer_question_type)

                        # 商品信息
                        product_info_str = dataset_yaml["product_info_struct"][0].replace("{name}", product)
                        product_info_str += dataset_yaml["product_info_struct"][1].replace("{highlights}", hightlight_str)

                        content_str = (
                            data_gen_setting["dataset_gen_prompt"]
                            .replace("{role_type}", role_type)
                            .replace("{character}", character)
                            .replace("{product_info}", product_info_str)
                            .replace("{customer_question}", customer_question_str)
                            .replace("{each_conversation_qa}", str(data_gen_setting["each_conversation_qa"]))
                            .replace(
                                "{dataset_json_format}",
                                data_gen_setting["dataset_json_format"].replace("{product_info}", product_info_str),
                            )
                        )

                        print(f"\n Resquest [ {model_name} ] {idx + 1}/{gen_num} ==> {content_str} \n")
                        if model_name == "qwen":
                            format_json = process_request(call_qwen_message, content_str, qwen_model_type[idx], model_name)
                        elif model_name == "ernie":
                            format_json = process_request(call_ernie_message, content_str, api_key, model_name)
                        else:
                            raise ValueError(f"model_name {model_name} not support")

                        if "conversation" in format_json and len(format_json["conversation"]) > 0:

                            # 第一个结果因为节省 token，需要将 system 和 input 放回去
                            conversation_setting = deepcopy(dataset_yaml["conversation_setting"])
                            system_str = (
                                conversation_setting["system"].replace("{role_type}", role_type).replace("{character}", character)
                            )
                            input_str = conversation_setting["first_input"].replace("{product_info}", product_info_str)

                            # 将第一个对话加入必要信息
                            format_json["conversation"][0] = {
                                "system": system_str,
                                "input": input_str,
                                "output": format_json["conversation"][0]["output"],
                            }
                        else:
                            format_json = {"Error": "Error"}

                        print(f"\n Response [ {model_name} ] {idx + 1}/{gen_num} <== {format_json} \n")
                        gen_json[product].append(format_json)

                    pbar.update(1)

                    # 备份旧的
                    if save_json_path.exists():
                        save_json_path.rename(bk_json_path)

                    # 保存 json
                    with open(save_json_path, "w", encoding="utf-8") as f:
                        json.dump(gen_json, f, indent=4, ensure_ascii=False)

                    # 如果保存成功，删掉旧的
                    if bk_json_path.exists():
                        bk_json_path.unlink()


if __name__ == "__main__":

    # 例子：全部人物使用 Qwen api 生成数据
    # cd /path/to/Streamer-Sales/dataset/gen_dataset
    # python gen_dataset.py qwen

    # 命令行输入参数
    parser = argparse.ArgumentParser(description="Gen Dataset")
    parser.add_argument("model_name", type=str, choices=["qwen", "ernie"], help="Model name for data generation")
    parser.add_argument("--data_yaml", type=str, default="../../configs/conversation_cfg.yaml", help="data setting file path")
    parser.add_argument("--api_yaml", type=str, default="../../configs/api_cfg.yaml", help="api setting file path")
    parser.add_argument("--output_dir", type=str, default="./train_dataset/response", help="generation json output dir")
    parser.add_argument("--specific_name", type=str, default="", help="Character name for data generation")
    args = parser.parse_args()

    # 生成产品特性（可选）
    # gen_product_highlights(args.data_yaml, args.api_yaml)

    # 生成对话数据集
    gen_dataset(
        args.data_yaml, args.api_yaml, Path(args.output_dir), model_name=args.model_name, specific_name=args.specific_name
    )
