from agent.toolkit import execute_tool


class RuleAgent:
    def handle(self, user_input: str) -> dict:
        text = user_input.strip()

        poi_id = self._extract_poi_id(text)

        # 多步任务：导航 + 介绍
        if (
            ("带我去" in text or "去展品" in text)
            and ("介绍" in text or "讲讲" in text)
        ):
            if poi_id is None:
                return {
                    "success": False,
                    "message": "没有识别到目标展品"
                }

            nav_result = execute_tool(
                "navigate_to",
                {
                    "poi_id": poi_id
                }
            )

            if not nav_result.get("success"):
                return nav_result

            knowledge_result = execute_tool(
                "query_knowledge",
                {
                    "poi_id": poi_id
                }
            )

            if not knowledge_result.get("success"):
                return knowledge_result

            text_to_speak = (
                f"已到达{knowledge_result['name']}。"
                f"{knowledge_result['description']}"
            )

            speak_result = execute_tool(
                "speak",
                {
                    "text": text_to_speak
                }
            )

            return {
                "success": True,
                "task": "navigate_and_explain",
                "poi_id": poi_id,
                "navigation": nav_result,
                "knowledge": knowledge_result,
                "speech": speak_result
            }

        # 单独导航
        if "带我去" in text or "去展品" in text:
            if poi_id is None:
                return {
                    "success": False,
                    "message": "没有识别到目标展品"
                }

            return execute_tool(
                "navigate_to",
                {
                    "poi_id": poi_id
                }
            )

        # 单独介绍
        if "介绍" in text or "讲讲" in text:
            if poi_id is None:
                return {
                    "success": False,
                    "message": "没有识别到目标展品"
                }

            knowledge_result = execute_tool(
                "query_knowledge",
                {
                    "poi_id": poi_id
                }
            )

            if not knowledge_result.get("success"):
                return knowledge_result

            text_to_speak = (
                f"{knowledge_result['name']}。"
                f"{knowledge_result['description']}"
            )

            speak_result = execute_tool(
                "speak",
                {
                    "text": text_to_speak
                }
            )

            return {
                "success": True,
                "task": "explain",
                "poi_id": poi_id,
                "knowledge": knowledge_result,
                "speech": speak_result
            }

        return {
            "success": False,
            "message": "暂时无法理解这个指令"
        }

    def _extract_poi_id(self, text: str):
        for i in range(1, 10):
            if f"展品{i}" in text:
                return f"exhibit_{i}"

        return None