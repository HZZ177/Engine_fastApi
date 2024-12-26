#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/11/10 上午11:54
# @Author  : Heshouyi
# @File    : configer.py.py
# @Software: PyCharm
# @description:

from ruamel.yaml import YAML
from .file_path import dev_config_path, pro_config_path


class Config:

    def __init__(self, config_file):
        self.config = None
        self.yaml = YAML()
        self.config_file = config_file

    def load_config(self):
        with open(self.config_file, 'r', encoding='utf-8') as file:
            self.config = self.yaml.load(file)
        return self.config

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as file:
            self.yaml.dump(self.config, file)

    def update_config(self, key_path, value):
        """
        更新配置文件中的某个值
        :param key_path: 需要更新的键路径（如 "database.host"）
        :param value: 更新的期望值
        :return:
        """
        _config = self.config
        keys = key_path.split('.')
        for key in keys[:-1]:
            _config = _config.setdefault(key, {})
        _config[keys[-1]] = value
        self.save_config()


# dev_config_path / pro_config_path
# 默认使用dev配置文件
configger = Config(dev_config_path)
config = configger.load_config()
