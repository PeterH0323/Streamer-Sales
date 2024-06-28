from torch import hub
from utils.web_configs import WEB_CONFIGS
from pathlib import Path

# 部分模型会使用 torch download 下载，需要设置路径
hub.set_dir(str(Path(WEB_CONFIGS.DIGITAL_HUMAN_MODEL_DIR).joinpath("face-alignment")))
