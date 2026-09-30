from abc import ABC, abstractmethod
from typing import Dict, Any


class RobotAdapter(ABC):
    """
    机器人统一接口。

    上层 Agent 不关心底层是真机、仿真还是 Mock，
    只通过这一层调用机器人能力。
    """

    @abstractmethod
    def navigate_to(self, poi_id: str) -> Dict[str, Any]:
        """导航到指定 POI。"""
        pass

    @abstractmethod
    def speak(self, text: str) -> Dict[str, Any]:
        """机器人语音播报。"""
        pass

    @abstractmethod
    def stop(self) -> Dict[str, Any]:
        """停止机器人运动。"""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取机器人当前状态。"""
        pass