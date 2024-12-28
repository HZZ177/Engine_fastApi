#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/27 16:39
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:
from typing import Literal

from pydantic import BaseModel, conint
from enum import Enum


# 枚举类，维护各种数据类型对应值
class EnumBase(Enum):
    """对枚举类统一处理返回值，默认返回其 value 而不是枚举成员"""
    def __str__(self):
        return self.value


class CarTriggerFlag(EnumBase):
    """
    相机触发事件枚举值
    2-去车
    3-来车
    """
    TO_CAR = 2
    FROM_CAR = 3


class CarBackFlag(EnumBase):
    """
    相机后退事件枚举值
    9-来车后车辆又后退
    9-去车后车辆又后退
    """
    BACK_FROM_CAR = 9
    BACK_TO_CAR = 10


class CarColour(EnumBase):
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


class AreaState(EnumBase):
    """
    区域交通流量状态枚举值
    0：正常；1：繁忙；2：拥堵
    """
    NORMAL = 0
    BUSY = 1
    JAM = 2


class CameraFaultType(EnumBase):
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


class AlarmRecoveryReportModel(BaseModel):
    """报警恢复上报数据模型"""
    message: CameraFaultType
    moreInfo: str = ""


class CarTriggerEventModel(BaseModel):
    """相机触发事件数据模型"""
    triggerFlag: CarTriggerFlag
    plate: str
    plateReliability: conint(ge=0, le=1000)
    carType: Literal["小型车", "大型车"]
    carColour: CarColour


class CarBackEventModel(BaseModel):
    """相机后退事件数据模型"""
    triggerFlag: CarBackFlag
    plate: str
    plateReliability: conint(ge=0, le=1000)
    carType: Literal["小型车", "大型车"]
    carColour: CarColour


class CarTrafficEventModel(BaseModel):
    """相机流量事件数据模型"""
    areaState: AreaState
    area_state_reliability: conint(ge=0, le=1000)
    car_num: int


if __name__ == '__main__':
    data = AlarmRecoveryReportModel(message="videoFault1")
    print(data.message)
