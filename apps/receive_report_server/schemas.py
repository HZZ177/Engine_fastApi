#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/1/2 14:35
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:

from pydantic import BaseModel, conint


class GetHistoryReportModel(BaseModel):
    """获取历史上报数据模型"""
    page_no: conint(ge=1) = 1
    page_size: conint(ge=1) = 10
    source: conint(ge=1, le=2) = None
