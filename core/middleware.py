#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/26 16:22
# @Author  : Heshouyi
# @File    : middleware.py
# @Software: PyCharm
# @description:
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from core.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        继承自BaseHTTPMiddleware的类必须定义的中间件
        使用中间件后将请求传递
        """
        # 记录请求信息
        await self.log_request_info(request)

        # 继续处理请求，调用下一个中间件或请求处理
        response = await call_next(request)

        # 处理完请求后返回响应
        return response

    @staticmethod
    async def log_request_info(request: Request):
        """
        中间件，打印接口被请求的详细信息，包括方法、路径、查询参数、请求体等
        """
        # 获取 HTTP 方法、路径和查询参数
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)  # 查询参数

        logger.info(f"【接口调用】- 接口{path}被调用")

        # 获取请求体（如果存在）
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:  # 只对带有请求体的请求进行处理
            try:
                # 尝试获取请求体
                request_body = await request.json()
            except Exception:
                pass  # 如果请求体不是JSON，忽略

        # 打印记录请求的基本信息
        if query_params:
            logger.info(f"请求查询参数: {query_params}")
        if request_body:
            # 打印请求体
            logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False)}")
