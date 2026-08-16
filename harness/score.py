"""Stage 3 evaluation: the eval-card generator, v0.

Runs a model (base or base+adapter) against the FROZEN eval split and
scores what can be scored mechanically. Structured tasks get hard
numbers; prose tasks get printed side by side for human judgment.
The numbers printed here are the numbers that go on the eval card, so
nothing in this file may ever see the training data.

Run:  uv run python stage3/evaluate.py                 (base model)
      uv run python stage3/evaluate.py --adapter runs/stage3/adapter-x
"""

import argparse
import json
from pathlib import Path

from mlx_lm import load, generate

HERE = Path(__file__).resolve().parent
EVAL = HERE / "data" / "mlx" / "eval.jsonl"
EVAL_V2 = HERE / "data" / "exam-v2.jsonl"
DEFAULT_BASE = "mlx-community/Qwen3-1.7B-4bit"

TAG_FIELDS = ["hook", "angle", "persona", "offer", "funnel_stage"]
VOCAB = {
    "hook": {"question", "bold_claim", "statistic", "problem_callout", "curiosity_gap",
             "social_proof", "direct_offer", "story_open", "none_evident"},
    "angle": {"pain_relief", "aspiration", "authority", "novelty", "price_value",
              "urgency", "comparison", "community", "none_evident"},
    "persona": {"consumer_general", "parent", "professional", "business_owner",
                "developer", "student", "enthusiast", "none_evident"},
    "offer": {"discount", "free_trial", "free_shipping", "bundle", "gift_with_purchase",
              "lead_magnet", "demo_or_consult", "none_evident"},
    "funnel_stage": {"awareness", "consideration", "decision", "retention", "none_evident"},
}


def task_of(row: dict) -> str:
    if row.get("task"):
        return row["task"]
    text = row["messages"][1]["content"]
    if text.startswith("Tag this ad"):
        return "creative_tag"
    if text.startswith("Score this lead") or text.startswith("Qualify"):
        return "lead_qualify"
    if text.startswith("Diagnose"):
        return "metric_diagnosis"
    if text.startswith("Write"):
        return "ad_copy"
    return "chat"


def first_json(text: str):
    """Extract the first JSON object from a reply; strict answers are the
    whole reply, so anything needing rescue already loses points."""
    start = text.find("{")
    if start < 0:
        return None, False
    depth = 0
    for i, ch in enumerate(text[start:], start):
        depth += ch == "{"
        depth -= ch == "}"
        if depth == 0:
            try:
                obj = json.loads(text[start : i + 1])
                clean = text.strip() == text[start : i + 1].strip()
                return obj, clean
            except json.JSONDecodeError:
                return None, False
    return None, False


def score_tag(expected: str, got: str) -> dict:
    exp = json.loads(expected)
    obj, clean = first_json(got)
    if obj is None:
        return {"json_valid": 0, "strict": 0, "fields": 0, "in_vocab": 0}
    fields = sum(obj.get(f) == exp[f] for f in TAG_FIELDS) / len(TAG_FIELDS)
    in_vocab = sum(obj.get(f) in VOCAB[f] for f in TAG_FIELDS) / len(TAG_FIELDS)
    return {"json_valid": 1, "strict": int(clean), "fields": fields, "in_vocab": in_vocab}


def score_lead(expected: str, got: str) -> dict:
    exp = json.loads(expected)
    obj, clean = first_json(got)
    if obj is None:
        return {"json_valid": 0, "strict": 0, "band": 0, "score_close": 0}
    band = int(obj.get("band") == exp.get("band"))
    try:
        close = int(abs(int(obj.get("score", -100)) - int(exp.get("score"))) <= 15)
    except (TypeError, ValueError):
        close = 0
    return {"json_valid": 1, "strict": int(clean), "band": band, "score_close": close}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", default=None)
    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--max-tokens", type=int, default=420)
    p.add_argument("--dump", default=None, help="write raw generations to this jsonl")
    p.add_argument("--exam", default="v1", choices=["v1", "v2"],
                   help="v1 is the pinned continuity series, v2 the stratified benchmark")
    args = p.parse_args()

    src = EVAL if args.exam == "v1" else EVAL_V2
    rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
    model, tok = load(args.base, adapter_path=args.adapter)
    name = (args.adapter or "base") + " on " + args.base

    structured_scores: list[dict] = []
    by_stratum: dict = {}
    print(f"eval: exam {args.exam}, {len(rows)} items  model={name}\n")
    for row in rows:
        msgs = row["messages"][:2]
        # prose exam items carry no reference answer: they are judged
        # pairwise by judge.py, so there is nothing to score mechanically
        expected = row["messages"][2]["content"] if len(row["messages"]) > 2 else None
        prompt = tok.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False)
        got = generate(model, tok, prompt=prompt, max_tokens=args.max_tokens, verbose=False)
        task = task_of(row)
        if args.dump:
            with open(args.dump, "a") as df:
                df.write(json.dumps({"id": row.get("id"), "task": task,
                                     "prompt": msgs[1]["content"],
                                     "expected": expected, "got": got}) + "\n")
        if task == "creative_tag":
            s = score_tag(expected, got)
        elif task == "lead_qualify":
            s = score_lead(expected, got)
        else:
            s = None
        if s:
            structured_scores.append(s)
            if row.get("stratum"):
                by_stratum.setdefault(row["stratum"], []).append(s)
            print(f"[{task}] {s}")
        else:
            print(f"[{task}] (judged pairwise, not scored here)")
            if expected:
                print(f"  expected: {expected[:120]}...")
            print(f"  got:      {got[:120]}...")
        print()

    if structured_scores:
        keys = sorted({k for s in structured_scores for k in s})
        print("eval card, structured tasks")
        print("---------------------------")
        for k in keys:
            vals = [s[k] for s in structured_scores if k in s]
            print(f"{k:12s} {sum(vals) / len(vals):.2f}")

    if by_stratum:
        print("\nby stratum (the point of exam v2)")
        print("---------------------------------")
        for st, ss in sorted(by_stratum.items()):
            metric = "fields" if "fields" in ss[0] else "band"
            vals = [s[metric] for s in ss if metric in s]
            print(f"{st:14s} n={len(vals):3d}  {metric} {sum(vals) / len(vals):.3f}")


if __name__ == "__main__":
    main()
