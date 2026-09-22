from tools.navigation import navigate_to
from tools.knowledge import query_knowledge
from tools.speech import speak


TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "Navigate the robot to a specified exhibit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {
                        "type": "string",
                        "description": "Exhibit ID, for example exhibit_1."
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
            "description": "Retrieve factual information about a specified exhibit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {
                        "type": "string",
                        "description": "Exhibit ID, for example exhibit_1."
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
            "description": "Send visitor-facing text to the robot speech module.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Natural, concise text for the robot to speak."
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
            "error": f"Unknown tool: {tool_name}"
        }

    try:
        return tool(**arguments)

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
