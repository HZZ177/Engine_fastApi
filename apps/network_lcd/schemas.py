#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/28 下午10:59
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:

from pydantic import BaseModel, conint, field_validator, ValidationInfo


# 数据模型
class GetHistoryCommandMessageModel(BaseModel):
    """查询LCD一体屏历史指令数据模型"""
    pageNo: conint(ge=0) = 1
    pageSize: conint(ge=0) = 10


if __name__ == '__main__':
    pass
