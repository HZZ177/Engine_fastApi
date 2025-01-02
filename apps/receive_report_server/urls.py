#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/1/2 11:07
# @Author  : Heshouyi
# @File    : urls.py
# @Software: PyCharm
# @description: 

from fastapi import APIRouter, Request
from core.util import handle_exceptions
from .schemas import GetHistoryReportModel
from core.logger import logger
from core.util import return_success_response
from .services import FindcarReportService

receive_report_router = APIRouter()


def get_findcar_report_service():
    """获取通道相机设备实例"""
    service: FindcarReportService = FindcarReportService()
    return service


@receive_report_router.post('/findcarFieldReport', summary="接收单车场上报接口")
@handle_exceptions(model_name="寻车上报相关接口")
async def findcar_field_report(request: Request):
    """接收服务器发来的单车场上报数据，存库后格式化返回"""
    message = await request.json()  # 获取所有json数据
    logger.info(f"接收到寻车单车场上报数据 {message}")
    # 数据入库
    findcar_report_service = get_findcar_report_service()
    await findcar_report_service.store_received_message(1, message)
    return return_success_response()


@receive_report_router.post('/findcarUnifiedReport', summary="接收统一接口上报接口")
@handle_exceptions(model_name="寻车上报相关接口")
async def findcar_unified_report(request: Request):
    """接收服务器发来的统一平台上报数据，存库后格式化返回"""
    message = await request.json()
    logger.info(f"接收到寻车统一平台上报数据 {message}")
    # 数据入库
    findcar_report_service = get_findcar_report_service()
    await findcar_report_service.store_received_message(2, message)
    return return_success_response()


@receive_report_router.post('/getHistoryReport', summary="查询寻车上报历史记录接口")
@handle_exceptions(model_name="寻车上报相关接口")
async def get_history_report(data: GetHistoryReportModel):
    """查询数据库中记录的寻车上报历史数据"""
    page_no = data.page_no
    page_size = data.page_size
    source = data.source

    findcar_report_service = get_findcar_report_service()
    result = await findcar_report_service.get_db_history_report(page_no, page_size, source)
    logger.info(f"寻车上报服务查询历史记录成功，返回结果：{result}")
    return return_success_response(data=result)
