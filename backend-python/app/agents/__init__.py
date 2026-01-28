"""
数字员工/Agent 模块
Digital Employee / Agent Module

提供基于 LangGraph 的智能 Agent 功能
Provides intelligent Agent features based on LangGraph
"""
from .agent_service import AgentService, get_agent_service

__all__ = [
    "AgentService",
    "get_agent_service",
]
