"""
Agent 服务模块
Agent Service Module

提供基于 LangGraph 的 Agent 工作流引擎
Provides LangGraph-based Agent workflow engine
"""
import json
import logging
import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.agent import (
    EXECUTION_STATUS_COMPLETED,
    EXECUTION_STATUS_FAILED,
    EXECUTION_STATUS_RUNNING,
    Agent,
    AgentExecution,
)

logger = logging.getLogger(__name__)


# ==================== 常量定义 ====================

# 工具名称
TOOL_CALCULATOR = "calculator"
TOOL_DATETIME = "datetime"
TOOL_KNOWLEDGE_SEARCH = "knowledge_search"

# 节点名称
NODE_THINK = "think"
NODE_ACT = "act"
NODE_OBSERVE = "observe"

# 状态键
STATE_MESSAGES = "messages"
STATE_INPUT = "input"
STATE_OUTPUT = "output"
STATE_TOOLS_CALLED = "tools_called"
STATE_STEPS = "steps"
STATE_ERROR = "error"
STATE_LAST_RESULT = "last_result"

# 事件类型
EVENT_TYPE_START = "start"
EVENT_TYPE_STEP = "step"
EVENT_TYPE_TOOL_CALL = "tool_call"
EVENT_TYPE_COMPLETE = "complete"
EVENT_TYPE_ERROR = "error"
EVENT_TYPE_DONE = "done"

# 计算器相关关键词
CALC_OPS = ("+", "-", "*", "/", "计算", "求")
DATETIME_KEYWORDS = ("时间", "日期", "几点", "今天")

# 默认值
DEFAULT_MAX_STEPS = 10
DEFAULT_TOP_K = 5
ERROR_MAX_STEPS = "max_steps_reached"
ERROR_NO_TOOL_MSG = "我收到您的问题：{}\n\n抱歉，我暂时无法回答这个问题。"
ERROR_EXECUTION_MSG = "执行过程中发生错误: {}"


# ==================== 异常类 ====================

class ToolExecutionError(Exception):
    """工具执行错误"""
    pass


# ==================== Agent 状态 ====================

class AgentState(dict):
    """Agent 状态类"""

    def __init__(self, **kwargs):
        # 设置默认值
        defaults = {
            STATE_MESSAGES: [],
            STATE_INPUT: "",
            STATE_OUTPUT: "",
            STATE_TOOLS_CALLED: [],
            STATE_STEPS: 0,
            STATE_ERROR: None
        }
        # 合并默认值和传入的参数
        defaults.update(kwargs)
        super().__init__(defaults)


# ==================== Agent 服务 ====================

class AgentService:
    """Agent 服务"""

    def __init__(self):
        """初始化 Agent 服务"""
        self.tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        from .tools import (
            calculator_tool,
            datetime_tool,
            knowledge_search_tool,
        )

        self.register_tool(TOOL_KNOWLEDGE_SEARCH, knowledge_search_tool)
        self.register_tool(TOOL_CALCULATOR, calculator_tool)
        self.register_tool(TOOL_DATETIME, datetime_tool)

        logger.info(f"已注册 {len(self.tools)} 个工具")

    def register_tool(self, name: str, func: Callable) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            func: 工具函数
        """
        self.tools[name] = func
        logger.info(f"注册工具: {name}")

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        执行工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数
            context: 上下文信息（如 user_id, knowledge_base_ids）

        Returns:
            工具执行结果

        Raises:
            ToolExecutionError: 工具不存在或执行失败
        """
        logger.info(f"🔧 [工具执行] 开始执行工具: {tool_name}")
        logger.info(f"🔧 [工具执行] 参数: {parameters}")
        logger.info(f"🔧 [工具执行] 上下文: {context}")

        if tool_name not in self.tools:
            logger.error(f"❌ [工具执行] 工具不存在: {tool_name}")
            logger.error(f"❌ [工具执行] 可用工具: {list(self.tools.keys())}")
            raise ToolExecutionError(f"工具 '{tool_name}' 不存在")

        try:
            if context:
                parameters.update(context)
                logger.info(f"🔧 [工具执行] 合并后参数: {parameters}")

            logger.info(f"⚙️  [工具执行] 调用工具函数...")
            tool_start_time = datetime.now()

            result = await self.tools[tool_name](**parameters)

            tool_duration = (datetime.now() - tool_start_time).total_seconds()
            logger.info(f"✅ [工具执行] 工具执行成功: {tool_name}")
            logger.info(f"✅ [工具执行] 耗时: {tool_duration:.3f}秒")
            logger.info(f"✅ [工具执行] 结果类型: {type(result).__name__}")

            # 根据结果类型记录不同信息
            if isinstance(result, dict):
                if "context" in result:
                    logger.info(f"✅ [工具执行] 结果包含 context，长度: {len(str(result['context']))} 字符")
                elif "answer" in result:
                    logger.info(f"✅ [工具执行] 结果包含 answer，长度: {len(str(result['answer']))} 字符")
                else:
                    logger.info(f"✅ [工具执行] 结果键: {list(result.keys())}")
            elif isinstance(result, str):
                logger.info(f"✅ [工具执行] 结果长度: {len(result)} 字符")
                logger.info(f"✅ [工具执行] 结果预览: {result[:200]}...")
            else:
                logger.info(f"✅ [工具执行] 结果: {str(result)[:200]}...")

            return result

        except Exception as e:
            logger.error(f"❌ [工具执行] 工具执行失败: {tool_name}")
            logger.error(f"❌ [工具执行] 错误类型: {type(e).__name__}")
            logger.error(f"❌ [工具执行] 错误信息: {str(e)}")
            raise ToolExecutionError(f"工具 '{tool_name}' 执行失败: {str(e)}")

    async def create_agent_graph(
        self,
        agent: Agent,
        user_id: str,
        session_id: Optional[str] = None
    ) -> StateGraph:
        """
        创建 Agent 工作流图

        Args:
            agent: Agent 配置
            user_id: 用户 ID
            session_id: 会话 ID

        Returns:
            LangGraph StateGraph
        """
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node(NODE_THINK, self._think_node)
        workflow.add_node(NODE_ACT, self._act_node)
        workflow.add_node(NODE_OBSERVE, self._observe_node)

        # 设置入口
        workflow.set_entry_point(NODE_THINK)

        # 添加边
        # Think 节点后：总是去 Act 节点
        workflow.add_conditional_edges(
            NODE_THINK,
            self._after_think,
            {NODE_ACT: NODE_ACT, "end": END}
        )
        # Act 节点后：总是去 Observe 节点
        workflow.add_edge(NODE_ACT, NODE_OBSERVE)
        # Observe 节点后：根据结果决定是回到 Think 还是结束
        workflow.add_conditional_edges(
            NODE_OBSERVE,
            self._should_continue,
            {NODE_THINK: NODE_THINK, "end": END}
        )

        return workflow.compile()

    async def _think_node(self, state: AgentState) -> AgentState:
        """思考节点：决定下一步行动"""
        # 从状态中获取配置（在 execute 方法中设置）
        agent_config = state.get("_config", {}).get("agent_config", {})
        max_steps = agent_config.get("config", {}).get("max_steps", DEFAULT_MAX_STEPS)

        logger.info(f"🤔 [思考节点] 开始思考...")
        logger.info(f"🤔 [思考节点] 当前步骤: {state.get(STATE_STEPS, 0)}")
        logger.info(f"🤔 [思考节点] 最大步数: {max_steps}")
        logger.info(f"🤔 [思考节点] 输入: {state.get(STATE_INPUT, '')[:100]}...")

        if state.get(STATE_STEPS, 0) >= max_steps:
            logger.warning(f"⚠️  [思考节点] 达到最大步数限制: {max_steps}")
            state[STATE_OUTPUT] = f"已达到最大步数限制 ({max_steps})，停止执行。"
            state[STATE_ERROR] = ERROR_MAX_STEPS
            return state

        state[STATE_STEPS] = state.get(STATE_STEPS, 0) + 1
        logger.info(f"✅ [思考节点] 思考完成，进入第 {state.get(STATE_STEPS, 0)} 步")
        return state

    async def _act_node(self, state: AgentState) -> AgentState:
        """行动节点：执行工具或生成回答"""
        # 从状态中获取配置（在 execute 方法中设置）
        config_dict = state.get("_config") or {}
        agent_config = config_dict.get("agent_config") or {}
        available_tools = agent_config.get("tools", [])
        input_text = state.get(STATE_INPUT, "")

        logger.info(f"🎬 [行动节点] 开始行动...")
        logger.info(f"🎬 [行动节点] 可用工具: {available_tools}")
        logger.info(f"🎬 [行动节点] 输入文本: {input_text[:100]}...")
        logger.info(f"🎬 [行动节点] agent_config: {agent_config}")

        # 决定使用哪个工具
        tool_decision = self._decide_tool(input_text, available_tools, agent_config)

        if tool_decision is None:
            # 没有合适的工具
            logger.warning(f"⚠️  [行动节点] 未找到合适的工具")
            state[STATE_OUTPUT] = ERROR_NO_TOOL_MSG.format(input_text)
            return state

        tool_name, parameters = tool_decision
        logger.info(f"🎯 [行动节点] 选择工具: {tool_name}")
        logger.info(f"🎯 [行动节点] 工具参数: {parameters}")

        # 执行工具
        try:
            logger.info(f"⚙️  [行动节点] 开始执行工具: {tool_name}...")
            tool_start_time = datetime.now()

            result = await self.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                context={
                    "user_id": state.get("_config", {}).get("user_id"),
                    "knowledge_base_ids": agent_config.get("knowledge_base_ids", [])
                }
            )

            tool_duration = (datetime.now() - tool_start_time).total_seconds()
            logger.info(f"✅ [行动节点] 工具执行完成: {tool_name} (耗时: {tool_duration:.3f}秒)")
            logger.info(f"✅ [行动节点] 结果类型: {type(result).__name__}")
            logger.info(f"✅ [行动节点] 结果长度: {len(str(result))} 字符")

            # 记录工具调用（确保列表存在）
            tools_called = state.get(STATE_TOOLS_CALLED, [])
            tools_called.append({
                "tool": tool_name,
                "parameters": parameters,
                "result": result  # 保存原始结果对象（可能是字典或其他类型）
            })
            state[STATE_TOOLS_CALLED] = tools_called
            state[STATE_LAST_RESULT] = result

        except ToolExecutionError as e:
            logger.error(f"❌ [行动节点] 工具执行失败: {tool_name}")
            logger.error(f"❌ [行动节点] 错误信息: {str(e)}")
            state[STATE_ERROR] = str(e)

        return state

    def _decide_tool(
        self,
        input_text: str,
        available_tools: List[str],
        agent_config: Dict[str, Any]
    ) -> Optional[tuple]:
        """决定使用哪个工具"""
        # 防御性处理：确保 agent_config 不是 None
        if agent_config is None:
            agent_config = {}

        # 检查计算器
        if TOOL_CALCULATOR in available_tools and any(op in input_text for op in CALC_OPS):
            return TOOL_CALCULATOR, {"expression": input_text}

        # 检查时间
        if TOOL_DATETIME in available_tools and any(kw in input_text for kw in DATETIME_KEYWORDS):
            return TOOL_DATETIME, {}

        # 检查知识库搜索
        if TOOL_KNOWLEDGE_SEARCH in available_tools:
            return TOOL_KNOWLEDGE_SEARCH, {
                "query": input_text,
                "knowledge_base_ids": agent_config.get("knowledge_base_ids", []),
                "top_k": DEFAULT_TOP_K
            }

        return None

    async def _observe_node(self, state: AgentState) -> AgentState:
        """观察节点：根据结果决定下一步"""
        logger.info(f"👀️ [观察节点] 开始观察...")

        error = state.get(STATE_ERROR)
        if error:
            logger.error(f"❌ [观察节点] 检测到错误: {error}")
            state[STATE_OUTPUT] = ERROR_EXECUTION_MSG.format(error)
            return state

        # 根据工具结果生成最终回答
        tools_called = state.get(STATE_TOOLS_CALLED, [])
        if tools_called:
            last_tool = tools_called[-1]
            logger.info(f"👀️ [观察节点] 最后调用的工具: {last_tool['tool']}")
            output = self._format_tool_output(last_tool)
            state[STATE_OUTPUT] = output
            logger.info(f"✅ [观察节点] 生成输出: {output[:100]}...")
        else:
            # 没有工具调用记录，返回默认消息
            logger.info(f"ℹ️  [观察节点] 没有工具调用记录，返回默认消息")
            input_text = state.get(STATE_INPUT, "")
            state[STATE_OUTPUT] = ERROR_NO_TOOL_MSG.format(input_text)

        return state

    def _format_tool_output(self, tool_call: Dict[str, Any]) -> str:
        """格式化工具输出"""
        tool_name = tool_call["tool"]
        result = tool_call["result"]

        if tool_name == TOOL_CALCULATOR:
            return f"计算结果: {result}"
        if tool_name == TOOL_DATETIME:
            return f"当前时间: {result}"
        if tool_name == TOOL_KNOWLEDGE_SEARCH:
            # result 可能是字典或字符串
            if isinstance(result, dict):
                # 检查是否有 context 字段
                if "context" in result:
                    context = result["context"]
                    return f"根据知识库搜索结果：\n\n{context[:500]}..."
                # 检查是否有 error 字段
                elif "error" in result:
                    return f"知识库检索失败: {result['error']}"
                else:
                    # 其他字典格式，转为字符串
                    return f"知识库搜索结果: {str(result)[:500]}..."
            else:
                # result 是字符串或其他类型
                return f"知识库搜索结果: {str(result)[:500]}..."

        return str(result)[:500]

    def _should_continue(self, state: AgentState) -> str:
        """Observe 节点后的条件判断：决定是否继续循环"""
        # 如果有错误或输出，结束
        if state.get(STATE_ERROR) or state.get(STATE_OUTPUT):
            return "end"

        # 如果达到最大步数，结束
        if state.get(STATE_STEPS, 0) >= DEFAULT_MAX_STEPS:
            return "end"

        # 否则回到 Think 节点，开始新一轮循环
        return NODE_THINK

    def _after_think(self, state: AgentState) -> str:
        """Think 节点后的条件判断：总是去 Act 节点执行工具"""
        return NODE_ACT

    async def execute(
        self,
        agent: Agent,
        query: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行 Agent 任务（流式输出）

        Args:
            agent: Agent 配置
            query: 用户查询
            user_id: 用户 ID
            session_id: 会话 ID

        Yields:
            执行步骤的事件
        """
        execution_id = str(uuid.uuid4())
        db = SessionLocal()
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info(f"🎯 [Agent 执行初始化] 执行ID: {execution_id}")
        logger.info(f"🎯 [Agent 执行初始化] Agent: {agent.display_name} ({agent.name})")
        logger.info(f"🎯 [Agent 执行初始化] 用户ID: {user_id}")
        logger.info(f"🎯 [Agent 执行初始化] 会话ID: {session_id}")
        logger.info(f"🎯 [Agent 执行初始化] 查询: {query}")
        logger.info("=" * 80)

        try:
            # 创建执行记录
            logger.info("📝 [数据库] 创建执行记录...")
            execution = AgentExecution(
                id=execution_id,
                agent_id=agent.id,
                user_id=user_id,
                session_id=session_id,
                input_prompt=query,
                status=EXECUTION_STATUS_RUNNING
            )
            db.add(execution)
            db.commit()
            logger.info(f"✅ [数据库] 执行记录已创建: {execution_id}")

            # 配置（必须在 state 之前定义）
            config = {
                "agent_config": {
                    "agent_id": agent.id,
                    "agent_type": agent.agent_type,
                    "tools": agent.tools or [],
                    "knowledge_base_ids": agent.knowledge_base_ids or [],
                    "config": agent.config or {}
                },
                "user_id": user_id,
                "execution_id": execution_id
            }

            logger.info(f"🔧 [配置] 工具列表: {config['agent_config']['tools']}")
            logger.info(f"🔧 [配置] 知识库IDs: {config['agent_config']['knowledge_base_ids']}")
            logger.info(f"🔧 [配置] Agent配置: {config['agent_config']['config']}")

            # 初始化状态
            logger.info("🔄 [状态初始化] 设置初始状态...")
            state = AgentState(
                messages=[HumanMessage(content=query)],
                input=query,
                steps=0,
                _config=config  # 将配置添加到状态中
            )

            # 创建并执行工作流
            logger.info("🏗️  [工作流] 创建 Agent 工作流图...")
            graph = await self.create_agent_graph(agent, user_id, session_id)
            logger.info("✅ [工作流] 工作流图创建完成")

            # 发送开始事件
            logger.info("🚀 [执行] 开始执行工作流...")
            yield {
                "type": EVENT_TYPE_START,
                "execution_id": execution_id,
                "agent_name": agent.display_name or agent.name,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

            # 执行工作流（流式输出中间步骤）
            step_num = 0
            async for event_state in graph.astream(state):
                for node_name, node_state in event_state.items():
                    # 跳过 None 状态
                    if node_state is None:
                        logger.warning(f"⚠️  [节点执行] 节点 {node_name} 的状态为 None，跳过")
                        continue

                    step_num += 1
                    node_start_time = datetime.now()

                    logger.info("-" * 80)
                    logger.info(f"📍 [节点执行] 第{step_num}步 - 节点: {node_name}")
                    logger.info(f"📍 [节点状态] steps: {node_state.get(STATE_STEPS, 0)}")
                    logger.info(f"📍 [节点状态] input: {node_state.get(STATE_INPUT, '')[:100]}")
                    logger.info(f"📍 [节点状态] output: {node_state.get(STATE_OUTPUT, '')[:100] if node_state.get(STATE_OUTPUT) else 'N/A'}")
                    logger.info(f"📍 [节点状态] error: {node_state.get(STATE_ERROR, 'N/A')}")
                    logger.info(f"📍 [节点状态] tools_called: {len(node_state.get(STATE_TOOLS_CALLED, []))}")

                    yield {
                        "type": EVENT_TYPE_STEP,
                        "node": node_name,
                        "step": node_state.get(STATE_STEPS, 0),
                        "state": dict(node_state),
                        "timestamp": datetime.now().isoformat()
                    }

                    tools_called = node_state.get(STATE_TOOLS_CALLED, [])
                    if tools_called:
                        for idx, tool_call in enumerate(tools_called, 1):
                            tool_name = tool_call.get("tool", "unknown")
                            parameters = tool_call.get("parameters", {})
                            result = tool_call.get("result", "")

                            logger.info(f"  🔧 [工具调用 #{idx}] 工具: {tool_name}")
                            logger.info(f"  🔧 [工具调用 #{idx}] 参数: {parameters}")
                            logger.info(f"  🔧 [工具调用 #{idx}] 结果长度: {len(str(result))} 字符")
                            logger.info(f"  🔧 [工具调用 #{idx}] 结果预览: {str(result)[:150]}...")

                            yield {
                                "type": EVENT_TYPE_TOOL_CALL,
                                "tool": tool_name,
                                "parameters": parameters,
                                "result": result,
                                "timestamp": datetime.now().isoformat()
                            }

                    node_duration = (datetime.now() - node_start_time).total_seconds()
                    logger.info(f"⏱️  [节点执行] 耗时: {node_duration:.3f}秒")

            # 最终结果
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            final_output = state.get(STATE_OUTPUT, "执行完成")

            logger.info("=" * 80)
            logger.info(f"✅ [Agent 执行完成] 执行ID: {execution_id}")
            logger.info(f"✅ [Agent 执行完成] 总步骤: {state.get(STATE_STEPS, 0)}")
            logger.info(f"✅ [Agent 执行完成] 总耗时: {total_duration:.2f}秒")
            logger.info(f"✅ [Agent 执行完成] 工具调用次数: {len(state.get(STATE_TOOLS_CALLED, []))}")
            logger.info(f"✅ [Agent 执行完成] 最终输出: {final_output[:200]}...")
            logger.info("=" * 80)

            yield {
                "type": EVENT_TYPE_COMPLETE,
                "output": final_output,
                "steps": state.get(STATE_STEPS, 0),
                "duration": total_duration,
                "tools_called_count": len(state.get(STATE_TOOLS_CALLED, [])),
                "timestamp": datetime.now().isoformat()
            }

            # 更新执行记录
            logger.info("💾 [数据库] 更新执行记录...")
            execution.status = EXECUTION_STATUS_COMPLETED
            execution.steps = state.get(STATE_STEPS, 0)
            execution.result = final_output
            execution.execution_log = state.get(STATE_TOOLS_CALLED, [])
            execution.completed_at = datetime.now()
            db.commit()
            logger.info("✅ [数据库] 执行记录已更新")

        except Exception as e:
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            logger.error("=" * 80)
            logger.error(f"❌ [Agent 执行失败] 执行ID: {execution_id}")
            logger.error(f"❌ [Agent 执行失败] 错误类型: {type(e).__name__}")
            logger.error(f"❌ [Agent 执行失败] 错误信息: {str(e)}")
            logger.error(f"❌ [Agent 执行失败] 总耗时: {total_duration:.2f}秒")
            logger.error(f"❌ [Agent 执行失败] 堆栈跟踪:\n{traceback.format_exc()}")
            logger.error("=" * 80)

            execution.status = EXECUTION_STATUS_FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            db.commit()

            yield {
                "type": EVENT_TYPE_ERROR,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": total_duration,
                "timestamp": datetime.now().isoformat()
            }

        finally:
            db.close()
            logger.info("🔒 [清理] 数据库连接已关闭")

        logger.info("🏁 [Agent 执行] 流程结束")



# ==================== 全局服务实例 ====================

_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取全局 Agent 服务实例（单例模式）"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
