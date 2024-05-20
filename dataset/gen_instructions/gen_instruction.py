import argparse
from pathlib import Path

import cv2
import numpy as np
import yaml

from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
from openai import OpenAI


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Get OCR result for images directory")
    parser.add_argument("--image_dir", type=str, required=True, help="Images directory.")
    parser.add_argument("--ocr_output_dir", type=str, default="./ocr_output", help="OCR result output directory.")

    parser.add_argument(
        "--instruction_output_dir", type=str, default="./instructions", help="Instructions result output directory."
    )
    parser.add_argument("--data_yaml", type=str, default="../../configs/conversation_cfg.yaml", help="data setting file path")
    parser.add_argument("--api_yaml", type=str, default="../../configs/api_cfg.yaml", help="api setting file path")

    args = parser.parse_args()
    return args


def create_slices(image_path, slices_save_dir: Path):
    image = cv2.imread(image_path)
    height, width, _ = image.shape

    ratio_thres = 2  # 大于 2 倍就会需要进行切图
    wh_ratio = max(width / height, height / width)
    if wh_ratio < ratio_thres:
        return [image_path]

    if height > width:
        direction = "vertical"
        max_side = height
        step = width
    else:
        direction = "horizontal"
        step = height
        max_side = width

    slices = []

    # TODO 滑动窗口重合度0.1
    for i in range(0, max_side, step):

        if i + step > max_side:
            # 最后一张如果超过了单次切割的步长，将当前切片与上一个切片合并
            if direction == "vertical":
                # 垂直
                slices[-1]["img"] = np.concatenate((slices[-1]["img"], image[i:height, :]), axis=0)
            else:
                # 水平
                slices[-1]["img"] = np.concatenate((slices[-1]["img"], image[:, i:width]), axis=1)
            break

        if direction == "vertical":
            # 垂直切
            top_left = [0, i]
            slice = image[i : i + step, :]
        else:
            # 水平切
            top_left = [i, 0]
            slice = image[:, i : i + step, :]

        # 图片像素点，左上角 [x, y]
        slices.append({"img": slice, "top_left": top_left})

    slice_path_list = []
    # 保存图片，变为
    for idx, slice in enumerate(slices):
        slice_path = f"{slices_save_dir / str(idx)}.png"
        cv2.imwrite(str(slice_path), slice["img"])
        slice_path_list.append({"img": slice_path, "top_left": slice["top_left"]})

    return slice_path_list


def ocr_pred(ocr_model, image_path: Path, output_dir: Path, show_res=False):

    work_dir = output_dir.joinpath("work_dir", image_path.stem)
    work_dir.mkdir(parents=True, exist_ok=True)

    show_dir = output_dir.joinpath("work_dir", image_path.stem + "_show")

    # 如果太大了，进行切图
    # 创建横切图
    iamge_slices = create_slices(str(image_path), work_dir)

    result = []
    for img_info in iamge_slices:

        img_path = img_info["img"]

        # 推理
        ocr_res = ocr_model.ocr(img_path, cls=True)[0]
        if ocr_res == None:
            continue

        # 根据左上角回归到原图坐标点
        # res = [ [文字框], [识别结果，置信度] ]
        # left_top = img_info["top_left"]
        # for res in ocr_res:
        #     for points in res[0]:
        #         points[0] += left_top[0]
        #         points[1] += left_top[1]
        #     result.append(res)

        result += ocr_res

        if not show_res:
            continue

        if not show_dir.exists():
            show_dir.mkdir(parents=True, exist_ok=True)

        # 显示结果
        image = Image.open(img_path).convert("RGB")
        boxes = [line[0] for line in ocr_res]
        txts = [line[1][0] for line in ocr_res]
        scores = [line[1][1] for line in ocr_res]
        im_show = draw_ocr(image, boxes, txts, scores, font_path="./fonts/simfang.ttf")
        im_show = Image.fromarray(im_show)
        im_show.save(str(show_dir.joinpath("result_" + Path(img_path).name)))

    # 删除过程文件
    # shutil.rmtree(work_dir)

    return result


def get_ocr_res(image_dir: str, output_dir: str, show_res=True):

    # 判断图片路径是否存在
    image_dir = Path(image_dir)
    if not image_dir.exists():
        raise FileNotFoundError(f"Cannot find image dir: {image_dir}")

    # 初始化模型
    ocr_model = PaddleOCR(use_angle_cls=True, lang="ch")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_path in Path(image_dir).iterdir():
        print(f"processing ocr result for {str(img_path)}")

        if img_path.suffix.lower() not in [".png", ".jpeg", ".jpg", ".bmp"]:
            continue

        result_list = ocr_pred(ocr_model, img_path, output_dir, show_res)

        # 将结果写入文件
        with open(output_dir.joinpath(img_path.stem + ".txt"), "w", encoding="utf-8") as f:
            for res in result_list:
                # res = [ [文字框], [识别结果，置信度] ]
                f.write(res[1][0])


def gen_instructions_according_ocr_res(ocr_txt_root, instruction_save_root, api_yaml_path, data_yaml_path):

    instruction_save_root = Path(instruction_save_root)
    instruction_save_root.mkdir(parents=True, exist_ok=True)

    # 读取 yaml 文件
    with open(api_yaml_path, "r", encoding="utf-8") as f:
        api_yaml = yaml.safe_load(f)

    client = OpenAI(
        api_key=api_yaml["kimi_api_key"],
        base_url="https://api.moonshot.cn/v1",
    )

    # 读取 yaml 文件
    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)

    for txt_path in Path(ocr_txt_root).iterdir():

        print("Processing txt: ", txt_path.name)

        if txt_path.suffix not in [".txt"]:
            continue

        file_object = client.files.create(file=txt_path, purpose="file-extract")

        # 获取结果
        # file_content = client.files.retrieve_content(file_id=file_object.id)
        # 注意，之前 retrieve_content api 在最新版本标记了 warning, 可以用下面这行代替
        # 如果是旧版本，可以用 retrieve_content
        file_content = client.files.content(file_id=file_object.id).text

        # 把它放进请求中
        messages = [
            {
                "role": "system",
                "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
            },
            {
                "role": "system",
                "content": file_content,
            },
            {
                "role": "user",
                "content": data_yaml["instruction_generation_setting"]["dataset_gen_prompt"],
            },
        ]

        # 然后调用 chat-completion, 获取 Kimi 的回答
        completion = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=messages,
            temperature=0.3,
        )

        res_msg = completion.choices[0].message

        with open(instruction_save_root.joinpath(txt_path.stem + ".md"), "w", encoding="utf-8") as f:
            f.write(res_msg.content)


if __name__ == "__main__":
    args = parse_args()

    # 使用 OCR 对图片文字进行识别
    get_ocr_res(args.image_dir, args.ocr_output_dir)

    # 调用 kimi API 进行总结
    gen_instructions_according_ocr_res(args.ocr_output_dir, args.instruction_output_dir, args.api_yaml, args.data_yaml)

    print("All done !")
