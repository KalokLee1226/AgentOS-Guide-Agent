from fastapi import FastAPI
from pydantic import BaseModel

from agent.llm_agent import LLMAgent


app = FastAPI(
    title="AgentOS Guide Agent API",
    version="0.1.0"
)

agent = LLMAgent()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "service": "AgentOS Guide Agent",
        "status": "running"
    }


@app.get("/state")
def get_state():
    return agent.state.to_dict()


@app.post("/chat")
def chat(request: ChatRequest):
    result = agent.handle(request.message)

    return {
        "reply": result,
        "state": agent.state.to_dict()
    }