from robot import create_robot


robot = create_robot()


def navigate_to(poi_id: str) -> dict:
    """
    导航机器人到指定展品。

    Args:
        poi_id: 展品ID，例如 exhibit_1

    Returns:
        dict: 导航执行结果
    """
    return robot.navigate_to(poi_id)