#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/27 13:42
# @Author  : Heshouyi
# @File    : network_lcd_model.py
# @Software: PyCharm
# @description:

import time


class NetworkLcdModel:

    @staticmethod
    def create_heartbeat_packet():
        """
        创建心跳包
        :return:
        """
        packet = {
            "cmd": "heart",
            "reqid": int(time.time() * 1000)     # 毫秒级时间戳
        }
        return packet

    @ staticmethod
    def create_command_response_packet(reqid):
        """
        创建命令响应包
        :param reqid: 接收到的下发指令中的reqid，此处直接复用该标识，方便确定是对哪个指令做回复
        :return:
        """
        packet = {
            "message": "接收到了信息",
            "reqid": reqid
        }
        return packet
