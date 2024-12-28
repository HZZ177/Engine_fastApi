#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:28
# @Author  : Heshouyi
# @File    : channel_camera_api.py
# @Software: PyCharm
# @description:

import time
from fastapi import APIRouter
from core.logger import logger
from core.configer import config
from core.util import generate_uuid
from core.device_manager import DeviceManager
from .services import ChannelCameraService
from core.util import handle_exceptions
from .schemas import CustomCommandModel, AlarmReportModel, AlarmRecoveryReportModel, CarTriggerEventModel, \
    CarBackEventModel, CarTrafficEventModel

# 创建路由
channel_camera_router = APIRouter()

# 从配置文件获取通道相机设备信息
device_id = config["devices_info"]["channel_camera"]["device_id"]
device_version = config["devices_info"]["channel_camera"]["device_version"]


def get_channel_camera():
    """从设备管理层统一获取通道相机设备实例"""
    service: ChannelCameraService = DeviceManager.get_channel_camera_service()
    return service


# API 路由
@channel_camera_router.get('/connect', summary="连接到服务器")
@handle_exceptions(model_name="通道相机相关接口")
def connect():
    """
    尝试连接设备到服务器
    连接后发送注册包并开启心跳
    """
    camera = get_channel_camera()
    camera.connect()
    logger.info("通道相机成功连接服务器")
    return {"message": "成功连接服务器"}


@channel_camera_router.get('/disconnect', summary="断开连接")
@handle_exceptions(model_name="通道相机相关接口")
def disconnect():
    """断开服务器连接"""
    logger.info("通道相机disconnect接口被调用")
    camera = get_channel_camera()
    camera.disconnect()
    logger.info("通道相机成功断开连接")
    return {"message": "成功断连"}


@channel_camera_router.get('/startHeartbeat', summary="开启心跳")
@handle_exceptions(model_name="通道相机相关接口")
def start_heartbeat():
    """开启持续心跳"""
    logger.info("通道相机startHeartbeat接口被调用")
    camera = get_channel_camera()
    camera.start_heartbeat()
    logger.info("通道相机成功开启心跳")
    return {"message": "开启心跳成功"}


@channel_camera_router.get('/stopHeartbeat', summary="停止心跳")
@handle_exceptions(model_name="通道相机相关接口")
def stop_heartbeat():
    """停止心跳"""
    logger.info("通道相机stopHeartbeat接口被调用")
    camera = get_channel_camera()
    camera.stop_heartbeat()
    logger.info("通道相机成功停止心跳")
    return {"message": "停止心跳成功"}


@channel_camera_router.post('/sendCustomCommand', summary="自定义指令发送")
@handle_exceptions(model_name="通道相机相关接口")
def send_custom_command(data: CustomCommandModel):
    """
    工具方法，构造数据体向服务器上报指令，默认T包
    请求参数中需要自己提供发送的所有消息体部分
    """
    command_data = data.commandData
    command_code = data.commandCode
    camera = get_channel_camera()
    camera.send_command(command_data, command_code)
    logger.info(f"通道相机自定义指令成功发送指令: {command_data}")
    return {"message": "自定义指令发送成功"}


@channel_camera_router.post('/alarmReport', summary="告警上报")
@handle_exceptions(model_name="通道相机相关接口")
def alarm_report(data: AlarmReportModel):
    """
    告警上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体
    
    故障类型(分别顺序对应必填参数内的值)：
    视频故障/算法未正常运行/图片编码失败/连接图片服务器失败/网络故障

    必填参数：
        message (str): 故障类型：videoFault/algNotWork/jpgEncodeFault/ossNetFault/NetFault
    选填参数：
        moreInfo (str)：更多详细信息
    """
    message = data.message
    more_info = data.moreInfo

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
    return {"message": "告警上报成功"}


@channel_camera_router.post('/alarmRecoveryReport', summary="告警恢复上报")
@handle_exceptions(model_name="通道相机相关接口")
def alarm_recovery_report(data: AlarmRecoveryReportModel):
    """
    告警恢复上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体
    
    可恢复故障类型(分别顺序对应必填参数内的值)：
    视频故障/算法未正常运行/图片编码失败/连接图片服务器失败/网络故障

    必填参数：
    message (str): 要恢复的故障类型：videoFault/algNotWork/jpgEncodeFault/ossNetFault/NetFault

    选填参数：
    moreInfo (str)：更多详细信息
    """
    message = data.message
    more_info = data.moreInfo

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
    return {"message": "告警恢复上报成功"}


@channel_camera_router.post('/carTriggerEvent', summary="相机来去车事件上报")
@handle_exceptions(model_name="通道相机相关接口")
def car_trigger_event(data: CarTriggerEventModel):
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
    """
    trigger_flag = data.triggerFlag  # 触发类型
    plate = data.plate  # 车牌号
    plate_reliability = data.plateReliability  # 车牌可信度
    car_type = data.carType  # 车辆类型
    car_colour = data.carColour  # 车身颜色

    # 组装上报数据
    content = {
        "cmd": "reportInfo",
        "eventType": "trigerEvent",  # trigerEvent没写错，协议就是这个单词
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
    return {"message": "来去车事件上报成功"}


@channel_camera_router.post('/carBackEvent', summary="相机后退事件上报")
@handle_exceptions(model_name="通道相机相关接口")
def car_back_event(data: CarBackEventModel):
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
    """

    trigger_flag = data.triggerFlag  # 触发类型
    plate = data.plate  # 车牌号
    plate_reliability = data.plateReliability  # 车牌可信度
    car_type = data.carType  # 车辆类型
    car_colour = data.carColour  # 车身颜色

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
    return {"message": "相机后退事件上报成功"}


@channel_camera_router.post('/carTrafficEvent', summary="相机交通流量状态上报")
@handle_exceptions(model_name="通道相机相关接口")
def car_traffic_event(data: CarTrafficEventModel):
    """
    相机交通流量状态上报接口
    这几个上报事件接口用的是一个协议，只是协议体内的参数有区别，所以service公用一个工具方法，因此在api层直接构建参数体

    区域状态——0：正常；1：繁忙；2：拥堵

    必填参数：
        areaState (int)： 区域状态， 0：正常；1：繁忙；2：拥堵
        area_state_reliability (int)： 区域状态可信度
        car_num (int)： 车辆数量
    """
    area_state = data.areaState.value
    area_state_reliability = data.area_state_reliability
    car_num = data.car_num

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
    logger.info(f"通道相机成功上报交通流量状态: {data.areaState.value}")
    return {"message": "相机交通流量状态上报成功"}
