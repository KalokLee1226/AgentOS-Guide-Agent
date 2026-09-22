import json
import os
from urllib import error, request


def speak(text: str) -> dict:
    """
    Send text to the configured speech service, or use the local mock.

    Args:
        text: Visitor-facing text to speak.

    Returns:
        dict: Structured delivery result.
    """
    service_url = os.getenv("SPEECH_SERVICE_URL")

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

    print(f"[Speech] {text}")

    return {
        "success": True,
        "text": text,
        "status": "mocked"
    }
