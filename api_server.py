from threading import Lock, RLock
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from agent.llm_agent import LLMAgent


app = FastAPI(
    title="AgentOS Guide Agent API",
    version="0.2.0",
    description="Session-based HTTP API for text, voice, and robot clients.",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)
    source: Literal["text", "voice", "robot", "other"] = "text"


class VoiceTranscriptRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)


class AgentResponse(BaseModel):
    session_id: str
    reply: str
    speech: list[str]
    tool_calls: list[dict[str, Any]]
    state: dict[str, Any]


class AgentSession:
    def __init__(self):
        self.agent = LLMAgent()
        self.lock = Lock()


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}
        self._lock = RLock()

    def get_or_create(self, session_id: str | None = None):
        resolved_id = session_id or str(uuid4())

        with self._lock:
            session = self._sessions.setdefault(resolved_id, AgentSession())

        return resolved_id, session

    def get(self, session_id: str):
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


sessions = SessionStore()


def run_agent(message: str, session_id: str | None) -> AgentResponse:
    resolved_id, session = sessions.get_or_create(session_id)

    try:
        with session.lock:
            result = session.agent.handle_detailed(message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent execution failed: {exc}") from exc

    return AgentResponse(
        session_id=resolved_id,
        reply=result.reply,
        speech=result.speech,
        tool_calls=result.tool_calls,
        state=result.state,
    )


@app.get("/")
def root():
    return {
        "service": "AgentOS Guide Agent",
        "version": "0.2.0",
        "status": "running",
    }


@app.post("/v1/chat", response_model=AgentResponse)
def v1_chat(request: ChatRequest):
    return run_agent(request.message, request.session_id)


@app.post("/v1/voice/transcripts", response_model=AgentResponse)
def voice_transcript(request: VoiceTranscriptRequest):
    """Accept final ASR text and return reply text plus TTS-ready speech items."""
    return run_agent(request.transcript, request.session_id)


@app.get("/v1/sessions/{session_id}/state")
def session_state(session_id: str):
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.agent.state.to_dict()


@app.delete("/v1/sessions/{session_id}", status_code=204)
def delete_session(session_id: str):
    if not sessions.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return Response(status_code=204)


# Backward-compatible v0.1 endpoints. New integrations should use /v1/*.
LEGACY_SESSION_ID = "legacy-default"


@app.get("/state")
def get_state():
    _, session = sessions.get_or_create(LEGACY_SESSION_ID)
    return session.agent.state.to_dict()


@app.post("/chat")
def chat(request: ChatRequest):
    response = run_agent(request.message, LEGACY_SESSION_ID)
    return {"reply": response.reply, "state": response.state}
