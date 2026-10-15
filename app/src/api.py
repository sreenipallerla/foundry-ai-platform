from fastapi import FastAPI
from pydantic import BaseModel

from . import config as c
from .agent import run_agent, run_rag
from .rag import ingest

app = FastAPI(title="foundry-ai-platform", version="0.1.0")


class Ask(BaseModel):
    question: str
    thread_id: str = "default"


@app.get("/health")
def health():
    return {"status": "ok", "env": c.ENV_NAME, "provider": c.PROVIDER}


@app.post("/ingest")
def do_ingest():
    return {"chunks": ingest()}


@app.post("/rag")
def rag(body: Ask):
    return run_rag(body.question)


@app.post("/chat")
def chat(body: Ask):
    return run_agent(body.question, body.thread_id)
