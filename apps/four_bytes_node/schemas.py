#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/27 16:39
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:
from typing import Literal
from pydantic import BaseModel, conint, field_validator
from enum import Enum


# 枚举类
class ReportStatus(Enum):
    """
    四字节下探测器状态枚举类
    1: 无车 2: 有车 3: 故障
    """
    NO_CAR = 1
    HAS_CAR = 2
    FAULT = 3


# 数据模型
class ReportStatusModel(BaseModel):
    """上报探测器状态数据模型"""
    sensorAddr: conint(gt=0)
    sensorStatus: ReportStatus

    @field_validator("sensorStatus")
    @classmethod
    def transform_park_event(cls, v: ReportStatus):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value


class StartReportStatusModel(ReportStatusModel):
    """持续上报探测器状态数据模型"""
    reportInterval: conint(gt=0) = 10


if __name__ == '__main__':
    pass
