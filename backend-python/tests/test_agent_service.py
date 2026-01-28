"""
Agent 服务测试
Test Agent Service
"""
import pytest
import asyncio
from tests.test_utils import TestAgentBuilder


@pytest.mark.agent
@pytest.mark.unit
class TestAgentService:
    """Agent服务测试"""

    def test_service_initialization(self):
        """测试服务初始化"""
        try:
            from agents.agent_service import AgentService
            service = AgentService()

            assert service is not None
            assert service.tools is not None
            assert len(service.tools) > 0

        except ImportError:
            pytest.skip("Agent模块未安装")

    def test_default_tools_registered(self):
        """测试默认工具注册"""
        try:
            from agents.agent_service import AgentService
            service = AgentService()

            # 检查默认工具
            assert "calculator" in service.tools
            assert "datetime" in service.tools
            assert "knowledge_search" in service.tools

        except ImportError:
            pytest.skip("Agent模块未安装")

    def test_calculator_tool(self):
        """测试计算器工具"""
        try:
            from agents.tools.calculator import calculator_tool

            # 测试基本计算
            result = calculator_tool(expression="2 + 3 * 4")
            assert result == 14

            # 测试复杂计算
            result = calculator_tool(expression="(10 + 5) / 3")
            assert abs(result - 5.0) < 0.001

        except ImportError:
            pytest.skip("Agent模块未安装")

    def test_calculator_error_handling(self):
        """测试计算器错误处理"""
        try:
            from agents.tools.calculator import calculator_tool

            # 测试除零错误
            result = calculator_tool(expression="1 / 0")
            assert "error" in str(result).lower() or "除数不能为零" in str(result)

            # 测试语法错误
            result = calculator_tool(expression="2 + * 3")
            assert "error" in str(result).lower() or "语法" in str(result).lower()

        except ImportError:
            pytest.skip("Agent模块未安装")

    def test_datetime_tool(self):
        """测试日期时间工具"""
        try:
            from agents.tools.datetime_tool import datetime_tool

            result = datetime_tool()

            assert result is not None
            assert "datetime" in result
            assert "date" in result
            assert "time" in result
            assert "year" in result
            assert "month" in result
            assert "day" in result

        except ImportError:
            pytest.skip("Agent模块未安装")


@pytest.mark.agent
@pytest.mark.unit
class TestAgentWorkflow:
    """Agent工作流测试"""

    @pytest.mark.asyncio
    async def test_agent_graph_creation(self):
        """测试Agent图创建"""
        try:
            from agents.agent_service import AgentService
            from app.models.agent import Agent

            service = AgentService()

            # 创建测试Agent
            agent_data = TestAgentBuilder.build(
                name="test_workflow_agent",
                tools=["calculator", "datetime"]
            )
            agent = Agent(**agent_data)

            # 创建图
            graph = service.create_agent_graph(agent, "test-user-001")

            assert graph is not None

        except ImportError:
            pytest.skip("Agent模块未安装")

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """测试工具执行"""
        try:
            from agents.agent_service import AgentService
            service = AgentService()

            # 测试计算器工具执行
            result = await service.execute_tool(
                tool_name="calculator",
                parameters={"expression": "5 + 3"},
                context={"user_id": "test-user-001"}
            )

            assert result == 8

        except ImportError:
            pytest.skip("Agent模块未安装")

    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """测试未知工具错误"""
        try:
            from agents.agent_service import AgentService

            service = AgentService()

            # 尝试执行不存在的工具
            with pytest.raises(Exception):  # ToolExecutionError
                await service.execute_tool(
                    tool_name="unknown_tool",
                    parameters={},
                    context={}
                )

        except ImportError:
            pytest.skip("Agent模块未安装")


@pytest.mark.agent
@pytest.mark.unit
class TestAgentKnowledgeIntegration:
    """Agent与知识库集成测试"""

    def test_knowledge_search_tool(self):
        """测试知识库搜索工具"""
        try:
            from agents.tools.knowledge_tool import knowledge_search_tool

            # 测试工具存在性
            import asyncio
            result = asyncio.run(knowledge_search_tool(
                query="Python",
                knowledge_base_ids=["test-kb-001"],
                top_k=3
            ))

            # 即使没有数据，也应该返回结果结构
            assert result is not None
            assert "query" in result
            assert "total_results" in result

        except ImportError:
            pytest.skip("Agent模块未安装")


@pytest.mark.agent
@pytest.mark.unit
class TestAgentTools:
    """Agent工具测试"""

    def test_available_tools_list(self):
        """测试可用工具列表"""
        try:
            from app.models.agent import PREDEFINED_TOOLS

            assert len(PREDEFINED_TOOLS) > 0

            # 验证工具结构
            for tool in PREDEFINED_TOOLS:
                assert tool.name is not None
                assert tool.display_name is not None
                assert tool.description is not None
                assert tool.category is not None
                assert tool.parameters is not None

        except ImportError:
            pytest.skip("Agent模块未安装")
