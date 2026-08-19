"""Run the marketing-bench exams against a frontier model.

Produces generations in the same JSONL shape the local evaluator emits,
so score.py grades every model through identical code. That matters: a
leaderboard where entries were scored by different paths is not a
leaderboard.

Keys are read from the environment, or from a .env file beside this
repo. Nothing is ever written to disk or into a generation file.

  export OPENAI_API_KEY=sk-...
  export GOOGLE_API_KEY=...

  uv run python harness/run_frontier.py --provider openai --model gpt-5.5 \
      --exam tasks/exam-v3.1.jsonl --out results/v31-gpt55.jsonl

Cost control: --limit stops after N items, so you can price a run before
committing to it. The full v3.1 exam is 150 items.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load_env() -> None:
    """Read a .env beside the repo, without adding a dependency."""
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def post(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            # rate limits and transient server errors are worth retrying;
            # a bad key or a bad request never is
            if e.code in (429, 500, 502, 503, 529) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"HTTP {e.code} from the API: {body}")
    raise SystemExit("giving up after 5 attempts")


def ask_openai(model: str, system: str, user: str, key: str) -> str:
    data = post(
        "https://api.openai.com/v1/chat/completions",
        {"model": model, "messages": [{"role": "system", "content": system},
                                      {"role": "user", "content": user}],
         "temperature": 0},
        {"Authorization": f"Bearer {key}"},
    )
    return data["choices"][0]["message"]["content"]


def ask_google(model: str, system: str, user: str, key: str) -> str:
    data = post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        {"systemInstruction": {"parts": [{"text": system}]},
         "contents": [{"parts": [{"text": user}]}],
         "generationConfig": {"temperature": 0}},
        {},
    )
    return data["candidates"][0]["content"]["parts"][0]["text"]


def main() -> None:
    load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["openai", "google"])
    p.add_argument("--model", required=True, help="e.g. gpt-5.5 or gemini-3.6-flash")
    p.add_argument("--exam", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int, default=0, help="stop after N items, for pricing a run")
    args = p.parse_args()

    env_var = "OPENAI_API_KEY" if args.provider == "openai" else "GOOGLE_API_KEY"
    key = os.environ.get(env_var)
    if not key:
        raise SystemExit(
            f"{env_var} is not set.\n"
            f"Either export it, or put it in {ROOT / '.env'} as {env_var}=your-key-here"
        )

    rows = [json.loads(l) for l in Path(args.exam).read_text().splitlines() if l.strip()]
    if args.limit:
        rows = rows[: args.limit]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = 0
    with out.open("w") as fh:
        for i, row in enumerate(rows, 1):
            msgs = row["messages"]
            system = msgs[0]["content"] if msgs[0]["role"] == "system" else ""
            user = next(m for m in msgs if m["role"] == "user")["content"]
            expected = msgs[2]["content"] if len(msgs) > 2 else None

            got = (ask_openai if args.provider == "openai" else ask_google)(
                args.model, system, user, key
            )
            fh.write(json.dumps({"id": row.get("id"), "task": row.get("task"),
                                 "prompt": user, "expected": expected, "got": got}) + "\n")
            fh.flush()
            done += 1
            print(f"\r{done}/{len(rows)}", end="", file=sys.stderr)

    print(f"\nwrote {done} generations to {out}", file=sys.stderr)
    print(f"score with:  uv run python harness/score.py {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
