#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/1/2 11:07
# @Author  : Heshouyi
# @File    : services.py
# @Software: PyCharm
# @description:
from tortoise.expressions import Q

from apps.models import UpperReportRecordModel
from core.logger import logger


class FindcarReportService:

    @staticmethod
    async def store_received_message(source, command_data):
        """
        将接收到的上报信息写入数据库
        :param source: 数据来源，1：单车场 2：统一平台
        :param command_data: 接收的寻车上行数据
        :return: None
        """
        message_type = command_data.get("cmd")  # 单车场接口应该都有，可能为空，获取不到就存None
        # 规范格式，json中的单引号转换成双引号，方便后续使用
        command_data = str(command_data).replace("'", '"')

        try:
            await UpperReportRecordModel.create(
                source=source, message_type=message_type, message=command_data
            )
            logger.info("接收到的寻车上报数据入库成功")
        except Exception as e:
            raise e

    @staticmethod
    async def get_db_history_report(page_no, page_size, source):
        """从数据库中获取寻车上报记录"""
        try:
            # 等效于：
            # SELECT *
            # FROM upper_report_record
            # WHERE (source = {source} OR {source} IS NULL)
            # ORDER BY create_time DESC
            # LIMIT {page_size} OFFSET {offset};
            if source:
                result = await (
                    UpperReportRecordModel.filter(source=source).
                    order_by("-create_time")
                    .offset((page_no - 1) * page_size)
                    .limit(page_size)
                    .values()
                )
            else:
                result = await (
                    UpperReportRecordModel.all()
                    .order_by("-create_time")
                    .offset((page_no - 1) * page_size)
                    .limit(page_size)
                    .values()
                )
            return result
        except Exception as e:
            raise e
