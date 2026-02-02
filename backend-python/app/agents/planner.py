"""
任务规划器 - Agent 的规划引擎

负责：
1. 分析查询复杂度（简单/复杂）
2. 将复杂查询分解为子任务
3. 生成执行计划

参考：AutoGPT、BabyAGI 的任务分解设计
"""

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================== 枚举类型 ====================

class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"      # 单步完成，直接执行
    COMPLEX = "complex"    # 需要分解为多个子任务


class TaskPriority(Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStrategy(Enum):
    """执行策略"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行（暂未实现）


# ==================== 数据类 ====================

@dataclass
class SubTask:
    """子任务"""
    id: str                               # task_1, task_2...
    description: str                      # 简短描述
    objective: str                        # 具体目标
    priority: str                         # high/medium/low
    dependencies: List[str]               # 依赖的任务ID
    required_tools: List[str]             # 需要的工具
    estimated_steps: int                  # 预计步骤数
    success_criteria: Dict                # 成功标准
    status: str = TaskStatus.PENDING.value  # 当前状态

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "objective": self.objective,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "required_tools": self.required_tools,
            "estimated_steps": self.estimated_steps,
            "success_criteria": self.success_criteria,
            "status": self.status
        }


@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    original_query: str
    subtasks: List[SubTask]
    execution_strategy: str               # sequential/parallel
    estimated_duration: int               # 预计时长（秒）
    confidence_score: float               # 置信度 0-1
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_simple(self) -> bool:
        """是否为简单计划（单任务）"""
        return len(self.subtasks) <= 1

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "original_query": self.original_query,
            "subtasks": [task.to_dict() for task in self.subtasks],
            "execution_strategy": self.execution_strategy,
            "estimated_duration": self.estimated_duration,
            "confidence_score": self.confidence_score,
            "is_simple": self.is_simple,
            "created_at": self.created_at.isoformat()
        }


# ==================== 任务规划器 ====================

class TaskPlanner:
    """
    任务规划引擎

    功能：
    1. 分析查询复杂度
    2. 分解复杂任务为子任务
    3. 生成执行计划
    """

    def __init__(self, reasoner):
        """
        初始化任务规划器

        Args:
            reasoner: LLMReasoner 实例，用于 LLM 调用
        """
        self.reasoner = reasoner
        logger.info("📋 TaskPlanner 初始化完成")

    async def create_plan(
        self,
        query: str,
        available_tools: List[str],
        agent_config: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        创建执行计划

        Args:
            query: 用户查询
            available_tools: 可用工具列表
            agent_config: Agent 配置

        Returns:
            ExecutionPlan: 执行计划
        """
        logger.info(f"📋 [规划器] 开始分析查询: {query[:100]}...")

        # 1. 分析复杂度
        complexity = await self._analyze_complexity(query)
        logger.info(f"🔍 [规划器] 复杂度分析结果: {complexity.value}")

        # 2. 简单查询 → 单任务计划
        if complexity == TaskComplexity.SIMPLE:
            logger.info("✅ [规划器] 简单查询，创建单任务计划")
            return self._create_simple_plan(query, available_tools, agent_config)

        # 3. 复杂查询 → LLM 分解任务
        logger.info("🔄 [规划器] 复杂查询，开始任务分解...")
        try:
            plan = await self._decompose_task(query, available_tools, agent_config)
            logger.info(f"✅ [规划器] 任务分解完成: {len(plan.subtasks)} 个子任务")
            return plan
        except Exception as e:
            logger.error(f"❌ [规划器] 任务分解失败: {e}")
            # Fallback: 创建单任务计划
            logger.info("⬇️ [规划器] 降级到单任务计划")
            return self._create_simple_plan(query, available_tools, agent_config)

    async def _analyze_complexity(self, query: str) -> TaskComplexity:
        """
        分析查询复杂度

        Args:
            query: 用户查询

        Returns:
            TaskComplexity: SIMPLE 或 COMPLEX
        """
        # 方法1: 基于关键词的快速规则判断
        rule_result = self._rule_based_complexity_check(query)
        if rule_result is not None:
            return rule_result

        # 方法2: 使用 LLM 判断（如果可用）
        try:
            if self.reasoner and hasattr(self.reasoner, '_call_llm'):
                return await self._llm_based_complexity_check(query)
        except Exception as e:
            logger.warning(f"⚠️ [规划器] LLM 复杂度判断失败，使用规则: {e}")

        # 默认: 简单查询
        return TaskComplexity.SIMPLE

    def _rule_based_complexity_check(self, query: str) -> Optional[TaskComplexity]:
        """
        基于规则的复杂度判断（快速路径）

        Returns:
            TaskComplexity 或 None（无法判断）
        """
        query_lower = query.lower()

        # ========== 简单查询特征 ==========
        # 单一意图问题
        simple_patterns = [
            r"现在几点",  # 时间
            r"今天.*日期",  # 日期
            r"计算\s*[\d+\-*/\s]+",  # 纯计算
            r"^[\d+\-*/\s]+$",  # 纯表达式
            r"你好|hello|hi",  # 问候
        ]

        for pattern in simple_patterns:
            if re.search(pattern, query):
                logger.debug(f"🔍 [规则] 匹配简单查询模式: {pattern}")
                return TaskComplexity.SIMPLE

        # ========== 复杂查询特征 ==========
        # 多意图、需要分解的查询
        complex_keywords = [
            "研究",  # 研究X
            "对比",  # 对比X和Y
            "分析",  # 分析X
            "总结",  # 总结X
            "制定",  # 制定计划
            "并列",  # 并列列出
            "分别",  # 分别处理
            "首先.*然后",  # 多步骤
            "步骤",  # 多步骤
            "包括.*和",  # 多个目标
        ]

        for keyword in complex_keywords:
            if keyword in query:
                logger.debug(f"🔍 [规则] 匹配复杂查询关键词: {keyword}")
                return TaskComplexity.COMPLEX

        # 句子长度判断（超过50字且包含多个动词，可能是复杂查询）
        if len(query) > 50 and "，" in query:
            logger.debug("🔍 [规则] 长句且包含逗号，判定为复杂查询")
            return TaskComplexity.COMPLEX

        # 无法通过规则判断
        return None

    async def _llm_based_complexity_check(self, query: str) -> TaskComplexity:
        """
        使用 LLM 判断查询复杂度

        Args:
            query: 用户查询

        Returns:
            TaskComplexity
        """
        prompt = f"""分析以下查询的复杂程度：

查询: {query}

请判断这是一个简单查询还是复杂查询:

简单查询特征:
- 单一意图
- 可以直接回答或使用单个工具完成
- 不需要多步骤推理
- 例如: "现在几点了?", "计算 2+2", "搜索 Python 教程"

复杂查询特征:
- 多个意图或目标
- 需要多个步骤完成
- 需要综合多个信息源
- 需要推理或分析
- 例如: "研究2024年AI发展趋势并总结关键点",
       "对比分析三个产品的优缺点",
       "制定一个学习计划并寻找相关资源"

请只回答一个词: simple 或 complex
"""

        try:
            response = await self.reasoner._call_llm(
                prompt=prompt,
                question=query,
                agent_config={},
                has_knowledge_base=False
            )

            response_lower = response.strip().lower()
            if "complex" in response_lower:
                return TaskComplexity.COMPLEX
            else:
                return TaskComplexity.SIMPLE

        except Exception as e:
            logger.warning(f"⚠️ [规划器] LLM 复杂度判断失败: {e}")
            raise

    def _create_simple_plan(
        self,
        query: str,
        available_tools: List[str],
        agent_config: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        创建简单查询的单任务计划

        Args:
            query: 用户查询
            available_tools: 可用工具列表
            agent_config: Agent 配置

        Returns:
            ExecutionPlan
        """
        # 创建单任务
        subtask = SubTask(
            id="task_1",
            description="直接回答用户问题",
            objective=query,
            priority=TaskPriority.MEDIUM.value,
            dependencies=[],
            required_tools=[],  # 由推理器动态决定
            estimated_steps=1,
            success_criteria={"type": "direct_answer"},
            status=TaskStatus.PENDING.value
        )

        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            original_query=query,
            subtasks=[subtask],
            execution_strategy=ExecutionStrategy.SEQUENTIAL.value,
            estimated_duration=5,
            confidence_score=0.9
        )

        return plan

    async def _decompose_task(
        self,
        query: str,
        available_tools: List[str],
        agent_config: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        使用 LLM 将复杂查询分解为子任务

        Args:
            query: 用户查询
            available_tools: 可用工具列表
            agent_config: Agent 配置

        Returns:
            ExecutionPlan
        """
        # 构建工具描述
        tool_descriptions = self._build_tool_descriptions(available_tools)

        # 构建提示词
        prompt = TASK_DECOMPOSITION_PROMPT.format(
            tool_descriptions=tool_descriptions,
            query=query
        )

        # 调用 LLM
        response = await self.reasoner._call_llm(
            prompt=prompt,
            question=query,
            agent_config=agent_config,
            has_knowledge_base=agent_config.get("knowledge_base_ids", []) != []
        )

        # 解析 JSON 响应
        try:
            json_match = self._extract_json(response)
            if not json_match:
                raise ValueError("LLM 响应中未找到 JSON")

            plan_data = json.loads(json_match)

            # 构建 ExecutionPlan
            subtasks = []
            for i, task_data in enumerate(plan_data.get("subtasks", [])):
                subtask = SubTask(
                    id=task_data.get("id", f"task_{i+1}"),
                    description=task_data.get("description", ""),
                    objective=task_data.get("objective", ""),
                    priority=task_data.get("priority", TaskPriority.MEDIUM.value),
                    dependencies=task_data.get("dependencies", []),
                    required_tools=task_data.get("required_tools", []),
                    estimated_steps=task_data.get("estimated_steps", 2),
                    success_criteria=task_data.get("success_criteria", {}),
                    status=TaskStatus.PENDING.value
                )
                subtasks.append(subtask)

            # 验证子任务数量
            if len(subtasks) == 0:
                raise ValueError("未生成任何子任务")

            # 限制子任务数量（防止过度分解）
            if len(subtasks) > 7:
                logger.warning(f"⚠️ [规划器] 子任务过多 ({len(subtasks)})，限制为前7个")
                subtasks = subtasks[:7]

            plan = ExecutionPlan(
                plan_id=str(uuid.uuid4()),
                original_query=query,
                subtasks=subtasks,
                execution_strategy=plan_data.get("execution_strategy", ExecutionStrategy.SEQUENTIAL.value),
                estimated_duration=plan_data.get("estimated_duration", 120),
                confidence_score=plan_data.get("confidence", 0.85)
            )

            return plan

        except Exception as e:
            logger.error(f"❌ [规划器] 解析任务分解结果失败: {e}")
            logger.error(f"❌ [规划器] LLM 响应: {response[:500]}")
            raise

    def _build_tool_descriptions(self, tools: List[str]) -> str:
        """构建工具描述"""
        descriptions = {
            "calculator": "计算器 - 执行数学计算",
            "datetime": "日期时间 - 获取当前日期和时间",
            "knowledge_search": "知识库搜索 - 在知识库中搜索相关信息",
            "code_executor": "代码执行 - 安全执行 Python 代码",
            "browser": "浏览器 - 访问网页、搜索信息、抓取内容",
            "file": "文件操作 - 读取、写入、列出文件",
        }

        lines = []
        for tool in tools:
            desc = descriptions.get(tool, "未知工具")
            lines.append(f"- {tool}: {desc}")

        return "\n".join(lines) if lines else "无可用工具"

    def _extract_json(self, text: str) -> Optional[str]:
        """
        从文本中提取 JSON

        Args:
            text: 可能包含 JSON 的文本

        Returns:
            JSON 字符串或 None
        """
        # 尝试直接解析
        try:
            json.loads(text.strip())
            return text.strip()
        except:
            pass

        # 尝试提取 ```json ... ``` 代码块
        json_block_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 尝试提取 {...} 花括号内容
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(brace_pattern, text, re.DOTALL)
        if match:
            return match.group(0).strip()

        return None


# ==================== 提示词模板 ====================

TASK_DECOMPOSITION_PROMPT = """你是一个任务规划专家。请将用户的复杂查询分解为可执行的子任务。

# 可用工具
{tool_descriptions}

# 用户查询
{query}

# 任务要求
请分析用户查询，将其分解为 3-7 个子任务。每个子任务应该:
1. 目标明确 - 清楚说明要达成什么
2. 可执行 - 知道具体需要做什么
3. 可验证 - 有明确的成功标准
4. 依赖关系 - 标识依赖的前置任务

# 输出格式 (JSON)
```json
{{
    "subtasks": [
        {{
            "id": "task_1",
            "description": "简短描述（一句话）",
            "objective": "具体目标（详细说明）",
            "priority": "high|medium|low",
            "dependencies": [],
            "required_tools": ["tool1", "tool2"],
            "estimated_steps": 2,
            "success_criteria": {{
                "type": "information_retrieval|analysis|calculation",
                "min_quality": 0.8,
                "expected_output": "描述期望的输出"
            }}
        }}
    ],
    "execution_strategy": "sequential",
    "estimated_duration": 120,
    "confidence": 0.85
}}
```

请生成 JSON 格式的任务分解方案:
"""


COMPLEXITY_ANALYSIS_PROMPT = """分析以下查询的复杂程度：

查询: {query}

请判断这是一个简单查询还是复杂查询:

简单查询特征:
- 单一意图
- 可以直接回答或使用单个工具完成
- 不需要多步骤推理
- 例如: "现在几点了?", "计算 2+2", "搜索 Python 教程"

复杂查询特征:
- 多个意图或目标
- 需要多个步骤完成
- 需要综合多个信息源
- 需要推理或分析
- 例如: "研究2024年AI发展趋势并总结关键点",
       "对比分析三个产品的优缺点",
       "制定一个学习计划并寻找相关资源"

请只回答一个词: simple 或 complex
"""
