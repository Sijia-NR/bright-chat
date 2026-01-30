"""
LLM 推理器 - Agent 的大脑

负责 Agent 的思考和决策:
1. 分析用户问题
2. 决定是否需要使用工具
3. 选择合适的工具
4. 生成推理链
"""

import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..services.ias_proxy import IASProxyService
from ..models.ias import IASChatRequest, IASChatMessage, ChatRole
from ..core.database import get_db
from ..models.llm_model import LLMModel

logger = logging.getLogger(__name__)


class LLMReasoner:
    """
    LLM 推理器

    使用 LangChain BaseLanguageModel 接口封装 LLM 调用,
    支持多种 LLM 提供商 (OpenAI, Anthropic, Custom)
    """

    def __init__(self, llm_model_id: Optional[str] = None):
        """
        初始化 LLM 推理器

        Args:
            llm_model_id: LLM 模型 ID (如果为 None,使用默认模型)
        """
        self.llm_model_id = llm_model_id
        self.ias_proxy = IASProxyService()
        self.llm: Optional[BaseLanguageModel] = None
        self._model_config: Optional[Dict[str, Any]] = None

        logger.info(f"🧠 LLMReasoner 初始化 (model_id={llm_model_id})")

    async def initialize(self, db) -> bool:
        """
        从数据库加载 LLM 模型配置

        Args:
            db: 数据库会话

        Returns:
            是否初始化成功
        """
        try:
            # 如果指定了模型 ID,使用指定的模型
            if self.llm_model_id:
                model = db.query(LLMModel).filter(
                    LLMModel.id == self.llm_model_id,
                    LLMModel.is_active == True
                ).first()
            else:
                # 否则使用默认的活跃模型
                model = db.query(LLMModel).filter(
                    LLMModel.is_active == True
                ).order_by(LLMModel.created_at).first()

            if not model:
                logger.error(f"❌ 未找到可用的 LLM 模型 (model_id={self.llm_model_id})")
                return False

            self._model_config = {
                "id": model.id,
                "name": model.name,
                "display_name": model.display_name,
                "model_type": model.model_type,
                "api_url": model.api_url,
                "api_key": model.api_key,
                "temperature": model.temperature / 100 if model.temperature else 0.7,
            }

            logger.info(f"✅ LLMReasoner 使用模型: {model.display_name} ({model.name})")
            return True

        except Exception as e:
            logger.error(f"❌ LLMReasoner 初始化失败: {e}")
            return False

    async def reason(
        self,
        question: str,
        available_tools: List[str],
        conversation_history: List[Dict[str, Any]],
        previous_steps: List[Dict[str, Any]],
        agent_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行推理决策

        Args:
            question: 用户问题
            available_tools: 可用工具列表
            conversation_history: 对话历史
            previous_steps: 之前的执行步骤
            agent_config: Agent 配置

        Returns:
            决策结果:
            {
                "reasoning": "推理链",
                "tool": "工具名称" 或 None,
                "parameters": {参数},
                "confidence": 0.95,
                "should_continue": True
            }
        """
        # ✅ Phase 1: 检测用户是否选择了知识库
        logger.info(f"🔍 [DEBUG] agent_config 类型: {type(agent_config)}")
        logger.info(f"🔍 [DEBUG] agent_config 内容: {agent_config}")

        knowledge_base_ids = agent_config.get("knowledge_base_ids", [])
        has_knowledge_base = len(knowledge_base_ids) > 0

        logger.info(f"🔍 [DEBUG] knowledge_base_ids: {knowledge_base_ids}")
        logger.info(f"🔍 [DEBUG] has_knowledge_base: {has_knowledge_base}")

        if has_knowledge_base:
            logger.info(f"📚 [推理] 检测到用户选择了知识库: {knowledge_base_ids}")
        else:
            logger.info(f"📚 [推理] 用户未选择知识库")

        # 1. 构建推理提示词
        prompt = self._build_reasoning_prompt(
            question=question,
            available_tools=available_tools,
            conversation_history=conversation_history,
            previous_steps=previous_steps,
            agent_config=agent_config,
            has_knowledge_base=has_knowledge_base  # ← 传递知识库状态
        )

        # 🔍 调试：显示提示词内容
        logger.info(f"📝 [提示词] 长度: {len(prompt)} 字符")
        if "⚠️ 重要提示：用户已经选择了知识库" in prompt:
            logger.info("✅ [提示词] 包含知识库提示")
        else:
            logger.warning("⚠️  [提示词] 不包含知识库提示！")
        logger.info(f"📄 [提示词] 内容预览:\n{prompt[:500]}...")

        # 2. 调用 LLM 进行推理
        try:
            response = await self._call_llm(
                prompt=prompt,
                question=question,
                agent_config=agent_config,
                has_knowledge_base=has_knowledge_base  # ← 新增参数
            )

            # 3. 解析 LLM 响应
            decision = self._parse_decision(response, available_tools)
            return decision

        except Exception as e:
            logger.error(f"❌ LLM 推理失败: {e}")
            # 降级: 返回默认决策
            return self._fallback_decision(question, available_tools, previous_steps)

    def _build_reasoning_prompt(
        self,
        question: str,
        available_tools: List[str],
        conversation_history: List[Dict[str, Any]],
        previous_steps: List[Dict[str, Any]],
        agent_config: Dict[str, Any],
        has_knowledge_base: bool = False
    ) -> str:
        """构建推理提示词"""

        # 工具描述
        tool_descriptions = self._get_tool_descriptions(available_tools)

        # 对话历史摘要
        history_summary = ""
        if conversation_history:
            recent = conversation_history[-3:]  # 最近 3 轮
            # 处理 LangChain Message 对象或字典
            formatted_messages = []
            for msg in recent:
                # 如果是 LangChain Message 对象，转换为字典格式
                if hasattr(msg, 'content') and hasattr(msg, 'type'):
                    role = msg.type  # 'human', 'ai', 'system'
                    content = msg.content
                # 如果是字典格式
                else:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                formatted_messages.append(f"{role}: {str(content)[:100]}")
            history_summary = "\n".join(formatted_messages)

        # 之前步骤摘要
        steps_summary = ""
        if previous_steps:
            steps_summary = "\n".join([
                f"- 步骤 {i+1}: 使用 {step.get('tool', 'unknown')} 工具"
                for i, step in enumerate(previous_steps[-3:])
            ])

        # ✅ 知识库状态提示
        knowledge_base_hint = ""
        if has_knowledge_base:
            knowledge_base_hint = """
⚠️ 重要提示：用户已经选择了知识库！如果问题涉及信息检索，请优先使用 knowledge_search 工具。
"""

        prompt = f"""你是一个智能助手,需要分析用户问题并决定是否使用工具。

# 可用工具
{tool_descriptions}

# 用户问题
{question}

# 对话历史
{history_summary if history_summary else "(无)"}

# 之前的步骤
{steps_summary if steps_summary else "(无)"}

{knowledge_base_hint}

# 任务
请按以下格式回答:

## 推理
[你的推理过程 - 分析问题需要什么信息,是否需要使用工具]

## 工具决策
[如果需要工具,填写工具名称;如果不需要,填写 "none"]

## 工具参数
[如果选择了工具,以 JSON 格式提供参数;否则填写 "{{}}"]

## 置信度
[你对这个决策的信心程度,0-1 之间的浮点数]

## 继续执行
[工具执行后是否需要继续思考 true/false]

注意:
- 如果用户已经选择了知识库，优先使用 knowledge_search 工具
- 如果问题可以直接回答,不要使用工具
- 如果问题涉及计算、搜索、时间等,使用相应工具
- 置信度应该基于问题是否清晰、工具是否匹配
- 如果使用工具后可能需要更多信息,设置继续执行为 true
"""

        return prompt

    def _get_tool_descriptions(self, tools: List[str]) -> str:
        """获取工具描述"""
        descriptions = {
            "calculator": "计算器 - 执行数学计算,例如: '2+2', '100*5.5'",
            "datetime": "日期时间 - 获取当前日期和时间",
            "knowledge_search": "知识库搜索 - 在知识库中搜索相关信息,需要 query 参数",
            "code_executor": "代码执行 - 安全执行 Python 代码并返回结果",
            "browser": "浏览器 - 访问网页、搜索信息、抓取内容",
            "file": "文件操作 - 读取、写入、列出文件",
        }

        lines = []
        for tool in tools:
            desc = descriptions.get(tool, "未知工具")
            lines.append(f"- {tool}: {desc}")

        return "\n".join(lines) if lines else "无可用工具"

    async def _call_llm(
        self,
        prompt: str,
        question: str,
        agent_config: Dict[str, Any],
        has_knowledge_base: bool = False  # ← 新增参数
    ) -> str:
        """
        调用 LLM API（真正的 LLM 推理）

        Args:
            prompt: 完整的提示词（包含上下文）
            question: 原始用户问题（用于规则判断）
            agent_config: Agent 配置
            has_knowledge_base: 用户是否选择了知识库
        """
        try:
            # 检查模型配置
            if not self._model_config:
                logger.error("❌ LLM 模型未配置，无法调用 API")
                # 降级到规则引擎
                return await self._call_ias_direct(
                    request=None,
                    question=question,
                    has_knowledge_base=has_knowledge_base
                )

            # 获取 API Key 和 URL
            api_key = self._model_config.get("api_key")
            api_url = self._model_config.get("api_url")
            model_name = self._model_config.get("name")

            if not api_key or not api_url:
                logger.error(f"❌ LLM API 配置不完整: api_key={bool(api_key)}, api_url={bool(api_url)}")
                # 降级到规则引擎
                return await self._call_ias_direct(
                    request=None,
                    question=question,
                    has_knowledge_base=has_knowledge_base
                )

            logger.info(f"🤖 [LLM 调用] 使用模型: {model_name}")
            logger.info(f"📝 [LLM 调用] Prompt 长度: {len(prompt)} 字符")
            logger.info(f"🌐 [LLM 调用] API URL: {api_url}")

            # 构建请求体（智谱 AI OpenAI 兼容格式）
            request_data = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "你是一个智能助手,擅长推理和工具使用决策。请严格按照指定的格式回答。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "stream": False
            }

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 直接调用 API
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("🌐 [LLM 调用] 发送请求...")
                response = await client.post(
                    api_url,
                    json=request_data,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"❌ [LLM 调用] API 返回错误: {response.status_code}")
                    logger.error(f"❌ [LLM 调用] 响应内容: {response.text[:500]}")
                    # 降级到规则引擎
                    return await self._call_ias_direct(
                        request=None,
                        question=question,
                        has_knowledge_base=has_knowledge_base
                    )

                # 解析响应
                response_json = response.json()
                logger.info(f"✅ [LLM 调用] API 调用成功")

                # 智谱 AI 响应格式: {"choices": [{"message": {"content": "..."}}]}
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    content = response_json["choices"][0]["message"]["content"]
                    logger.info(f"✅ [LLM 响应] 内容长度: {len(content)} 字符")
                    logger.info(f"📄 [LLM 响应] 内容预览: {content[:200]}...")
                    return content
                else:
                    logger.error(f"❌ [LLM 响应] 格式错误: {response_json}")
                    # 降级到规则引擎
                    return await self._call_ias_direct(
                        request=None,
                        question=question,
                        has_knowledge_base=has_knowledge_base
                    )

        except Exception as e:
            logger.error(f"❌ LLM API 调用失败: {e}")
            logger.error(f"❌ [错误详情] {type(e).__name__}: {str(e)}")
            # 降级到规则引擎
            logger.info("⬇️  [降级] 使用规则引擎作为降级方案")
            return await self._call_ias_direct(
                request=None,
                question=question,
                has_knowledge_base=has_knowledge_base
            )

    async def _call_ias_direct(
        self,
        request: Optional[IASChatRequest],
        question: str,
        has_knowledge_base: bool = False  # ← 新增参数
    ) -> str:
        """
        降级方案：使用规则引擎（当 LLM API 不可用时）

        Args:
            request: IAS 请求对象（未使用，保留兼容性）
            question: 原始用户问题（用于规则判断）
            has_knowledge_base: 用户是否选择了知识库

        注意：这是降级方案，优先使用真正的 LLM API
        """
        # 这里应该调用真实的 IAS API
        # 暂时使用规则引擎进行降级处理

        logger.info(f"📋 [规则引擎] 分析问题: {question[:50]}...")
        logger.info(f"📚 [规则引擎] 知识库状态: {'已选择' if has_knowledge_base else '未选择'}")

        # ✅ Phase 1 关键修复: 如果用户选择了知识库，优先使用知识库搜索
        if has_knowledge_base:
            logger.info("🎯 [规则引擎] 检测到知识库选择，优先使用知识库搜索")
            # 使用实际的查询内容，而不是硬编码
            query_json = json.dumps({"query": question}, ensure_ascii=False)
            return f"""## 推理
用户选择了知识库，应该使用知识库搜索工具查找相关信息

## 工具决策
knowledge_search

## 工具参数
{query_json}

## 置信度
0.95

## 继续执行
false
"""

        # 简单规则判断 (基于原始问题)
        question_lower = question.lower()

        # 规则 1: 计算类问题
        if any(keyword in question for keyword in ["计算", "加", "减", "乘", "除", "+", "-", "*", "/", "="]):
            logger.info("🎯 [规则引擎] 匹配规则: 计算")
            expression_json = json.dumps({"expression": question}, ensure_ascii=False)
            return f"""## 推理
用户问题涉及数学计算,需要使用计算器工具

## 工具决策
calculator

## 工具参数
{expression_json}

## 置信度
0.95

## 继续执行
false
"""

        # 规则 2: 时间日期类问题
        elif any(keyword in question for keyword in ["时间", "日期", "几点", "现在", "今天", "几点了"]):
            logger.info("🎯 [规则引擎] 匹配规则: 时间日期")
            return """## 推理
用户询问当前时间或日期,需要使用日期时间工具

## 工具决策
datetime

## 工具参数
{}

## 置信度
0.95

## 继续执行
false
"""

        # 规则 3: 搜索类问题
        elif any(keyword in question_lower for keyword in ["搜索", "search", "查找", "知识", "信息", "什么是"]):
            logger.info("🎯 [规则引擎] 匹配规则: 搜索")
            query_json = json.dumps({"query": question}, ensure_ascii=False)
            return f"""## 推理
用户需要查找信息,应该使用知识库搜索工具

## 工具决策
knowledge_search

## 工具参数
{query_json}

## 置信度
0.90

## 继续执行
false
"""

        # 规则 4: 问候类问题（直接回答）
        elif any(keyword in question for keyword in ["你好", "hello", "hi", "嗨", "您好"]):
            logger.info("🎯 [规则引擎] 匹配规则: 问候")
            return """## 推理
用户在打招呼,应该友好回应,不需要使用工具

## 工具决策
none

## 工具参数
{}

## 置信度
0.95

## 继续执行
false
"""

        else:
            # 默认: 不使用工具,尝试直接回答
            logger.info("🎯 [规则引擎] 使用默认规则")
            return """## 推理
问题可以直接回答或不需要特定工具,将尝试提供有帮助的回复

## 工具决策
none

## 工具参数
{}

## 置信度
0.70

## 继续执行
false
"""

    def _parse_decision(self, response: str, available_tools: List[str]) -> Dict[str, Any]:
        """解析 LLM 响应为决策"""
        try:
            # 提取各个部分
            reasoning = self._extract_section(response, "推理")
            tool = self._extract_section(response, "工具决策").strip().lower()
            parameters_str = self._extract_section(response, "工具参数")
            confidence = float(self._extract_section(response, "置信度").strip())
            should_continue_str = self._extract_section(response, "继续执行").strip().lower()
            should_continue = should_continue_str in ["true", "yes", "是"]

            # 解析参数 JSON
            try:
                parameters = json.loads(parameters_str) if parameters_str != "{}" else {}
            except json.JSONDecodeError:
                logger.warning(f"⚠️ 工具参数 JSON 解析失败: {parameters_str}")
                parameters = {}

            # 验证工具是否可用
            if tool and tool != "none" and tool not in available_tools:
                logger.warning(f"⚠️ LLM 选择的工具 {tool} 不可用,降级到 none")
                tool = "none"

            return {
                "reasoning": reasoning,
                "tool": tool if tool != "none" else None,
                "parameters": parameters,
                "confidence": confidence,
                "should_continue": should_continue
            }

        except Exception as e:
            logger.error(f"❌ 解析决策失败: {e}")
            # 返回安全默认值
            return {
                "reasoning": response[:200] if response else "解析失败",
                "tool": None,
                "parameters": {},
                "confidence": 0.5,
                "should_continue": False
            }

    def _extract_section(self, text: str, section_name: str) -> str:
        """提取文本中的某个部分"""
        # 查找 ## section_name
        marker = f"## {section_name}"
        if marker not in text:
            return ""

        start = text.index(marker) + len(marker)
        # 查找下一个 ## 或文本结束
        next_marker = text.find("##", start)
        if next_marker == -1:
            return text[start:].strip()
        else:
            return text[start:next_marker].strip()

    def _fallback_decision(
        self,
        question: str,
        available_tools: List[str],
        previous_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        降级决策 (当 LLM 调用失败时)

        使用简单规则进行工具选择
        """
        question_lower = question.lower()

        # 规则 1: 计算
        if any(word in question for word in ["计算", "加", "减", "乘", "除", "+", "-", "*", "/"]) and "calculator" in available_tools:
            return {
                "reasoning": "问题涉及数学计算,使用计算器",
                "tool": "calculator",
                "parameters": {"expression": question},
                "confidence": 0.70,
                "should_continue": False
            }

        # 规则 2: 日期时间
        if any(word in question for word in ["时间", "日期", "几点", "今天", "现在"]) and "datetime" in available_tools:
            return {
                "reasoning": "问题询问当前时间,使用日期时间工具",
                "tool": "datetime",
                "parameters": {},
                "confidence": 0.80,
                "should_continue": False
            }

        # 规则 3: 知识库搜索
        if any(word in question for word in ["搜索", "查找", "知识", "信息"]) and "knowledge_search" in available_tools:
            return {
                "reasoning": "问题需要搜索信息,使用知识库",
                "tool": "knowledge_search",
                "parameters": {"query": question},
                "confidence": 0.70,
                "should_continue": False
            }

        # 默认: 不使用工具
        return {
            "reasoning": "问题可以直接回答,不需要工具",
            "tool": None,
            "parameters": {},
            "confidence": 0.60,
            "should_continue": False
        }

    async def generate_final_answer(
        self,
        question: str,
        tools_called: List[Dict[str, Any]],
        agent_config: Dict[str, Any]
    ) -> str:
        """
        生成最终答案

        Args:
            question: 用户问题
            tools_called: 工具调用记录
            agent_config: Agent 配置

        Returns:
            最终答案
        """
        # 这个方法在 agent_service.py 中已实现
        # 这里只是接口定义
        raise NotImplementedError("使用 AgentService._generate_final_answer 代替")
