#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   user_db.py
@Time    :   2024/08/31
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Author  :   HinGwenWong
@Version :   1.0
@Desc    :   用户信息数据库操作
'''


# TODO 假数据库，后续删除！
fake_users_db = {
    "hingwen.wong": {
        "username": "hingwen.wong",
        "user_id": 1,
        "ip_address": "127.0.0.1",
        "email": "peterhuang0323@qq.com",
        "hashed_password": "$2b$12$zXXveodjipHZMoSxJz5ODul7Z9YeRJd0GeSBjpwHdqEtBbAFvEdre",
        "avatar": "https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png",
        "disabled": False,
    }
}


async def get_user_info(id: int):

    for username, user_info in fake_users_db.items():
        if user_info["user_id"] == id:
            return fake_users_db[username]

    return None
