"""
日期时间工具
DateTime Tool

允许 Agent 获取当前日期和时间
Allows Agent to get current date and time
"""
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def datetime_tool() -> Dict[str, Any]:
    """
    获取当前日期和时间

    Returns:
        包含日期时间信息的字典
    """
    try:
        now = datetime.now()

        return {
            "datetime": now.isoformat(),
            "date": now.date().isoformat(),
            "time": now.time().isoformat(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.weekday(),
            "weekday_name": now.strftime("%A"),
            "timezone": "Asia/Shanghai"
        }

    except Exception as e:
        logger.error(f"获取日期时间失败: {e}")
        return {
            "error": str(e),
            "datetime": None
        }
