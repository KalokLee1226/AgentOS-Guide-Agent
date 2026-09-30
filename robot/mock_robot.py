from typing import Dict, Any

from robot.base import RobotAdapter


class MockRobot(RobotAdapter):

    def __init__(self):
        self.current_poi = None
        self.status = "idle"

    def navigate_to(self, poi_id: str) -> Dict[str, Any]:
        self.status = "moving"

        print(f"[MockRobot] 正在前往 {poi_id} ...")

        self.current_poi = poi_id
        self.status = "arrived"

        print(f"[MockRobot] 已到达 {poi_id}")

        return {
            "success": True,
            "poi_id": poi_id,
            "status": "arrived",
        }

    def speak(self, text: str) -> Dict[str, Any]:
        print(f"[MockRobot] 播报：{text}")

        return {
            "success": True,
            "text": text,
        }

    def stop(self) -> Dict[str, Any]:
        self.status = "stopped"

        print("[MockRobot] 已停止")

        return {
            "success": True,
            "status": "stopped",
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "success": True,
            "status": self.status,
            "current_poi": self.current_poi,
        }