#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   llm_model.py
@Time    :   2024/09/01
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   大模型对话数据结构
"""

from pydantic import BaseModel


class GenProductItem(BaseModel):
    gen_type: str
    instruction: str
