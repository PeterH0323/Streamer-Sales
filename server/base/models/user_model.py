#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   user_model.py
@Time    :   2024/08/31
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   用户信息数据结构
"""

from pydantic import BaseModel


class TokenItem(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    username: str
    user_id: int
    ip_adress: str = ""
    full_name: str = ""
    avater: str = ""
    email: str = ""
    hashed_password: str = ""
    disabled: bool = False
