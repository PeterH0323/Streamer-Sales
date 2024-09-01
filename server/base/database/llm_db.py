#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   llm_db.py
@Time    :   2024/09/01
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   大模型对话数据库交互
"""

import yaml

from ...web_configs import WEB_CONFIGS


async def get_llm_product_prompt_base_info():
    # 加载对话配置文件
    with open(WEB_CONFIGS.CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    return dataset_yaml
