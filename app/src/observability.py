import logging

from . import config as c

log = logging.getLogger(__name__)


def callbacks(session_id: str | None = None, user_id: str | None = None) -> list:
    if not c.LANGFUSE_ENABLED:
        return []
    try:
        from langfuse.langchain import CallbackHandler
        return [CallbackHandler()]
    except Exception as exc:
        log.warning("Langfuse tracing disabled: %s", exc)
        return []