#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/27 16:39
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:

from pydantic import BaseModel


class CustomCommandData(BaseModel):
    """自定义指令数据体"""
    commandData: dict
    commandCode: str = "T"
