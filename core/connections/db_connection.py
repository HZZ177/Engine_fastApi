#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/26 10:48
# @Author  : Heshouyi
# @File    : db_connection.py
# @Software: PyCharm
# @description:

import sqlite3
from core.logger import logger


class DBConnection:
    def __init__(self, db_path: str):
        """
        初始化数据库连接对象
        :param db_path: 数据库文件的路径
        """
        # 初始化数据库
        self.db_path = db_path
        self.connection = None

    def __enter__(self):
        """
        上下文管理器，在进入上下文时自动连接数据库，退出时自动关闭连接，从而支持with用法
        :return:
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        退出上下文时自动关闭数据库连接，从而支持with用法
        :param exc_type: 异常类型：如果with中发生了异常，此处是异常的类型，例如ValueError；如果没有异常，则此参数为None
        :param exc_value: 异常实例：如果with中发生了异常，此处是异常的具体实例，包含异常信息；如果没有异常，则此参数为None
        :param traceback: 回溯信息：如果with中发生了异常，此处是一个traceback对象，是异常的调用栈信息；如果没有异常则此参数为None
        :return:
        """
        self.close()

    def init(self):
        """
        引擎初始化时需要调用一次
        尝试创建表，已存在则忽略，兼容多环境初次运行没有表结构的问题
        :return:
        """
        # 设备接收下发消息表
        device_message_sql = """
CREATE TABLE IF NOT EXISTS device_message (         -- 设备接收下发消息表
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,  -- 主键id，自增
    device_addr TEXT DEFAULT NULL,                  -- 设备IP地址
    message_source INT DEFAULT NULL,                -- 信息来源 0=未知 1=车位相机 2=通道相机 3=LED网络屏 4=LCD一体屏 5=Lora节点 6=四字节节点
    message TEXT DEFAULT NULL,                      -- 接收的服务器下发指令
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP  -- 创建时间
);
        """
        self.execute(device_message_sql)

        # 接收单车场/统一平台上行记录表
        report_record_sql = """
CREATE TABLE IF NOT EXISTS upper_report_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,  -- 主键id
    source INTEGER DEFAULT NULL,           -- 信息来源 1：单车场上报 2：统一平台上报 3：未知
    message_type TEXT DEFAULT NULL,        -- 上报类型
    message TEXT DEFAULT NULL,             -- 上报内容
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP      -- 创建时间
);
        """
        self.execute(report_record_sql)

        # 由于sqlite是库级锁，读取和写入会互相阻塞
        # 启用wal模式，支持同时可以读取和写入，提升性能
        # 可以通过执行"PRAGMA journal_mode=DELETE;"关闭
        self.execute("PRAGMA journal_mode=WAL;")

    def connect(self):
        """
        建立数据库连接
        """
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
        return self.connection

    def close(self):
        """
        关闭数据库连接
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, query: str, params: tuple = None):
        """
        执行SQL语句
        :param query: SQL语句
        :param params: 参数（可选）
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor

    def fetchall(self, query: str, params: tuple = None):
        """
        执SQL并返回所有结果
        :param query: SQL语句
        :param params: 参数（可选）
        :return: 查询结果 list(tuple)
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def fetchone(self, query: str, params: tuple = None):
        """
        执行SQL并返回单条结果
        :param query: SQL语句
        :param params: 参数（可选）
        :return: 查询结果 tuple
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall_as_dict(self, query: str, params: tuple = None):
        """
        查询数据库，拼接上字段名称并以字典形式返回
        :param query: SQL查询语句
        :param params: 查询参数（可选）
        :return: list[dict] 包含字段名的字典列表
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # 获取字段名，cursor.description可以动态获取所有查询的字段名
            columns = [desc[0] for desc in cursor.description]
            # 获取所有查询结果
            results = []
            rows = cursor.fetchall()  # 获取所有结果
            # 拼接字段名称和查询结果转换为字典列表
            for row in rows:
                result_dict = {}  # 用于存储每一行的字典
                for i, column_name in enumerate(columns):  # 遍历字段名和索引
                    result_dict[column_name] = row[i]  # 根据索引赋值
                results.append(result_dict)  # 将字典添加到结果列表中
            return results
