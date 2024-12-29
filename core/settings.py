#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/29 下午1:21
# @Author  : Heshouyi
# @File    : settings.py
# @Software: PyCharm
# @description:

from core.file_path import db_path
print(db_path)

# 注册的模型
INSTALLED_MODELS = [
    "apps.network_led.models"
]

# tortoise基本配置
TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite:///{db_path}"
    },
    # 迁移模型应用配置，后必须添加aerich.models，是serich默认配置
    "apps": {
        "models": {
            "models": [*INSTALLED_MODELS, "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai"
}
