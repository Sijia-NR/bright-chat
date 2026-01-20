"""
配置文件
"""
import os
from typing import Optional

class Config:
    # 服务器配置
    HOST = "0.0.0.0"
    PORT = int(os.getenv("MOCK_SERVER_PORT", 18063))

    # 应用配置
    APP_ID = "564866165928038400"
    DEFAULT_APP_KEY = "APP_KEY"

    # 模拟响应延迟（毫秒）
    RESPONSE_DELAY_MIN = 100
    RESPONSE_DELAY_MAX = 1000

    # 流式响应配置
    STREAM_DELAY = 30  # 每个字符的延迟（毫秒）
    STREAM_CHUNK_SIZE = 1  # 每次发送的字符数

    # 支持的模型
    SUPPORTED_MODELS = [
        "BrightChat-General-v1",
        "BrightChat-Pro-v1",
        "BrightChat-Code-v1",
        "SGGM-VL-7B"
    ]

    # 错误消息
    ERROR_MESSAGES = {
        "200001": "请求参数不是标准的JSON格式",
        "200002": "请求参数错误",
        "200003": "必填字段为空",
        "200004": "参数长度超过限制",
        "200005": "参数枚举值无效",
        "300001": "鉴权失败",
        "300002": "权限被拒绝",
        "400001": "服务器内部错误",
        "400002": "远程服务调用失败"
    }