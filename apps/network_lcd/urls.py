#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/27 13:39
# @Author  : Heshouyi
# @File    : network_lcd_api.py
# @Software: PyCharm
# @description:

from fastapi import APIRouter
from core.logger import logger
from .schemas import GetHistoryCommandMessageModel
from .services import NetworkLcdService
from core.device_manager import DeviceManager
from core.util import handle_exceptions, return_success_response

# 创建路由
network_lcd_router = APIRouter()


def get_network_lcd():
    """获取LCD一体屏设备实例"""
    service: NetworkLcdService = DeviceManager.get_network_lcd_service()
    return service


# API 路由
@network_lcd_router.get("/connect", summary="连接服务器")
@handle_exceptions(model_name="LCD一体屏相关接口")
def connect():
    """
    尝试连接设备到服务器
    连接后发送注册包并开启心跳
    :return:
    """
    network_lcd = get_network_lcd()
    network_lcd.connect()
    logger.info("LCD一体屏成功连接服务器")
    return return_success_response(message="成功连接服务器")


@network_lcd_router.get("/disconnect", summary="断连服务器")
@handle_exceptions(model_name="LCD一体屏相关接口")
def disconnect():
    """
    断开服务器连接
    :return:
    """
    network_lcd = get_network_lcd()
    network_lcd.disconnect()
    logger.info("LCD一体屏成功断开连接")
    return return_success_response(message="成功断开连接")


@network_lcd_router.get("/startHeartbeat", summary="开启心跳")
@handle_exceptions(model_name="LCD一体屏相关接口")
def start_heartbeat():
    """
    开启持续心跳
    :return:
    """
    network_lcd = get_network_lcd()
    network_lcd.start_heartbeat()
    logger.info("LCD一体屏成功开启心跳")
    return return_success_response(message="成功开启心跳")


@network_lcd_router.get("/stopHeartbeat", summary="停止心跳")
@handle_exceptions(model_name="LCD一体屏相关接口")
def stop_heartbeat():
    """
    停止心跳
    :return:
    """
    network_lcd = get_network_lcd()
    network_lcd.stop_heartbeat()
    logger.info("LCD一体屏成功停止心跳")
    return return_success_response(message="成功停止心跳")


@network_lcd_router.post("/getHistoryCommandMessage", summary="查询服务器给该屏下发的历史指令")
@handle_exceptions(model_name="LCD一体屏相关接口")
async def get_history_command_message(data: GetHistoryCommandMessageModel):
    """
    查询数据库中记录的服务器对屏下发的命令消息
    必填参数：
        pageNo: 页码
        pageSize: 每页数量
    """
    page_no = data.pageNo
    page_size = data.pageSize

    network_lcd = get_network_lcd()
    result = await network_lcd.get_db_command_message(page_no, page_size)
    logger.info(f"LCD一体屏查询服务器对屏下发的历史命令消息成功，返回结果：{result}")
    return return_success_response(message="成功", data=result)
