#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   user_db.py
@Time    :   2024/08/31
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   用户信息数据库操作
"""

from sqlmodel import Session, select

from ...web_configs import API_CONFIG
from ..models.user_model import UserBaseInfo, UserInfo
from .init_db import DB_ENGINE


def get_db_user_info(id: int = -1, username: str = "", all_info: bool = False) -> UserBaseInfo | UserInfo | None:
    """查询数据库获取用户信息

    Args:
        id (int): 用户 ID
        username (str): 用户名
        all_info (bool): 是否返回含有密码串的敏感信息

    Returns:
        UserInfo | None: 用户信息，没有查到返回 None
    """

    if username == "":
        # 使用 ID 的方式进行查询
        query = select(UserInfo).where(UserInfo.user_id == id)
    else:
        query = select(UserInfo).where(UserInfo.username == username)

    # 查询数据库
    with Session(DB_ENGINE) as session:
        results = session.exec(query).first()

    # 返回服务器地址
    results.avatar = API_CONFIG.REQUEST_FILES_URL + results.avatar

    if results is not None and all_info is False:
        # 返回不含用户敏感信息的基本信息
        results = UserBaseInfo(**results.model_dump())

    return results
