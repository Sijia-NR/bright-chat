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
import inspect
import threading
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

from typing import TypedDict

class AgentState(TypedDict):
    """Agent 状态类"""
    messages: list
    input: str
    output: str
    tools_called: list
    steps: int
    error: str | None


# ==================== 辅助函数 ====================

def serialize_state(state: AgentState) -> dict:
    """序列化 AgentState 为可 JSON 序列化的字典"""
    serialized = {}
    for key, value in state.items():
        if key == "messages" and isinstance(value, list):
            # 将 LangChain Message 对象转换为字典
            serialized[key] = [
                {"type": type(msg).__name__, "content": msg.content}
                if hasattr(msg, 'content') else str(msg)
                for msg in value
            ]
        else:
            serialized[key] = value
    return serialized


# ==================== Agent 服务 ====================

class AgentService:
    """Agent 服务（线程安全单例模式）"""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        """线程安全的单例实现（双重检查锁定）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # 双重检查
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 Agent 服务（只执行一次）"""
        if AgentService._initialized:
            return

        self.tools: Dict[str, Callable] = {}
        self._register_default_tools()
        AgentService._initialized = True
        logger.info("AgentService 单例初始化完成")

    def _register_default_tools(self):
        """注册默认工具"""
        from .tools import (
            calculator_tool,
            datetime_tool,
            knowledge_search_tool,
            code_executor_tool,
            browser_tool,
            file_tool,
        )

        # 基础工具
        self.register_tool(TOOL_CALCULATOR, calculator_tool)
        self.register_tool(TOOL_DATETIME, datetime_tool)
        self.register_tool(TOOL_KNOWLEDGE_SEARCH, knowledge_search_tool)

        # 高级工具
        self.register_tool("code_executor", code_executor_tool)
        self.register_tool("browser", browser_tool)
        self.register_tool("file", file_tool)

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
            # 只添加工具函数实际需要的上下文参数
            if context:
                # 获取工具函数的签名
                tool_func = self.tools[tool_name]
                sig = inspect.signature(tool_func)
                valid_params = set(sig.parameters.keys())

                # 只合并工具函数接受的参数
                filtered_context = {k: v for k, v in context.items() if k in valid_params}
                parameters.update(filtered_context)
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
        # 准备 Agent 配置
        agent_config = {
            "agent_id": agent.id,
            "agent_type": agent.agent_type,
            "tools": agent.tools or [],
            "knowledge_base_ids": agent.knowledge_base_ids or [],
            "config": agent.config or {}
        }

        # 创建带配置的闭包节点函数
        def make_think_node(agent_cfg):
            async def think_node(state: AgentState) -> AgentState:
                """思考节点：决定下一步行动（不可变状态更新）"""
                max_steps = agent_cfg["config"].get("max_steps", DEFAULT_MAX_STEPS)
                current_steps = state.get(STATE_STEPS, 0)

                logger.info(f"🤔 [思考节点] 开始思考...")
                logger.info(f"🤔 [思考节点] 当前步骤: {current_steps}")
                logger.info(f"🤔 [思考节点] 最大步数: {max_steps}")
                logger.info(f"🤔 [思考节点] 输入: {state.get(STATE_INPUT, '')[:100]}...")
                logger.info(f"🤔 [思考节点] agent_config: {agent_cfg}")

                # 创建新状态（不可变更新）
                if current_steps >= max_steps:
                    logger.warning(f"⚠️  [思考节点] 达到最大步数限制: {max_steps}")
                    return {
                        **state,
                        STATE_OUTPUT: f"已达到最大步数限制 ({max_steps})，停止执行。",
                        STATE_ERROR: ERROR_MAX_STEPS
                    }

                new_state = {
                    **state,
                    STATE_STEPS: current_steps + 1
                }
                logger.info(f"✅ [思考节点] 思考完成，进入第 {new_state[STATE_STEPS]} 步")
                return new_state
            return think_node

        def make_act_node(agent_cfg, user_id_val):
            async def act_node(state: AgentState) -> AgentState:
                """行动节点：执行工具或生成回答（不可变状态更新）"""
                available_tools = agent_cfg["tools"]
                input_text = state.get(STATE_INPUT, "")
                tools_called = list(state.get(STATE_TOOLS_CALLED, []))  # 创建副本

                logger.info(f"🎬 [行动节点] 开始行动...")
                logger.info(f"🎬 [行动节点] 可用工具: {available_tools}")
                logger.info(f"🎬 [行动节点] 输入文本: {input_text[:100]}...")
                logger.info(f"🎬 [行动节点] agent_config: {agent_cfg}")
                logger.info(f"🎬 [行动节点] agent_config 类型: {type(agent_cfg)}")

                # 决定使用哪个工具
                tool_decision = self._decide_tool(input_text, available_tools, agent_cfg)

                if tool_decision is None:
                    # 没有合适的工具
                    logger.warning(f"⚠️  [行动节点] 未找到合适的工具")
                    return {
                        **state,
                        STATE_OUTPUT: ERROR_NO_TOOL_MSG.format(input_text)
                    }

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
                            "user_id": user_id_val,
                            "knowledge_base_ids": agent_cfg.get("knowledge_base_ids", [])
                        }
                    )

                    tool_duration = (datetime.now() - tool_start_time).total_seconds()
                    logger.info(f"✅ [行动节点] 工具执行完成: {tool_name} (耗时: {tool_duration:.3f}秒)")
                    logger.info(f"✅ [行动节点] 结果类型: {type(result).__name__}")
                    logger.info(f"✅ [行动节点] 结果长度: {len(str(result))} 字符")

                    # 创建新的工具调用列表（不可变更新）
                    new_tools_called = tools_called + [{
                        "tool": tool_name,
                        "parameters": parameters,
                        "result": result
                    }]

                    return {
                        **state,
                        STATE_TOOLS_CALLED: new_tools_called,
                        STATE_LAST_RESULT: result
                    }

                except ToolExecutionError as e:
                    logger.error(f"❌ [行动节点] 工具执行失败: {tool_name}")
                    logger.error(f"❌ [行动节点] 错误信息: {str(e)}")
                    return {
                        **state,
                        STATE_ERROR: str(e)
                    }

            return act_node

        workflow = StateGraph(AgentState)

        # 添加节点（使用闭包捕获配置）
        workflow.add_node(NODE_THINK, make_think_node(agent_config))
        workflow.add_node(NODE_ACT, make_act_node(agent_config, user_id))
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
        """思考节点：决定下一步行动（不可变状态更新）"""
        # 从状态中获取配置（使用双下划线键名）
        agent_config = state.get("__agent_config", {})
        max_steps = agent_config.get("config", {}).get("max_steps", DEFAULT_MAX_STEPS)
        current_steps = state.get(STATE_STEPS, 0)

        logger.info(f"🤔 [思考节点] 开始思考...")
        logger.info(f"🤔 [思考节点] 当前步骤: {current_steps}")
        logger.info(f"🤔 [思考节点] 最大步数: {max_steps}")
        logger.info(f"🤔 [思考节点] 输入: {state.get(STATE_INPUT, '')[:100]}...")
        logger.info(f"🤔 [思考节点] agent_config: {agent_config}")

        # 创建新状态（不可变更新）
        if current_steps >= max_steps:
            logger.warning(f"⚠️  [思考节点] 达到最大步数限制: {max_steps}")
            return {
                **state,
                STATE_OUTPUT: f"已达到最大步数限制 ({max_steps})，停止执行。",
                STATE_ERROR: ERROR_MAX_STEPS
            }

        new_state = {
            **state,
            STATE_STEPS: current_steps + 1
        }
        logger.info(f"✅ [思考节点] 思考完成，进入第 {new_state[STATE_STEPS]} 步")
        return new_state

    async def _act_node(self, state: AgentState) -> AgentState:
        """行动节点：执行工具或生成回答（不可变状态更新）"""
        # 从状态中获取配置（使用双下划线键名）
        agent_config = state.get("__agent_config", {})
        available_tools = agent_config.get("tools", [])
        input_text = state.get(STATE_INPUT, "")
        tools_called = list(state.get(STATE_TOOLS_CALLED, []))  # 创建副本

        logger.info(f"🎬 [行动节点] 开始行动...")
        logger.info(f"🎬 [行动节点] 可用工具: {available_tools}")
        logger.info(f"🎬 [行动节点] 输入文本: {input_text[:100]}...")
        logger.info(f"🎬 [行动节点] agent_config: {agent_config}")
        logger.info(f"🎬 [行动节点] agent_config 类型: {type(agent_config)}")

        # 决定使用哪个工具
        tool_decision = self._decide_tool(input_text, available_tools, agent_config)

        if tool_decision is None:
            # 没有合适的工具
            logger.warning(f"⚠️  [行动节点] 未找到合适的工具")
            return {
                **state,
                STATE_OUTPUT: ERROR_NO_TOOL_MSG.format(input_text)
            }

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

            # 创建新的工具调用列表（不可变更新）
            new_tools_called = tools_called + [{
                "tool": tool_name,
                "parameters": parameters,
                "result": result
            }]

            return {
                **state,
                STATE_TOOLS_CALLED: new_tools_called,
                STATE_LAST_RESULT: result
            }

        except ToolExecutionError as e:
            logger.error(f"❌ [行动节点] 工具执行失败: {tool_name}")
            logger.error(f"❌ [行动节点] 错误信息: {str(e)}")
            return {
                **state,
                STATE_ERROR: str(e)
            }

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

        # 新增工具关键词
        CODE_KEYWORDS = ("执行", "运行", "计算", "代码", "python", "程序")
        BROWSER_KEYWORDS = ("搜索", "浏览", "访问", "网页", "网站", "爬虫", "抓取")
        FILE_KEYWORDS = ("保存", "写入", "读取", "文件", "创建文件")

        # 优先级 1: 检查代码执行（需要明确的前缀）
        if "code_executor" in available_tools:
            import re
            # 检查是否有明确的代码执行前缀
            code_prefix_patterns = [
                r'^执行代码[：:]\s*',
                r'^运行代码[：:]\s*',
                r'^运行[：:]\s*',
                r'^代码[：:]\s*',
                r'^python[：:]\s*',
                r'^程序[：:]\s*',
            ]
            has_code_prefix = any(re.search(pattern, input_text, re.IGNORECASE) for pattern in code_prefix_patterns)

            # 检查是否有 markdown 代码块
            has_code_block = re.search(r'```(?:python)?\n?', input_text, re.IGNORECASE) is not None

            # 检查是否有代码关键词（不包括纯"计算"，因为可能是指数学计算）
            has_code_keyword = any(kw in input_text for kw in ("执行", "运行", "代码", "python", "程序"))

            if has_code_prefix or has_code_block or (has_code_keyword and "计算" not in input_text.split()[0] if input_text else False):
                # 提取代码部分
                code_match = re.search(r'```(?:python)?\n?(.*?)```', input_text, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()
                else:
                    # 移除常见前缀
                    code = input_text
                    for pattern in code_prefix_patterns:
                        code = re.sub(pattern, '', code, flags=re.IGNORECASE).strip()
                    # 如果移除前缀后为空，使用原始输入
                    if not code:
                        code = input_text

                return "code_executor", {"code": code}

        # 优先级 2: 检查计算器（仅当没有代码执行意图时）
        if TOOL_CALCULATOR in available_tools and any(op in input_text for op in CALC_OPS):
            return TOOL_CALCULATOR, {"expression": input_text}

        # 优先级 3: 检查时间查询
        if TOOL_DATETIME in available_tools and any(kw in input_text for kw in DATETIME_KEYWORDS):
            return TOOL_DATETIME, {}

        # 检查浏览器操作
        if "browser" in available_tools and any(kw in input_text for kw in BROWSER_KEYWORDS):
            # 提取 URL（如果有）
            import re
            url_match = re.search(r'https?://[^\s]+', input_text)
            url = url_match.group(0) if url_match else None

            # 判断操作类型
            if "搜索" in input_text or "search" in input_text.lower():
                query = re.sub(r'(搜索|search|网页|网站).*?(https?://\S+)?', '', input_text).strip()
                return "browser", {
                    "action": "search",
                    "text": query or input_text
                }
            elif url:
                return "browser", {
                    "action": "scrape",
                    "url": url
                }
            else:
                return "browser", {
                    "action": "navigate",
                    "url": "https://www.google.com"
                }

        # 检查文件操作
        if "file" in available_tools and any(kw in input_text for kw in FILE_KEYWORDS):
            # 改进的文件操作推断
            import re

            # 提取文件名
            filename_match = re.search(r'["\']?([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)["\']?', input_text)
            filename = filename_match.group(1) if filename_match else None

            # 如果没有文件扩展名，尝试其他模式
            if not filename:
                filename_match = re.search(r'文件\s*["\']?([a-zA-Z0-9_\-./]+)["\']?', input_text)
                filename = filename_match.group(1) if filename_match else "output.txt"

            if "保存" in input_text or "写入" in input_text or "创建文件" in input_text:
                # 提取文件内容
                content_match = re.search(r'内容为[：:]\s*["\']?(.+?)["\']?$', input_text)
                content = content_match.group(1).strip() if content_match else input_text

                return "file", {
                    "action": "write",
                    "path": filename,
                    "content": content
                }
            elif "读取" in input_text or "打开" in input_text:
                return "file", {
                    "action": "read",
                    "path": filename
                }
            elif "列出" in input_text:
                # 提取目录路径
                dir_match = re.search(r'(?:目录|文件夹|路径)\s*["\']?([a-zA-Z0-9_\-./]*)["\']?', input_text)
                dir_path = dir_match.group(1) if dir_match else "."

                return "file", {
                    "action": "list",
                    "path": dir_path
                }

        # 检查知识库搜索（默认工具，优先级最低）
        if TOOL_KNOWLEDGE_SEARCH in available_tools:
            return TOOL_KNOWLEDGE_SEARCH, {
                "query": input_text,
                "knowledge_base_ids": agent_config.get("knowledge_base_ids", []),
                "top_k": DEFAULT_TOP_K
            }

        return None

    async def _observe_node(self, state: AgentState) -> AgentState:
        """观察节点：根据结果决定下一步（不可变状态更新）"""
        logger.info(f"👀️ [观察节点] 开始观察...")

        error = state.get(STATE_ERROR)
        if error:
            logger.error(f"❌ [观察节点] 检测到错误: {error}")
            return {
                **state,
                STATE_OUTPUT: ERROR_EXECUTION_MSG.format(error)
            }

        # 根据工具结果生成最终回答
        tools_called = state.get(STATE_TOOLS_CALLED, [])
        if tools_called:
            last_tool = tools_called[-1]
            logger.info(f"👀️ [观察节点] 最后调用的工具: {last_tool['tool']}")
            output = self._format_tool_output(last_tool)
            logger.info(f"✅ [观察节点] 生成输出: {output[:100]}...")
            return {
                **state,
                STATE_OUTPUT: output
            }
        else:
            # 没有工具调用记录，返回默认消息
            logger.info(f"ℹ️  [观察节点] 没有工具调用记录，返回默认消息")
            input_text = state.get(STATE_INPUT, "")
            return {
                **state,
                STATE_OUTPUT: ERROR_NO_TOOL_MSG.format(input_text)
            }

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

        if tool_name == "code_executor":
            # 代码执行结果
            if isinstance(result, dict):
                if result.get("success"):
                    output = result.get("output", "执行完成")
                    exec_time = result.get("execution_time", 0)
                    return f"代码执行成功（耗时: {exec_time:.2f}秒）：\n\n{output[:500]}..."
                else:
                    error = result.get("error", "未知错误")
                    return f"代码执行失败: {error}"
            return f"代码执行结果: {str(result)[:500]}..."

        if tool_name == "browser":
            # 浏览器操作结果
            if isinstance(result, dict):
                if result.get("success"):
                    action = tool_call.get("parameters", {}).get("action", "unknown")
                    data = result.get("data", {})

                    if action == "search":
                        results = data.get("results", [])
                        return f"搜索完成，找到 {len(results)} 个结果:\n\n" + "\n".join(
                            f"{r.get('rank')}. {r.get('title')}\n   {r.get('url')}"
                            for r in results[:5]
                        )
                    elif action == "scrape":
                        title = data.get("title", "")
                        content_len = data.get("content_length", 0)
                        return f"页面抓取成功: {title}\n内容长度: {content_len} 字符\n\n{data.get('content', '')[:300]}..."
                    else:
                        return f"浏览器操作完成: {action}"
                else:
                    error = result.get("error", "未知错误")
                    return f"浏览器操作失败: {error}"
            return f"浏览器操作结果: {str(result)[:500]}..."

        if tool_name == "file":
            # 文件操作结果
            if isinstance(result, dict):
                if result.get("success"):
                    action = tool_call.get("parameters", {}).get("action", "unknown")
                    data = result.get("data", {})

                    if action == "read":
                        content = data.get("content", "")
                        return f"文件读取成功 ({data.get('size', 0)} 字符):\n\n{content[:500]}..."
                    elif action == "write":
                        return f"文件保存成功: {data.get('path')}\n大小: {data.get('size', 0)} 字符"
                    elif action == "list":
                        items = data.get("items", [])
                        return f"目录列表 ({data.get('count', 0)} 项):\n\n" + "\n".join(
                            f"- {item['name']} ({item['type']})"
                            for item in items[:10]
                        )
                    else:
                        return f"文件操作完成: {action}"
                else:
                    error = result.get("error", "未知错误")
                    return f"文件操作失败: {error}"
            return f"文件操作结果: {str(result)[:500]}..."

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

    async def _create_execution_record(
        self,
        execution_id: str,
        agent_id: str,
        user_id: str,
        session_id: Optional[str],
        query: str
    ) -> str:
        """
        短事务：创建 Agent 执行记录

        Args:
            execution_id: 执行ID
            agent_id: Agent ID
            user_id: 用户 ID
            session_id: 会话 ID
            query: 用户查询

        Returns:
            执行ID
        """
        db = SessionLocal()
        try:
            logger.info("📝 [数据库] 创建执行记录...")
            execution = AgentExecution(
                id=execution_id,
                agent_id=agent_id,
                user_id=user_id,
                session_id=session_id,
                input_prompt=query,
                status=EXECUTION_STATUS_RUNNING
            )
            db.add(execution)
            db.commit()
            logger.info(f"✅ [数据库] 执行记录已创建: {execution_id}")
            return execution_id
        except Exception as e:
            logger.error(f"❌ [数据库] 创建执行记录失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    async def _update_execution_record(
        self,
        execution_id: str,
        status: str,
        steps: Optional[int] = None,
        result: Optional[str] = None,
        execution_log: Optional[list] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        短事务：更新 Agent 执行记录

        Args:
            execution_id: 执行ID
            status: 执行状态
            steps: 执行步数
            result: 执行结果
            execution_log: 执行日志
            error_message: 错误信息
        """
        db = SessionLocal()
        try:
            logger.info(f"💾 [数据库] 更新执行记录状态: {status}...")
            execution = db.query(AgentExecution).filter(
                AgentExecution.id == execution_id
            ).first()

            if execution:
                execution.status = status
                if steps is not None:
                    execution.steps = steps
                if result is not None:
                    execution.result = result
                if execution_log is not None:
                    execution.execution_log = execution_log
                if error_message is not None:
                    execution.error_message = error_message
                execution.completed_at = datetime.now()

                db.commit()
                logger.info(f"✅ [数据库] 执行记录已更新: {execution_id}")
            else:
                logger.warning(f"⚠️  [数据库] 执行记录不存在: {execution_id}")
        except Exception as e:
            logger.error(f"❌ [数据库] 更新执行记录失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

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
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info(f"🎯 [Agent 执行初始化] 执行ID: {execution_id}")
        logger.info(f"🎯 [Agent 执行初始化] Agent: {agent.display_name} ({agent.name})")
        logger.info(f"🎯 [Agent 执行初始化] 用户ID: {user_id}")
        logger.info(f"🎯 [Agent 执行初始化] 会话ID: {session_id}")
        logger.info(f"🎯 [Agent 执行初始化] 查询: {query}")
        logger.info("=" * 80)

        # 短事务：创建执行记录
        execution_id = await self._create_execution_record(
            execution_id=execution_id,
            agent_id=agent.id,
            user_id=user_id,
            session_id=session_id,
            query=query
        )

        try:

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
            state: AgentState = {
                "messages": [HumanMessage(content=query)],
                "input": query,
                "output": "",
                "tools_called": [],
                "steps": 0,
                "error": None
            }

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
            final_state = None  # 保存最终状态

            async for event_state in graph.astream(state):
                for node_name, node_state in event_state.items():
                    # 跳过 None 状态
                    if node_state is None:
                        logger.warning(f"⚠️  [节点执行] 节点 {node_name} 的状态为 None，跳过")
                        continue

                    # 保存最终状态
                    final_state = node_state

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
                        "state": serialize_state(node_state),
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

            # 使用最终状态获取输出
            if final_state:
                final_output = final_state.get(STATE_OUTPUT, "执行完成")
                final_steps = final_state.get(STATE_STEPS, 0)
                final_tools_called = final_state.get(STATE_TOOLS_CALLED, [])
            else:
                final_output = "执行完成（无状态返回）"
                final_steps = 0
                final_tools_called = []

            logger.info("=" * 80)
            logger.info(f"✅ [Agent 执行完成] 执行ID: {execution_id}")
            logger.info(f"✅ [Agent 执行完成] 总步骤: {final_steps}")
            logger.info(f"✅ [Agent 执行完成] 总耗时: {total_duration:.2f}秒")
            logger.info(f"✅ [Agent 执行完成] 工具调用次数: {len(final_tools_called)}")
            logger.info(f"✅ [Agent 执行完成] 最终输出: {final_output[:200]}...")
            logger.info("=" * 80)

            yield {
                "type": EVENT_TYPE_COMPLETE,
                "output": final_output,
                "steps": final_steps,
                "duration": total_duration,
                "tools_called_count": len(final_tools_called),
                "timestamp": datetime.now().isoformat()
            }

            # 短事务：更新执行记录为完成状态
            await self._update_execution_record(
                execution_id=execution_id,
                status=EXECUTION_STATUS_COMPLETED,
                steps=final_steps,
                result=final_output,
                execution_log=final_tools_called
            )

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

            # 短事务：更新执行记录为失败状态
            await self._update_execution_record(
                execution_id=execution_id,
                status=EXECUTION_STATUS_FAILED,
                error_message=str(e)
            )

            yield {
                "type": EVENT_TYPE_ERROR,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": total_duration,
                "timestamp": datetime.now().isoformat()
            }

        logger.info("🏁 [Agent 执行] 流程结束")



# ==================== 全局服务实例 ====================

_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取全局 Agent 服务实例（单例模式）"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
