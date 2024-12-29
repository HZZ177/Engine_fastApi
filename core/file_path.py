#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/9 下午7:21
# @Author  : Heshouyi
# @File    : file_path.py
# @Software: PyCharm
# @description:

import os
# from core.logger import logger

'''项目目录'''
# 项目根目录，指向device_simulation_engine
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

'''一级目录'''
apps_path = os.path.abspath(os.path.join(project_path, 'apps'))     # app根目录
core_path = os.path.abspath(os.path.join(project_path, 'core'))     # core目录
sqlite_path = os.path.abspath(os.path.join(project_path, 'SQlite'))     # SQlite数据库目录
log_path = os.path.abspath(os.path.join(project_path, 'logs'))      # 日志目录
static_path = os.path.abspath(os.path.join(project_path, 'static'))     # 资源目录

'''二级目录'''
dev_config_path = os.path.abspath(os.path.join(core_path, 'config_dev.yml'))     # 开发环境配置文件
pro_config_path = os.path.abspath(os.path.join(core_path, 'config_pro.yml'))     # 正式环境配置文件
db_path = os.path.abspath(os.path.join(sqlite_path, 'findcar_automation.db'))

# # 检测数据库跟路径是否存在，不存在则创建一个空路径
# if not os.path.exists(sqlite_path):
#     try:
#         os.makedirs(sqlite_path)
#         logger.info(f"数据库路径不存在，创建成功！")
#     except Exception as e:
#         logger.error(f"创建数据库路径失败：{e}")
#         raise e


if __name__ == '__main__':
    print(project_path)
    # pass
