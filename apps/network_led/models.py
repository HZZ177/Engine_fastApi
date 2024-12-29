#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/12/29 上午11:53
# @Author  : Heshouyi
# @File    : models.py
# @Software: PyCharm
# @description:

from tortoise import models, fields


class DeviceMessage(models.Model):
    """
    设备信息表
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,  -- 主键id，自增
    device_addr TEXT DEFAULT NULL,                  -- 设备IP地址
    message_source INT DEFAULT NULL,                -- 信息来源 0=未知 1=车位相机 2=通道相机 3=LED网络屏 4=LCD一体屏 5=Lora节点 6=四字节节点
    message TEXT DEFAULT NULL,                      -- 接收的服务器下发指令
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP  -- 创建时间
    """
    id = fields.IntField(pk=True, auto_increment=True, description="主键id")
    device_addr = fields.CharField(max_length=20, null=True, description="设备IP地址")
    message_source = fields.IntField(null=True, description="信息来源 0=未知 1=车位相机 2=通道相机 3=LED网络屏 4=LCD一体屏 5=Lora节点 6=四字节节点")
    message = fields.CharField(max_length=1000, null=True, description="接收的服务器下发指令")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

