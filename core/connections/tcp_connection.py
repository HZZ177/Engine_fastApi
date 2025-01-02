#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:48
# @Author  : Heshouyi
# @File    : tcp_connection.py
# @Software: PyCharm
# @description:
import asyncio
import socket
import threading
import time
from core.logger import logger
from core.util import is_valid_ip


class TCPClient:
    def __init__(self):
        self.local_ip = None  # 用来连接服务器的设备IP
        self.server_ip = None  # 服务器IP
        self.server_port = None  # 服务器端口
        self.server_socket = None
        self.receive_callback = None  # 处理监控服务器下发数据的回调函数
        self.disconnect_callback = None  # 处理connection层主动断开时后续逻辑的回调函数
        self.reconnect_thread = None    # 断线重连线程
        self.stop_reconnect_flag = threading.Event()    # 停止重连线程的标志
        self.reconnect_interval = 10    # 重连间隔时间，默认为10秒
        self.manual_disconnect = None   # 手动断开连接的标志

    def connect(self, server_ip, server_port, local_ip):
        """连接到服务器"""
        self.local_ip = local_ip
        self.server_ip = server_ip
        self.server_port = server_port
        try:
            # 检查本地IP是否合法
            if not is_valid_ip(local_ip):
                logger.error(f"无效的本地IP地址: {local_ip}")
                return False
            # 创建TCP套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 绑定用于连接的本地IP和端口，端口0表示系统自动分配
            self.server_socket.bind((local_ip, 0))
            # 连接服务器
            self.server_socket.connect((server_ip, server_port))
            self.server_socket.settimeout(5)    # 设置超时时间为5秒
            logger.debug(f"成功使用本地IP：{local_ip}，连接到服务器：{server_ip}:{server_port} ")
            # 连接后启动监听线程，接收服务器返回的数据
            threading.Thread(target=self.receive_data, daemon=True).start()
            self.stop_reconnect_flag.set()  # 停止断线重连线程
            return True
        except Exception as e:
            logger.error(f"连接失败，错误信息: {e}")
            self.start_reconnect(server_ip, server_port, local_ip)  # 启动断线重连
            return False

    def send_data(self, data, need_log=True):
        """发送数据到服务器"""
        if not self.is_connected():
            logger.error("发送数据失败：未与服务器建立连接，开始尝试重连")
            self.start_reconnect(self.server_ip, self.server_port, self.local_ip)
            return

        try:
            # 如果data是字符串，则先encode成bytes，否则直接发送
            if isinstance(data, str):
                data = data.encode()
            self.server_socket.sendall(data)
            if need_log:  # 根据参数选择是否打印info日志，为False打debug
                logger.info(f"发送数据：{data}")
            else:
                logger.debug(f"发送数据: {data}")
        except (socket.error, ConnectionResetError) as e:
            logger.error(f"发送数据失败: {e}")
            self.server_socket = None  # 关闭当前套接字
            self.start_reconnect(self.server_ip, self.server_port, self.local_ip)  # 启动断线重连
        except Exception as e:
            logger.error(f"发送数据时出现未知错误: {e}")
            raise e

    def receive_data(self):
        """监听来自服务器的数据并调用回调处理"""
        while self.is_connected():
            try:
                if not self.server_socket:
                    logger.error("套接字未连接，停止接收数据")
                    break
                data = self.server_socket.recv(2048)    # 一旦缓冲区有数据可读，则接收数据并处理
                if data:
                    logger.debug(f"接收到原始数据: {data}")
                    if self.receive_callback:
                        self.receive_callback(data)     # 调用回调函数，将数据传回业务层处理
            except socket.timeout:
                continue  # 忽略超时异常
            except (socket.error, ConnectionResetError) as e:
                logger.warning(f"连接断开: {e}")
                self.server_socket = None
                self.start_reconnect(self.server_ip, self.server_port, self.local_ip)  # 断开后开始重连
                break
            except Exception as e:
                logger.error(f"接收服务器数据时出现未知错误: {e}")

    def disconnect(self):
        """断开连接"""
        self.manual_disconnect = True  # 设置手动断开标记，防止触发自动断线重连
        self.stop_reconnect_flag.set()  # 停止重连
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                logger.warning(f"关闭套接字时发生异常: {e}")
            finally:
                self.server_socket.close()
                self.server_socket = None
                self.receive_callback = None
                logger.info("TCP连接已断开")

    def is_connected(self):
        return self.server_socket is not None

    def set_receive_callback(self, callback):
        """设置接收数据的回调函数"""
        self.receive_callback = callback

    def set_disconnect_callback(self, callback):
        """设置connection层主动断开时的回调函数"""
        self.disconnect_callback = callback

    def start_reconnect(self, server_ip, server_port, local_ip):
        """启动断线重连线程"""
        if self.manual_disconnect:  # 手动断开，不启动重连
            return

        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return  # 防止重复启动重连线程

        self.stop_reconnect_flag.clear()  # 清除停止标志

        def reconnect():
            while not self.stop_reconnect_flag.is_set():
                logger.info(f"{local_ip} 正在尝试重连...")
                try:
                    if self.connect(server_ip, server_port, local_ip):
                        logger.info(f"{local_ip} 重连成功")
                        break
                    else:
                        logger.info(f"{local_ip} 重连失败，{self.reconnect_interval} 秒后重试")

                except Exception as e:
                    logger.error(f"{local_ip} 重连失败: {e}，{self.reconnect_interval}秒后重试")
                time.sleep(self.reconnect_interval)  # 每次重连间隔时间

        self.reconnect_thread = threading.Thread(target=reconnect, daemon=True)
        self.reconnect_thread.start()
