EXHIBITS = {
    "exhibit_1": {
        "name": "智能机器人展区",
        "description": "这里主要展示智能机器人相关技术，包括感知、规划与控制等内容。"
    },
    "exhibit_2": {
        "name": "人工智能展区",
        "description": "这里展示人工智能在视觉、语言和机器人等方向上的应用。"
    },
    "exhibit_3": {
        "name": "具身智能展区",
        "description": "这里主要介绍具身智能系统如何通过感知、推理和动作与真实环境进行交互。"
    }
}


def query_knowledge(poi_id: str) -> dict:
    """
    查询指定展品的介绍信息。
    """
    print(f"[Knowledge] 正在查询 {poi_id} 的信息 ...")

    exhibit = EXHIBITS.get(poi_id)

    if exhibit is None:
        return {
            "success": False,
            "poi_id": poi_id,
            "error": "未找到该展品信息"
        }

    return {
        "success": True,
        "poi_id": poi_id,
        "name": exhibit["name"],
        "description": exhibit["description"]
    }