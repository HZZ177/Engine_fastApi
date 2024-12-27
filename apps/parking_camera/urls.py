#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:28
# @Author  : Heshouyi
# @File    : parking_camera_api.py
# @Software: PyCharm
# @description:
import json
from functools import wraps
from enum import Enum
from fastapi import APIRouter
from core.device_manager import DeviceManager
from core.logger import logger
from core.util import get_inner_picture
from .services import ParkingCameraService

# 创建路由
parking_camera_router = APIRouter(tags=["车位相机相关接口"])


# 枚举类，维护各种数据类型对应值
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


# 公共工具函数和装饰器
def handle_exceptions(func):
    """通用异常处理装饰器"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"调用车位相机接口时系统异常: {e}")
            return error_response("系统异常", 500)

    return wrapper


def coming_record(message):
    """
    请求进入时统一记录请求参数
    :return:
    """
    return logger.info(f"{message}被调用，请求参数: {request.get_data(as_text=True)}")


def success_response(message="成功", data=None):
    """生成成功响应"""
    response_data = {"message": message, "data": data}
    return Response(
        json.dumps(response_data, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=200,
    )


def error_response(message="系统异常", code=500):
    """生成失败响应"""
    response_data = {"message": message}
    return Response(
        json.dumps(response_data, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=code,
    )


def validate_json(required_fields, request_data):
    """
    校验接口JSON必填参数
    :param required_fields: 必填参数列表
    :param request_data: 接口请求传入的数据
    :return:
    """
    missing_fields = [field for field in required_fields if field not in request_data]
    if missing_fields:
        return error_response(f"缺少必填参数: {', '.join(missing_fields)}", 400)
    return None


def validate_form_field(field_name, data, valid_values=None):
    """
    检查表单字段中的整数必填参数，可选校验范围，没有范围不校验
    :param field_name: 要校验的表单字段名称（字符串类型）
    :param data: 表单数据，一般通过request.form获取，类型为dict
    :param valid_values: 可选的字段取值范围（列表或其他可迭代对象）如果不为None，字段值必须在这个范围内
    :return:
    """
    try:
        value = int(data.get(field_name))
    except (TypeError, ValueError):
        return error_response(f"缺少必填参数: {field_name}或参数不是有效的整数", 400)
    if valid_values and value not in valid_values:
        return error_response(
            f"错误的参数值: {field_name}={value}，有效范围: {valid_values}", 400
        )
    return value


def get_parking_camera():
    """获取车位相机设备实例"""
    service: ParkingCameraService = DeviceManager.get_parking_camera_service()
    return service


# 核心 API 路由
@parking_camera_router.get("/connect", summary="连接设备到服务器")
@handle_exceptions
def connect():
    """
    尝试连接设备到服务器
    连接后发送注册包并开启心跳
    :return:
    """
    logger.info("车位相机connect接口被调用")
    parking_camera = get_parking_camera()
    parking_camera.connect()
    logger.info("车位相机成功连接服务器")
    return success_response()


@parking_camera_router.get("/disconnect")
@handle_exceptions
def disconnect():
    """
    断开服务器连接并停止心跳
    :return:
    """
    logger.info("车位相机disconnect接口被调用")
    parking_camera = get_parking_camera()
    parking_camera.disconnect()
    logger.info("车位相机成功断开连接")
    return success_response()


@parking_camera_router.get("/startHeartbeat")
@handle_exceptions
def start_heartbeat():
    """
    开启持续心跳
    :return:
    """
    logger.info("车位相机startHeartbeat接口被调用")
    parking_camera = get_parking_camera()
    parking_camera.start_heartbeat()
    logger.info("车位相机成功开启心跳")
    return success_response()


@parking_camera_router.get("/stopHeartbeat")
@handle_exceptions
def stop_heartbeat():
    """
    停止心跳
    :return:
    """
    logger.info("车位相机stopHeartbeat接口被调用")
    parking_camera = get_parking_camera()
    parking_camera.stop_heartbeat()
    logger.info("车位相机成功停止心跳")
    return success_response()


@parking_camera_router.post("/parkingStatusReport")
@handle_exceptions
def parking_status_report():
    """
    上报单个车位状态（事件）
    必填参数：
    port (int): 车位号——范围1-6
    parkEvent (int): 车位状态——0：无车；1：有车；2：出车；3：进车；4：设备故障；5：压线告警：6：压线取消
    """
    coming_record("车位相机parkingStatusReport接口")
    # 校验必填参数
    data = request.get_json()
    validation_error = validate_json(["port", "parkEvent"], data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    park_num = data["port"]
    park_event = data["parkEvent"]

    if park_num not in range(1, 7):  # 车位号范围1-6
        return error_response(f"错误的车位号: {park_num}，范围应为1-6", 400)
    if park_event not in (item.value for item in ParkingEvent):
        return error_response(f"错误的事件类型: {park_event}，范围应为0-6", 400)

    parking_camera = get_parking_camera()  # 获取设备实例
    parking_camera.send_parking_status(park_num, park_event)  # 上报车位状态
    logger.info(f"车位相机上报车位状态成功，车位号: {park_num}, 车位状态: {park_event}")
    return success_response()


@parking_camera_router.post("/startParkingStatusReport")
@handle_exceptions
def start_parking_status_report():
    """
    开启持续上报车位状态
    必填参数：
    port (int): 车位号——范围1-6
    parkEvent (int): 车位状态——0：无车；1：有车；
    :return:
    """
    coming_record("车位相机startParkingStatusReport接口")
    # 校验必填参数
    data = request.get_json()
    validation_error = validate_json(["port", "parkEvent"], data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    park_num = data["port"]
    park_event = data["parkEvent"]

    if park_num not in range(1, 7):  # 车位号范围1-6
        return error_response(f"错误的车位号: {park_num}，范围应为1-6", 400)
    if park_event not in [0, 1]:
        return error_response(f"错误的事件类型: {park_event}，应该为0或1", 400)

    parking_camera = get_parking_camera()  # 获取设备实例
    parking_camera.start_parking_status_report(park_num, park_event)  # 上报车位状态
    logger.info(f"车位相机上报车位状态成功，车位号: {park_num}, 车位状态: {park_event}")
    return success_response()


@parking_camera_router.get("/stopParkingStatusReport")
@handle_exceptions
def stop_parking_status_report():
    """停止持续上报车位状态"""
    logger.info("车位相机stopParkingStatusReport接口被调用")
    parking_camera = get_parking_camera()
    parking_camera.stop_reporting_parking_status()
    return success_response()


@parking_camera_router.post("/uploadParkingPicture")
@handle_exceptions
def upload_parking_picture():
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
    logger.info(f"车位相机uploadParkingPicture接口被调用")
    # 校验必填参数；因为涉及文件上传，需要使用表单类型提交，所以用form获取，另起一个检验方法
    park_num = validate_form_field("parkNum", request.form, valid_values=range(1, 7))
    if isinstance(park_num, tuple):  # 校验不通过会返回flask的错误对象，直接返回错误信息
        return park_num
    model = validate_form_field("model", request.form, valid_values=[1, 2])
    if isinstance(model, tuple):
        return model

    # 校验image和innerPic至少存在一个
    image = request.files.get("image")  # 上传的图片文件
    inner_pic = request.form.get("innerPic")  # 内置图片名称
    if not image and not inner_pic:
        return error_response("image或innerPic至少需要填一个", 400)

    # 尝试获取三个选填参数
    plate_color = int(request.form.get("plateColor"))
    plate_number = str(request.form.get("plateNumber"))
    confidence = int(request.form.get("confidence"))

    # 当模式为硬识别时，三个参数必填
    if model == 1:
        if any(i is None for i in [plate_color, plate_number, confidence]):
            return error_response(
                "模式为硬识别时，plateColor、plateNumber和confidence三个参数必填", 400
            )

    # 获取图片数据
    if inner_pic:  # 如果有内置图片，尝试获取，忽略自定义上传图片参数
        image_bytes = get_inner_picture(inner_pic)
        if image_bytes is None:
            return error_response(f"无法找到内置图片: {inner_pic}", 400)
    else:
        image_bytes = image.read()  # 如果没有指定内置图片，将上传的文件转换为二进制数据

    parking_camera = get_parking_camera()  # 获取设备实例
    parking_camera.upload_picture(
        park_num, image_bytes, model, plate_color, plate_number, confidence
    )  # 上传图片
    logger.info(f"车位相机{park_num}号车位成功上报车位图片")
    return success_response()
