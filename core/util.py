#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/11 17:39
# @Author  : Heshouyi
# @File    : util.py
# @Software: PyCharm
# @description:

import re
import uuid
from .file_path import static_path
from .logger import logger


def is_valid_ip(ip):
    """验证IPv4地址格式"""
    ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    return bool(ip_pattern.match(ip))


def get_inner_picture(inner_pic_name):
    """获取引擎内置图片，以字节形式返回"""
    inner_pic_path = f"{static_path}/{inner_pic_name}.jpg"
    try:
        with open(inner_pic_path, "rb") as f:
            return f.read()  # 返回图片的二进制数据
    except FileNotFoundError:
        logger.error(f"内置图片文件未找到: {inner_pic_path}")
        return None


def generate_uuid():
    """生成UUID"""
    return str(uuid.uuid4())
