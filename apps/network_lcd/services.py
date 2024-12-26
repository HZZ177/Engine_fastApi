#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/27 13:42
# @Author  : Heshouyi
# @File    : network_lcd_service.py
# @Software: PyCharm
# @description:
import json
import threading
from core.connections.websocket_connection import WebSocketClient
from .protocols import NetworkLcdModel
from core.logger import logger
from core.connections.db_connection import DBConnection
from core.file_path import db_path


class NetworkLcdService:

    def __init__(self, server_ip, server_port, local_ip, server_url):
        self.client = WebSocketClient()  # TCP连接客户端
        self.server_ip = server_ip      # 服务器IP地址
        self.server_port = server_port  # 服务器端口
        self.local_ip = local_ip    # 用于连接服务器的设备IP
        self.server_url = server_url    # 服务器websocket地址
        self.is_reporting = False  # 是否正在上报数据
        self.heartbeat_interval = 5  # 心跳间隔时间，单位为秒
        self.timer = None       # 用于定时发送心跳包的定时器
        self.network_lcd_model = NetworkLcdModel()  # LCD一体屏数据模型实例
        self.db_path = db_path

    def connect(self):
        status = self.client.is_connected()
        try:
            if status:
                logger.debug(f"LCD一体屏尝试连接服务器时，已有连接，断开后重连")
                self.client.disconnect()
            # 设置接收数据和断开连接的回调函数
            self.client.set_receive_callback(self.handle_received_data)
            self.client.set_disconnect_callback(self.disconnect)
            # 连接服务器
            self.client.connect(self.server_url, self.server_ip, self.server_port, self.local_ip)
            # 启动心跳
            self.start_heartbeat()
        except Exception as e:
            raise e

    def start_heartbeat(self):
        try:
            self.is_reporting = True
            self.schedule_next_heartbeat()
            logger.debug("LCD一体屏定时心跳开始")
        except Exception as e:
            raise e

    def stop_heartbeat(self):
        try:
            self.is_reporting = False
            if self.timer:
                self.timer.cancel()
                self.timer = None
                logger.debug("LCD一体屏定时心跳停止")
        except Exception as e:
            raise e

    def schedule_next_heartbeat(self):
        if self.is_reporting:
            heartbeat_packet = json.dumps(self.network_lcd_model.create_heartbeat_packet(), ensure_ascii=False)
            self.client.send_data(heartbeat_packet, need_log=False)
            self.timer = threading.Timer(self.heartbeat_interval, self.schedule_next_heartbeat)
            self.timer.start()

    def handle_received_data(self, data):
        """接收到服务器数据时的处理函数"""
        logger.debug(f"LCD一体屏收到来自服务器的数据，原始数据： {data}")
        # 根据数据内容进行处理
        try:
            parsed_data = json.loads(data)
            if not isinstance(data, str):
                logger.error(f"LCD一体屏收到来自服务器的非str数据：{type(data)}")
                return

            logger.info(f"LCD一体屏收到来自服务器的指令 {parsed_data}")

            # 根据接收的指令，返回响应包
            reqid = parsed_data.get("reqid")
            command_response_packet = json.dumps(
                self.network_lcd_model.create_command_response_packet(reqid),
                ensure_ascii=False
            )
            self.client.send_data(command_response_packet, need_log=False)
            logger.info(f"LCD一体屏指令响应包发送成功，reqid：{reqid}")

            # 将接收到的服务器下发的指令录入数据库
            self.store_received_command(data)
            logger.info(f"LCD一体屏录入接收到的下发指令到数据库成功{data}")

        except Exception as e:
            logger.exception(f"LCD一体屏解析服务器下发数据失败: {e}")

    def store_received_command(self, command_data):
        """
        将接收到的服务器下发的lcd数据写入数据库
        :param command_data: 服务器下发的屏显示数据
        :return: None
        """
        # 在使用时创建数据库连接，提前创建会有跨线程问题
        db = DBConnection(self.db_path)  # 初始化数据库连接
        with db:
            insert_sql = "INSERT INTO device_message (device_addr, message_source, message) VALUES (?, ?, ?)"
            db.execute(insert_sql, (self.local_ip, 4, command_data))

    def get_db_command_message(self, page_no, page_size):
        """
        查询数据库中记录的服务器对屏下发的命令消息
        :return: 查询结果
        """
        # 计算分页偏移量
        offset = (page_no - 1) * page_size
        sql = f"""
            SELECT * FROM device_message
            WHERE message_source=4
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
