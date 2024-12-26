#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:35
# @Author  : Heshouyi
# @File    : parking_camera_model.py
# @Software: PyCharm
# @description:

import struct
import time


class ParkingCameraModel:
    PROTOCOL_HEAD = 0xfb  # 协议头
    PROTOCOL_TAIL = 0xfe  # 协议尾

    def construct_packet(self, command_data: bytes, timestamp, command_code: str,
                         total_packets: int = 1, packet_number: int = 0) -> bytes:
        """
        构造事件数据包
        :param timestamp: 时间戳，协议要求图片所有包用同一个时间戳
        :param command_data: 要发送的数据字节码
        :param command_code: 命令码
        :param packet_number: 包序号，默认为0
        :param total_packets:  总包数，默认为1
        :return:
        """
        data_content = command_data
        command_code_ascii = ord(command_code)  # 命令码转换为ASCII码
        data_length = len(data_content)  # 数据长度
        checksum = self.calculate_checksum(timestamp, command_code_ascii, total_packets, packet_number, data_length, data_content)  # 校验码

        packet = (
                struct.pack('>B', self.PROTOCOL_HEAD) +
                struct.pack('>I', timestamp) +
                struct.pack('>B', command_code_ascii) +
                struct.pack('>H', total_packets) +
                struct.pack('>H', packet_number) +
                struct.pack('>H', data_length) +
                data_content +
                struct.pack('>H', checksum) +
                struct.pack('>B', self.PROTOCOL_TAIL)
        )
        # 组装数据包，按协议要求处理转义
        processed_packet = self.escape_packet(packet)
        return processed_packet

    @staticmethod
    def deconstruct_packet(data):
        """
        根据协议解包服务器下发的数据
        :param data: 返回的原数据字节码
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

    def create_register_packet(self, device_type, device_version):
        """根据参数封装注册包字节码"""
        registration_data = struct.pack(">BH", device_type, device_version)    # 协议要求的注册信息
        timestamp = int(time.time())
        packet = self.construct_packet(registration_data, timestamp, command_code='C')
        return packet

    def create_heartbeat_packet(self):
        """按参数封装心跳包"""
        timestamp = int(time.time())
        packet = self.construct_packet(b"", timestamp, command_code='F')     # 心跳包没有任何数据内容
        return packet

    def create_parking_status_packet(self, selected_port, status_values):
        """
        按参数封装车位状态包
        :param selected_port: 车位号
        :param status_values: 车位状态
        :return:
        """
        # 初始化要发送的数据体字节码
        parking_status_data = b''
        # 前6个字节用于填充车位状态
        for idx in range(6):
            if idx == selected_port - 1:
                # 传入的车位号，写入对应状态
                status = status_values
            else:
                # 不开启上报的车位状态默认用9填充，会被服务器过滤
                status = 9
            # 每个状态1字节
            parking_status_data += struct.pack(">B", status)
        # 后6个字节为预留位，填充为9
        parking_status_data += struct.pack(">BBBBBB", 9, 9, 9, 9, 9, 9)
        timestamp = int(time.time())
        packet = self.construct_packet(parking_status_data, timestamp, command_code='S')
        return packet

    def create_all9_parking_status_packet(self):
        """特殊步骤，生成12字节全为9占位的车位状态上报包，用于注册后让服务器识别设备类型"""
        data = struct.pack(">BBBBBBBBBBBB", 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9)
        timestamp = int(time.time())
        packet = self.construct_packet(data, timestamp, command_code='S')
        return packet

    def create_parking_picture_head_packet(self, park_num: int, timestamp, total_packets, image_bytes: bytes, command_code="J",
                                           plate_color: int = 3, plate_number: str = '川ABC123', confidence: int = 900):
        """
        按参数封装软识别模式车位图片头包
        默认所有不使用的字符用9占位，并设置每个车位的状态和端口号
        :param total_packets: 总包数
        :param timestamp: 时间戳
        :param park_num: 车位号
        :param image_bytes: 车位图片二进制数据
        :param command_code: 命令码
        :param confidence: 车牌可信度，用于硬识别，暂不支持，直接填充默认值
        :param plate_number: 车牌号，用于硬识别，暂不支持，直接填充默认值
        :param plate_color: 车牌颜色，用于硬识别，暂不支持，直接填充默认值
        :return:
        """

        # 头包内的车位信息主体
        data_content = b''
        # 有卡/无卡标志位
        #   低4位为6：找车系统主动上传
        #   高4位为0：旧模式(单车牌+车型信息等)
        has_card_flag = struct.pack(">B", 0x06)  # 高4位为0，低4位为6

        # 封装4个车位信息的参数
        for i in range(4):
            """
            此部分不按照现有的协议文档封装
            文档要求固定封装四个车位的数据，但服务器端实际是根据收到的数据长度取不同位置的数据作为通道口数据
            数据长度为65时，取第16byte数据作为通道口，因此直接简单的把所有车位状态都封装为选中车位的车位端口号
            """
            # 车位状态和端口号
            port_with_car = ((park_num & 0x0F) << 4) | 0x01

            # 暂时不支持硬识别，因此硬识别相关参数直接封装默认值
            # 默认车牌颜色【蓝(3)】、车牌号码【川ABC123】，可信度【900】
            plate_number_encoded = plate_number.encode('gbk')

            # 按协议格式封装每个车位的包
            data_content += struct.pack(">B B 11s H", port_with_car, plate_color, plate_number_encoded, confidence)

        # 总图像数据长度
        total_image_length = struct.pack(">I", len(image_bytes))

        # 组装头包（包含有卡/无卡标志位、车位信息和图像数据总长度）
        head_packet = self.construct_packet(
            command_data=has_card_flag + data_content + total_image_length,     # 头包数据：有卡/无卡标志位+4车位信息+总图像数据长度
            command_code=command_code,      # 命令码，J包
            timestamp=timestamp,
            total_packets=total_packets + 1,    # 头包+数据包的包数
            packet_number=0     # 头包为0
        )
        return head_packet

    def create_parking_picture_hard_head_packet(self, park_num: int, timestamp, total_packets, image_bytes: bytes,
                                                plate_color: int, plate_number: str, confidence: int, command_code="J"):
        """
        按参数封装硬识别模式的车位图片头包
        默认所有不使用的字符用9占位，并设置每个车位的状态和端口号
        :param total_packets: 总包数
        :param timestamp: 时间戳
        :param park_num: 车位号
        :param image_bytes: 车位图片二进制数据
        :param command_code: 命令码
        :param confidence: 车牌可信度
        :param plate_number: 车牌号
        :param plate_color: 车牌颜色
        :return:
        """

        # 头包内的车位信息主体
        data_content = b''
        # 有卡/无卡标志位
        #   低4位为6：找车系统主动上传
        #   高4位为0：旧模式(单车牌+车型信息等)
        #   高4位为1：新模式(多车牌)
        #   硬识别模式要求高4位为1
        has_card_flag = struct.pack(">B", 0x16)  # 高4位为1，低4位为6

        # 封装4个车位信息的参数
        for i in range(4):
            """
            此部分不按照现有的协议文档封装
            固定封装四个车位的数据
            直接将第一个设置为硬识别对应的端口和有车状态，其余都为无车
            无车状态的包部分会被服务器过滤，因此车牌等硬识别数据直接用一样的，不做单独处理
            """
            # 转化车位包的第一个字节状态码，高四位为端口号=传进的车位号，第四位为车位状态
            port_with_car = ((park_num & 0x0F) << 4) | 0x01     # 有车包
            port_without_car = ((park_num & 0x0F) << 4) | 0x00  # 无车包

            # 默认车牌颜色【蓝(3)】、车牌号码【川ABC123】，可信度【900】
            plate_number_encoded = plate_number.encode('gbk')

            # 按协议格式封装每个车位的包
            if i == 0:
                data_content += struct.pack(">B B 11s H", port_with_car, plate_color, plate_number_encoded, confidence)
            else:
                data_content += struct.pack(">B B 11s H", port_without_car, plate_color, plate_number_encoded, confidence)

        # 总图像数据长度
        total_image_length = struct.pack(">I", len(image_bytes))

        # 组装头包（包含有卡/无卡标志位、车位信息和图像数据总长度）
        head_packet = self.construct_packet(
            command_data=has_card_flag + data_content + total_image_length,     # 头包数据：有卡/无卡标志位+4车位信息+总图像数据长度
            command_code=command_code,      # 命令码，J包
            timestamp=timestamp,
            total_packets=total_packets + 1,    # 头包+数据包的包数
            packet_number=0     # 头包为0
        )
        return head_packet
