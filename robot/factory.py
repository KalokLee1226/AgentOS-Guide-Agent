import os

from robot.base import RobotAdapter


_robot_instance = None


def create_robot() -> RobotAdapter:
    global _robot_instance

    if _robot_instance is not None:
        return _robot_instance

    backend = os.getenv("ROBOT_BACKEND", "mock").lower()

    if backend == "mock":
        from robot.mock_robot import MockRobot

        _robot_instance = MockRobot()
        return _robot_instance

    if backend == "tienkung":
        from robot.tienkung_robot import TienKungRobot

        _robot_instance = TienKungRobot()
        return _robot_instance

    raise ValueError(
        f"Unsupported ROBOT_BACKEND: {backend}"
    )