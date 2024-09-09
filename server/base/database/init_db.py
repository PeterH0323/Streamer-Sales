#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   init_db.py
@Time    :   2024/09/06
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   数据库初始化
"""

from loguru import logger
from pydantic import PostgresDsn
from pydantic_core import MultiHostUrl
from sqlmodel import SQLModel, create_engine

from ...web_configs import WEB_CONFIGS

ECHO_DB_MESG = True  # 数据库执行中是否回显，for debug


def sqlalchemy_db_url() -> PostgresDsn:
    """生成数据库 URL

    Returns:
        PostgresDsn: 数据库地址
    """
    return MultiHostUrl.build(
        scheme="postgresql+psycopg",
        username=WEB_CONFIGS.POSTGRES_USER,
        password=WEB_CONFIGS.POSTGRES_PASSWORD,
        host=WEB_CONFIGS.POSTGRES_SERVER,
        port=WEB_CONFIGS.POSTGRES_PORT,
        path=WEB_CONFIGS.POSTGRES_DB,
    )


logger.info(f"connecting to db: {str(sqlalchemy_db_url())}")
DB_ENGINE = create_engine(str(sqlalchemy_db_url()), echo=ECHO_DB_MESG)


def create_db_and_tables():
    """创建所有数据库和对应的表，有则跳过"""
    SQLModel.metadata.create_all(DB_ENGINE)
