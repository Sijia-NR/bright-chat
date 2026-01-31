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
import re
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
        执行推理决策（纯 LLM 驱动，无规则引擎）

        Args:
            question: 用户问题
            available_tools: 可用工具列表
            conversation_history: 对话历史
            previous_steps: 之前的执行步骤
            agent_config: Agent 配置

        Returns:
            决策结果
        """
        # 检测知识库状态
        knowledge_base_ids = agent_config.get("knowledge_base_ids", [])
        has_knowledge_base = len(knowledge_base_ids) > 0

        logger.info(f"🤖 [LLM 推理] agent_config: {agent_config}")
        logger.info(f"🤖 [LLM 推理] knowledge_base_ids: {knowledge_base_ids}")
        logger.info(f"🤖 [LLM 推理] has_knowledge_base: {has_knowledge_base}")
        logger.info(f"🤖 [LLM 推理] 使用纯 LLM 分析（无规则引擎）")

        try:
            # 构建增强的 prompt
            prompt = self._build_reasoning_prompt(
                question, available_tools, conversation_history,
                previous_steps, agent_config, has_knowledge_base
            )

            # 调用 LLM
            response = await self._call_llm(prompt, question, agent_config, has_knowledge_base)

            # 解析决策
            decision = self._parse_decision(response, available_tools)

            logger.info(f"✅ [LLM 推理] 工具: {decision.get('tool')}, 置信度: {decision.get('confidence', 0)}")

            return decision

        except Exception as e:
            logger.error(f"❌ LLM 推理失败: {e}")
            # 降级到简单规则（仅作为后备）
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
✅ 用户已选择知识库：可以使用 knowledge_search 工具检索信息
"""
        else:
            knowledge_base_hint = """
❌ 用户未选择知识库：禁止使用 knowledge_search 工具（请直接回答或使用其他工具）
"""

        prompt = f"""你是一个专业的智能体工具决策专家。

# 可用工具
{tool_descriptions}

# 用户问题
{question}

{knowledge_base_hint}

# 🎯 核心决策原则

1. **理解用户意图**: 仔细分析用户真正想要做什么
2. **工具优先级**:
   - 用户明确要求使用某个工具 → 优先使用该工具
   - 计算问题 → 优先使用 code_executor（更精确）
   - 时间/日期 → datetime
   - 网页操作 → browser
     - 直接访问URL → action: "scrape"
     - 搜索关键词 → action: "search"
   - 信息检索 → 仅在用户已选择知识库时使用 knowledge_search
3. **直接回答场景**:
   - 问候、闲聊不需要工具
   - 用户未选择知识库时，信息类问题应直接回答
4. **参数完整性**: 确保工具所需参数完整且正确

# ⚠️ 重要：必须返回完整的 JSON 格式

{{
  "reasoning": "详细分析：为什么选择这个工具，用户的意图是什么",
  "tool": "工具名称或 null",
  "parameters": {{"参数名": "参数值"}},
  "confidence": 0.95,
  "should_continue": false
}}

# 💡 完整示例（必须包含所有字段）

1. 计算问题：
{{
  "reasoning": "用户要求进行数学计算，使用 code_executor 工具执行 Python 代码",
  "tool": "code_executor",
  "parameters": {{"code": "print(100 * 200)"}},
  "confidence": 0.95,
  "should_continue": false
}}

2. 查询时间：
{{
  "reasoning": "用户询问当前时间，使用 datetime 工具获取",
  "tool": "datetime",
  "parameters": {{}},
  "confidence": 0.95,
  "should_continue": false
}}

3. 问候：
{{
  "reasoning": "用户在打招呼，直接友好回应，不需要使用工具",
  "tool": null,
  "parameters": {{}},
  "confidence": 0.95,
  "should_continue": false
}}

4. 直接访问网页：
{{
  "reasoning": "用户要求总结指定网页内容，使用 browser 工具的 scrape 操作直接获取网页",
  "tool": "browser",
  "parameters": {{"action": "scrape", "url": "https://example.com"}},
  "confidence": 0.95,
  "should_continue": false
}}

5. 搜索网页：
{{
  "reasoning": "用户要求搜索相关信息，使用 browser 工具的 search 操作",
  "tool": "browser",
  "parameters": {{"action": "search", "text": "Python教程"}},
  "confidence": 0.90,
  "should_continue": false
}}

6. 知识库搜索（已选择知识库）：
{{
  "reasoning": "用户已选择知识库，使用 knowledge_search 工具检索相关信息",
  "tool": "knowledge_search",
  "parameters": {{"query": "Python教程"}},
  "confidence": 0.95,
  "should_continue": false
}}

现在请分析用户问题，返回完整的 JSON（必须包含所有5个字段）：
"""

        return prompt

    def _get_tool_descriptions(self, tools: List[str]) -> str:
        """获取工具描述"""
        descriptions = {
            "calculator": "计算器 - 执行数学计算,例如: '2+2', '100*5.5'",
            "datetime": "日期时间 - 获取当前日期和时间",
            "knowledge_search": "知识库搜索 - 在知识库中搜索相关信息,需要 query 参数",
            "code_executor": "代码执行 - 安全执行 Python 代码并返回结果",
            "browser": "浏览器 - 访问网页、搜索信息、抓取内容。参数: action(navigate/scrape/search), url(可选), text(可选)",
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
                raise ValueError("LLM 模型未配置")

            # 获取 API Key 和 URL
            api_key = self._model_config.get("api_key")
            api_url = self._model_config.get("api_url")
            model_name = self._model_config.get("name")

            if not api_key or not api_url:
                logger.error(f"❌ LLM API 配置不完整: api_key={bool(api_key)}, api_url={bool(api_url)}")
                raise ValueError("LLM API 配置不完整")

            logger.info(f"🤖 [LLM 调用] 使用模型: {model_name}")
            logger.info(f"📝 [LLM 调用] Prompt 长度: {len(prompt)} 字符")
            logger.info(f"🌐 [LLM 调用] API URL: {api_url}")

            # 构建请求体（智谱 AI OpenAI 兼容格式）
            request_data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是 Agent 的工具决策专家。严格遵守规则：用户明确要求使用工具时必须使用该工具。使用 Few-shot 示例来理解格式。"
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # 降低温度以获得更确定的输出
                "top_p": 0.9,
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
                    raise ValueError(f"LLM API 返回错误: {response.status_code}")

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
                    raise ValueError("LLM 响应格式错误")

        except Exception as e:
            logger.error(f"❌ LLM API 调用失败: {e}")
            logger.error(f"❌ [错误详情] {type(e).__name__}: {str(e)}")
            # 抛出异常，让上层处理
            raise

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

        # ✅ 规则 1.5: 代码执行类问题（最高优先级）
        # 检测用户明确要求使用代码执行
        if any(keyword in question for keyword in ["使用代码", "执行代码", "用代码", "代码执行", "python代码", "运行代码"]):
            logger.info("🎯 [规则引擎] 匹配规则: 代码执行（高优先级）")
            # 提取计算表达式
            # 尝试提取数学表达式
            expr_match = re.search(r'(\d+(?:\s*[\*\+\-\/]\s*\d+)+)', question)
            if expr_match:
                expression = expr_match.group(1)
            else:
                expression = question
            code_json = json.dumps({"code": f"print({expression})"}, ensure_ascii=False)
            return f"""## 推理
用户明确要求使用代码执行计算,必须使用 code_executor 工具

## 工具决策
code_executor

## 工具参数
{code_json}

## 置信度
0.98

## 继续执行
false
"""

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
        """解析 LLM 响应为决策（支持多种格式）"""
        try:
            response_stripped = response.strip()

            # 🔍 格式 1: 标准 JSON（以 { 开头）
            if response_stripped.startswith('{'):
                logger.info(f"📋 [格式检测] 标准 JSON")
                return self._parse_json_format(response_stripped, available_tools)

            # 🔍 格式 2: JSON 代码块（```json ... ```）
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                logger.info(f"📋 [格式检测] JSON 代码块")
                return self._parse_json_format(json_match.group(1), available_tools)

            # 🔍 格式 3: 工具名 + JSON 参数（新格式）
            # 例如: browser\n{"action": "search", "url": "..."}
            lines = response_stripped.split('\n', 1)
            if len(lines) == 2:
                first_line = lines[0].strip()
                second_line = lines[1].strip()

                if first_line in available_tools and second_line.startswith('{'):
                    logger.info(f"📋 [格式检测] 工具名+参数格式")
                    logger.info(f"   工具: {first_line}")

                    try:
                        parameters = json.loads(second_line)
                        logger.info(f"   参数: {parameters}")

                        return {
                            "reasoning": f"使用 {first_line} 工具执行任务",
                            "tool": first_line,
                            "parameters": parameters,
                            "confidence": 0.9,
                            "should_continue": False
                        }
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ 参数解析失败: {e}")

            # 🔍 格式 4: Markdown 格式（包含 ## 标题）
            has_markdown_sections = any(
                f"## {section}" in response
                for section in ["推理", "工具决策", "工具参数", "置信度", "继续执行"]
            )

            if has_markdown_sections:
                logger.info(f"📋 [格式检测] Markdown 格式")
                return self._parse_markdown_format(response, available_tools)

            # 🔍 格式 5: 直接答案（兜底）
            logger.info(f"📋 [格式检测] 直接答案（非结构化文本）")
            logger.info(f"📄 [直接答案] 内容: {response[:100]}...")

            return {
                "reasoning": response,
                "tool": None,
                "parameters": {},
                "confidence": 0.9,
                "should_continue": False
            }

        except Exception as e:
            logger.error(f"❌ 解析决策失败: {e}")
            logger.error(f"📄 响应内容: {response[:500]}")
            return {
                "reasoning": response[:200] if response else "解析失败",
                "tool": None,
                "parameters": {},
                "confidence": 0.5,
                "should_continue": False
            }

    def _parse_json_format(self, json_str: str, available_tools: List[str]) -> Dict[str, Any]:
        """解析标准 JSON 格式"""
        try:
            data = json.loads(json_str)
            if data is None:
                data = {}

            logger.info(f"✅ [JSON 解析] 成功")

            tool = data.get("tool")
            if tool is None or tool == "null":
                tool = None
            elif isinstance(tool, str):
                tool = tool.strip().lower()
                if tool in ["none", "null"]:
                    tool = None

            if tool and tool not in available_tools:
                logger.warning(f"⚠️ 工具 {tool} 不可用")
                tool = None

            return {
                "reasoning": data.get("reasoning", ""),
                "tool": tool,
                "parameters": data.get("parameters", {}),
                "confidence": float(data.get("confidence", 0.8)),
                "should_continue": bool(data.get("should_continue", False))
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ [JSON 解析] 失败: {e}")
            raise

    def _parse_markdown_format(self, response: str, available_tools: List[str]) -> Dict[str, Any]:
        """解析 Markdown 格式"""
        reasoning = self._extract_section(response, "推理")
        tool = self._extract_section(response, "工具决策").strip().lower()
        parameters_str = self._extract_section(response, "工具参数")
        confidence_str = self._extract_section(response, "置信度").strip()
        should_continue_str = self._extract_section(response, "继续执行").strip().lower()

        # 解析参数
        try:
            parameters = json.loads(parameters_str) if parameters_str and parameters_str != "{}" else {}
        except json.JSONDecodeError:
            logger.warning(f"⚠️ 参数解析失败")
            parameters = {}

        # 解析置信度
        try:
            confidence = float(confidence_str) if confidence_str else 0.5
        except ValueError:
            confidence = 0.5

        should_continue = should_continue_str in ["true", "yes", "是"]

        # 验证工具
        if tool and tool != "none" and tool not in available_tools:
            logger.warning(f"⚠️ 工具 {tool} 不可用")
            tool = "none"

        return {
            "reasoning": reasoning,
            "tool": tool if tool != "none" else None,
            "parameters": parameters,
            "confidence": confidence,
            "should_continue": should_continue
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

        # ✅ 规则 0: 代码执行（最高优先级）
        if any(word in question for word in ["使用代码", "执行代码", "用代码", "代码执行"]) and "code_executor" in available_tools:
            # 提取表达式
            expr_match = re.search(r'(\d+(?:\s*[\*\+\-\/]\s*\d+)+)', question)
            if expr_match:
                expression = expr_match.group(1)
                code = f"print({expression})"
            else:
                code = question
            return {
                "reasoning": "用户明确要求使用代码执行",
                "tool": "code_executor",
                "parameters": {"code": code},
                "confidence": 0.95,
                "should_continue": False
            }

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
