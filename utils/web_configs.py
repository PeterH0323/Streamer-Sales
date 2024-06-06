from dataclasses import dataclass
import os


@dataclass
class WebConfigs:
    """
    项目所有的配置
    """

    # ==================================================================
    #                               模型配置
    # ==================================================================
    LLM_MODEL_DIR: str = "HinGwenWoong/streamer-sales-lelemiao-7b"
    # LLM_MODEL_DIR = "HinGwenWoong/streamer-sales-lelemiao-7b-4bit"

    SALES_NAME: str = "乐乐喵"  # 启动的角色名

    # ==================================================================
    #                               组件配置
    # ==================================================================
    USING_LMDEPLOY: bool = True  # True 使用 LMDeploy 作为推理后端加速推理，False 使用原生 HF 进行推理用于初步验证模型
    ENABLE_RAG: bool = True  # True 启用 RAG 检索增强，False 不启用
    ENABLE_TTS: bool = True  # True 启动 tts，False 不启用
    ENABLE_DIGITAL_HUMAN: bool = True  # True 启动 数字人，False 不启用
    DISABLE_UPLOAD: bool = os.getenv("DISABLE_UPLOAD") == "true"

    CACHE_MAX_ENTRY_COUNT: float = 0.2  # KV cache 占比，如果部署出现 OOM 降低这个配置，反之可以加大

    # ==================================================================
    #                               页面配置
    # ==================================================================
    PRODUCT_IMAGE_HEIGHT: int = 400  # 商品图片高度
    EACH_CARD_OFFSET: int = 100  # 每个商品卡片比图片高度多出的距离
    EACH_ROW_COL: int = 2  # 商品页显示多少列

    # 定义用户和机器人头像路径
    USER_AVATOR = "./assets/user.png"
    ROBOT_AVATOR = "./assets/logo.png"

    # ==================================================================
    #                               商品配置
    # ==================================================================
    PRODUCT_INSTRUCTION_DIR: str = r"./product_info/instructions"
    PRODUCT_IMAGES_DIR: str = r"./product_info/images"

    PRODUCT_INFO_YAML_PATH = r"./product_info/product_info.yaml"
    PRODUCT_INFO_YAML_BACKUP_PATH = PRODUCT_INFO_YAML_PATH + ".bk"

    # ==================================================================
    #                             配置文件路径
    # ==================================================================
    CONVERSATION_CFG_YAML_PATH: str = r"./configs/conversation_cfg.yaml"

    # ==================================================================
    #                               RAG 配置
    # ==================================================================
    RAG_CONFIG_PATH: str = r"./configs/rag_config.yaml"
    RAG_VECTOR_DB_DIR: str = r"./work_dirs/instruction_db"
    PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP: str = r"./work_dirs/instructions_gen_db_tmp"

    # ==================================================================
    #                               TTS 配置
    # ==================================================================
    TTS_WAV_GEN_PATH: str = r"./work_dirs/tts_wavs"

    # ==================================================================
    #                             数字人 配置
    # ==================================================================
    DIGITAL_HUMAN_GEN_PATH: str = r"./work_dirs/digital_human"
    DIGITAL_HUMAN_MODEL_DIR: str = r"./work_dirs/digital_human_weights/"
    DIGITAL_HUMAN_BBOX_SHIFT: int = 0
    DIGITAL_HUMAN_VIDEO_PATH: str = r"/root/hingwen_camp/demos/ComfyUI/output/AnimateDiff_00015.mp4"
    DIGITAL_HUMAN_FPS: str = 25


# 实例化
WEB_CONFIGS = WebConfigs()
