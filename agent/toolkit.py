from tools.navigation import navigate_to
from tools.knowledge import query_knowledge
from tools.speech import speak


TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "导航到指定展品位置。",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {
                        "type": "string",
                        "description": "展品ID，例如 exhibit_1"
                    }
                },
                "required": ["poi_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge",
            "description": "查询指定展品的介绍信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {
                        "type": "string",
                        "description": "展品ID，例如 exhibit_1"
                    }
                },
                "required": ["poi_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "speak",
            "description": "让机器人播报指定文本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要播报的文本"
                    }
                },
                "required": ["text"]
            }
        }
    }
]


TOOLS = {
    "navigate_to": navigate_to,
    "query_knowledge": query_knowledge,
    "speak": speak,
}


def get_tools_spec() -> list:
    return TOOLS_SPEC


def execute_tool(tool_name: str, arguments: dict) -> dict:
    tool = TOOLS.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": f"未知工具: {tool_name}"
        }

    try:
        return tool(**arguments)

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }