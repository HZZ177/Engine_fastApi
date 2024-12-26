#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:34
# @Author  : Heshouyi
# @File    : parking_camera_service.py
# @Software: PyCharm
# @description:

import threading
import time
from core.connections.tcp_connection import TCPClient
from .protocols import ParkingCameraModel
from core.logger import logger


class ParkingCameraService:
    def __init__(self, server_ip, server_port, local_ip, device_type, device_version):
        self.device_type = device_type          # 设备类型，默认为0x00
        self.device_version = device_version    # 设备版本号，默认为0x0400
        self.client = TCPClient()           # TCP客户端连接
        self.server_ip = server_ip          # 服务器IP
        self.server_port = server_port      # 服务器端口
        self.local_ip = local_ip            # 用于连接服务器的设备IP
        self.is_reporting = False           # 是否正在上报数据
        self.is_reporting_parking_status = False     # 是否正在上报车位状态
        self.heartbeat_interval = 30        # 心跳间隔时间，单位为秒
        self.reporting_interval = 30        # 上报车位状态的间隔时间，单位为秒
        self.timer = None                   # 用于定时发送心跳包的定时器
        self.image_confirmation_event = threading.Event()  # 线程事件对象，用于发送图片时阻塞发送进程，等待服务器返回确认信息
        self.register_confirmation_event = threading.Event()  # 线程事件对象，用于注册时阻塞发送进程，等待服务器返回确认信息
        self.parking_camera_model = ParkingCameraModel()    # 车位相机的数据模型实例

    def connect(self):
        """连接服务器"""
        status = self.client.is_connected()
        try:
            if status:
                logger.warning(f"车位相机尝试连接服务器时，已有连接，断开后重连")
                self.client.disconnect()
            # 设置接收数据和断开连接的回调函数
            self.client.set_receive_callback(self.handle_received_data)
            self.client.set_disconnect_callback(self.disconnect)
            # 连接服务器
            self.client.connect(self.server_ip, self.server_port, self.local_ip)
            # 连接后发送注册包
            self.send_register_packet()
            # 特殊步骤，注册后立即发一个无实际业务数据的车位状态上报，全部用9占位，用于服务器识别设备类型
            self.send_all9_packet_for_recognition()
            # 注册后开始持续心跳
            self.start_heartbeat()
        except Exception as e:
            raise e

    def send_register_packet(self):
        """发送注册包"""
        try:
            packet = self.parking_camera_model.create_register_packet(self.device_type, self.device_version)
            self.client.send_data(packet, need_log=False)
            # 阻塞等待服务器返回注册确认包
            self.register_confirmation_event.clear()  # 设置事件为未触发状态
            if not self.register_confirmation_event.wait(timeout=5):  # 等待事件被触发，超时时间为5秒
                logger.exception("车位相机5秒内没有接收到服务器返回的注册确认包")
                raise Exception("车位相机5秒内没有接收到服务器返回的注册确认包，注册失败")
        except Exception as e:
            raise e

    def send_all9_packet_for_recognition(self):
        """
        特殊步骤
        发一个全部用9占位的车位状态上报，，用于服务器识别设备类型
        9会被服务器主动过滤，没有实际业务影响
        :return:
        """
        try:
            packet = self.parking_camera_model.create_all9_parking_status_packet()
            self.client.send_data(packet, need_log=False)
        except Exception as e:
            raise e

    def start_heartbeat(self):
        """开启持续心跳"""
        try:
            self.is_reporting = True
            self.schedule_next_heartbeat()
            logger.debug("车位相机定时心跳开始")
        except Exception as e:
            raise e

    def stop_heartbeat(self):
        """停止心跳"""
        try:
            self.is_reporting = False
            if self.timer:
                self.timer.cancel()
                self.timer = None
                logger.debug("车位相机定时心跳停止")
        except Exception as e:
            raise e

    def schedule_next_heartbeat(self):
        if self.is_reporting:
            heartbeat_packet = self.parking_camera_model.create_heartbeat_packet()
            self.client.send_data(heartbeat_packet, need_log=False)
            self.timer = threading.Timer(self.heartbeat_interval, self.schedule_next_heartbeat)
            self.timer.start()

    def send_command(self, command_data: bytes, command_code: str):
        """
        发送指令工具方法，向上供不同指令的发送接口使用
        :param command_data: 需要发送的数据体
        :param command_code: 命令码
        :return:
        """
        try:
            # 根据协议和数据体构造包
            timestamp = int(time.time())
            packet = self.parking_camera_model.construct_packet(command_data, timestamp, command_code)
            self.client.send_data(packet)
        except Exception as e:
            raise e

    def start_parking_status_report(self, park_num, park_event):
        """
        开启持续上报车位状态
        :return:
        """
        try:
            if self.is_reporting_parking_status:
                logger.debug("车位相机当前已存在定时任务，被新上报覆盖")
                self.stop_reporting_parking_status()
            self.is_reporting_parking_status = True
            self.schedule_next_parking_status_report(park_num, park_event)
            logger.debug("车位相机定时上报车位状态开始")
        except Exception as e:
            raise e

    def schedule_next_parking_status_report(self, park_num, park_event):
        """调度下一次上报"""
        if self.is_reporting_parking_status:
            try:
                # 执行上报逻辑
                self.send_parking_status(park_num, park_event)
                logger.info(f"车位相机定时上报成功，车位号: {park_num}, 车位状态: {park_event}")
            except Exception as e:
                logger.exception(f"车位相机定时上报失败: {e}")

            # 调度下一次上报
            self.timer = threading.Timer(
                self.reporting_interval,
                self.schedule_next_parking_status_report,
                args=[park_num, park_event]
            )
            self.timer.start()

    def stop_reporting_parking_status(self):
        """停止持续上报"""
        try:
            self.is_reporting = False
            if self.timer:
                self.timer.cancel()
                self.timer = None
        except Exception as e:
            raise e

    def send_parking_status(self, selected_port, status_values):
        """
        上报车位状态(事件)
        :param selected_port: 要上报的车位号
        :param status_values: 车位状态
        :return:
        """
        try:
            packet = self.parking_camera_model.create_parking_status_packet(selected_port, status_values)
            self.client.send_data(packet)
        except Exception as e:
            raise e

    def upload_picture(self, park_num: int, image_bytes: bytes,
                       model: int, plate_color: int, plate_number: str, confidence: int):
        """
        给服务器上传图片数据包，包类型为J包
        首先发送一次头包，阻塞进程等待服务器的确认返回，接收到返回后分包发送图片的二进制内容
        :param confidence: 可信度
        :param plate_number: 车牌号
        :param plate_color: 车牌颜色
        :param model: 识别模式 1：硬识别 2：软识别
        :param park_num: 车位号
        :param image_bytes: 图片二进制数据
        :return:
        """
        try:
            # 流程中需要共同的参数
            total_packets = len(image_bytes) // 1024 + (1 if len(image_bytes) % 1024 != 0 else 0)
            timestamp_all = int(time.time())  # 协议要求一个图片的所有包共用同一个时间戳

            # 构造头包后发送
            if model == 1:  # 硬识别模式
                head_packet = self.parking_camera_model.create_parking_picture_hard_head_packet(
                    park_num, timestamp_all, total_packets, image_bytes, plate_color, plate_number, confidence
                )
            else:   # 软识别模式
                head_packet = self.parking_camera_model.create_parking_picture_head_packet(
                    park_num, timestamp_all, total_packets, image_bytes
                )
            self.client.send_data(head_packet)

            # 等待服务器返回确认
            logger.debug("图片头包已发送，等待服务器返回确认")
            self.image_confirmation_event.clear()  # 设置事件为未触发状态
            if not self.image_confirmation_event.wait(timeout=5):  # 等待事件被触发，超时时间为5秒
                logger.exception("车位相机5秒内没有接收到服务器返回的图片头包确认包，停止上传图片")
                raise Exception("车位相机5秒内没有接收到服务器返回的图片头包确认包，停止上传图片")
            logger.debug("车位相机收到服务器的头包确认返回，开始发送图片数据")

            # 分包发送图片数据
            for i in range(total_packets):
                chunk = image_bytes[i * 1024:(i + 1) * 1024]    # 每1024字节为一包
                packet = self.parking_camera_model.construct_packet(
                    command_data=chunk,
                    command_code="J",
                    timestamp=timestamp_all,
                    total_packets=total_packets,
                    packet_number=i + 1  # 图片数据包的序号从1开始
                )
                self.client.send_data(packet, need_log=False)
        except Exception as e:
            raise e

    def handle_received_data(self, data):
        """接收到服务器数据时的处理函数"""
        logger.debug(f"车位相机收到来自服务器的数据，开始解包 {data}")
        # 根据数据内容进行处理
        try:
            parsed_data = self.parking_camera_model.deconstruct_packet(data)
            if parsed_data.get("command_code") == "F":    # 处理车位相机的F心跳包
                logger.debug(f"车位相机收到服务器的心跳返回：{parsed_data}")
            elif parsed_data.get("command_code") == "C":    # 处理注册确认C包
                logger.debug(f"车位相机收到服务器的注册确认包：{parsed_data}")
                self.register_confirmation_event.set()  # 触发事件解除等待状态
            elif parsed_data.get("command_code") == "J":  # 处理服务器返回的图片头包ACK返回包，返回J包视为确认通过
                logger.debug(f"车位相机收到服务器的图片头包确认返回：{parsed_data}")
                self.image_confirmation_event.set()  # 触发事件解除等待状态
            elif parsed_data.get("command_code") == "S":    # 处理车位相机的F心跳包
                logger.info(f"车位相机收到服务器的车位状态上报返回：{parsed_data}")
            else:
                logger.info(f"车位相机收到服务器下发数据，解包结果: {parsed_data}")
        except Exception as e:
            logger.exception(f"车位相机解析服务器下发数据失败: {e}")

    def disconnect(self):
        try:
            self.stop_heartbeat()
            self.client.disconnect()
        except Exception as e:
            raise e
