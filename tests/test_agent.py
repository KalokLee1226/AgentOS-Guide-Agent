import json
import unittest
from types import SimpleNamespace

from agent.llm_agent import LLMAgent


def completion(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, responses):
        self.responses = iter(responses)

    def create(self, **_kwargs):
        return next(self.responses)


class FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


class AgentTests(unittest.TestCase):
    def test_detailed_result_exposes_speech_for_voice_clients(self):
        tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(
                name="speak",
                arguments=json.dumps({"text": "Welcome to exhibit 1."}),
            ),
        )
        client = FakeClient(
            [
                completion(SimpleNamespace(content=None, tool_calls=[tool_call])),
                completion(SimpleNamespace(content="Done.", tool_calls=[])),
            ]
        )
        agent = LLMAgent(client=client)

        result = agent.handle_detailed("Please introduce exhibit 1")

        self.assertEqual(result.reply, "Done.")
        self.assertEqual(result.speech, ["Welcome to exhibit 1."])
        self.assertEqual(result.tool_calls[0]["name"], "speak")
        self.assertEqual(result.tool_calls[0]["result"]["status"], "mocked")

    def test_prompt_and_runtime_state_are_english(self):
        agent = LLMAgent(client=FakeClient([]))

        self.assertIn("exhibition-hall robot", agent.system_prompt)
        self.assertIn("Current robot state", agent.build_request_messages()[-1]["content"])


if __name__ == "__main__":
    unittest.main()
