#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:35
# @Author  : Heshouyi
# @File    : lora_node_model.py
# @Software: PyCharm
# @description:


class LoraNodeModel:

    # 车位状态枚举值对应协议数据
    CAR_STATUS_CODES = {
        1: "A",  # 有车正常
        2: "@",  # 无车正常
        3: "C",  # 有车故障
        4: "B",  # 无车故障
    }

    # 故障详情枚举值对应二进制标志位
    FAULT_FLAGS = {
        1: 0x80,  # 传感器故障
        2: 0x40,  # 传感器满偏
        3: 0x20,  # 雷达故障
        4: 0x10,  # 高低温预警
        5: 0x08,  # RTC故障
        6: 0x04,  # 通讯故障
        7: 0x01,  # 电池低压
    }

    @staticmethod
    def construct_status_report_packet(sensor_addr, sensor_status, fault_details):
        """
        构造节点状态上报的数据包
        :param sensor_addr: 车位地址
        :param sensor_status: 车位状态（整数枚举值）
        :param fault_details: 故障详情列表（整数枚举值）
        :return: 构造完成的数据包字符串
        """
        if not isinstance(sensor_addr, int) or sensor_addr <= 0:
            raise ValueError("无效的车位地址")

        # 获取车位状态代码
        car_status_code = LoraNodeModel.CAR_STATUS_CODES.get(sensor_status)
        if not car_status_code:
            raise ValueError(f"无效的探测器状态: {sensor_status}")

        # 合并故障标志位
        zz = 0x00
        for fault_id in fault_details:
            zz |= LoraNodeModel.FAULT_FLAGS.get(fault_id, 0)

        zz_hex = f"{zz:02X}"

        # 拼装地址和状态数据
        node_last_octet = 123  # 这个值没有实际使用，默认占位123
        aaaaa = f"{(node_last_octet << 8 | sensor_addr):05d}"

        # 返回最终数据包
        return f"({aaaaa}{car_status_code}{zz_hex})"
