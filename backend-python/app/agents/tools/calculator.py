"""
计算器工具
Calculator Tool

允许 Agent 执行数学计算
Allows Agent to perform mathematical calculations
"""
import logging
import re
from typing import Union

logger = logging.getLogger(__name__)


async def calculator_tool(expression: str) -> Union[float, int, str]:
    """
    计算器工具

    Args:
        expression: 数学表达式（如 "2 + 3 * 4"）

    Returns:
        计算结果
    """
    try:
        # 安全检查：只允许数字、基本运算符和括号
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
            raise ValueError("表达式包含非法字符")

        # 使用 eval 计算表达式（注意：生产环境应使用更安全的方法）
        # 这里添加了限制，只允许特定的数学运算
        allowed_names = {}
        result = eval(expression, {"__builtins__": {}}, allowed_names)

        logger.info(f"计算: {expression} = {result}")
        return result

    except ZeroDivisionError:
        return "错误：除数不能为零"
    except SyntaxError:
        return "错误：表达式语法不正确"
    except ValueError as e:
        return f"错误：{str(e)}"
    except Exception as e:
        logger.error(f"计算失败: {e}")
        return f"计算失败: {str(e)}"
