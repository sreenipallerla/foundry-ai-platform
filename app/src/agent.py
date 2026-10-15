"""LangGraph agent: the model decides when to call tools, the graph loops until it answers.
Two graphs: a strict RAG chain (always retrieve, answer only with verified quotes) and a tool-calling agent."""
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from .llm import chat_model
from .observability import callbacks
from .rag import retrieve_relevant
from .tools import TOOLS

REFUSAL = "I don't know based on the knowledge base."

SYSTEM = (
    "Answer ONLY using passages returned by search_knowledge_base and results from calculate. "
    "Never use general knowledge. Cite the [source] file names you used. If the passages do not answer "
    f"the question, reply with exactly: {REFUSAL} Add nothing else: no guesses and no suggestions."
)

RAG_PROMPT = (
    "You answer only from the passages given. Reply with JSON only, no other text: "
    '{"answer": "<one or two sentences>", "quotes": ["<sentence copied EXACTLY from the passages>"]}. '
    "Every claim in the answer must be supported by a quote. Do not use outside knowledge. "
    f'If the passages do not answer the question, reply {{"answer": "{REFUSAL}", "quotes": []}}.'
)

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_react_agent(chat_model(), TOOLS, checkpointer=MemorySaver(), prompt=SYSTEM)
    return _agent


def run_agent(question: str, thread_id: str = "default") -> dict:
    cfg = {"configurable": {"thread_id": thread_id}, "callbacks": callbacks(session_id=thread_id)}
    result = get_agent().invoke({"messages": [HumanMessage(content=question)]}, config=cfg)
    msgs = result["messages"]
    tools_used = [m.name for m in msgs if getattr(m, "type", "") == "tool"]
    answer = msgs[-1].content
    if not tools_used:
        answer = REFUSAL  # no tool was used, so nothing grounded the reply
    return {"answer": answer, "tools_used": tools_used}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        return {}


def run_rag(question: str) -> dict:
    """Strict RAG: answer only with quotes that are verifiably in the retrieved passages."""
    hits = retrieve_relevant(question, k=4)
    if not hits:
        return {"answer": REFUSAL, "sources": [], "contexts": []}
    context = "\n\n".join(f"[{d.metadata.get('source', '?')}] {d.page_content}" for d in hits)
    out = chat_model().invoke(
        [SystemMessage(content=RAG_PROMPT + "\n\nPassages:\n" + context), HumanMessage(content=question)],
        config={"callbacks": callbacks()},
    )
    data = _parse_json(out.content)
    haystack = _norm(" ".join(d.page_content for d in hits))
    quotes = [q for q in data.get("quotes", []) if _norm(q) and _norm(q) in haystack]
    if not quotes:
        return {"answer": REFUSAL, "sources": [], "contexts": [d.page_content for d in hits]}
    sources = sorted({d.metadata.get("source", "?") for d in hits
                      if any(_norm(q) in _norm(d.page_content) for q in quotes)})
    return {"answer": " ".join(quotes), "quotes": quotes, "sources": sources,
            "contexts": [d.page_content for d in hits]}