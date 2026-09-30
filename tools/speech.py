import json
import os
from urllib import error, request

from robot import create_robot


robot = create_robot()


def speak(text: str) -> dict:
    """
    Send text to the configured speech service.
    If no external speech service is configured,
    use the current robot backend.

    Args:
        text: Visitor-facing text to speak.

    Returns:
        dict: Structured delivery result.
    """
    service_url = os.getenv("SPEECH_SERVICE_URL")

    # 1. 如果配置了外部语音服务，优先转发
    if service_url:
        payload = json.dumps({"text": text}).encode("utf-8")

        http_request = request.Request(
            service_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            timeout = float(os.getenv("SPEECH_SERVICE_TIMEOUT", "10"))

            with request.urlopen(http_request, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")

                return {
                    "success": 200 <= response.status < 300,
                    "text": text,
                    "status": "forwarded",
                    "upstream_status": response.status,
                    "upstream_response": response_body,
                }

        except (error.URLError, TimeoutError, ValueError) as exc:
            return {
                "success": False,
                "text": text,
                "status": "failed",
                "error": str(exc),
            }

    # 2. 未配置外部语音服务时，交给当前机器人后端
    return robot.speak(text)