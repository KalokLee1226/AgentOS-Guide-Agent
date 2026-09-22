"""Minimal ASR-to-Agent client using only the Python standard library."""

import json
from urllib import request


AGENT_URL = "http://127.0.0.1:8000/v1/voice/transcripts"


def send_transcript(transcript: str, session_id: str | None = None) -> dict:
    body = {"transcript": transcript}
    if session_id:
        body["session_id"] = session_id

    http_request = request.Request(
        AGENT_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(http_request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    result = send_transcript("带我去展品3，然后介绍一下")
    print("session_id:", result["session_id"])
    print("reply:", result["reply"])

    for text in result["speech"]:
        print("Send this text to TTS:", text)
