import cv2
import streamlit as st


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


def show_video(video_path, autoplay=True, loop=False, muted=False):
    # 需要 fp25 才能显示
    # with open(video_path, "rb") as f_wav:
    #     video_bytes = f_wav.read()

    print(f"Show video: {video_path}")
    st.video(video_path, format="video/mp4", autoplay=autoplay, loop=loop, muted=muted)


def show_audio(tts_path):

    if tts_path is None:
        return

    with open(tts_path, "rb") as f_wav:
        audio_bytes = f_wav.read()
    st.audio(audio_bytes, format="audio/wav")


def combine_history(prompt, meta_instruction, history_msg=None, first_input_str=""):
    total_prompt = [{"role": "system", "content": meta_instruction}]

    if first_input_str != "":
        total_prompt.append({"role": "user", "content": first_input_str})

    if history_msg is not None:
        for message in history_msg:
            total_prompt.append({"role": message["role"], "content": message["content"]})

    total_prompt.append({"role": "user", "content": prompt})
    return total_prompt



SYMBOL_SPLITS = {
    "。",
    "？",
    "！",
    "……",
    ".",
    "?",
    "!",
    "~",
    "…",
}


def make_text_chunk(original_text, strat_index, max_len=5, max_try=5000):
    cut_string = original_text
    end_index = strat_index

    while True:
        if original_text[end_index] in SYMBOL_SPLITS:
            end_index += 1
            cut_string = original_text[strat_index:end_index]
            break
        else:
            end_index += 1

        if end_index >= len(original_text):
            # 文本太短，没找到
            return 0, ""

        if end_index > max_try:
            # 有问题
            raise ValueError("Reach max try")
    return end_index, cut_string
