#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/26 10:50
# @Author  : Heshouyi
# @File    : urls.py
# @Software: PyCharm
# @description:

from fastapi import APIRouter
from functools import wraps
from core.logger import logger
from core.device_manager import DeviceManager
from .services import LoraNodeService

# 创建路由
lora_router = APIRouter(tags=["Lora节点相关接口"])


# 工具函数和装饰器
def handle_exceptions(func):
    """通用异常处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Lora节点接口调用时系统异常: {e}")
            return error_response()
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
        status=200
    )


def error_response(message="系统异常", code=500):
    """生成失败响应"""
    response_data = {"message": message}
    return Response(
        json.dumps(response_data, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=code
    )


def validate_json(required_fields, request_data):
    """
    校验接口JSON传参的必填参数
    校验通过返回None
    校验失败返回错误信息，包含缺少的具体参数信息
    """
    missing_fields = [field for field in required_fields if field not in request_data]
    if missing_fields:
        return error_response(f"缺少必填参数: {','.join(missing_fields)}", 400)
    return None


def get_lora_node():
    """获取通道相机设备实例"""
    service: LoraNodeService = DeviceManager.get_lora_node_service()
    return service


# API 路由
@lora_router.get('/connect')
@handle_exceptions
def connect():
    """
    尝试连接设备到服务器
    :return:
    """
    logger.info("Lora节点connect接口被调用")
    lora_node = get_lora_node()
    lora_node.connect()
    logger.info("Lora节点成功连接服务器")
    return success_response()


@lora_router.get('/disconnect')
@handle_exceptions
def disconnect():
    """
    断开服务器连接
    :return:
    """
    logger.info("Lora节点disconnect接口被调用")
    lora_node = get_lora_node()
    lora_node.disconnect()
    logger.info("Lora节点成功断开连接")
    return success_response()


@lora_router.post('/reportStatus')
@handle_exceptions
def report_status():
    """
    上报节点下探测器状态，车位为故障时必须上报故障详情
    必填参数：
        sensorAddr (int): 探测器地址
        sensorStatus (int): 车位状态
        faultDetails (list[int]): 故障详情列表，每个元素为故障类型枚举值
    车位状态枚举值：
        1: 有车正常 2: 无车正常 3: 有车故障 4: 无车故障
    故障详情枚举值：
        1: 传感器故障 2: 传感器满偏 3: 雷达故障 4: 高低温预警
        5: RTC故障 6: 通讯故障 7: 电池低压
    :return:
    """
    coming_record("Lora节点reportStatus接口")
    data = request.json
    sensor_addr = data.get("sensorAddr")
    sensor_status = data.get("sensorStatus")
    fault_details = data.get("faultDetails")

    # 参数校验
    if not isinstance(sensor_addr, int) or sensor_addr <= 0:
        return error_response(f"无效的车位地址{sensor_addr}", 400)

    if not isinstance(sensor_status, int) or sensor_status not in [1, 2, 3, 4]:
        return error_response(f"无效的探测器状态{sensor_addr}", 400)

    if not isinstance(fault_details, list):
        return error_response(f"故障详情参数类型错误: {sensor_status}", 400)

    # 故障详情范围1-7
    if any(fault_detail not in [1, 2, 3, 4, 5, 6, 7] for fault_detail in fault_details):
        return error_response("故障详情中包含无效值，有效范围位1-7的整数", 400)

    # 上报为故障状态时，必须有故障详情
    if sensor_status in [3, 4]:
        if not fault_details:
            return error_response("上报车位为故障状态时，必须提供至少一个故障详情", 400)
    else:   # 如果车位状态为正常，强制将故障详情丢弃
        fault_details = []

    lora_node = get_lora_node()
    lora_node.report_status(sensor_addr, sensor_status, fault_details)
    return success_response(data="上报成功")


@lora_router.post('/startReporting')
@handle_exceptions
def start_reporting():
    """
    开启持续上报，同时需提供持续上报的状态
    必填参数：
        sensorAddr (int): 探测器地址
        sensorStatus (int): 车位状态
        faultDetails (list[int]): 故障详情列表，每个元素为故障类型枚举值
    选填参数：
        reportInterval (int): 上报时间间隔，不传默认10s/次
    车位状态枚举值：
        1: 有车正常 2: 无车正常 3: 有车故障 4: 无车故障
    故障详情枚举值：
        1: 传感器故障 2: 传感器满偏 3: 雷达故障 4: 高低温预警
        5: RTC故障 6: 通讯故障 7: 电池低压
    :return:
    """
    coming_record("Lora节点startReporting接口")
    data = request.json
    sensor_addr = data.get("sensorAddr")
    sensor_status = data.get("sensorStatus")
    fault_details = data.get("faultDetails")
    report_interval = data.get("reportInterval", 10)    # 上报的间隔时间，不传的话默认时间10s/次

    # 参数校验
    if not isinstance(sensor_addr, int) or sensor_addr <= 0:
        return error_response(f"无效的车位地址{sensor_addr}", 400)

    if not isinstance(sensor_status, int) or sensor_status not in [1, 2, 3, 4]:
        return error_response(f"无效的探测器状态: {sensor_status}", 400)
    if not isinstance(fault_details, list):
        return error_response(f"故障详情参数类型错误: {sensor_status}", 400)

    if report_interval is not None and not isinstance(report_interval, int):
        return error_response(f"无效的上报时间间隔: {sensor_status}", 400)
    # 故障详情范围1-7
    if any(fault_detail not in [1, 2, 3, 4, 5, 6, 7] for fault_detail in fault_details):
        return error_response(f"故障详情中包含无效值，有效范围位1-7的整数", 400)
    # 有故障状态时，必须有故障详情
    if sensor_status in [3, 4]:
        if not fault_details:
            return error_response("上报车位为故障状态时，必须提供至少一个故障详情", 400)
    else:   # 如果车位状态为正常，强制将故障详情丢弃
        fault_details = []

    lora_node = get_lora_node()
    lora_node.start_reporting(sensor_addr, sensor_status, fault_details, report_interval)
    logger.info("Lora节点成功开启持续上报")
    return success_response(data="开启持续上报成功")


@lora_router.get('/stopReporting')
@handle_exceptions
def stop_reporting():
    """
    停止持续上报
    :return:
    """
    logger.info("Lora节点stopReporting接口被调用")
    lora_node = get_lora_node()
    lora_node.stop_reporting()
    logger.info("Lora节点成功停止持续上报")
    return success_response(data="停止持续上报成功")
