#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/28 下午10:59
# @Author  : Heshouyi
# @File    : schemas.py
# @Software: PyCharm
# @description:
from typing import Optional

from pydantic import BaseModel, conint, field_validator
from fastapi import Form, File, UploadFile
from enum import Enum


# 枚举类
class ParkingEvent(Enum):
    """
    车位状态枚举值
    0：无车；1：有车；2：出车；3：进车；4：设备故障；5：压线告警：6：压线取消
    """
    NO_CAR = 0
    HAS_CAR = 1
    CAR_OUT = 2
    CAR_IN = 3
    FAULT = 4
    PRESSURE = 5
    PRESSURE_CANCEL = 6


# 数据模型
class ParkingStatusReportModel(BaseModel):
    """车位相机状态上报数据模型"""
    port: conint(ge=1, le=6)
    parkEvent: ParkingEvent

    @field_validator("parkEvent")
    @classmethod
    def transform_park_event(cls, v: ParkingEvent):
        """转换字段成员对象为真实值，方便后续使用"""
        return v.value


class StartParkingStatusReportModel(ParkingStatusReportModel):
    """开启车位相机状态持续上报数据模型"""
    ...


class UploadParkingPictureModel(BaseModel):
    """
    上传车位图片数据模型
    该模型处理的字段都来自于表单提交，使用Form()来获取
    """
    parkNum: conint(ge=1, le=6) = Form(..., description="车位号，范围1-6")
    model: conint(ge=1, le=2) = Form(..., description="识别模式：1（硬识别），2（软识别）")
    image: Optional[UploadFile] = File(None, description="车牌图片文件，base64编码")
    innerPic: Optional[str] = Form(None, description="内置图片名称")
    plateColor: Optional[conint(ge=1, le=5)] = Form(None, description="车牌颜色：1:白 2:黑 3:蓝 4:黄 5:绿")
    plateNumber: Optional[str] = Form(None, description="车牌号")
    confidence: Optional[conint(ge=0, le=1000)] = Form(None, description="识别可信度，范围0-1000")


if __name__ == '__main__':
    data = UploadParkingPictureModel(parkNum=1, model=2, image=None, innerPic="test.jpg", plateColor=1,
                                     plateNumber="粤B88888", confidence=1000)
    print(data.model)
