#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:28
# @Author  : Heshouyi
# @File    : channel_camera_api.py
# @Software: PyCharm
# @description:
import json
import time
from functools import wraps
from enum import Enum
from fastapi import APIRouter
from core.logger import logger
from core.configer import config
from core.util import generate_uuid
from core.device_manager import DeviceManager
from .services import ChannelCameraService

# 创建路由
channel_camera_router = APIRouter(tags=["通道相机相关接口"])


# 从配置文件获取通道相机设备信息
device_id = config["devices_info"]["channel_camera"]["device_id"]
device_version = config["devices_info"]["channel_camera"]["device_version"]


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


# 工具函数和装饰器
def handle_exceptions(func):
    """通用异常处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"通道相机接口调用时系统异常: {e}")
            return {}
    return wrapper


def get_channel_camera():
    """获取通道相机设备实例"""
    service: ChannelCameraService = DeviceManager.get_channel_camera_service()
    return service


# API 路由
@channel_camera_router.get('/connect')
@handle_exceptions
def connect():
    """
    尝试连接设备到服务器
    连接后发送注册包并开启心跳
    :return:
    """
    logger.info("通道相机connect接口被调用")
    camera = get_channel_camera()
    camera.connect()
    logger.info("通道相机成功连接服务器")
    return {"success"}


@channel_camera_router.get('/disconnect')
@handle_exceptions
def disconnect():
    """
    断开服务器连接
    :return:
    """
    logger.info("通道相机disconnect接口被调用")
    camera = get_channel_camera()
    camera.disconnect()
    logger.info("通道相机成功断开连接")
    return {"success"}


@channel_camera_router.get('/startHeartbeat')
@handle_exceptions
def start_heartbeat():
    """
    开启持续心跳
    :return:
    """
    logger.info("通道相机startHeartbeat接口被调用")
    camera = get_channel_camera()
    camera.start_heartbeat()
    logger.info("通道相机成功开启心跳")
    return {"success"}


@channel_camera_router.get('/stopHeartbeat')
@handle_exceptions
def stop_heartbeat():
    """
    停止心跳
    :return:
    """
    logger.info("通道相机stopHeartbeat接口被调用")
    camera = get_channel_camera()
    camera.stop_heartbeat()
    logger.info("通道相机成功停止心跳")
    return {"success"}


@channel_camera_router.post('/sendCustomCommand')
@handle_exceptions
def send_custom_command():
    """
    工具方法，构造数据体向服务器上报指令，默认T包
    请求参数中需要自己提供发送的所有消息体部分

    必填参数：
        commandData (dict): 指令数据体，类型dict
    选填参数：
        commandCode (str): 指令类型，不传默认为T包
    :return:
    """
    # 检验必填参数
    data = request.get_json()
    validation_error = validate_json(["commandData"], data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    command_data = data["commandData"]
    command_code = data.get("commandCode", "T")

    camera = get_channel_camera()
    camera.send_command(command_data, command_code)
    logger.info(f"通道相机自定义指令成功发送指令: {command_data}")
    return {"success"}


@channel_camera_router.post('/alarmReport')
@handle_exceptions
def alarm_report():
    """
    告警上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体
    
    故障类型(分别顺序对应必填参数内的值)：
    视频故障/算法未正常运行/图片编码失败/连接图片服务器失败/网络故障

    必填参数：
        message (str): 故障类型：videoFault/algNotWork/jpgEncodeFault/ossNetFault/NetFault
    选填参数：
        moreInfo (str)：更多详细信息
    :return:
    """
    # 检验必填参数
    data = request.get_json()
    validation_error = validate_json(["message"], data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    message = data["message"]
    more_info = data.get("moreInfo", "")

    if message not in (item.value for item in CameraFaultType):
        return error_response(f"未知的告警类型: {message}", 400)

    # 组装上报数据
    content = {
        "cmd": "faultMessage",
        "cmdTime": str(int(time.time())),
        "deviceType": "5",
        "deviceId": device_id,
        "message": message,
        "moreInfo": more_info
    }

    camera = get_channel_camera()
    camera.send_command(content, "T")
    logger.info(f"通道相机成功上报告警: {message}")
    return {"success"}


@channel_camera_router.post('/alarmRecoveryReport')
@handle_exceptions
def alarm_recovery_report():
    """
    告警恢复上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体
    
    可恢复故障类型(分别顺序对应必填参数内的值)：
    视频故障/算法未正常运行/图片编码失败/连接图片服务器失败/网络故障

    必填参数：
    message (str): 要恢复的故障类型：videoFault/algNotWork/jpgEncodeFault/ossNetFault/NetFault

    选填参数：
    moreInfo (str)：更多详细信息
    :return:
    """
    # 检验必填参数
    data = request.get_json()
    validation_error = validate_json(["message"], data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    message = data["message"]
    more_info = data.get("moreInfo", "")

    if message not in (item.value for item in CameraFaultType):
        return error_response(f"未知的告警类型: {message}", 400)

    # 组装上报数据
    content = {
        "cmd": "faultMessage",
        "cmdTime": str(int(time.time())),
        "deviceType": "5",
        "deviceId": device_id,
        "recovery": message,
        "moreInfo": more_info
    }

    camera = get_channel_camera()
    camera.send_command(content, "T")
    logger.info(f"通道相机成功上报告警恢复: {message}")
    return {"success"}


@channel_camera_router.post('/carTriggerEvent')
@handle_exceptions
def car_trigger_event():
    """
    相机来去车事件上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体
    
    触发事件：2：从下到上/去车；3：从上到下/来车

    必填参数：
        triggerFlag (int)：触发事件类型——2：去车；3：来车
        plate (str)：车牌号
        plateReliability (int)：车牌可信度
        carType (str)：车辆类型——小型车/大型车
        carColour (int)：车身颜色——0：无  1："白",  2："黑", 3："蓝", 4："黄", 5："绿"，6："红"
    :return:
    """
    # 检验必填参数
    required_fields = ["triggerFlag", "plate", "plateReliability", "carType", "carColour"]
    data = request.get_json()
    validation_error = validate_json(required_fields, data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    trigger_flag = data["triggerFlag"]  # 触发类型
    plate = data["plate"]               # 车牌号
    plate_reliability = data["plateReliability"]    # 车牌可信度
    car_type = data["carType"]          # 车辆类型
    car_colour = data["carColour"]      # 车身颜色

    if trigger_flag not in (item.value for item in CarTriggerFlag):
        return error_response(f"未知的车位事件类型: {trigger_flag}", 400)
    if plate_reliability not in range(0, 1001):     # 可信度范围0-1000
        return error_response(f"无效的可信度 {plate_reliability}，取值范围0-1000: ", 400)
    if car_type not in ["小型车", "大型车"]:      # 预留字段，暂时只有小型车/大型车
        return error_response(f"无效的车辆类型: {car_type}", 400)
    if car_colour not in (item.value for item in CarColour):
        return error_response(f"无效的车辆颜色: {car_colour}", 400)

    # 组装上报数据
    content = {
        "cmd": "reportInfo",
        "eventType": "trigerEvent",     # trigerEvent没写错，协议就是这个单词
        "eventId": generate_uuid(),
        "triggerFlag": trigger_flag,
        "cmdTime": str(int(time.time())),
        "deviceType": "5",
        "deviceId": device_id,
        "plate": plate,
        "plateReliability": plate_reliability,
        "carType": car_type,
        "carColour": car_colour
    }

    camera = get_channel_camera()
    camera.send_command(content, "T")
    logger.info(f"通道相机成功上报事件类型: {trigger_flag}")
    return {"success"}


@channel_camera_router.post('/carBackEvent')
@handle_exceptions
def car_back_event():
    """
    相机后退事件上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体
    
    触发类型：9：“/从上到下/来车”后车辆又后退；10: “/从下到上/去车”后车辆又后退

    必填参数：
        triggerFlag (int): 触发类型——9：来车后车辆又后退；10: 去车后车辆又后退
        plate (str)：车牌号
        plateReliability (int)：车牌可信度
        carType (str)：车辆类型；大型车/小型车
        carColour (int)：车身颜色——0：无  1："白",  2："黑", 3："蓝", 4："黄", 5："绿"，6："红"
    :return:
    """
    # 检验必填参数
    required_fields = ["triggerFlag", "plate", "plateReliability", "carType", "carColour"]
    data = request.get_json()
    validation_error = validate_json(required_fields, data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    trigger_flag = data["triggerFlag"]  # 触发类型
    plate = data["plate"]               # 车牌号
    plate_reliability = data["plateReliability"]    # 车牌可信度
    car_type = data["carType"]          # 车辆类型
    car_colour = data["carColour"]      # 车身颜色

    if trigger_flag not in (item.value for item in CarBackFlag):
        return error_response(f"未知的车位事件类型: {trigger_flag}", 400)
    if plate_reliability not in range(0, 1001):     # 可信度范围0-1000
        return error_response(f"无效的可信度 {plate_reliability}，取值范围0-1000: ", 400)
    if car_type not in ["小型车", "大型车"]:      # 预留字段，暂时只有小型车/大型车
        return error_response(f"无效的车辆类型: {car_type}", 400)
    if car_colour not in (item.value for item in CarColour):
        return error_response(f"无效的车辆颜色: {car_colour}", 400)

    # 组装上报数据
    content = {
        "cmd": "reportInfo",
        "eventType": "reverseEvent",
        "eventId": generate_uuid(),
        "triggerFlag": trigger_flag,
        "cmdTime": str(int(time.time())),
        "deviceType": "5",
        "deviceId": device_id,
        "plate": plate,
        "plateReliability": plate_reliability,
        "carType": car_type,
        "carColour": car_colour
    }

    camera = get_channel_camera()
    camera.send_command(content, "T")
    logger.info(f"通道相机成功上报后退事件: {trigger_flag}")
    return {"success"}


@channel_camera_router.post('/carTrafficEvent')
@handle_exceptions
def car_traffic_event():
    """
    相机交通流量状态上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体

    区域状态——0：正常；1：繁忙；2：拥堵

    必填参数：
        areaState (int)： 区域状态， 0：正常；1：繁忙；2：拥堵
        area_state_reliability (int)： 区域状态可信度
        car_num (int)： 车辆数量
    :return:
    """
    # 检验必填参数
    required_fields = ["areaState", "areaStateReliability", "carNum"]
    data = request.get_json()
    validation_error = validate_json(required_fields, data)
    if validation_error:
        return validation_error

    # 校验参数合法性
    area_state = data["areaState"]
    area_state_reliability = data["areaStateReliability"]
    car_num = data["carNum"]

    if area_state not in (item.value for item in AreaState):
        return error_response(f"未知的区域状态: {data['areaState']}", 400)
    if area_state_reliability not in range(0, 1001):
        return error_response(f"无效的区域状态可信度 {area_state_reliability}，取值范围0-1000: ", 400)

    # 组装上报数据
    content = {
        "cmd": "reportInfo",
        "eventType": "trafficEvent",
        "cmdTime": str(int(time.time())),
        "deviceType": "5",
        "deviceId": device_id,
        "areaState": area_state,
        "areaStateReliability": area_state_reliability,
        "carNum": car_num
    }

    camera = get_channel_camera()
    camera.send_command(content, "T")
    logger.info(f"通道相机成功上报交通流量状态: {data['areaState']}")
    return {"success"}
