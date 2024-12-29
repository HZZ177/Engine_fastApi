#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/27 16:39
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:

from typing import List
from pydantic import BaseModel, conint, field_validator, ValidationInfo
from enum import Enum


# 枚举类
class SensorStatus(Enum):
    """
    车位状态枚举值
        1: 有车正常 2: 无车正常 3: 有车故障 4: 无车故障
    """
    HAS_CAR_NORMAL = 1
    NO_CAR_NORMAL = 2
    HAS_CAR_FAULT = 3
    NO_CAR_FAULT = 4


class FaultDetails(Enum):
    """
    故障详情枚举值：
        1: 传感器故障 2: 传感器满偏 3: 雷达故障 4: 高低温预警
        5: RTC故障 6: 通讯故障 7: 电池低压
    """
    SENSOR_FAULT = 1
    SENSOR_FULL_DEVIATION = 2
    RADAR_FAULT = 3
    TEMPERATURE_WARNING = 4
    RTC_FAULT = 5
    COMMUNICATION_FAULT = 6
    BATTERY_LOW_VOLTAGE = 7


# 数据模型
class ReportStatusModel(BaseModel):
    """上报探测器状态数据模型"""
    sensorAddr: conint(gt=0)
    sensorStatus: SensorStatus
    faultDetails: List[FaultDetails] = []

    @field_validator("sensorStatus")
    @classmethod
    def transform_sensor_status(cls, v: SensorStatus):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value

    @field_validator("faultDetails", mode="after")
    @classmethod
    def validate_fault_details(cls, field_data, values: ValidationInfo):
        """
        faultDetails字段校验特殊规则
        当车位状态为无故障的枚举时，不管参数传的什么，直接清空异常详情为[]
        当车位状态为有车故障或无车故障的枚举时，faultDetails不能为空
        最后都返回 List[int] 的形式方便后续调用

        field_data: faultDetails字段的值
        values: 所有字段的值
        """
        # 先将faultDetails的值从List[FaultDetails]转换为list[int]
        field_data = [fault_detail.value for fault_detail in field_data]
        # 校验faultDetails的值范围
        for value in field_data:
            if value not in range(1, 8):
                raise ValueError('faultDetails字段的值必须在1到7之间')

        # 检查sensorStatus是否为3或4时，faultDetails不能为空
        sensor_status = values.data["sensorStatus"]
        if sensor_status in [1, 2]:     # 有车正常或无车正常时直接清空异常列表
            field_data = []
        if sensor_status in [3, 4] and not field_data:
            raise ValueError('sensorStatus为3或4时，faultDetails字段不能为空')

        return field_data


class StartReportingModel(ReportStatusModel):
    """探测器状态持续上报数据模型"""
    reportInterval: conint(gt=0) = 10


if __name__ == '__main__':
    data = ReportStatusModel(sensorAddr=1, sensorStatus=2, faultDetails=[1, 4])
    print(data.sensorAddr, data.sensorStatus, data.faultDetails)
