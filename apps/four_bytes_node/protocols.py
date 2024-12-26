#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/21 22:35
# @Author  : Heshouyi
# @File    : four_bytes_node_model.py
# @Software: PyCharm
# @description:


class FourBytesNodeModel:

    @staticmethod
    def construct_status_report_packet(sensor_addr, sensor_status):
        """
        构造节点状态上报的数据包
        :param sensor_addr: 车位地址
        :param sensor_status: 车位状态
        :return: 构造完成的数据包字符串
        """
        # 探测器地址对应的ASCII编码
        address_char = chr(64 + sensor_addr)  # 根据协议，A对应拨码1，A的ASCII是65，因此统一加64
        # 拼装数据包
        packet = f"({address_char}{sensor_status})"

        return packet
