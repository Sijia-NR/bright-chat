"""
文件操作工具
File Operations Tool

允许 Agent 读写文件（需要限制访问路径）
Allows Agent to read and write files
"""
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# 默认允许的目录（可配置）
DEFAULT_ALLOWED_DIRS = [
    "/tmp",
    "/data1/allresearchProject/Bright-Chat/uploads",
    "/data1/allresearchProject/Bright-Chat/agent_workspace",
]


async def file_tool(
    action: str,
    path: str,
    content: Optional[str] = None,
    allowed_dirs: Optional[list] = None
) -> Dict[str, Any]:
    """
    文件操作工具

    支持的操作：
    - read: 读取文件
    - write: 写入文件
    - list: 列出目录
    - exists: 检查文件是否存在
    - delete: 删除文件

    Args:
        action: 操作类型 (read/write/list/exists/delete)
        path: 文件路径
        content: 文件内容（用于 write）
        allowed_dirs: 允许访问的目录列表

    Returns:
        操作结果
    """
    import time
    start_time = time.time()

    # 设置允许的目录
    if allowed_dirs is None:
        allowed_dirs = DEFAULT_ALLOWED_DIRS

    # 确保工作目录存在
    workspace_dir = "/data1/allresearchProject/Bright-Chat/agent_workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    if workspace_dir not in allowed_dirs:
        allowed_dirs.append(workspace_dir)

    logger.info(f"📁 [文件工具] 操作: {action}")
    logger.info(f"📁 [文件工具] 路径: {path}")

    result = {"success": False, "data": None, "error": None}

    try:
        # 解析路径（支持相对路径）
        file_path = Path(path)

        # 如果是相对路径，相对于工作目录
        if not file_path.is_absolute():
            file_path = Path(workspace_dir) / file_path

        file_path = file_path.resolve()

        # 安全检查：确保路径在允许的目录内
        is_allowed = False
        for allowed_dir in allowed_dirs:
            allowed_path = Path(allowed_dir).resolve()
            try:
                file_path.relative_to(allowed_path)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            result["error"] = f"访问被拒绝：路径不在允许的目录内"
            logger.warning(f"📁 [文件工具] {result['error']}: {file_path}")
            return result

        # 执行操作
        if action == "read":
            # 读取文件
            if not file_path.exists():
                result["error"] = "文件不存在"
                return result

            if not file_path.is_file():
                result["error"] = "路径不是文件"
                return result

            content_text = file_path.read_text(encoding='utf-8')
            result["success"] = True
            result["data"] = {
                "path": str(file_path),
                "content": content_text,
                "size": len(content_text)
            }

        elif action == "write":
            # 写入文件
            if content is None:
                result["error"] = "缺少内容参数"
                return result

            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            file_path.write_text(content, encoding='utf-8')
            result["success"] = True
            result["data"] = {
                "path": str(file_path),
                "size": len(content)
            }

        elif action == "list":
            # 列出目录
            if not file_path.exists():
                result["error"] = "目录不存在"
                return result

            if not file_path.is_dir():
                result["error"] = "路径不是目录"
                return result

            items = []
            for item in file_path.iterdir():
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })

            result["success"] = True
            result["data"] = {
                "path": str(file_path),
                "items": items,
                "count": len(items)
            }

        elif action == "exists":
            # 检查文件是否存在
            result["success"] = True
            result["data"] = {
                "path": str(file_path),
                "exists": file_path.exists(),
                "type": "directory" if file_path.is_dir() else "file" if file_path.is_file() else "other"
            }

        elif action == "delete":
            # 删除文件
            if not file_path.exists():
                result["error"] = "文件不存在"
                return result

            if file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
            else:
                file_path.unlink()

            result["success"] = True
            result["data"] = {"path": str(file_path), "deleted": True}

        else:
            result["error"] = f"不支持的操作: {action}"
            return result

        execution_time = time.time() - start_time
        logger.info(f"✅ [文件工具] 操作完成，耗时: {execution_time:.3f}秒")

        return result

    except Exception as e:
        error_msg = f"文件操作失败: {str(e)}"
        logger.error(f"❌ [文件工具] {error_msg}")
        return {"success": False, "error": error_msg, "data": None}


async def create_file(filename: str, content: str, directory: Optional[str] = None) -> Dict[str, Any]:
    """
    创建文件的便捷方法

    Args:
        filename: 文件名
        content: 文件内容
        directory: 目录（可选，默认为工作目录）

    Returns:
        操作结果
    """
    workspace_dir = directory or "/data1/allresearchProject/Bright-Chat/agent_workspace"

    if not filename.startswith("/"):
        full_path = f"{workspace_dir}/{filename}"
    else:
        full_path = filename

    return await file_tool(action="write", path=full_path, content=content)


async def read_file(filename: str, directory: Optional[str] = None) -> Dict[str, Any]:
    """
    读取文件的便捷方法

    Args:
        filename: 文件名
        directory: 目录（可选，默认为工作目录）

    Returns:
        操作结果
    """
    workspace_dir = directory or "/data1/allresearchProject/Bright-Chat/agent_workspace"

    if not filename.startswith("/"):
        full_path = f"{workspace_dir}/{filename}"
    else:
        full_path = filename

    return await file_tool(action="read", path=full_path)
