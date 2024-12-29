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


# 枚举类，维护各种数据类型对应值
class CarTriggerFlag(Enum):
    """
    相机触发事件枚举值
    2-去车
    3-来车
    """
    TO_CAR = 2
    FROM_CAR = 3


class CarBackFlag(Enum):
    """
    相机后退事件枚举值
    9-来车后车辆又后退
    9-去车后车辆又后退
    """
    BACK_FROM_CAR = 9
    BACK_TO_CAR = 10


class CarColour(Enum):
    """
    车牌颜色枚举值
    0：无  1："白",  2："黑", 3："蓝", 4："黄", 5："绿"，6："红"
    """
    NONE = 0
    WHITE = 1
    BLACK = 2
    BLUE = 3
    YELLOW = 4
    GREEN = 5
    RED = 6


class AreaState(Enum):
    """
    区域交通流量状态枚举值
    0：正常；1：繁忙；2：拥堵
    """
    NORMAL = 0
    BUSY = 1
    JAM = 2


class CameraFaultType(Enum):
    """
    相机故障类型枚举值
    videoFault：视频故障
    algNotWork：算法未正常运行
    jpgEncodeFault：图片编码失败
    ossNetFault：连接图片服务器oss失败
    NetFault：网络故障
    """
    VIDEO_FAULT = "videoFault"
    ALG_NOT_WORK = "algNotWork"
    JPG_ENCODE_FAULT = "jpgEncodeFault"
    OSS_NET_FAULT = "ossNetFault"
    NET_FAULT = "NetFault"


# pydantic模型类
class CustomCommandModel(BaseModel):
    """自定义指令数据模型"""
    commandData: dict
    commandCode: str = "T"


class AlarmReportModel(BaseModel):
    """报警上报数据模型"""
    message: CameraFaultType
    moreInfo: str = ""

    @field_validator("message")
    @classmethod
    def transform_message(cls, v: CameraFaultType):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value


class AlarmRecoveryReportModel(AlarmReportModel):
    """报警恢复上报数据模型"""
    ...


class CarTriggerEventModel(BaseModel):
    """相机触发事件数据模型"""
    triggerFlag: CarTriggerFlag
    plate: str
    plateReliability: conint(ge=0, le=1000)
    carType: Literal["小型车", "大型车"]
    carColour: CarColour

    @field_validator("triggerFlag")
    @classmethod
    def transform_trigger_flag(cls, v: CarTriggerFlag):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value

    @field_validator("carColour")
    @classmethod
    def transform_car_colour(cls, v: CarColour):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value


class CarBackEventModel(CarTriggerEventModel):
    """相机后退事件数据模型"""
    ...


class CarTrafficEventModel(BaseModel):
    """相机流量事件数据模型"""
    areaState: AreaState
    area_state_reliability: conint(ge=0, le=1000)
    car_num: int

    @field_validator("areaState")
    @classmethod
    def transform_area_state(cls, v: AreaState):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value


if __name__ == '__main__':
    data = AlarmRecoveryReportModel(message="videoFault")
    print(data.message.value)
