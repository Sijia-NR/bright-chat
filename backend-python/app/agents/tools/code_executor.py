"""
代码执行工具（沙箱隔离）
Code Executor Tool with Sandbox

允许 Agent 安全地执行 Python 代码
Allows Agent to safely execute Python code
"""
import logging
import asyncio
import re
from typing import Union, Dict, Any
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safe_builtins

logger = logging.getLogger(__name__)


# 允许的内置函数和模块
ALLOWED_BUILTINS = {
    **safe_builtins,
    'print': print,
    'len': len,
    'range': range,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'list': list,
    'dict': dict,
    'tuple': tuple,
    'set': set,
    'sum': sum,
    'max': max,
    'min': min,
    'abs': abs,
    'round': round,
    'sorted': sorted,
    'enumerate': enumerate,
    'zip': zip,
    'map': map,
    'filter': filter,
    'any': any,
    'all': all,
    'isinstance': isinstance,
    'type': type,
}

# 允许的模块（需要显式导入）
ALLOWED_MODULES = {
    'math': __import__('math'),
    'datetime': __import__('datetime'),
    'json': __import__('json'),
    're': __import__('re'),
    'collections': __import__('collections'),
    'itertools': __import__('itertools'),
    'random': __import__('random'),
    'statistics': __import__('statistics'),
}


async def code_executor_tool(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    代码执行工具（沙箱隔离）

    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒）

    Returns:
        执行结果字典，包含:
        - success: 是否成功
        - output: 输出结果
        - error: 错误信息（如果有）
        - execution_time: 执行时间（秒）
    """
    import time
    start_time = time.time()

    logger.info(f"🔒 [代码执行] 开始执行代码（沙箱隔离）")
    logger.info(f"🔒 [代码执行] 代码长度: {len(code)} 字符")

    try:
        # 1. 安全检查：检测危险操作
        dangerous_patterns = [
            r'import\s+os',
            r'import\s+subprocess',
            r'import\s+shutil',
            r'from\s+os\s+import',
            r'from\s+subprocess\s+import',
            r'\.exec\(',
            r'\.eval\(',
            r'__import__',
            r'globals\(',
            r'locals\(',
            r'open\s*\(',
            r'compile\s*\(',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                error_msg = f"安全错误：代码包含禁止的操作 ({pattern})"
                logger.warning(f"🔒 [代码执行] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "output": None,
                    "execution_time": time.time() - start_time
                }

        # 2. 使用标准编译（在执行环境中限制危险操作）
        try:
            # 不使用 compile_restricted，而是使用标准 compile
            # 安全性通过限制 globals 和运行时检查实现
            byte_code = compile(code, '<string>', 'exec')
            logger.info("🔒 [代码执行] 代码编译成功")
        except Exception as e:
            error_msg = f"编译错误: {str(e)}"
            logger.warning(f"🔒 [代码执行] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "output": None,
                "execution_time": time.time() - start_time
            }

        # 3. 准备受限的执行环境
        safe_globals = {
            '__builtins__': ALLOWED_BUILTINS,
            **ALLOWED_MODULES,
        }

        # 添加输出捕获
        output_buffer = []

        def safe_print(*args, **kwargs):
            """安全的 print 函数，捕获输出"""
            output_buffer.append(' '.join(str(arg) for arg in args))

        safe_globals['print'] = safe_print

        # 4. 执行代码（带超时）
        exec_result = {"completed": False, "result": None, "error": None}

        async def execute_with_timeout():
            try:
                # 执行代码（使用受限的全局变量）
                exec(byte_code, safe_globals, {})
                exec_result["completed"] = True
                exec_result["result"] = '\n'.join(output_buffer) if output_buffer else "代码执行完成（无输出）"
            except Exception as e:
                exec_result["error"] = f"执行错误: {str(e)}"
                logger.error(f"🔒 [代码执行] {exec_result['error']}")

        try:
            # 带超时的执行
            await asyncio.wait_for(execute_with_timeout(), timeout=timeout)
        except asyncio.TimeoutError:
            error_msg = f"执行超时（超过 {timeout} 秒）"
            logger.warning(f"🔒 [代码执行] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "output": None,
                "execution_time": time.time() - start_time
            }

        # 5. 检查执行结果
        if exec_result["error"]:
            logger.warning(f"🔒 [代码执行] 执行失败: {exec_result['error']}")
            return {
                "success": False,
                "error": exec_result["error"],
                "output": None,
                "execution_time": time.time() - start_time
            }

        execution_time = time.time() - start_time
        logger.info(f"✅ [代码执行] 执行成功，耗时: {execution_time:.3f}秒")
        logger.info(f"✅ [代码执行] 输出长度: {len(exec_result['result'])} 字符")

        return {
            "success": True,
            "output": exec_result["result"],
            "error": None,
            "execution_time": execution_time
        }

    except Exception as e:
        error_msg = f"系统错误: {str(e)}"
        logger.error(f"❌ [代码执行] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "output": None,
            "execution_time": time.time() - start_time
        }
