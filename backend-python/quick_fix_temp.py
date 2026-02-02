"""
临时修复方案：如果 reasoning 丢失，从问题重新生成
"""

async def _generate_direct_answer_fallback(self, question: str, reasoning: str, available_tools: List[str]) -> str:
    """
    当 reasoning 为空时的降级方案：直接从问题生成友好回复
    """
    logger.info(f"🔧 [降级方案] reasoning 为空，从问题生成回复")

    # 场景 1: 问候类问题
    if any(keyword in question for keyword in ["你好", "hello", "hi", "嗨", "您好"]):
        return "你好！有什么我可以帮助你的吗？"

    # 场景 2: 计算类问题
    if any(keyword in question for keyword in ["计算", "+", "-", "*", "/", "="]):
        if "calculator" in available_tools:
            return f"我可以帮你{question}这个问题，但我当前没有配置计算器工具。我可用的工具有：{', '.join(available_tools)}"
        else:
            return f"我可以帮你计算{question}，但我当前没有配置计算器工具。"

    # 场景 3: 时间类问题
    if any(keyword in question for keyword in ["时间", "日期", "几点", "今天"]):
        if "datetime" in available_tools:
            return f"我可以告诉你当前时间，但我当前没有配置时间工具。"
        else:
            return f"我理解你想知道时间，但我当前没有配置相关工具。"

    # 场景 4: 搜索类问题
    if any(keyword in question.lower() for keyword in ["搜索", "search", "查找"]):
        if "knowledge_search" in available_tools:
            return f"我可以帮你搜索「{question}」相关的信息。请告诉我你想在哪个知识库中搜索？"
        else:
            return f"我可以帮你搜索信息，但我当前没有配置搜索工具。"

    # 默认回复
    if available_tools:
        tools_desc = ", ".join(available_tools)
        return f"我收到你的问题了。我当前可以使用以下工具：{tools_desc}。请尝试提出与这些工具相关的问题，我会尽力帮助你。"
    else:
        return "我收到你的问题了，但目前我还没有配置任何工具来协助回答问题。"
