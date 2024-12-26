#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:34
# @Author  : Heshouyi
# @File    : network_led_model.py
# @Software: PyCharm
# @description:

import struct
import time


class NetworkLedModel:
    PROTOCOL_HEAD = 0xfb    # 协议头
    PROTOCOL_TAIL = 0xfe    # 协议尾

    @staticmethod
    def construct_packet(command_data: bytes, command_code: str) -> bytes:
        """
        构造事件数据包
        :param command_data: 要发送的数据体
        :param command_code: 命令码
        :return:
        """
        try:
            data_bytes = command_data     # 要发送的数据体，bytes格式
            timestamp = int(time.time())    # 时间戳
            command_code_ascii = ord(command_code)  # 命令码转换为ASCII码
            total_packets = 1   # 总包数，默认只有一个
            packet_number = 0   # 包序号，默认为0
            data_length = len(data_bytes)   # 数据长度
            # 校验码
            checksum = NetworkLedModel.calculate_checksum(timestamp, command_code_ascii, total_packets,
                                                             packet_number, data_length, data_bytes)

            packet = (struct.pack('>B', NetworkLedModel.PROTOCOL_HEAD) +
                      struct.pack('>I', timestamp) +
                      struct.pack('>B', command_code_ascii) +
                      struct.pack('>H', total_packets) +
                      struct.pack('>H', packet_number) +
                      struct.pack('>H', data_length) +
                      data_bytes +
                      struct.pack('>H', checksum) +
                      struct.pack('>B', NetworkLedModel.PROTOCOL_TAIL))
            # 组装数据包，按协议要求处理转义
            processed_packet = NetworkLedModel.escape_packet(packet)
            return processed_packet
        except Exception as e:
            raise e

    @staticmethod
    def deconstruct_packet(data):
        """
        根据协议解包服务器下发的数据
        :param data: 返回的原数据字节流
        :return: 根据协议解析后的json
        """
        # 根据协议解析：包含如下字段
        #   协议头 (1字节), 时间戳 (4字节), 命令码 (1字节), 数据长度 (2字节), 数据内容 (N字节), 校验码 (2字节), 协议尾 (1字节)
        protocol_head, timestamp, command_code, total_packets, packet_number, data_length = struct.unpack(
            '>BIBHHH', data[:12])

        # 根据data_length提取数据内容
        data_content = data[12:12 + data_length].decode()
        # 提取校验码和协议尾
        checksum, protocol_tail = struct.unpack('>HB', data[12 + data_length:12 + data_length + 3])

        # 组装解析后数据
        parsed_data = {
            "protocol_head": hex(protocol_head),
            "timestamp": timestamp,
            "command_code": chr(command_code),
            "total_packets": total_packets,
            "packet_number": packet_number,
            "data_length": data_length,
            "data_content": data_content,
            "checksum": checksum,
            "protocol_tail": hex(protocol_tail),
        }

        return parsed_data

    @staticmethod
    def calculate_checksum(timestamp, command_code_ascii, total_packets, packet_number, data_length, data_bytes):
        """按照协议要求，计算校验码"""
        checksum_data = (
            struct.pack('>I', timestamp) +
            struct.pack('>B', command_code_ascii) +
            struct.pack('>H', total_packets) +
            struct.pack('>H', packet_number) +
            struct.pack('>H', data_length) +
            data_bytes
        )
        checksum = sum(checksum_data) & 0xFFFF
        return checksum

    @staticmethod
    def escape_packet(packet):
        """
        按协议要求，将除了头尾的中间字节进行转义处理
        :param packet: 组装后的未处理字节数据
        :return:
        """
        escaped_packet = bytearray()

        # 保留协议头
        escaped_packet.append(packet[0])

        # 对中间数据部分进行转义（排除头尾字节）
        for byte in packet[1:-1]:
            if byte == 0xfb:
                escaped_packet.extend([0xff, 0xbb])
            elif byte == 0xfe:
                escaped_packet.extend([0xff, 0xee])
            elif byte == 0xff:
                escaped_packet.extend([0xff, 0xfc])
            else:
                escaped_packet.append(byte)

        # 保留协议尾
        escaped_packet.append(packet[-1])

        return bytes(escaped_packet)

    @staticmethod
    def create_register_packet(device_type, device_version):
        """按参数封装注册包"""
        register_data = struct.pack(">B H", device_type, device_version)    # 注册包的bytes数据，包含设备类型和版本号
        packet = NetworkLedModel.construct_packet(register_data, command_code='C')
        return packet

    @staticmethod
    def create_heartbeat_packet():
        """按参数封装心跳包"""
        packet = NetworkLedModel.construct_packet(b"", command_code='F')    # led的心跳包数据为空
        return packet
