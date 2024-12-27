#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/21 下午10:29
# @Author  : Heshouyi
# @File    : four_bytes_node_api.py
# @Software: PyCharm
# @description:
import json
from functools import wraps
from fastapi import APIRouter
from core.logger import logger
from core.device_manager import DeviceManager
from .services import FourBytesNodeService

# 创建路由
four_bytes_node_router = APIRouter()


# 工具函数和装饰器
def handle_exceptions(func):
    """通用异常处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"四字节网络节点接口调用时系统异常: {e}")
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


def get_four_bytes_node():
    """获取四字节网络节点设备实例"""
    service: FourBytesNodeService = DeviceManager.get_four_bytes_node_service()
    return service


# API 路由
@four_bytes_node_router.get('/connect')
@handle_exceptions
def connect():
    """
    尝试连接设备到服务器
    :return:
    """
    logger.info("四字节网络节点connect接口被调用")
    four_bytes_node = get_four_bytes_node()
    four_bytes_node.connect()
    logger.info("四字节网络节点成功连接服务器")
    return success_response()


@four_bytes_node_router.get('/disconnect')
@handle_exceptions
def disconnect():
    """
    断开服务器连接
    :return:
    """
    logger.info("四字节网络节点disconnect接口被调用")
    four_bytes_node = get_four_bytes_node()
    four_bytes_node.disconnect()
    logger.info("四字节网络节点成功断开连接")
    return success_response()


@four_bytes_node_router.post('/reportStatus')
@handle_exceptions
def report_status():
    """
    上报节点下探测器状态，1: 无车 2: 有车 3: 故障
    必填参数：
        sensorAddr (int): 探测器地址
        sensorStatus (int): 车位状态
    车位状态枚举值：
        1: 无车 2: 有车 3: 故障

    :return:
    """
    coming_record("四字节网络节点reportStatus接口")
    try:
        data = request.json
        sensor_addr = data.get("sensorAddr")
        sensor_status = data.get("sensorStatus")

        # 参数校验
        if not isinstance(sensor_addr, int) or sensor_addr <= 0:
            return error_response(f"无效的车位地址{sensor_addr}", 400)

        if not isinstance(sensor_status, int) or sensor_status not in [1, 2, 3]:
            return error_response(f"无效的探测器状态: {sensor_status}", 400)

        four_bytes_node = get_four_bytes_node()
        # sensor_status-1是为了跟其他设备习惯同一，参数用1/2/3，实际对应协议0/1/2
        four_bytes_node.report_status(sensor_addr, sensor_status - 1)
        return success_response(data="上报成功")
    except Exception:
        return error_response()


@four_bytes_node_router.post('/startReporting')
@handle_exceptions
def start_reporting():
    """
    开启持续上报，同时需提供持续上报的状态 1: 无车 2: 有车 3: 故障
    必填参数：
        sensorAddr (int): 探测器地址
        sensorStatus (int): 车位状态
    选填参数：
        reportInterval (int): 上报间隔时间，不传的话默认10s/次
    车位状态枚举值：
        1: 无车 2: 有车 3: 故障
    :return:
    """
    coming_record("四字节网络节点startReporting接口")
    try:
        data = request.json
        sensor_addr = data.get("sensorAddr")
        sensor_status = data.get("sensorStatus")
        report_interval = data.get("reportInterval", 10)    # 上报的间隔时间，不传的话默认时间10s/次

        # 参数校验
        if not isinstance(sensor_addr, int) or sensor_addr <= 0:
            return error_response(f"无效的车位地址{sensor_addr}", 400)

        if not isinstance(sensor_status, int) or sensor_status not in [1, 2, 3]:
            return error_response(f"无效的探测器状态: {sensor_status}", 400)

        if report_interval is not None and not isinstance(report_interval, int):
            return error_response(f"无效的上报时间间隔: {report_interval}", 400)

        four_bytes_node = get_four_bytes_node()
        # sensor_status-1是为了跟其他设备习惯同一，参数用1/2/3，实际对应协议0/1/2
        four_bytes_node.start_reporting(sensor_addr, sensor_status - 1, report_interval)
        logger.info("四字节网络节点成功开启持续上报")
        return success_response(data="开启持续上报成功")
    except Exception:
        return error_response()


@four_bytes_node_router.get('/stopReporting')
@handle_exceptions
def stop_reporting():
    """
    停止持续上报
    :return:
    """
    logger.info("四字节网络节点stopReporting接口被调用")
    try:
        four_bytes_node = get_four_bytes_node()
        four_bytes_node.stop_reporting()
        logger.info("四字节网络节点成功停止持续上报")
        return success_response(data="停止持续上报成功")
    except Exception:
        return error_response()
