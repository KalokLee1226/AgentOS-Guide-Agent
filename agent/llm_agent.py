import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        """Allow library imports before optional environment helpers are installed."""
        return False

from agent.toolkit import get_tools_spec, execute_tool
from agent.state import AgentState
from agent.prompt import SYSTEM_PROMPT, build_state_prompt


load_dotenv()


@dataclass
class AgentResult:
    reply: str
    state: dict[str, Any]
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    speech: list[str] = field(default_factory=list)


class LLMAgent:
    def __init__(self, client=None, model: str | None = None):
        self.client = client

        self.model = model or os.getenv(
            "LLM_MODEL",
            "qwen3.8-omni-flash",
        )

        self.system_prompt = SYSTEM_PROMPT

        # 结构化 Agent 状态
        self.state = AgentState()

        # 短期对话记忆
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

    def _get_client(self):
        """
        创建 OpenAI-compatible 客户端。

        云端模式：
        - 使用 LLM_BASE_URL
        - 使用 LLM_API_KEY 或 DASHSCOPE_API_KEY

        本地模式：
        - LLM_BASE_URL 指向 localhost / 127.0.0.1
        - 如果没有真实 API Key，则自动使用 "local" 占位
        """

        if self.client is None:
            base_url = os.getenv(
                "LLM_BASE_URL",
                "https://maas.qianwenaiapi.com/compatible-mode/v1",
            )

            api_key = (
                os.getenv("LLM_API_KEY")
                or os.getenv("DASHSCOPE_API_KEY")
            )

            # 本地 OpenAI-compatible 服务通常不需要真实 API Key
            if not api_key:
                if (
                    base_url.startswith("http://127.0.0.1")
                    or base_url.startswith("http://localhost")
                ):
                    api_key = "local"
                else:
                    raise RuntimeError(
                        "No LLM API key configured. "
                        "Set LLM_API_KEY or DASHSCOPE_API_KEY in the .env file."
                    )

            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

        return self.client

    def _clean_assistant_text(self, text: str) -> str:
        """
        清理部分本地推理模型输出中的 <think>...</think> 内容，
        避免将模型内部思考文本直接展示给用户。
        """

        if not text:
            return ""

        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        return cleaned.strip()

    def trim_memory(self, max_messages=12):
        """
        滑动窗口记忆：
        永久保留最前面的 system prompt，
        其余只保留最近 max_messages 条消息。
        """

        if len(self.messages) <= max_messages + 1:
            return

        system_message = self.messages[0]
        recent_messages = self.messages[-max_messages:]

        self.messages = [
            system_message,
            *recent_messages,
        ]

    def build_request_messages(self):
        """
        构造本次发给 LLM 的消息。

        AgentState 不永久写入 self.messages，
        而是每次请求模型时动态加入最新状态。
        """

        state_message = {
            "role": "system",
            "content": build_state_prompt(
                self.state.current_poi,
                self.state.visited_pois,
                self.state.status,
            ),
        }

        return self.messages + [state_message]

    def handle(self, user_input: str) -> str:
        return self.handle_detailed(user_input).reply

    def handle_detailed(self, user_input: str) -> AgentResult:
        tool_events = []

        # 保存当前用户输入
        self.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        # 裁剪过长的历史消息
        self.trim_memory()

        max_turns = 8

        for turn in range(max_turns):
            # 每轮都使用最新 AgentState
            request_messages = self.build_request_messages()

            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=request_messages,
                tools=get_tools_spec(),
                tool_choice="auto",
            )

            message = response.choices[0].message

            # 没有工具调用，说明本轮任务完成
            if not message.tool_calls:
                self.state.set_status("idle")

                assistant_text = self._clean_assistant_text(
                    message.content or ""
                )

                self.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_text,
                    }
                )

                self.trim_memory()

                return AgentResult(
                    reply=assistant_text,
                    state=self.state.to_dict(),
                    tool_calls=tool_events,
                    speech=[
                        event["arguments"]["text"]
                        for event in tool_events
                        if event["name"] == "speak"
                        and event["result"].get("success")
                    ],
                )

            # 保存模型发起的 tool call
            self.messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )
                except json.JSONDecodeError:
                    arguments = {}

                print(
                    f"\n[LLM] Tool Call -> "
                    f"{tool_name}({arguments})"
                )

                # Agent 进入工作状态
                self.state.set_status("working")

                # 真正执行工具
                result = execute_tool(
                    tool_name,
                    arguments,
                )

                tool_events.append(
                    {
                        "name": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                print(
                    f"[Tool Result] {result}"
                )

                # 如果导航成功，更新当前位置和访问记录
                if (
                    tool_name == "navigate_to"
                    and result.get("success")
                ):
                    poi_id = result.get("poi_id")

                    if poi_id:
                        self.state.set_current_poi(
                            poi_id
                        )

                # 把工具结果加入短期记忆
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                        ),
                    }
                )

            # 每完成一轮工具调用后裁剪一次
            self.trim_memory()

        self.state.set_status("idle")

        return AgentResult(
            reply="The task exceeded the maximum number of agent turns and was stopped.",
            state=self.state.to_dict(),
            tool_calls=tool_events,
            speech=[],
        )