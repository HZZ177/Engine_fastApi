#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/25 13:51
# @Author  : Heshouyi
# @File    : websocket_connection.py
# @Software: PyCharm
# @description:

import websocket
import threading
import socket
from core.logger import logger
from typing import Union


class WebSocketClient:
    def __init__(self):
        self.ws: Union[websocket.WebSocket, None] = None
        self.local_ip = None  # 用来连接服务器的设备IP
        self.server_url = ""    # 服务器地址，需要以ws://或wss://开头
        self.receive_callback = None  # 处理服务器下发数据的回调函数
        self.disconnect_callback = None  # 处理主动断开连接时的回调函数
        self.connected = False

    def connect(self, server_url, server_ip, server_port, local_ip):
        """
        连接到服务器
        由于websocket协议抽象掉了底层的TCP套接字操作，不支持自定义绑定本地IP来连接
        因此先通过基础socket创建一个绑定了本地IP地址的套接字，然后将其传递给websocket来实现指定本地地址的websocket

        :param local_ip: 本地IP地址
        :param server_url: websocket地址，要求格式 ws://{server_ip}:8080/device-access/lcd/{network_lcd_ip}&0
        :param server_ip: 服务器端口号
        :param server_port: 服务器IP
        :return:
        """
        self.local_ip = local_ip
        # 创建底层socket
        sock = socket.create_connection(
            (server_ip, server_port),
            timeout=5,
            source_address=(self.local_ip, 0)
        )

        self.server_url = server_url
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(server_url, socket=sock, timeout=5)     # 通过自定义的套接字sock连接
            self.connected = True
            logger.debug(f"成功连接到WebSocket服务器：{server_url}")
            # 启动线程接收数据
            threading.Thread(target=self.receive_data, daemon=True).start()
        except Exception as e:
            logger.error(f"WebSocket连接失败，错误信息: {e}")
            self.connected = False
            raise e

    def send_data(self, data: Union[str, bytes], need_log=True):
        """发送数据到服务器"""
        if self.ws and self.connected:
            try:
                if isinstance(data, str):
                    self.ws.send(data)
                elif isinstance(data, bytes):
                    self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)  # 发送二进制帧
                else:
                    logger.error("发送的数据必须是字符串或二进制数据")

                if need_log:
                    logger.info(f"websocket发送数据：{data}")
                else:
                    logger.debug(f"websocket发送数据: {data}")
            except Exception as e:
                logger.error(f"websocket发送数据失败: {e}")
                raise e
        else:
            logger.error("websocket尝试发送数据，但是还未与服务器建立连接")
            raise Exception("websocket尝试发送数据，但是还未与服务器建立连接")

    def receive_data(self):
        """监听来自服务器的数据并调用回调处理"""
        while self.connected:
            try:
                if not self.ws:
                    logger.error("WebSocket未连接，停止接收数据")
                    break

                data = self.ws.recv()  # 阻塞等待接收数据
                if data:
                    logger.debug(f"websocket接收到原始数据: {data}")
                    if self.receive_callback:
                        self.receive_callback(data)  # 调用回调函数处理数据
            except websocket.WebSocketTimeoutException:
                continue  # 超时大概率是服务器一段时间内没有返回数据，可忽略
            except websocket.WebSocketConnectionClosedException:
                logger.warning("WebSocket连接已关闭")
                self.disconnect()
                break
            except Exception as e:
                logger.error(f"websocket接收服务器数据时出现未知错误: {e}")

    def disconnect(self):
        """断开连接"""
        if self.ws:
            try:
                self.ws.close()
                self.ws = None
                self.connected = False
                logger.info("WebSocket连接已断开")
            except Exception as e:
                logger.error(f"断开WebSocket连接失败: {e}")

    def is_connected(self):
        return self.connected

    def set_receive_callback(self, callback):
        """设置接收数据的回调函数"""
        self.receive_callback = callback

    def set_disconnect_callback(self, callback):
        """设置主动断开连接时的回调函数"""
        self.disconnect_callback = callback
