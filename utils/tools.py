"""处理函数"""

import cv2
import torch

from utils.rag.retriever import CacheRetriever

# 基础配置
CONTEXT_MAX_LENGTH = 3000  # 上下文最大长度
GENERATE_TEMPLATE = "这是说明书：“{}”\n 客户的问题：“{}” \n 请阅读说明并运用你的性格进行解答。"  # RAG prompt 模板


def build_rag_prompt(rag_retriever: CacheRetriever, product_name, prompt):
    
    real_retriever = rag_retriever.get(fs_id="default")
    chunk, db_context, references = real_retriever.query(
        f"商品名：{product_name}。{prompt}", context_max_length=CONTEXT_MAX_LENGTH - 2 * len(GENERATE_TEMPLATE)
    )
    print(f"db_context = {db_context}")

    if db_context is not None and len(db_context) > 1:
        prompt_rag = GENERATE_TEMPLATE.format(db_context, prompt)
    else:
        print("db_context get error")
        prompt_rag = prompt

    print(f"RAG reference = {references}")
    print("=" * 20)

    return prompt_rag


def init_rag_retriever(rag_config: str, db_path: str):
    torch.cuda.empty_cache()

    retriever = CacheRetriever(config_path=rag_config)

    # 初始化
    retriever.get(fs_id="default", config_path=rag_config, work_dir=db_path)

    return retriever


def resize_image(image_path, max_height):
    """
    缩放图像，保持纵横比，将图像的高度调整为指定的最大高度。

    参数:
    - image_path: 图像文件的路径。
    - max_height: 指定的最大高度值。

    返回:
    - resized_image: 缩放后的图像。
    """

    # 读取图片
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # 计算新的宽度，保持纵横比
    new_width = int(width * max_height / height)

    # 缩放图片
    resized_image = cv2.resize(image, (new_width, max_height))

    return resized_image
