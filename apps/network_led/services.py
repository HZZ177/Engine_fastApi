#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:34
# @Author  : Heshouyi
# @File    : network_led_service.py
# @Software: PyCharm
# @description:

import threading
from core.connections.tcp_connection import TCPClient
from .protocols import NetworkLedModel
from core.logger import logger
from core.connections.db_connection import DBConnection
from core.file_path import db_path


class NetworkLedService:

    def __init__(self, server_ip, server_port, local_ip, device_type, device_version):
        self.client = TCPClient()  # TCP连接客户端
        self.server_ip = server_ip  # 服务器IP
        self.server_port = server_port  # 服务器端口
        self.local_ip = local_ip    # 用于连接服务器的设备IP
        self.device_type = device_type          # 设备类型
        self.device_version = device_version    # 设备版本
        self.is_reporting = False  # 是否正在上报数据
        self.heartbeat_interval = 30  # 心跳间隔时间，单位为秒
        self.timer = None       # 用于定时发送心跳包的定时器
        self.network_led_model = NetworkLedModel()  # 网络LED屏数据模型实例
        self.db_path = db_path

    def connect(self):
        status = self.client.is_connected()
        try:
            if status:
                logger.debug(f"LED网络屏尝试连接服务器时，已有连接，断开后重连")
                self.client.disconnect()
            # 设置接收数据和断开连接的回调函数
            self.client.set_receive_callback(self.handle_received_data)
            self.client.set_disconnect_callback(self.disconnect)
            # 连接服务器
            self.client.connect(self.server_ip, self.server_port, self.local_ip)
            # 连接后发送注册包
            self.send_register_packet()
            # 注册后开始持续心跳
            self.start_heartbeat()
        except Exception as e:
            raise e

    def send_register_packet(self):
        """发送注册包"""
        try:
            packet = self.network_led_model.create_register_packet(self.device_type, self.device_version)
            self.client.send_data(packet, need_log=False)
        except Exception as e:
            raise e

    def start_heartbeat(self):
        try:
            self.is_reporting = True
            self.schedule_next_heartbeat()
            logger.debug("LED网络屏定时心跳开始")
        except Exception as e:
            raise e

    def stop_heartbeat(self):
        try:
            self.is_reporting = False
            if self.timer:
                self.timer.cancel()
                self.timer = None
                logger.debug("LED网络屏定时心跳停止")
        except Exception as e:
            raise e

    def schedule_next_heartbeat(self):
        if self.is_reporting:
            heartbeat_packet = self.network_led_model.create_heartbeat_packet()
            self.client.send_data(heartbeat_packet, need_log=False)
            self.timer = threading.Timer(self.heartbeat_interval, self.schedule_next_heartbeat)
            self.timer.start()

    def handle_received_data(self, data):
        """接收到服务器数据时的处理函数"""
        logger.debug(f"LED网络屏收到来自服务器的数据，开始解包 {data}")
        # 根据数据内容进行处理
        try:
            parsed_data = self.network_led_model.deconstruct_packet(data)
            if parsed_data.get("command_code") == "C":     # 注册包
                logger.debug(f"LED网络屏收到服务器的注册返回包：{parsed_data}")
            elif parsed_data.get("command_code") == "F":     # 心跳包
                logger.debug(f"LED网络屏收到服务器的心跳返回包：{parsed_data}")
            elif parsed_data.get("command_code") == "T":   # T包为服务器下发的显示数据包
                logger.info(f"LED网络屏收到服务器下发的屏显示包：{parsed_data}")
                # 下发的屏显示数据写入数据库
                command_data = parsed_data.get("data_content")  # 提取屏显示指令部分
                self.store_received_command(command_data)
                logger.info(f"LED网络屏写入接收指令到数据库成功：{command_data}")
            else:
                logger.info(f"LED网络屏收到服务器下发的未知类型数据，解包结果: {parsed_data}")
        except Exception as e:
            logger.exception(f"LED网络屏解析服务器下发数据失败: {e}")

    def store_received_command(self, command_data):
        """
        将接收到的服务器下发的led数据写入数据库
        :param command_data: 服务器下发的屏显示数据
        :return: None
        """
        # 在使用时创建数据库连接，提前创建会有跨线程问题
        db = DBConnection(self.db_path)  # 初始化数据库连接
        with db:
            insert_sql = "INSERT INTO device_message (device_addr, message_source, message) VALUES (?, ?, ?)"
            db.execute(insert_sql, (self.local_ip, 3, command_data))

    def get_db_command_message(self, page_no, page_size):
        """
        查询数据库中记录的服务器对屏下发的命令消息
        :return: 查询结果
        """
        # 计算分页偏移量
        offset = (page_no - 1) * page_size
        sql = f"""
            SELECT * FROM device_message
            WHERE message_source=3
            ORDER BY create_time DESC
            LIMIT {page_size} OFFSET {offset}
        """
        try:
            db = DBConnection(self.db_path)
            with db:
                return db.fetchall_as_dict(sql)
        except Exception as e:
            raise e

    def disconnect(self):
        try:
            self.stop_heartbeat()
            self.client.disconnect()
        except Exception as e:
            raise e
