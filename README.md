# Activity 1: Azure AI Foundry platform (RAG, agents, evals, AKS, Azure DevOps)

A small, production-shaped AI service. You will build it locally, then deploy it to a new Azure resource group
through Azure DevOps into Dev, then QA, then Prod.

What is in it: Azure AI Foundry models, RAG, LangChain, LangGraph agent, tool calling, Langfuse tracing, an eval
gate, a fine-tuning flow, Ollama for free local models, Docker, AKS, and a three-stage Azure DevOps pipeline.

> Status: written without running against a live Azure subscription. Expect small fixes (API versions, model
> names and region availability change). Each step below says how to check it worked.

## What you need
Azure subscription (Contributor on it), Azure CLI (`az`), Docker, Python 3.12, git, `kubectl`, an Azure DevOps
organisation. Optional: Ollama (comes with the compose file).

## The picture
```
 laptop (Ollama, Chroma, Langfuse)           Azure
  step 1-5                                    rg-fai-dev | rg-fai-qa | rg-fai-prod
                                              Foundry (models) + AI Search + AKS + ACR + Key Vault + Log Analytics
 git push -> Azure DevOps: Build -> Dev -> (approve) QA -> (approve) Prod
```

## Step 1. Run it locally with free models (no Azure needed)
```bash
git clone <your repo> && cd foundry-ai-platform
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
cp .env.example .env            # set LLM_PROVIDER=ollama, VECTOR_STORE=chroma
docker compose -f ollama/docker-compose.yml up -d
docker exec -it $(docker ps -qf name=ollama) ollama pull llama3.1
docker exec -it $(docker ps -qf name=ollama) ollama pull nomic-embed-text
```
Check: `curl localhost:11434` prints "Ollama is running".

## Step 2. Ingest and ask (RAG)
```bash
cd app
uvicorn src.api:app --reload &
curl -X POST localhost:8000/ingest
curl -X POST localhost:8000/rag -H 'content-type: application/json' \
  -d '{"question":"How soon must covenant breaches be reported?"}'
```
Check: the answer says two business days and `sources` lists `lending-policy.md`.

## Step 3. Try the agent and tool calling
```bash
curl -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"question":"A 40m loan is 3.5 percent of NAV. What is 40 * 0.035, and is that under policy?","thread_id":"t1"}'
```
Check: `tools_used` shows `calculate` and `search_knowledge_base`. Read `app/src/tools.py` and add one tool of your own.

## Step 4. Turn on Langfuse tracing
Open http://localhost:3000, create a project, copy its keys into `.env` (`LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST=http://localhost:3000`), restart the API and ask again.
Check: a trace appears with the tool calls and the token counts.

## Step 5. Run the evals
```bash
cd app && python -m evals.run_evals
```
Check: a SUMMARY line and exit code 0. Break a document on purpose and watch it fail. This same command is the
release gate in the pipeline.

## Step 6. Create the Azure resource group (Dev)
```bash
az login
az account set --subscription <id>
./infra/deploy.sh dev swedencentral
```
This creates `rg-fai-dev` with Foundry (model deployments), AI Search, ACR, AKS, Key Vault and Log Analytics.
Check: the command prints `foundryEndpoint`, `searchEndpoint`, `acrName`, `aksName`. Note them.
If a model deployment fails, pick a region and model combination you have quota for and change `chatModel` in
`infra/main.bicep`. Repeat for `qa` and `prod` when you are ready.

## Step 7. Run the same app against Foundry
In `.env` set `LLM_PROVIDER=azure`, `AZURE_OPENAI_ENDPOINT=<foundryEndpoint>`. For a local run you may paste
a key; in AKS the app uses managed identity (give it the role *Cognitive Services OpenAI User* on the Foundry
resource, and *Search Index Data Contributor* on AI Search). Re-run steps 2 and 5.

## Step 8. Set up Azure DevOps (once)
1. Push the repo to Azure Repos or GitHub and create a pipeline from `pipelines/azure-pipelines.yml`.
2. Create a service connection (Azure Resource Manager, workload identity federation) and note its name.
3. Create three variable groups `fai-dev`, `fai-qa`, `fai-prod`, each with: `azureServiceConnection`, `acrName`,
   `aksName`, `rgName`, `foundryEndpoint`, `searchEndpoint`.
4. Create three Environments `fai-dev`, `fai-qa`, `fai-prod`. On `fai-qa` and `fai-prod` add an **Approval** check.
5. Give the service connection `AcrPush` on ACR, `Azure Kubernetes Service Cluster User` on AKS, and
   `Azure Kubernetes Service RBAC Writer` (or cluster-admin for a practice setup).

## Step 9. Ship it: Dev, QA, Prod
Push to `main`. The pipeline runs unit tests, builds the image once, pushes it to ACR, deploys to Dev, runs the
eval gate, waits for your approval, deploys the **same image** to QA, runs the evals again, waits for approval,
then deploys to Prod. Check each stage: `kubectl -n fai-dev get pods` and `curl` the service.

## Step 10. Fine-tuning (optional, practice flow)
```bash
cd app && python finetune/prepare_data.py
python finetune/submit_job.py gpt-4o-mini-2024-07-18
```
The sample file has six rows only, just enough to learn the flow; real fine-tuning needs hundreds of good
examples and a base model that supports it in your region. After it finishes, deploy the tuned model in Foundry
and point `CHAT_DEPLOYMENT` at it, then run the evals to compare. Try RAG and prompt changes first: fine-tune only
when evals show a style or format gap that retrieval cannot fix.

## Step 11. Learn to build it in parallel
Read `docs/VIBECODING.md`: it shows how to split the work into lanes with one branch and one AI coding session
each.

## Production checklist
- Secrets in Key Vault, not variable groups, once past practice (CSI driver or workload identity).
- Private endpoints and network rules for Foundry and AI Search.
- Content filters and prompt-injection tests added to `golden.jsonl`.
- Cost: set budgets and token limits; cheap models in Dev and QA.
- Rollback: `kubectl rollout undo` or redeploy the previous build id.
- Do not run Ollama in Prod; it is for local and offline practice.

## Cost warning
AKS, AI Search (Basic) and model deployments bill while they exist. Delete practice groups with
`az group delete -n rg-fai-dev --yes --no-wait`.
