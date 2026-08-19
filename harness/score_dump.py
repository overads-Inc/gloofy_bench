"""Score a generations dump. Every leaderboard entry goes through this.

The scoring logic here is identical to the local evaluator's, so a
frontier entry and a gloofy entry are graded by the same code. That is
the whole point: a leaderboard whose rows were scored by different paths
is not a leaderboard.

  uv run python harness/score_dump.py results/v31-gpt55.jsonl
"""

import json
import sys
from pathlib import Path

FIELDS = ["hook", "angle", "persona", "offer", "funnel_stage"]
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


def first_json(text):
    """Extract the first JSON object. Answers needing rescue from a code
    fence or surrounding prose lose the strict-format point but still
    score their fields: format and judgment are measured separately."""
    start = text.find("{")
    if start < 0:
        return None, False
    depth = 0
    for i, ch in enumerate(text[start:], start):
        depth += ch == "{"
        depth -= ch == "}"
        if depth == 0:
            try:
                obj = json.loads(text[start:i + 1])
                return obj, text.strip() == text[start:i + 1].strip()
            except json.JSONDecodeError:
                return None, False
    return None, False


def main(path):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    n = fields = in_vocab = valid = strict = 0
    per_facet = {f: 0 for f in FIELDS}
    for r in rows:
        if not r.get("expected"):
            continue
        exp = json.loads(r["expected"])
        obj, clean = first_json(r["got"])
        n += 1
        if obj is None:
            continue
        valid += 1
        strict += int(clean)
        for f in FIELDS:
            hit = obj.get(f) == exp[f]
            fields += hit
            per_facet[f] += hit
            in_vocab += obj.get(f) in VOCAB[f]

    print(f"{Path(path).name}   {n} items\n")
    print(f"fields      {fields / (n * 5):.3f}")
    print(f"in_vocab    {in_vocab / (n * 5):.3f}")
    print(f"json_valid  {valid / n:.3f}")
    print(f"strict      {strict / n:.3f}")
    print("\nper facet")
    for f in FIELDS:
        print(f"  {f:14s} {per_facet[f] / n:.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
