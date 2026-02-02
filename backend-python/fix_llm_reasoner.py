"""
修复 llm_reasoner.py 中的 _parse_decision 方法
"""
import re

# 读取文件
with open('/data1/allresearchProject/Bright-Chat/backend-python/app/agents/llm_reasoner.py', 'r') as f:
    content = f.read()

# 新的 _parse_decision 方法
new_method = '''    def _parse_decision(self, response: str, available_tools: List[str]) -> Dict[str, Any]:
        """解析 LLM 响应为决策（支持 JSON 和 Markdown 两种格式）"""
        try:
            # 尝试解析 JSON 格式（新格式）
            # 检查是否包含 JSON 代码块或以 { 开头
            json_match = re.search(r'```json\s*(\\{.*?\\})\\s*```', response, re.DOTALL)
            if json_match:
                # 从代码块中提取 JSON
                json_str = json_match.group(1)
                logger.info(f"📋 [JSON 解析] 从代码块中提取 JSON")
            elif response.strip().startswith('{'):
                # 直接尝试解析整个响应
                json_str = response.strip()
                logger.info(f"📋 [JSON 解析] 直接解析响应")
            else:
                # 回退到 Markdown 格式解析（旧格式兼容）
                logger.info("📋 使用 Markdown 格式解析（向后兼容）")
                reasoning = self._extract_section(response, "推理")
                tool = self._extract_section(response, "工具决策").strip().lower()
                parameters_str = self._extract_section(response, "工具参数")
                confidence_str = self._extract_section(response, "置信度").strip()
                should_continue_str = self._extract_section(response, "继续执行").strip().lower()

                # 解析参数 JSON
                try:
                    parameters = json.loads(parameters_str) if parameters_str and parameters_str != "{}" else {}
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ 工具参数 JSON 解析失败: {parameters_str}")
                    parameters = {}

                # 解析置信度
                try:
                    confidence = float(confidence_str) if confidence_str else 0.5
                except ValueError:
                    logger.warning(f"⚠️ 置信度解析失败: {confidence_str}")
                    confidence = 0.5

                should_continue = should_continue_str in ["true", "yes", "是"]

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

            # 解析提取的 JSON 字符串
            try:
                data = json.loads(json_str)
                logger.info(f"✅ [JSON 解析] JSON 解析成功")
            except json.JSONDecodeError as e:
                logger.error(f"❌ [JSON 解析] JSON 解析失败: {e}")
                logger.error(f"📄 [JSON 解析] JSON 字符串: {json_str[:200]}...")
                # 降级到 Markdown 格式
                logger.info("📋 降级到 Markdown 格式解析")
                reasoning = self._extract_section(response, "推理")
                tool = self._extract_section(response, "工具决策").strip().lower()
                parameters_str = self._extract_section(response, "工具参数")
                confidence_str = self._extract_section(response, "置信度").strip()
                should_continue_str = self._extract_section(response, "继续执行").strip().lower()

                try:
                    parameters = json.loads(parameters_str) if parameters_str and parameters_str != "{}" else {}
                except json.JSONDecodeError:
                    parameters = {}

                try:
                    confidence = float(confidence_str) if confidence_str else 0.5
                except ValueError:
                    confidence = 0.5

                should_continue = should_continue_str in ["true", "yes", "是"]

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

            # 解析 JSON 数据
            tool = data.get("tool")
            # 处理 null 值
            if tool is None or tool == "null":
                tool = None
            elif isinstance(tool, str):
                tool = tool.strip().lower()
                if tool == "none" or tool == "null":
                    tool = None

            # 验证工具是否可用
            if tool and tool not in available_tools:
                logger.warning(f"⚠️ LLM 选择的工具 {tool} 不可用,降级到 none")
                tool = None

            logger.info(f"✅ [JSON 解析] 工具决策: tool={tool}, parameters={data.get('parameters', {})}")

            return {
                "reasoning": data.get("reasoning", ""),
                "tool": tool,
                "parameters": data.get("parameters", {}),
                "confidence": float(data.get("confidence", 0.8)),
                "should_continue": bool(data.get("should_continue", False))
            }

        except Exception as e:
            logger.error(f"❌ 解析决策失败: {e}")
            logger.error(f"📄 响应内容: {response[:500]}")
            # 返回安全默认值
            return {
                "reasoning": response[:200] if response else "解析失败",
                "tool": None,
                "parameters": {},
                "confidence": 0.5,
                "should_continue": False
            }
'''

# 使用正则表达式替换旧的 _parse_decision 方法
pattern = r'def _parse_decision\(self, response: str, available_tools: List\[str\]\) -> Dict\[str, Any\]:.*?(?=\n    def _extract_section)'
replacement = new_method + '\n\n    def _extract_section'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 写回文件
with open('/data1/allresearchProject/Bright-Chat/backend-python/app/agents/llm_reasoner.py', 'w') as f:
    f.write(new_content)

print("✅ _parse_decision 方法已修复")
