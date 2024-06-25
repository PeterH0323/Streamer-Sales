import cv2


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
