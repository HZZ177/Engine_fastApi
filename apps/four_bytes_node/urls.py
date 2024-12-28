#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/21 下午10:29
# @Author  : Heshouyi
# @File    : four_bytes_node_api.py
# @Software: PyCharm
# @description:

from fastapi import APIRouter
from core.logger import logger
from core.device_manager import DeviceManager
from .schemas import ReportStatusModel, StartReportStatusModel
from .services import FourBytesNodeService
from core.util import handle_exceptions, return_success_response

# 创建路由
four_bytes_node_router = APIRouter()


def get_four_bytes_node():
    """获取四字节网络节点设备实例"""
    service: FourBytesNodeService = DeviceManager.get_four_bytes_node_service()
    return service


# API 路由
@four_bytes_node_router.get('/connect', summary="连接服务器")
@handle_exceptions(model_name="四字节TCP节点相关接口")
def connect():
    """尝试连接设备到服务器"""
    four_bytes_node = get_four_bytes_node()
    four_bytes_node.connect()
    logger.info("四字节网络节点成功连接服务器")
    return return_success_response(message="成功连接服务器")


@four_bytes_node_router.get('/disconnect', summary="断连服务器")
@handle_exceptions(model_name="四字节TCP节点相关接口")
def disconnect():
    """断开服务器连接"""
    four_bytes_node = get_four_bytes_node()
    four_bytes_node.disconnect()
    logger.info("四字节网络节点成功断开连接")
    return return_success_response(message="成功断连")


@four_bytes_node_router.post('/reportStatus', summary="上报四字节节点下探测器状态")
@handle_exceptions(model_name="四字节TCP节点相关接口")
def report_status(data: ReportStatusModel):
    """
    上报节点下探测器状态，1: 无车 2: 有车 3: 故障
    必填参数：
        sensorAddr (int): 探测器地址
        sensorStatus (int): 车位状态
    车位状态枚举值：
        1: 无车 2: 有车 3: 故障
    """
    sensor_addr = data.sensorAddr
    sensor_status = data.sensorStatus

    four_bytes_node = get_four_bytes_node()
    # sensor_status-1是为了跟其他设备习惯同一，参数用1/2/3，实际对应协议0/1/2
    four_bytes_node.report_status(sensor_addr, sensor_status - 1)
    return return_success_response(message="探测器状态成功上报")


@four_bytes_node_router.post('/startReporting', summary="持续上报探测器状态")
@handle_exceptions(model_name="四字节TCP节点相关接口")
def start_reporting(data: StartReportStatusModel):
    """
    开启持续上报，同时需提供持续上报的状态 1: 无车 2: 有车 3: 故障
    必填参数：
        sensorAddr (int): 探测器地址
        sensorStatus (int): 车位状态
    选填参数：
        reportInterval (int): 上报间隔时间，不传的话默认10s/次
    车位状态枚举值：
        1: 无车 2: 有车 3: 故障
    """
    sensor_addr = data.sensorAddr
    sensor_status = data.sensorStatus
    report_interval = data.reportInterval  # 上报的间隔时间，默认10s/次

    four_bytes_node = get_four_bytes_node()
    # sensor_status-1是为了跟其他设备习惯同一，参数用1/2/3，实际对应协议0/1/2
    four_bytes_node.start_reporting(sensor_addr, sensor_status - 1, report_interval)
    logger.info("四字节网络节点成功开启持续上报")
    return return_success_response(message="开启持续上报成功")


@four_bytes_node_router.get('/stopReporting', summary="停止探测器状态持续上报")
@handle_exceptions(model_name="四字节TCP节点相关接口")
def stop_reporting():
    """停止持续上报"""
    four_bytes_node = get_four_bytes_node()
    four_bytes_node.stop_reporting()
    logger.info("四字节网络节点成功停止持续上报")
    return return_success_response(message="停止持续上报成功")
