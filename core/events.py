#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/26 13:59
# @Author  : Heshouyi
# @File    : events.py
# @Software: PyCharm
# @description:

import psutil
import socket
from fastapi import FastAPI
from core.connections.db_connection import DBConnection
from core.device_manager import DeviceManager
from core.file_path import db_path
from core.logger import logger
from core.configer import config


def get_all_local_ips():
    """获取本机所有网卡的IP地址"""
    ips = []
    try:
        # 获取所有网络接口
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                # 过滤出IPv4地址，用socket.AF_INET来过滤是因为psutil没有提供AF_INET常量
                if addr.family == socket.AF_INET:
                    ips.append(addr.address)
    except Exception as e:
        logger.error(f"获取本机所有IP地址失败: {e}")
    return ips


def register_startup_and_shutdown_events(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        """
        应用启动时执行的初始化逻辑
        """
        try:
            logger.info("开始检查当前环境是否满足配置文件中设备所需全部IP")
            # 获取当前环境中的所有IP地址
            local_ips = get_all_local_ips()
            logger.debug(f"当前环境的所有IP地址: {local_ips}")

            # 加载配置中的设备IP
            try:
                required_ips = [addr for device, addr in config["devices_addr"].items()]
                devices = [device for device, addr in config["devices_addr"].items()]
                logger.info(
                    f"配置文件中所需的所有设备IP地址: {required_ips}，对应设备名称: {devices}"
                )
            except Exception as e:
                raise Exception(f"获取配置文件所需的IP失败: {e}")

            # 检查配置的IP是否存在当前环境中
            missing_ips = [ip for ip in required_ips if ip not in local_ips]
            if missing_ips:
                logger.error(f"环境缺少设备所需IP地址: {missing_ips}")
                raise Exception(f"环境缺少设备所需IP地址：{missing_ips}")

            # 如果检测通过，初始化所有设备
            logger.info("环境满足，开始初始化设备")
            try:
                DeviceManager.initialize_all_devices()
                logger.info("所有设备初始化成功")
            except Exception as e:
                raise Exception(f"设备初始化失败: {e}")

            # 初始化sqlite
            try:
                DBConnection(db_path).init()
                logger.info("sqlite初始化成功")
            except Exception as e:
                raise Exception(f"sqlite初始化失败: {e}")

        except Exception as e:
            logger.exception(f"引擎初始化失败: {e}")
            await shutdown_event()
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        应用关闭时的清理逻辑
        """
        try:
            logger.info("关闭引擎，注销所有设备中...")
            DeviceManager.shutdown_all_devices()
            logger.info("所有设备已成功注销")
        except Exception as e:
            logger.exception(f"注销设备时发生异常: {e}")
