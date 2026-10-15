# Parallel vibe-coding: build in lanes, not in one long chat

The idea: split the work into lanes that touch different files, give each lane its own branch and its own AI
coding session, and agree the interfaces first so the lanes plug together.

## Step 1. Write the contract (15 minutes, once)
`CLAUDE.md` in the repo root is the contract. Every session reads it first. It lists the layout, the rules and
which functions are shared. Edit it before you start; it is the single most useful file for vibe-coding.

## Step 2. Freeze the interfaces
These signatures are shared, so decide them first and do not change them without telling the other lanes:

| Interface | Signature |
|---|---|
| Model factory | `chat_model() -> BaseChatModel`, `embeddings() -> Embeddings` |
| Retrieval | `retrieve(query: str, k: int) -> list[Document]` |
| Tools | `TOOLS: list[BaseTool]` |
| Agent | `run_agent(question, thread_id) -> {"answer", "tools_used"}` |
| API | `POST /chat`, `POST /rag`, `POST /ingest`, `GET /health` |

## Step 3. Make one worktree per lane
```bash
git checkout -b main && git add -A && git commit -m "baseline"
git worktree add ../fai-lane-rag    -b lane/rag
git worktree add ../fai-lane-agent  -b lane/agent
git worktree add ../fai-lane-evals  -b lane/evals
git worktree add ../fai-lane-infra  -b lane/infra
```
Open each folder in its own terminal and start one AI coding session per folder.

## Step 4. Give each lane a short, specific brief
Copy a brief into the matching session. Keep each lane to its own files.

| Lane | Files it may touch | Brief |
|---|---|---|
| rag | `app/src/rag.py`, `data/docs/` | "Add Azure AI Search with hybrid search and a metadata filter. Keep retrieve() unchanged. Add tests." |
| agent | `app/src/tools.py`, `app/src/agent.py` | "Add a tool that looks up a borrower exposure from a JSON file. Add a golden question and a test." |
| evals | `app/evals/` | "Add 15 golden questions, a refusal test, and a latency print. Do not change src/." |
| infra | `infra/`, `k8s/`, `pipelines/` | "Add a Key Vault CSI secret mount in k8s and a workload identity role assignment in Bicep." |

## Step 5. Work in short loops
For each lane: ask for a plan, approve it, let the session implement, run `pytest`, read the diff, commit.
Keep every change under about 200 lines. If a session drifts into another lane's files, stop it.

## Step 6. Merge in this order
1. `lane/rag` then `lane/agent` (shared code)
2. `lane/evals` (rerun the eval gate against the merged code)
3. `lane/infra`

After each merge, rebase the remaining lanes: `git rebase main` inside each worktree.

## Step 7. Review like a lead engineer
Before merging any lane ask: does it follow `CLAUDE.md`, did it add a test, did it add a golden question, did it
introduce a secret, does the diff match the brief. Let a second AI session review the diff with a fresh context.

## Common traps
- Two lanes editing `agent.py`: split by file or serialise them.
- Prompts changing silently: any prompt change must pass the eval gate.
- Big-bang merges: merge each lane the day it is ready.
