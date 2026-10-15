"""Offline eval gate. Run from app/:  python -m evals.run_evals
Checks, per golden question: (1) retrieval hit, (2) answer contains the required facts, (3) LLM judge says grounded.
Exits non-zero if any aggregate score is under its threshold, so the pipeline can block a release."""
import json
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

from src.agent import run_rag
from src.llm import chat_model

THRESHOLDS = {"retrieval_hit": 0.8, "contains_facts": 0.8, "grounded": 0.8}
JUDGE = ("You grade an answer. Context passages and the answer follow. Reply with exactly GROUNDED if every "
         "claim in the answer is supported by the passages (or the answer says it does not know), else UNGROUNDED.\n\n"
         "Passages:\n{ctx}\n\nAnswer:\n{ans}")


def main() -> int:
    rows = [json.loads(line) for line in Path(__file__).with_name("golden.jsonl").read_text().splitlines() if line]
    scores = {k: [] for k in THRESHOLDS}
    for r in rows:
        out = run_rag(r["question"])
        ans = out["answer"].lower()
        if r["expected_source"]:
            scores["retrieval_hit"].append(r["expected_source"] in out["sources"])
        scores["contains_facts"].append(all(s.lower() in ans for s in r["must_contain"])
                                            and not any(s.lower() in ans for s in r.get("must_not_contain", [])) )
        verdict = chat_model().invoke([HumanMessage(content=JUDGE.format(ctx="\n".join(out["contexts"]), ans=out["answer"]))])
        scores["grounded"].append("UNGROUNDED" not in verdict.content.upper())
        print(r["id"], {k: v[-1] for k, v in scores.items() if v})
    summary = {k: round(sum(v) / len(v), 2) if v else 1.0 for k, v in scores.items()}
    print("SUMMARY", summary)
    failed = [k for k, t in THRESHOLDS.items() if summary[k] < t]
    if failed:
        print("FAILED:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
