"""Tools the agent can call. Keep each tool small, typed and documented: the docstring is the contract the model sees."""
from datetime import date

from langchain_core.tools import tool

from .rag import retrieve


@tool
def search_knowledge_base(query: str) -> str:
    """Search the internal knowledge base. Use for any question about policies, products or procedures.
    Returns the top passages with their source file names."""
    hits = retrieve(query, k=4)
    if not hits:
        return "No relevant passages found."
    return "\n\n".join(f"[{d.metadata.get('source', '?')}] {d.page_content}" for d in hits)


@tool
def calculate(expression: str) -> str:
    """Evaluate a simple arithmetic expression such as '1200 * 0.035'. Only numbers and + - * / ( ) are allowed."""
    allowed = set("0123456789+-*/(). ")
    if not expression or any(ch not in allowed for ch in expression):
        return "Error: only numbers and + - * / ( ) are allowed."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # input is whitelisted above
    except Exception as exc:  # noqa: BLE001
        return f"Error: {exc}"


@tool
def today() -> str:
    """Return today's date in ISO format."""
    return date.today().isoformat()


TOOLS = [search_knowledge_base, calculate, today]
