# Project contract for AI coding sessions
Purpose: RAG + tool-calling agent on Azure AI Foundry, deployed to AKS through Azure DevOps (Dev, QA, Prod).

## Layout
- app/src/config.py   settings from environment only
- app/src/llm.py      the only place that builds chat and embedding models
- app/src/rag.py      ingest and retrieve
- app/src/tools.py    agent tools (typed, documented)
- app/src/agent.py    LangGraph agent and plain RAG
- app/src/api.py      FastAPI endpoints
- app/evals/          golden questions and the eval gate
- infra/, k8s/, pipelines/   cloud, deployment, CI/CD

## Rules
1. Never hard-code secrets, endpoints or model names. Use config.py.
2. Every new tool needs a docstring, a unit test and a golden question in app/evals/golden.jsonl.
3. Do not change function signatures in llm.py, rag.py or tools.py without saying so: other lanes depend on them.
4. Keep PRs small. One lane, one branch, one concern.
5. Run before every commit: `cd app && python -m pytest -q`
