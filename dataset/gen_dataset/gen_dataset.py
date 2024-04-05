from http import HTTPStatus
import json
import os
from pathlib import Path
import random
import re
import dashscope
from tqdm import tqdm
import yaml


def call_qwen_message(content_str, system_str="You are a helpful assistant.", model_type=dashscope.Generation.Models.qwen_turbo):

    try:
        response = dashscope.Generation.call(model_type, prompt=content_str)
    except Exception as e:
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

    # return response.output.choices[0]["message"]["content"]
    return response_str


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
    elif api_type == "baidu":
        pass


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


def gen_qwen_dataset(dastset_yaml_path, api_yaml_path, save_json_root):
    # 读取 yaml 文件
    with open(dastset_yaml_path, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    # 设置 api key
    set_api_key("qwen", api_yaml_path)

    for role_type, role_character in dataset_yaml["role_type"].items():

        if role_type != "萝莉":
            # 先生成萝莉的
            break

        # 生成任务及其性格
        character = "、".join(role_character)

        gen_json = dict()

        # 遍历所有产品，方便进度条显示
        list_product = [
            product_name
            for _, products in dataset_yaml["product_list"].items()
            for _, product_name_list in products.items()
            for product_name in product_name_list.keys()
        ]

        pbar = tqdm(total=len(list_product))
        # 遍历产品
        for product_type, products in dataset_yaml["product_list"].items():
            for product_class, product_name_list in products.items():
                for product, hightlights in product_name_list.items():
                    pbar.set_description(product)

                    gen_json.update({product_type: {product_class: {product: []}}})

                    conversation_setting = dataset_yaml["conversation_setting"]
                    gen_num = conversation_setting["each_product_gen"]

                    # 配置调取的模型种类，确保有个一是最强模型
                    # gen_model_type = [dashscope.Generation.Models.qwen_plus] * (gen_num - 2)
                    # gen_model_type += [dashscope.Generation.Models.qwen_max] * 2
                    gen_model_type = [dashscope.Generation.Models.qwen_max] * 3

                    # 生成数据
                    for idx in range(gen_num):

                        # 随机抽取 3 个产品特性
                        hightlights_list = random.sample(hightlights, 3)
                        hightlight_str = "、".join(hightlights_list)

                        # 随机抽取 3 个提问角度
                        customer_question_type = random.sample(dataset_yaml["customer_question_type"], 3)
                        customer_question_str = "、".join(customer_question_type)

                        # 商品信息
                        product_info_str = dataset_yaml["product_info_struct"][0].replace("{name}", product)
                        product_info_str += dataset_yaml["product_info_struct"][1].replace("{highlights}", hightlight_str)

                        content_str = (
                            conversation_setting["dataset_gen_prompt"]
                            .replace("{role_type}", role_type)
                            .replace("{character}", character)
                            .replace("{product_info}", product_info_str)
                            .replace("{customer_question}", customer_question_str)
                            .replace("{each_conversation_qa}", str(conversation_setting["each_conversation_qa"]))
                            .replace(
                                "{dataset_json_format}",
                                conversation_setting["dataset_json_format"].replace("{product_info}", product_info_str),
                            )
                        )

                        try:
                            print(f"\n Resquest ==> {content_str} \n")
                            qwen_response = call_qwen_message(content_str=content_str, model_type=gen_model_type[idx])

                            if "```json" in qwen_response:
                                qwen_response = re.findall(r"```json(.*)```", qwen_response, flags=re.DOTALL)[0]

                            format_json = json.loads(
                                qwen_response.replace("\\", "\\\\"), strict=False
                            )  # 加上 strict=False 解决 decode Invalid control character

                            # 将第一个对话加入必要信息
                            format_json["conversation"][0] = {
                                "system": f"现在你是一位金牌带货{role_type}主播，你的说话方式是{character}。你能够根据产品信息讲解产品并且结合商品信息解答用户提出的疑问。",
                                "input": f"我的{product_info_str}，你需要根据我给出的商品信息撰写一段直播带货口播文案。你需要放大商品的亮点价值，激发用户的购买欲。",
                                "output": format_json["conversation"][0]["output"],
                            }
                            print(f"\n Response <== {format_json} \n")
                        except Exception as e:
                            print(f"\n Got error <== {e} \n")
                            format_json = {"@@@@ Error @@@@"}

                        gen_json[product_type][product_class][product].append(format_json)

                    pbar.update(1)

                    # json dump
                    with open(Path(save_json_root).joinpath(f"{role_type}_train_step.json"), "w", encoding="utf-8") as f:
                        json.dump(gen_json, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    DATA_YAML_PATH = "/path/to/dataset/gen_dataset/conversation_cfg.yaml"
    API_YAML_PATH =  "/path/to/dataset/gen_dataset/api_cfg.yaml"

    GEN_JSON_STEP_ROOT = "/path/to/dataset/trainval_dataset/step"

    # gen_product_highlights(DATA_YAML_PATH, API_YAML_PATH)
    gen_qwen_dataset(DATA_YAML_PATH, API_YAML_PATH, GEN_JSON_STEP_ROOT)
