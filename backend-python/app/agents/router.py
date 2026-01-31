"""
Agent API 路由
Agent API Router

提供 Agent 管理、Agent 聊天等 API 端点
Provides API endpoints for Agent management and Agent chat
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db, get_db_session
from ..core.security import get_current_user_id
from ..models.user import User
from ..models.agent import (
    Agent,
    AgentExecution,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentChatRequest,
    AgentExecutionResponse,
    AgentListResponse,
    AgentExecutionListResponse,
    APIResponse,
    PREDEFINED_TOOLS,
)
from ..models.llm_model import LLMModel
from .agent_service import get_agent_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== 依赖函数 ====================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """从 JWT token 获取当前用户"""
    from fastapi import status

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]
    try:
        user_id = get_current_user_id(token)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== 辅助函数 ====================

def _enhance_agent_response(agent: Agent, db: Session) -> dict:
    """增强 Agent 响应，添加 LLM 模型名称"""
    agent_dict = {
        "id": agent.id,
        "name": agent.name,
        "display_name": agent.display_name,
        "description": agent.description,
        "agent_type": agent.agent_type,
        "system_prompt": agent.system_prompt,
        "knowledge_base_ids": agent.knowledge_base_ids,
        "tools": agent.tools,
        "config": agent.config,
        "llm_model_id": agent.llm_model_id,
        "llm_model_name": None,
        "enable_knowledge": agent.enable_knowledge if hasattr(agent, 'enable_knowledge') else True,
        "order": agent.order if hasattr(agent, 'order') else 0,
        "is_active": agent.is_active,
        "created_by": agent.created_by,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
    }

    # 查询 LLM 模型名称
    if agent.llm_model_id:
        llm_model = db.query(LLMModel).filter(LLMModel.id == agent.llm_model_id).first()
        if llm_model:
            agent_dict["llm_model_name"] = llm_model.display_name

    return agent_dict


# ==================== Agent 管理 API ====================

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建 Agent"""
    try:
        # 验证工具列表
        if agent_data.tools:
            available_tools = [tool.name for tool in PREDEFINED_TOOLS]
            invalid_tools = set(agent_data.tools) - set(available_tools)

            if invalid_tools:
                # 创建工具映射建议
                tool_mapping = {
                    "database_query": "knowledge_search",
                    "web_search": "browser",
                    "code_interpreter": "code_executor"
                }

                suggestions = []
                for invalid_tool in invalid_tools:
                    if invalid_tool in tool_mapping:
                        suggested = tool_mapping[invalid_tool]
                        suggestions.append(f"  • '{invalid_tool}' → 建议使用 '{suggested}'")
                    else:
                        suggestions.append(f"  • '{invalid_tool}' → 暂不支持")

                # 构建友好的错误消息
                error_msg = f"不支持的工具: {', '.join(invalid_tools)}\n\n"
                error_msg += f"当前支持的工具:\n"
                for tool in PREDEFINED_TOOLS:
                    error_msg += f"  • {tool.name} - {tool.display_name}\n"

                if suggestions:
                    error_msg += f"\n建议:\n"
                    error_msg += "\n".join(suggestions)

                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )

        # 验证 llm_model_id 是否存在
        if agent_data.llm_model_id:
            llm_model = db.query(LLMModel).filter(LLMModel.id == agent_data.llm_model_id).first()
            if not llm_model:
                raise HTTPException(status_code=400, detail="指定的 LLM 模型不存在")

        # 获取下一个 order 值（如果未指定）
        order = agent_data.order
        if order is None:
            max_order = db.query(func.coalesce(func.max(Agent.order), -1)).scalar()
            order = max_order + 1

        agent = Agent(
            name=agent_data.name,
            display_name=agent_data.display_name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            system_prompt=agent_data.system_prompt,
            knowledge_base_ids=agent_data.knowledge_base_ids,
            tools=agent_data.tools,
            config=agent_data.config,
            llm_model_id=agent_data.llm_model_id,
            enable_knowledge=agent_data.enable_knowledge,
            order=order,
            created_by=current_user.id
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return _enhance_agent_response(agent, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建 Agent 失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20,
    agent_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
    """列出所有 Agent（支持分页、过滤、搜索）"""
    try:
        # 验证分页参数
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        # 构建查询
        query = db.query(Agent)

        # 非管理员只能看到激活的 Agent
        if current_user.role.value != "admin":
            query = query.filter(Agent.is_active == True)
        elif is_active is not None:
            query = query.filter(Agent.is_active == is_active)

        # 按 agent_type 过滤
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)

        # 搜索功能（匹配 name 或 display_name）
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Agent.name.like(search_pattern)) | (Agent.display_name.like(search_pattern))
            )

        # 获取总数
        total = query.count()

        # 按 order 排序，然后分页
        query = query.order_by(Agent.order.asc(), Agent.created_at.desc())
        agents = query.offset((page - 1) * limit).limit(limit).all()

        # 增强 Agent 响应（添加 llm_model_name）
        enhanced_agents = [_enhance_agent_response(agent, db) for agent in agents]

        has_more = (page * limit) < total

        return AgentListResponse(
            agents=enhanced_agents,
            total=total,
            page=page,
            limit=limit,
            has_more=has_more
        )
    except Exception as e:
        logger.error(f"获取 Agent 列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_available_tools():
    """列出所有可用的工具"""
    return {
        "tools": [
            {
                "name": tool.name,
                "display_name": tool.display_name,
                "description": tool.description,
                "category": tool.category,
                "parameters": tool.parameters
            }
            for tool in PREDEFINED_TOOLS
        ]
    }


@router.get("/service-health")
async def health_check():
    """Agent 服务健康检查"""
    try:
        agent_service = get_agent_service()
        tool_count = len(agent_service.tools)

        return {
            "status": "healthy",
            "tools_registered": tool_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取 Agent 详情"""
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        return _enhance_agent_response(agent, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 Agent 详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新 Agent"""
    try:
        # 只有管理员可以更新 Agent
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="无权限更新 Agent")

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        # 验证工具列表
        if agent_data.tools:
            available_tools = [tool.name for tool in PREDEFINED_TOOLS]
            invalid_tools = set(agent_data.tools) - set(available_tools)

            if invalid_tools:
                # 创建工具映射建议
                tool_mapping = {
                    "database_query": "knowledge_search",
                    "web_search": "browser",
                    "code_interpreter": "code_executor"
                }

                suggestions = []
                for invalid_tool in invalid_tools:
                    if invalid_tool in tool_mapping:
                        suggested = tool_mapping[invalid_tool]
                        suggestions.append(f"  • '{invalid_tool}' → 建议使用 '{suggested}'")
                    else:
                        suggestions.append(f"  • '{invalid_tool}' → 暂不支持")

                # 构建友好的错误消息
                error_msg = f"不支持的工具: {', '.join(invalid_tools)}\n\n"
                error_msg += f"当前支持的工具:\n"
                for tool in PREDEFINED_TOOLS:
                    error_msg += f"  • {tool.name} - {tool.display_name}\n"

                if suggestions:
                    error_msg += f"\n建议:\n"
                    error_msg += "\n".join(suggestions)

                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )

        # 验证 llm_model_id 是否存在
        if agent_data.llm_model_id:
            llm_model = db.query(LLMModel).filter(LLMModel.id == agent_data.llm_model_id).first()
            if not llm_model:
                raise HTTPException(status_code=400, detail="指定的 LLM 模型不存在")

        # 更新字段
        if agent_data.name is not None:
            agent.name = agent_data.name
        if agent_data.display_name is not None:
            agent.display_name = agent_data.display_name
        if agent_data.description is not None:
            agent.description = agent_data.description
        if agent_data.system_prompt is not None:
            agent.system_prompt = agent_data.system_prompt
        if agent_data.knowledge_base_ids is not None:
            agent.knowledge_base_ids = agent_data.knowledge_base_ids
        if agent_data.tools is not None:
            agent.tools = agent_data.tools
        if agent_data.config is not None:
            agent.config = agent_data.config
        if agent_data.llm_model_id is not None:
            agent.llm_model_id = agent_data.llm_model_id
        if agent_data.enable_knowledge is not None:
            agent.enable_knowledge = agent_data.enable_knowledge
        if agent_data.order is not None:
            agent.order = agent_data.order
        if agent_data.is_active is not None:
            agent.is_active = agent_data.is_active

        db.commit()
        db.refresh(agent)
        return _enhance_agent_response(agent, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 Agent 失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除 Agent"""
    try:
        # 只有管理员可以删除 Agent
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="无权限删除 Agent")

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        db.delete(agent)
        db.commit()
        return {"message": "Agent 删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 Agent 失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent 聊天 API ====================

@router.post("/{agent_id}/chat")
async def agent_chat(
    agent_id: str,
    request_obj: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agent 聊天（流式输出）"""
    execution = None
    execution_id = None

    try:
        # 获取 Agent
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.is_active == True
        ).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在或未激活")

        logger.info("=" * 80)
        logger.info(f"[Agent 聊天开始] Agent: {agent.display_name} ({agent.id})")
        logger.info(f"[Agent 聊天开始] 用户: {current_user.username} ({current_user.id})")
        logger.info(f"[Agent 聊天开始] 会话ID: {request_obj.session_id}")
        logger.info(f"[Agent 聊天开始] 查询: {request_obj.query}")
        logger.info(f"[Agent 聊天开始] Agent类型: {agent.agent_type}")
        logger.info(f"[Agent 聊天开始] 可用工具: {agent.tools or []}")
        logger.info(f"[Agent 聊天开始] 知识库: {agent.knowledge_base_ids or []}")
        logger.info("=" * 80)

        # 获取 Agent 服务
        agent_service = get_agent_service()

        # ✅ 创建执行记录（用于跟踪中断）
        from ..models.agent import AgentExecution, EXECUTION_STATUS_RUNNING
        import uuid

        execution_id = str(uuid.uuid4())
        execution = AgentExecution(
            id=execution_id,
            agent_id=agent_id,
            user_id=current_user.id,
            session_id=request_obj.session_id,
            input_prompt=request_obj.query,
            status=EXECUTION_STATUS_RUNNING
        )
        db.add(execution)
        db.commit()
        logger.info(f"✅ [数据库] 执行记录已创建: {execution_id}")

        # ✅ 获取原始 request 对象以检测断开连接
        from starlette.requests import Request
        request_obj_scope = request_obj

        # 流式输出
        async def generate():
            nonlocal execution, execution_id
            client_disconnected = False

            try:
                step_count = 0
                start_time = datetime.now()

                async for event in agent_service.execute(
                    agent=agent,
                    query=request_obj.query,
                    user_id=current_user.id,
                    session_id=request_obj.session_id,
                    runtime_knowledge_base_ids=request_obj.knowledge_base_ids,  # 运行时选择的知识库
                    message_id=request_obj.message_id  # 前端传入的用户消息ID
                ):
                    event_type = event.get("type")

                    # ✅ 检查客户端是否断开连接
                    # 注意：这里无法直接访问 request 对象，需要通过其他方式
                    # 我们将在 agent_service.execute 内部处理

                    # 记录每个事件
                    if event_type == "start":
                        logger.info(f"🚀 [Agent 执行开始] 执行ID: {event.get('execution_id')}")

                    elif event_type == "step":
                        step_count += 1
                        node = event.get("node")
                        step = event.get("step")
                        logger.info(f"📍 [步骤 {step_count}] 节点: {node} | 第 {step} 步")

                        # 记录详细状态
                        state = event.get("state", {})
                        if "error" in state and state["error"]:
                            logger.warning(f"⚠️  [步骤 {step_count}] 错误: {state['error']}")
                        elif "input" in state:
                            logger.info(f"📝 [步骤 {step_count}] 输入: {state['input'][:100]}...")
                        elif "output" in state and state["output"]:
                            logger.info(f"✅ [步骤 {step_count}] 输出: {state['output'][:100]}...")

                    elif event_type == "tool_call":
                        tool = event.get("tool")
                        parameters = event.get("parameters", {})
                        result = event.get("result", "")
                        logger.info(f"🔧 [工具调用] 工具: {tool}")
                        logger.info(f"🔧 [工具调用] 参数: {parameters}")
                        logger.info(f"🔧 [工具调用] 结果: {str(result)[:200]}...")

                    elif event_type == "complete":
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        steps = event.get("steps", 0)
                        output = event.get("output", "")

                        logger.info("=" * 80)
                        logger.info(f"✅ [Agent 执行完成] 总步骤: {steps}")
                        logger.info(f"✅ [Agent 执行完成] 执行时间: {duration:.2f}秒")
                        logger.info(f"✅ [Agent 执行完成] 最终输出: {output[:200]}...")
                        logger.info("=" * 80)

                        # ✅ 更新执行记录为完成状态
                        execution.status = "completed"
                        execution.steps = steps
                        execution.result = output
                        execution.completed_at = datetime.now()
                        db.commit()
                        logger.info(f"✅ [数据库] 执行记录已更新为完成状态")

                    elif event_type == "error":
                        logger.error("=" * 80)
                        logger.error(f"❌ [Agent 执行错误] 错误: {event.get('error')}")
                        logger.error("=" * 80)

                        # ✅ 更新执行记录为失败状态
                        execution.status = "failed"
                        execution.error_message = event.get('error', 'Unknown error')
                        execution.completed_at = datetime.now()
                        db.commit()
                        logger.info(f"✅ [数据库] 执行记录已更新为失败状态")

                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                yield "data: [DONE]\n\n"

            except asyncio.CancelledError:
                # ✅ 客户端断开连接，回滚状态
                logger.warning("=" * 80)
                logger.warning(f"⚠️  [客户端断开] execution_id={execution_id}")
                logger.warning(f"⚠️  [客户端断开] Agent: {agent.display_name}")
                logger.warning(f"⚠️  [客户端断开] 查询: {request_obj.query}")
                logger.warning("=" * 80)

                # 回滚执行记录状态
                if execution:
                    execution.status = "failed"
                    execution.error_message = "客户端断开连接（流传输中断）"
                    execution.completed_at = datetime.now()
                    db.commit()
                    logger.info(f"✅ [数据库] 执行记录已更新为失败状态（客户端断开）")

                # 发送断开事件
                disconnect_event = {
                    "type": "error",
                    "error": "连接已断开"
                }
                yield f"data: {json.dumps(disconnect_event, ensure_ascii=False)}\n\n"
                raise

            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"❌ [Agent 执行异常] 错误类型: {type(e).__name__}")
                logger.error(f"❌ [Agent 执行异常] 错误信息: {str(e)}")
                logger.error("=" * 80)

                # ✅ 更新执行记录为失败状态
                if execution:
                    execution.status = "failed"
                    execution.error_message = str(e)
                    execution.completed_at = datetime.now()
                    db.commit()
                    logger.info(f"✅ [数据库] 执行记录已更新为失败状态")

                error_event = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        # ✅ HTTP 错误时也要更新执行记录
        if execution and execution_id:
            try:
                execution.status = "failed"
                execution.error_message = "HTTP 异常"
                execution.completed_at = datetime.now()
                db.commit()
            except:
                pass
        raise

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ [Agent 聊天失败] AgentID: {agent_id}")
        logger.error(f"❌ [Agent 聊天失败] 错误: {e}")
        logger.error("=" * 80)

        # ✅ 更新执行记录为失败状态
        if execution and execution_id:
            try:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.now()
                db.commit()
            except:
                pass

        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent 执行历史 API ====================

@router.get("/{agent_id}/executions", response_model=AgentExecutionListResponse)
async def list_agent_executions(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 50
):
    """列出 Agent 的执行历史（支持分页）"""
    try:
        # 验证 Agent 存在
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        # 验证分页参数
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50

        # 构建查询
        query = db.query(AgentExecution).filter(AgentExecution.agent_id == agent_id)

        # 获取总数
        total = query.count()

        # 按开始时间倒序，然后分页
        executions = query.order_by(AgentExecution.started_at.desc()).offset((page - 1) * limit).limit(limit).all()

        has_more = (page * limit) < total

        return AgentExecutionListResponse(
            executions=executions,
            total=total,
            page=page,
            limit=limit,
            has_more=has_more
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}/execution")
async def get_message_execution(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取消息关联的 Agent 执行记录（含 reasoning_steps）

    通过 message_id 精确查询对应的 Agent 执行记录，用于恢复历史思维链
    """
    try:
        from app.models import Message, Session

        # 验证消息存在
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return {"message_id": message_id, "execution": None}

        # 验证会话归属（权限检查）
        session = db.query(Session).filter(
            Session.id == message.session_id,
            Session.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(status_code=403, detail="无权访问此消息")

        # 查询执行记录
        execution = db.query(AgentExecution).filter(
            AgentExecution.message_id == message_id
        ).first()

        if not execution:
            return {"message_id": message_id, "execution": None}

        # 返回执行记录（包装在 execution 字段中）
        return {
            "message_id": message_id,
            "execution": {
                "id": execution.id,
                "message_id": execution.message_id,
                "agent_id": execution.agent_id,
                "session_id": execution.session_id,
                "status": execution.status,
                "reasoning_steps": execution.reasoning_steps or [],
                "tool_calls": execution.execution_log or [],
                "steps": execution.steps,
                "result": execution.result,
                "error_message": execution.error_message,
                "started_at": execution.started_at.isoformat() + "Z" if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() + "Z" if execution.completed_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取消息执行记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
