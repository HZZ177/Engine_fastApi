#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:28
# @Author  : Heshouyi
# @File    : parking_camera_api.py
# @Software: PyCharm
# @description:

from fastapi import APIRouter
from core.device_manager import DeviceManager
from core.logger import logger
from core.util import get_inner_picture
from .schemas import ParkingStatusReportModel, StartParkingStatusReportModel, UploadParkingPictureModel
from .services import ParkingCameraService
from core.util import return_success_response, handle_exceptions

# 创建路由
parking_camera_router = APIRouter()


def get_parking_camera():
    """获取车位相机设备实例"""
    service: ParkingCameraService = DeviceManager.get_parking_camera_service()
    return service


# 核心 API 路由
@parking_camera_router.get("/connect", summary="连接服务器")
@handle_exceptions(model_name="车位相机相关接口")
def connect():
    """
    尝试连接设备到服务器
    连接后发送注册包并开启心跳
    """
    parking_camera = get_parking_camera()
    parking_camera.connect()
    logger.info("车位相机成功连接服务器")
    return return_success_response(message="成功连接服务器")


@parking_camera_router.get("/disconnect", summary="断连服务器")
@handle_exceptions(model_name="车位相机相关接口")
def disconnect():
    """
    断开服务器连接并停止心跳
    :return:
    """
    parking_camera = get_parking_camera()
    parking_camera.disconnect()
    logger.info("车位相机成功断开连接")
    return return_success_response(message="成功断连服务器")


@parking_camera_router.get("/startHeartbeat", summary="开启心跳")
@handle_exceptions(model_name="车位相机相关接口")
def start_heartbeat():
    """
    开启持续心跳
    :return:
    """
    parking_camera = get_parking_camera()
    parking_camera.start_heartbeat()
    logger.info("车位相机成功开启心跳")
    return return_success_response(message="成功开启心跳")


@parking_camera_router.get("/stopHeartbeat", summary="停止心跳")
@handle_exceptions(model_name="车位相机相关接口")
def stop_heartbeat():
    """
    停止心跳
    :return:
    """
    parking_camera = get_parking_camera()
    parking_camera.stop_heartbeat()
    logger.info("车位相机成功停止心跳")
    return return_success_response(message="成功关闭心跳")


@parking_camera_router.post("/parkingStatusReport", summary="上报车位状态")
@handle_exceptions(model_name="车位相机相关接口")
def parking_status_report(data: ParkingStatusReportModel):
    """
    上报单个车位状态（事件）
    必填参数：
    port (int): 车位号——范围1-6
    parkEvent (int): 车位状态——0：无车；1：有车；2：出车；3：进车；4：设备故障；5：压线告警：6：压线取消
    """
    park_num = data.port
    park_event = data.parkEvent

    parking_camera = get_parking_camera()
    parking_camera.send_parking_status(park_num, park_event)
    logger.info(f"车位相机上报车位状态成功，车位号: {park_num}, 车位状态: {park_event}")
    return return_success_response(message=f"车位相机上报车位状态成功，车位号: {park_num}, 车位状态: {park_event}")


@parking_camera_router.post("/startParkingStatusReport", summary="开启车位状态持续上报")
@handle_exceptions(model_name="车位相机相关接口")
def start_parking_status_report(data: StartParkingStatusReportModel):
    """
    开启持续上报车位状态，间隔30s
    必填参数：
    port (int): 车位号——范围1-6
    parkEvent (int): 车位状态——0：无车；1：有车；
    """
    park_num = data.port
    park_event = data.parkEvent

    parking_camera = get_parking_camera()
    parking_camera.start_parking_status_report(park_num, park_event)
    logger.info(f"成功开启车位相机持续上报，车位号: {park_num}, 车位状态: {park_event}")
    return return_success_response(message=f"成功开启车位相机持续上报，车位号: {park_num}, 车位状态: {park_event}")


@parking_camera_router.get("/stopParkingStatusReport", summary="停止车位状态持续上报")
@handle_exceptions(model_name="车位相机相关接口")
def stop_parking_status_report():
    """停止持续上报车位状态"""
    parking_camera = get_parking_camera()
    parking_camera.stop_reporting_parking_status()
    return return_success_response(message="成功停止持续上报")


@parking_camera_router.post("/uploadParkingPicture", summary="上传车位图片")
@handle_exceptions(model_name="车位相机相关接口")
async def upload_parking_picture(data: UploadParkingPictureModel):
    """
    上报车位图片，目前只支持软识别模式
    必填参数：
        parkNum (int): 车位号
        model (int): 识别模式 1：硬识别 2：软识别
    以下两个必填其一：
        image (file): 车牌图片，base64编码
        innerPic (str): 内置图片名称
    当模式为1：硬识别时，以下参数必填：
        plateColor (int) = 车牌颜色 1：白；2：黑；3：蓝，4：黄，5：绿
        plateNumber (str) = 车牌号
        confidence (int) = 识别可信度 0-1000
    """
    park_num = data.parkNum
    model = data.model

    # 校验image和innerPic至少存在一个
    image = data.image  # 上传的图片文件
    inner_pic = data.innerPic  # 内置图片名称
    if not image and not inner_pic:
        return return_success_response(message="image或innerPic至少需要填一个")

    # 尝试获取三个选填参数
    plate_color = data.plateColor
    plate_number = data.plateNumber
    confidence = data.confidence

    # 当模式为硬识别时，三个参数必填
    if model == 1:
        if any(i is None for i in [plate_color, plate_number, confidence]):
            return return_success_response(message="模式为硬识别时，plateColor、plateNumber和confidence三个参数必填")

    # 获取图片数据
    if inner_pic:  # 如果有内置图片，尝试获取，忽略自定义上传图片参数
        image_bytes = get_inner_picture(inner_pic)
        if image_bytes is None:
            return return_success_response(message=f"无法找到内置图片: {inner_pic}")
    else:
        image_bytes = await image.read()  # 如果没有指定内置图片，将上传的文件转换为二进制数据

    parking_camera = get_parking_camera()
    parking_camera.upload_picture(park_num, image_bytes, model, plate_color, plate_number, confidence)
    logger.info(f"车位相机{park_num}号车位成功上报车位图片")
    return return_success_response(message=f"车位相机{park_num}号车位成功上报车位图片")
