"""Rebuild a runnable exam from its reference file.

The published exams carry labels, sources and a content hash, but not the
ad copy. The copy belongs to the brands that wrote it, and a benchmark
has no business redistributing 988 companies' creative work under its own
licence. References cost nothing in reproducibility and avoid that
entirely.

You supply the copy, from the Meta Ad Library URLs in the reference file
or from your own archive, as a JSON map of {id: "Tag this ad
creative.\\n\\nHeadline: ...\\nPrimary text: ...\\nCTA: ..."}. This
script verifies each one against the recorded hash and writes the exam in
the format the scorer expects.

  uv run python harness/assemble.py tasks/exam-v3.1.refs.jsonl copy.json \
      --out tasks/exam-v3.1.jsonl

Any item whose hash does not match is REPORTED AND DROPPED rather than
silently included: an exam scored against copy that differs from what was
labelled is not the same exam, and would produce numbers nobody could
compare.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SYSTEM = (
    "You are gloofy, a marketing model by overads. Answer directly and honestly. "
    "For tagging and scoring tasks, reply with strict JSON only."
)


def content_hash(text: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode()).hexdigest()[:16]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("refs")
    p.add_argument("copy", help="JSON map of {id: prompt text}")
    p.add_argument("--out", required=True)
    p.add_argument("--allow-missing", action="store_true",
                   help="write the exam even if some items could not be assembled")
    args = p.parse_args()

    refs = [json.loads(l) for l in Path(args.refs).read_text().splitlines() if l.strip()]
    copy = json.loads(Path(args.copy).read_text())

    rows, missing, mismatched = [], [], []
    for r in refs:
        text = copy.get(r["id"])
        if not text:
            missing.append(r["id"])
            continue
        if content_hash(text) != r["content_sha256_16"]:
            mismatched.append(r["id"])
            continue
        rows.append({
            "id": r["id"], "task": r["task"], "stratum": r.get("stratum"),
            "brand": r.get("brand", ""), "source": r.get("source", ""),
            "taxonomy": r.get("taxonomy"),
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
                {"role": "assistant", "content": json.dumps(r["labels"])},
            ],
        })

    print(f"assembled {len(rows)} of {len(refs)}", file=sys.stderr)
    if missing:
        print(f"  {len(missing)} missing copy: {missing[:5]}{'...' if len(missing) > 5 else ''}", file=sys.stderr)
    if mismatched:
        print(f"  {len(mismatched)} HASH MISMATCH, dropped: {mismatched[:5]}", file=sys.stderr)
        print("  the copy you supplied is not what was labelled; scores would not be comparable", file=sys.stderr)

    if (missing or mismatched) and not args.allow_missing:
        print("\nrefusing to write a partial exam. Pass --allow-missing to override,\n"
              "and report the item count alongside any score you publish from it.", file=sys.stderr)
        raise SystemExit(1)

    Path(args.out).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
