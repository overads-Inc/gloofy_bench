"""Round 6: the prose judge protocol.

Three of the five tasks (ad_copy, metric_diagnosis, chat) produce prose,
which no mechanical scorer can grade. This builds blind pairwise
comparisons instead: for each exam item, model A's answer and model B's
answer are presented side by side with the order deterministically
scrambled, and judges pick a winner without knowing which is which.

Two design rules that make the number trustworthy:

1. The judge prompt is FROZEN and versioned. It ships with the eval card
   so anyone can rerun the same judging. Changing it bumps the version.
2. Order is scrambled per item by a hash of the id, not by chance, so a
   rerun produces the identical pairing. Position bias is then measured
   rather than assumed away: if the side-A win rate across all items is
   far from 50%, the judges are biased and the result is suspect.

Usage:
  prepare pairs:  uv run python stage3/judge.py pairs A.jsonl B.jsonl
  score verdicts: uv run python stage3/judge.py score verdicts.json
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROSE_TASKS = {"ad_copy", "metric_diagnosis", "chat"}
PAIRS = HERE.parent / "runs" / "stage3" / "judge-pairs.json"

JUDGE_PROMPT_VERSION = "v1"
JUDGE_PROMPT = """You are grading two answers to the same marketing question. You do not know which model wrote either one, and you must not guess or speculate about it.

Pick the better answer on these criteria, in this order of importance:

1. Correctness. Any arithmetic must be right. Any claim about how ad platforms behave must be true. An answer with a wrong number loses to one without, regardless of style.
2. Honesty. Saying "there is not enough data to tell" when that is true beats a confident diagnosis. Asking for a missing number beats inventing one. Naming what the answer cannot know is a strength.
3. Actionability. Naming the single highest-leverage action beats listing five options. Specific beats generic.
4. Discipline. For ad copy: the action named in the copy matches the CTA, platform character limits are respected, no real brand names, the headline is not restated in the body.
5. Concision. Shorter wins only when nothing of value is lost.

Reply with the winner and one sentence of reasoning. If the two answers are genuinely equivalent in quality, say tie: do not invent a preference."""


def scramble(item_id: str) -> bool:
    """Deterministic per-item order flip. Same input, same pairing forever."""
    return int(hashlib.sha256((item_id + "order").encode()).hexdigest(), 16) % 2 == 1


def load(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("task") in PROSE_TASKS:
            out[r["id"]] = r
    return out


def build_pairs(a_path: Path, b_path: Path, a_name: str, b_name: str,
                both_orders: bool = False):
    """both_orders presents every item twice, once each way. A verdict only
    counts if the same model wins in both presentations; anything that
    flips with position is position-dependent noise and is discarded."""
    a, b = load(a_path), load(b_path)
    shared = sorted(set(a) & set(b))
    pairs = []
    for i in shared:
        orders = [False, True] if both_orders else [scramble(i)]
        for flip in orders:
            pairs.append({
                "id": i + ("#rev" if (both_orders and flip) else "#fwd" if both_orders else ""),
                "item": i,
                "task": a[i]["task"],
                "question": a[i].get("prompt") or "",
                "left": (b if flip else a)[i]["got"],
                "right": (a if flip else b)[i]["got"],
                "left_is": (b_name if flip else a_name),
                "right_is": (a_name if flip else b_name),
            })
    PAIRS.write_text(json.dumps({
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "judge_prompt": JUDGE_PROMPT,
        "a": a_name, "b": b_name, "both_orders": both_orders, "pairs": pairs,
    }, indent=1))
    print(f"{len(pairs)} blind pairs written to {PAIRS}")
    print("by task:", dict(Counter(p["task"] for p in pairs)))


def score(verdicts_path: Path):
    """verdicts.json: [{id, winner: left|right|tie}] from the judges."""
    data = json.loads(PAIRS.read_text())
    by_id = {p["id"]: p for p in data["pairs"]}
    verdicts = json.loads(Path(verdicts_path).read_text())

    if data.get("both_orders"):
        return score_both_orders(data, by_id, verdicts)

    wins, tasks, positions = Counter(), {}, Counter()
    for v in verdicts:
        p = by_id.get(v["id"])
        if not p:
            continue
        positions[v["winner"]] += 1
        if v["winner"] == "tie":
            winner = "tie"
        else:
            winner = p[f"{v['winner']}_is"]
        wins[winner] += 1
        tasks.setdefault(p["task"], Counter())[winner] += 1

    total = sum(wins.values())
    print(f"judge protocol {data['judge_prompt_version']}  {total} judged pairs\n")
    for name in (data["a"], data["b"], "tie"):
        c = wins.get(name, 0)
        print(f"{name:28s} {c:3d}  {c / total * 100:5.1f}%")
    print("\nby task:")
    for t, c in sorted(tasks.items()):
        n = sum(c.values())
        print(f"  {t:18s} " + "  ".join(f"{k}: {v}/{n}" for k, v in c.most_common()))

    # Position bias must be measured per MODEL, not per slot: a raw slot
    # share is confounded by which model landed where. The real test is
    # whether one model wins more when it happens to sit on the left.
    slots = {"left": Counter(), "right": Counter()}
    for v in verdicts:
        p = by_id.get(v["id"])
        if not p or v["winner"] == "tie":
            continue
        a_slot = "left" if p["left_is"] == data["a"] else "right"
        slots[a_slot]["win" if p[f"{v['winner']}_is"] == data["a"] else "loss"] += 1
    rates = {}
    for s, c in slots.items():
        n = c["win"] + c["loss"]
        if n:
            rates[s] = c["win"] / n
            print(f"\n{data['a']} win rate when on the {s}: {c['win']}/{n} = {rates[s]:.1%}")
    if len(rates) == 2:
        gap = abs(rates["left"] - rates["right"])
        verdict = "acceptable" if gap < 0.20 else "REAL POSITION BIAS, result not publishable as is"
        print(f"position-bias gap: {gap:.1%} ({verdict})")
        if gap >= 0.20:
            print("remedy: judge every pair in BOTH orders and keep only "
                  "order-consistent verdicts")


def score_both_orders(data, by_id, verdicts):
    """Consistency-filtered scoring: an item counts only if both
    presentations agree on the winner."""
    seen = {}
    for v in verdicts:
        p = by_id.get(v["id"])
        if not p:
            continue
        winner = "tie" if v["winner"] == "tie" else p[f"{v['winner']}_is"]
        seen.setdefault(p["item"], {})[p["id"].split("#")[-1]] = (winner, p["task"])

    wins, tasks = Counter(), {}
    flipped = 0
    for item, got in seen.items():
        if len(got) < 2:
            continue
        (w1, task), (w2, _) = got.get("fwd", (None, None)), got.get("rev", (None, None))
        if w1 is None or w2 is None:
            continue
        if w1 != w2:
            flipped += 1
            continue
        wins[w1] += 1
        tasks.setdefault(task, Counter())[w1] += 1

    counted = sum(wins.values())
    total = counted + flipped
    print(f"judge protocol {data['judge_prompt_version']}, both orders")
    print(f"{total} items judged twice; {flipped} flipped with position and were DISCARDED")
    print(f"{counted} order-consistent verdicts counted\n")
    if not counted:
        print("no consistent verdicts, nothing to report")
        return
    for name in (data["a"], data["b"], "tie"):
        c = wins.get(name, 0)
        print(f"{name:28s} {c:3d}  {c / counted * 100:5.1f}% of consistent")
    print("\nby task (consistent only):")
    for t, c in sorted(tasks.items()):
        n = sum(c.values())
        print(f"  {t:18s} " + "  ".join(f"{k}: {v}/{n}" for k, v in c.most_common()))
    print(f"\nconsistency rate: {counted}/{total} = {counted / total:.1%} "
          f"({'healthy' if counted / total >= 0.7 else 'LOW, judges are unstable'})")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    mk = sub.add_parser("pairs")
    mk.add_argument("a")
    mk.add_argument("b")
    mk.add_argument("--a-name", default="A")
    mk.add_argument("--b-name", default="B")
    mk.add_argument("--both-orders", action="store_true")
    sc = sub.add_parser("score")
    sc.add_argument("verdicts")
    args = p.parse_args()

    if args.cmd == "pairs":
        build_pairs(Path(args.a), Path(args.b), args.a_name, args.b_name, args.both_orders)
    else:
        score(Path(args.verdicts))


if __name__ == "__main__":
    main()
