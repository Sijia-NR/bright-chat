"""
主应用入口
"""
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
import json
import logging
import traceback
from typing import Optional
from datetime import datetime

from models import *
from utils import validate_auth_header, create_error_response, validate_chat_request
from responses import MockResponseGenerator
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bright-Chat Mock Server",
    description="大模型智能应用服务模拟服务",
    version="1.0.0"
)

# 初始化响应生成器
response_generator = MockResponseGenerator()

@app.middleware("http")
async def add_cors_middleware(request: Request, call_next):
    """添加CORS中间件"""
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.options("/{path:path}")
async def options_handler():
    """处理OPTIONS请求"""
    return {}

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Bright-Chat Mock Server",
        "version": "1.0.0",
        "endpoints": {
            "语义大模型": "/lmp-cloud-ias-server/api/llm/chat/completions",
            "语义大模型V2": "/lmp-cloud-ias-server/api/llm/chat/completions/V2",
            "视觉大模型": "/lmp-cloud-ias-server/api/lvm/completions",
            "多模态大模型": "/lmp-cloud-ias-server/api/vlm/chat/completions",
            "多模态大模型V2": "/lmp-cloud-ias-server/api/vlm/chat/completions/V2"
        }
    }

@app.post("/lmp-cloud-ias-server/api/llm/chat/completions")
async def chat_completions(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """语义大模型服务接口"""
    start_time = datetime.now()
    request_id = f"req_{start_time.strftime('%Y%m%d%H%M%S%f')}"

    logger.info(f"[{request_id}] ========== 新请求开始 ==========")
    logger.info(f"[{request_id}] 请求路径: {request.url.path}")
    logger.info(f"[{request_id}] 请求方法: {request.method}")
    logger.info(f"[{request_id}] Authorization头: {authorization[:20]}..." if authorization else f"[{request_id}] Authorization头: (空)")

    # 验证鉴权
    logger.info(f"[{request_id}] 步骤1: 验证鉴权")
    if not validate_auth_header(authorization):
        logger.error(f"[{request_id}] 鉴权失败: Authorization头无效")
        logger.info(f"[{request_id}] ========== 请求结束 (401) ==========")
        raise HTTPException(status_code=401, detail=create_error_response("300001"))
    logger.info(f"[{request_id}] 鉴权验证通过")

    try:
        # 解析请求体
        logger.info(f"[{request_id}] 步骤2: 解析请求体")
        try:
            body = await request.json()
            logger.info(f"[{request_id}] 请求体解析成功")
            logger.info(f"[{request_id}] 模型: {body.get('model', '(未指定)')}")
            logger.info(f"[{request_id}] 流式: {body.get('stream', False)}")
            logger.info(f"[{request_id}] 消息数量: {len(body.get('messages', []))}")
            if body.get('messages'):
                user_msg = ""
                for msg in reversed(body['messages']):
                    if msg.get('role') == 'user':
                        user_msg = msg.get('content', '')
                        break
                logger.info(f"[{request_id}] 用户消息: {user_msg[:100]}{'...' if len(user_msg) > 100 else ''}")
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] JSON解析失败: {str(e)}")
            logger.error(f"[{request_id}] JSON解析失败位置: main.py:chat_completions - await request.json()")
            logger.info(f"[{request_id}] ========== 请求结束 (400) ==========")
            raise HTTPException(status_code=400, detail=create_error_response("200001"))

        # 验证请求
        logger.info(f"[{request_id}] 步骤3: 验证请求格式")
        logger.info(f"[{body}]")
        is_valid, error_code = validate_chat_request(body)
        if not is_valid:
            logger.error(f"[{request_id}] 请求验证失败: 错误码 {error_code}")
            logger.error(f"[{request_id}] 验证失败位置: main.py:chat_completions - validate_chat_request()")
            logger.info(f"[{request_id}] ========== 请求结束 (400) ==========")
            raise HTTPException(status_code=400, detail=create_error_response(error_code))
        logger.info(f"[{request_id}] 请求格式验证通过")

        # 生成响应
        logger.info(f"[{request_id}] 步骤4: 生成响应")
        is_stream = body.get("stream", False)
        logger.info(f"[{request_id}] 响应模式: {'流式' if is_stream else '非流式'}")

        try:
            response = response_generator.generate_semantic_response(body, is_stream)
            logger.info(f"[{request_id}] 响应生成成功")
        except Exception as e:
            logger.error(f"[{request_id}] 响应生成失败: {str(e)}")
            logger.error(f"[{request_id}] 响应生成失败位置: main.py:chat_completions - generate_semantic_response()")
            logger.error(f"[{request_id}] 错误堆栈:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=create_error_response("400002", str(e)))

        # 返回响应
        logger.info(f"[{request_id}] 步骤5: 返回响应")
        if is_stream:
            logger.info(f"[{request_id}] 返回流式响应")
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{request_id}] 请求处理耗时: {elapsed:.3f}秒")
            logger.info(f"[{request_id}] ========== 请求结束 (200 - 流式) ==========")
            return StreamingResponse(
                response,
                media_type="text/event-stream;charset=utf-8"
            )
        else:
            logger.info(f"[{request_id}] 返回非流式响应")
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{request_id}] 请求处理耗时: {elapsed:.3f}秒")
            logger.info(f"[{request_id}] ========== 请求结束 (200 - 非流式) ==========")
            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 未捕获的异常: {str(e)}")
        logger.error(f"[{request_id}] 异常位置: main.py:chat_completions")
        logger.error(f"[{request_id}] 错误堆栈:\n{traceback.format_exc()}")
        logger.info(f"[{request_id}] ========== 请求结束 (500) ==========")
        raise HTTPException(status_code=500, detail=create_error_response("400001", str(e)))

@app.post("/lmp-cloud-ias-server/api/llm/chat/completions/V2")
async def chat_completions_v2(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """语义大模型服务接口V2版本"""
    # V2版本与原接口相同，只是流式响应格式不同
    return await chat_completions(request, authorization)

@app.post("/lmp-cloud-ias-server/api/lvm/completions")
async def vision_completions(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """视觉大模型服务接口"""
    # 验证鉴权
    if not validate_auth_header(authorization):
        raise HTTPException(status_code=401, detail=create_error_response("300001"))

    try:
        # 解析请求体
        body = await request.json()

        # 简单验证
        if "data" not in body or "model" not in body:
            raise HTTPException(status_code=400, detail=create_error_response("200003"))

        # 生成响应
        response = response_generator.generate_vision_response(body)
        return response

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=create_error_response("200001"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_error_response("400001", str(e)))

@app.post("/lmp-cloud-ias-server/api/vlm/chat/completions")
async def multimodal_chat_completions(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """多模态大模型服务接口"""
    # 验证鉴权
    if not validate_auth_header(authorization):
        raise HTTPException(status_code=401, detail=create_error_response("300001"))

    try:
        # 解析请求体
        body = await request.json()

        # 验证请求
        if "model" not in body or "messages" not in body:
            raise HTTPException(status_code=400, detail=create_error_response("200003"))

        # 生成响应
        is_stream = body.get("stream", False)
        response = response_generator.generate_multimodal_response(body, is_stream)

        # 返回响应
        if is_stream:
            return StreamingResponse(
                response,
                media_type="text/event-stream;charset=utf-8"
            )
        else:
            return response

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=create_error_response("200001"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_error_response("400001", str(e)))

@app.post("/lmp-cloud-ias-server/api/vlm/chat/completions/V2")
async def multimodal_chat_completions_v2(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """多模态大模型服务接口V2版本"""
    # V2版本与原接口相同，只是流式响应格式不同
    return await multimodal_chat_completions(request, authorization)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level="info"
    )