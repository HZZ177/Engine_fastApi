#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/13 下午22:01
# @Author  : Heshouyi
# @File    : device_manager.py
# @Software: PyCharm
# @description:

from typing import Union
from core.configer import config
from core.logger import logger
from apps.channel_camera.services import ChannelCameraService
from apps.parking_camera.services import ParkingCameraService
from apps.lora_node.services import LoraNodeService
from apps.four_bytes_node.services import FourBytesNodeService
from apps.network_led.services import NetworkLedService
from apps.network_lcd.services import NetworkLcdService


class DeviceManager:
    channel_camera_service: Union[ChannelCameraService, None] = None   # 通道相机服务实例
    lora_node_service: Union[LoraNodeService, None] = None        # Lora节点设备服务实例
    four_bytes_node_service: Union[FourBytesNodeService, None] = None   # 四字节网络节点服务实例
    network_led_service: Union[NetworkLedService, None] = None      # 网络led屏服务实例
    network_lcd_service: Union[NetworkLcdService, None] = None      # lcd一体屏服务实例
    parking_camera_service: Union[ParkingCameraService, None] = None   # 车位相机服务实例

    @classmethod
    def initialize_all_devices(cls):
        """初始化所有设备实例"""

        # 读取配置文件
        try:
            # 服务器配置参数
            server_ip = config['server']['host']
            # 通道相机配置参数
            channel_camera_ip = config['devices_addr']['channel_camera_ip']
            channel_camera_device_id = config["devices_info"]["channel_camera"]["device_id"]
            channel_camera_device_version = config["devices_info"]["channel_camera"]["device_version"]
            # 车位相机配置参数
            parking_camera_ip = config['devices_addr']['parking_camera_ip']
            parking_camera_device_type = config["devices_info"]["parking_camera"]["device_type"]
            parking_camera_device_version = config["devices_info"]["parking_camera"]["device_version"]
            # lora节点配置参数
            lora_node_ip = config['devices_addr']['lora_node_ip']
            # 四字节网络节点配置参数
            four_bytes_node_ip = config['devices_addr']['four_bytes_node_ip']
            # led网络屏配置参数
            network_led_ip = config['devices_addr']['network_led_ip']
            network_led_device_type = config["devices_info"]["network_led"]["device_type"]
            network_led_device_version = config["devices_info"]["network_led"]["device_version"]
            # lcd一体屏配置参数
            network_lcd_ip = config['devices_addr']['network_lcd_ip']

        except Exception as e:
            raise Exception(f"初始化时配置读取失败：{e}")

        # 初始化通道相机设备
        try:
            # 初始化设备实例
            cls.channel_camera_service = ChannelCameraService(server_ip, 7799, channel_camera_ip,
                                                              channel_camera_device_id, channel_camera_device_version)
            # 连接服务器后自动注册并开始心跳
            cls.channel_camera_service.connect()
            logger.info("通道相机设备初始化成功")
        except Exception as e:
            raise Exception(f"通道相机设备初始化失败: {e}")

        # 初始化车位相机设备
        try:
            # 初始化设备实例
            cls.parking_camera_service = ParkingCameraService(server_ip, 7799, parking_camera_ip,
                                                              parking_camera_device_type, parking_camera_device_version)
            # 连接服务器后自动注册并开始心跳
            cls.parking_camera_service.connect()
            logger.info("车位相机设备初始化成功")
        except Exception as e:
            raise Exception(f"车位相机设备初始化失败: {e}")

        # 初始化lora节点设备
        try:
            # 初始化设备实例
            cls.lora_node_service = LoraNodeService(server_ip, 7777, lora_node_ip)
            # 连接服务器
            cls.lora_node_service.connect()
            logger.info("Lora节点初始化成功")
        except Exception as e:
            raise Exception(f"Lora节点初始化失败: {e}")

        # 初始化四字节节点设备
        try:
            # 初始化设备实例
            cls.four_bytes_node_service = FourBytesNodeService(server_ip, 7777, four_bytes_node_ip)
            # 连接服务器
            cls.four_bytes_node_service.connect()
            logger.info("四字节网络节点初始化成功")
        except Exception as e:
            raise Exception(f"四字节网络节点初始化失败: {e}")

        # 初始化网络led屏设备
        try:
            # 初始化设备实例
            cls.network_led_service = NetworkLedService(server_ip, 7799, network_led_ip,
                                                        network_led_device_type, network_led_device_version)
            # 连接服务器后自动注册并开始心跳
            cls.network_led_service.connect()
            logger.info("网络led屏初始化成功")
        except Exception as e:
            raise Exception(f"网络led屏初始化失败: {e}")

        # 初始化网络lcd一体屏设备
        try:
            # 初始化设备实例
            server_url = f"ws://{server_ip}:8080/device-access/lcd/{network_lcd_ip}&0"  # url固定格式，"&0"标识为LCD一体屏
            cls.network_lcd_service = NetworkLcdService(server_ip, 8080, network_lcd_ip, server_url)
            # 连接服务器后开始心跳
            cls.network_lcd_service.connect()
            logger.info("网络lcd一体屏初始化成功")
        except Exception as e:
            raise Exception(f"网络lcd一体屏初始化失败: {e}")

    @classmethod
    def shutdown_all_devices(cls):
        """注销所有设备"""
        logger.info("开始注销所有设备......")
        if cls.channel_camera_service:
            cls.channel_camera_service.disconnect()
        if cls.parking_camera_service:
            cls.parking_camera_service.disconnect()
        if cls.lora_node_service:
            cls.lora_node_service.disconnect()
        if cls.four_bytes_node_service:
            cls.four_bytes_node_service.disconnect()
        if cls.network_led_service:
            cls.network_led_service.disconnect()
        if cls.network_lcd_service:
            cls.network_lcd_service.disconnect()
        logger.info("所有设备注销成功")

    @classmethod
    def get_channel_camera_service(cls):
        """获取通道相机服务实例"""
        return cls.channel_camera_service

    @classmethod
    def get_lora_node_service(cls):
        """获取Lora节点设备服务实例"""
        return cls.lora_node_service

    @classmethod
    def get_four_bytes_node_service(cls):
        """获取四字节节点设备服务实例"""
        return cls.four_bytes_node_service

    @classmethod
    def get_network_led_service(cls):
        """获取网络led屏服务实例"""
        return cls.network_led_service

    @classmethod
    def get_network_lcd_service(cls):
        """获取lcd一体屏服务实例"""
        return cls.network_lcd_service

    @classmethod
    def get_parking_camera_service(cls):
        """获取车位相机服务实例"""
        return cls.parking_camera_service
