#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/26 10:50
# @Author  : Heshouyi
# @File    : urls.py
# @Software: PyCharm
# @description:

from fastapi import APIRouter
from core.logger import logger
from core.device_manager import DeviceManager
from .schemas import ReportStatusModel, StartReportingModel
from .services import LoraNodeService
from core.util import handle_exceptions, return_success_response

# 创建路由
lora_router = APIRouter()


def get_lora_node():
    """获取通道相机设备实例"""
    service: LoraNodeService = DeviceManager.get_lora_node_service()
    return service


# API 路由
@lora_router.get('/connect', summary="连接服务器")
@handle_exceptions(model_name="Lora节点相关接口")
def connect():
    """尝试连接设备到服务器"""
    lora_node = get_lora_node()
    lora_node.connect()
    logger.info("Lora节点成功连接服务器")
    return return_success_response(message="成功连接服务器")


@lora_router.get('/disconnect', summary="断连服务器")
@handle_exceptions(model_name="Lora节点相关接口")
def disconnect():
    """断开服务器连接"""
    lora_node = get_lora_node()
    lora_node.disconnect()
    logger.info("Lora节点成功断开连接")
    return return_success_response(message="成功断连")


@lora_router.post('/reportStatus', summary="上报探测器状态")
@handle_exceptions(model_name="Lora节点相关接口")
def report_status(data: ReportStatusModel):
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
    """
    sensor_addr = data.sensorAddr
    sensor_status = data.sensorStatus
    fault_details = data.faultDetails

    lora_node = get_lora_node()
    lora_node.report_status(sensor_addr, sensor_status, fault_details)
    return return_success_response(message="探测器状态上报成功")


@lora_router.post('/startReporting', summary="开启持续上报探测器状态")
@handle_exceptions(model_name="Lora节点相关接口")
def start_reporting(data: StartReportingModel):
    """
    开启持续上报探测器状态，同时需提供持续上报的状态
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
    """
    sensor_addr = data.sensorAddr
    sensor_status = data.sensorStatus
    fault_details = data.faultDetails
    report_interval = data.reportInterval

    lora_node = get_lora_node()
    lora_node.start_reporting(sensor_addr, sensor_status, fault_details, report_interval)
    logger.info("Lora节点成功开启持续上报")
    return return_success_response(message="开启持续上报成功")


@lora_router.get('/stopReporting', summary="停止持续上报探测器状态")
@handle_exceptions(model_name="Lora节点相关接口")
def stop_reporting():
    """停止持续上报探测器状态"""
    lora_node = get_lora_node()
    lora_node.stop_reporting()
    logger.info("Lora节点成功停止持续上报")
    return return_success_response(message="停止持续上报成功")
