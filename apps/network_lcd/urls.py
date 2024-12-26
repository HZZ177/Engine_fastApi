#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/27 13:39
# @Author  : Heshouyi
# @File    : network_lcd_api.py
# @Software: PyCharm
# @description:
import json
from functools import wraps
from fastapi import APIRouter
from core.logger import logger
from .services import NetworkLcdService
from core.device_manager import DeviceManager

# 创建路由
network_lcd_router = APIRouter(tags=["LCD一体屏相关接口"])


# 工具函数和装饰器
def handle_exceptions(func):
    """通用异常处理装饰器"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"LCD一体屏接口调用时系统异常: {e}")
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
    校验接口JSON传参的必填参数
    校验通过返回None
    校验失败返回错误信息，包含缺少的具体参数信息
    """
    missing_fields = [field for field in required_fields if field not in request_data]
    if missing_fields:
        return error_response(f"缺少必填参数: {','.join(missing_fields)}", 400)
    return None


def get_network_lcd():
    """获取LCD一体屏设备实例"""
    service: NetworkLcdService = DeviceManager.get_network_lcd_service()
    return service


# API 路由
@network_lcd_router.get("/connect")
@handle_exceptions
def connect():
    """
    尝试连接设备到服务器
    连接后发送注册包并开启心跳
    :return:
    """
    logger.info("LCD一体屏connect接口被调用")
    network_lcd = get_network_lcd()
    network_lcd.connect()
    logger.info("LCD一体屏成功连接服务器")
    return success_response()


@network_lcd_router.get("/disconnect")
@handle_exceptions
def disconnect():
    """
    断开服务器连接
    :return:
    """
    logger.info("LCD一体屏disconnect接口被调用")
    network_lcd = get_network_lcd()
    network_lcd.disconnect()
    logger.info("LCD一体屏成功断开连接")
    return success_response()


@network_lcd_router.get("/startHeartbeat")
@handle_exceptions
def start_heartbeat():
    """
    开启持续心跳
    :return:
    """
    logger.info("LCD一体屏startHeartbeat接口被调用")
    network_lcd = get_network_lcd()
    network_lcd.start_heartbeat()
    logger.info("LCD一体屏成功开启心跳")
    return success_response()


@network_lcd_router.get("/stopHeartbeat")
@handle_exceptions
def stop_heartbeat():
    """
    停止心跳
    :return:
    """
    logger.info("LCD一体屏stopHeartbeat接口被调用")
    network_lcd = get_network_lcd()
    network_lcd.stop_heartbeat()
    logger.info("LCD一体屏成功停止心跳")
    return success_response()


@network_lcd_router.post("/getHistoryCommandMessage")
@handle_exceptions
def get_history_command_message():
    """
    查询数据库中记录的服务器对屏下发的命令消息
    必填参数：
        pageNo: 页码
        pageSize: 每页数量
    :return:
    """
    coming_record("LCD一体屏getCommandMessage接口")
    # 校验必填参数
    data = request.json
    validation_error = validate_json(["pageNo", "pageSize"], data)
    if validation_error:
        return validation_error

    page_no = data.get("pageNo", 1)
    page_size = data.get("pageSize", 10)
    # 分页页数和每页数量校验必须为正整数
    if not isinstance(page_no, int) or not isinstance(page_size, int):
        return error_response(message="分页参数必须为正整数")
    if page_no <= 0 or page_size <= 0:
        return error_response(message="分页参数必须为正整数")

    network_lcd = get_network_lcd()
    result = network_lcd.get_db_command_message(page_no, page_size)
    logger.info(f"LCD一体屏查询服务器对屏下发的历史命令消息成功，返回结果：{result}")
    return success_response(data=result)
