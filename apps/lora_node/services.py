#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:34
# @Author  : Heshouyi
# @File    : lora_node_service.py
# @Software: PyCharm
# @description:

import threading
from core.connections.tcp_connection import TCPClient
from .protocols import LoraNodeModel
from core.logger import logger


class LoraNodeService:

    def __init__(self, server_ip, server_port, local_ip):
        self.client = TCPClient()  # TCP客户端连接
        self.server_ip = server_ip  # 服务器IP
        self.server_port = server_port  # 服务器端口
        self.local_ip = local_ip  # 用于连接服务器的设备IP
        self.is_reporting = False  # 是否正在上报数据
        self.timer = None       # 用于持续发送探测器状态的定时器
        self.lora_node_model = LoraNodeModel()  # Lora节点数据模型实例

    def connect(self):
        status = self.client.is_connected()
        try:
            if status:
                logger.debug(f"Lora节点尝试连接服务器时，已有连接，断开后重连")
                self.client.disconnect()
            self.client.connect(self.server_ip, self.server_port, self.local_ip)
        except Exception as e:
            raise e

    def disconnect(self):
        try:
            self.stop_reporting()   # 停止持续上报
            self.client.disconnect()
        except Exception as e:
            raise e

    def report_status(self, sensor_addr, sensor_status, fault_details):
        """
        上报一次节点下探测器状态
        :param sensor_addr: 探测器地址
        :param sensor_status: 探测器状态
        :param fault_details: 故障详情列表
        :return:
        """
        try:
            packet = self.lora_node_model.construct_status_report_packet(sensor_addr, sensor_status, fault_details)
            logger.debug(f"Lora节点发送数据: {packet}")
            self.client.send_data(packet)
        except Exception as e:
            raise e

    def start_reporting(self, sensor_addr, sensor_status, fault_details, report_interval):
        """开始持续上报探测器状态"""
        try:
            # 如果已存在运行中的定时任务，手动停止，确保同一时间只有一个上报
            if self.is_reporting:
                logger.debug("当前已存在定时任务，被新上报覆盖")
                self.stop_reporting()
            # 启动定时器
            self.is_reporting = True
            self.schedule_next_report(sensor_addr, sensor_status, fault_details, report_interval)
        except Exception as e:
            raise e

    def stop_reporting(self):
        """停止持续上报"""
        try:
            self.is_reporting = False
            if self.timer:
                self.timer.cancel()
                self.timer = None
        except Exception as e:
            raise e

    def schedule_next_report(self, sensor_addr, sensor_status, fault_details, report_interval):
        """调度下一次上报"""
        if self.is_reporting:
            try:
                # 执行上报逻辑
                self.report_status(sensor_addr, sensor_status, fault_details)
            except Exception as e:
                logger.exception(f"Lora节点上报失败: {e}")

            # 调度下一次上报
            self.timer = threading.Timer(
                report_interval,
                self.schedule_next_report,
                args=[sensor_addr, sensor_status, fault_details, report_interval]
            )
            self.timer.start()
