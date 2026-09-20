import time


def navigate_to(poi_id: str) -> dict:
    """
    模拟机器人导航到指定展品。

    Args:
        poi_id: 展品ID，例如 exhibit_1

    Returns:
        dict: 导航执行结果
    """
    print(f"[Navigation] 正在前往 {poi_id} ...")

    # 现在先用 sleep 模拟真实导航耗时
    time.sleep(1)

    print(f"[Navigation] 已到达 {poi_id}")

    return {
        "success": True,
        "poi_id": poi_id,
        "status": "arrived"
    }