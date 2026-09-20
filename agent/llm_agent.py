import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agent.toolkit import get_tools_spec, execute_tool
from agent.state import AgentState


load_dotenv()


class LLMAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://maas.qianwenaiapi.com/compatible-mode/v1",
        )

        self.model = "qwen3.8-omni-flash"

        self.system_prompt = """
你是一个展厅导览机器人 Agent。

你可以调用以下工具完成任务：
- navigate_to：导航到指定展品
- query_knowledge：查询展品介绍
- speak：让机器人播报文本

规则：
1. 如果用户要求去某个展品，调用 navigate_to。
2. 如果用户要求介绍某个展品，调用 query_knowledge。
3. 查询到介绍内容后，如果需要对用户讲解，调用 speak。
4. 如果是复合任务，例如“带我去展品3，然后介绍一下”，应按顺序完成多个工具调用。
5. 不要假装工具执行成功，必须等待工具返回结果。
6. 工具完成后，根据结果继续判断下一步。
7. 如果用户说“这里”“这个展品”“刚才那个展品”，应结合当前机器人状态和历史对话判断具体指代。
8. 如果用户询问已经参观过哪些展品，应优先参考 visited_pois。
"""

        # 结构化 Agent 状态
        self.state = AgentState()

        # 短期对话记忆
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

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
            "content": (
                "当前机器人状态：\n"
                f"current_poi={self.state.current_poi}\n"
                f"visited_pois={self.state.visited_pois}\n"
                f"status={self.state.status}"
            ),
        }

        return self.messages + [state_message]

    def handle(self, user_input: str) -> str:
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

            response = self.client.chat.completions.create(
                model=self.model,
                messages=request_messages,
                tools=get_tools_spec(),
                tool_choice="auto",
            )

            message = response.choices[0].message

            # 没有工具调用，说明本轮任务完成
            if not message.tool_calls:
                self.state.set_status("idle")

                assistant_text = message.content or ""

                self.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_text,
                    }
                )

                self.trim_memory()

                return assistant_text

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

        return "任务执行超过最大轮数，已停止。"