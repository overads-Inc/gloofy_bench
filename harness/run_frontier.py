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

# The exam files carry gloofy's own system prompt, which states edge-case
# rules but never names the five fields or their allowed values. gloofy
# knows those from training; a model meeting the task cold cannot guess
# them, and in testing GPT and Gemini both invented their own schema and
# scored zero for reasons that had nothing to do with marketing judgment.
#
# So every model that was not trained on the taxonomy is given it in the
# prompt. This is the fair comparison and it is the one Claude's published
# entry already used, but it MUST be disclosed on the leaderboard: gloofy
# carries the taxonomy in its weights, everyone else is handed it at
# inference. Both are legitimate; pretending they are the same is not.
TASK_SPEC = """You are tagging ad creative against a fixed taxonomy. Reply with strict JSON only, no prose and no code fence, using exactly these five keys and only values from these lists:

hook: question, bold_claim, statistic, problem_callout, curiosity_gap, social_proof, direct_offer, story_open, none_evident
angle: pain_relief, aspiration, authority, novelty, price_value, urgency, comparison, community, none_evident
persona: consumer_general, parent, professional, business_owner, developer, student, enthusiast, none_evident
offer: discount, free_trial, free_shipping, bundle, gift_with_purchase, lead_magnet, demo_or_consult, none_evident
funnel_stage: awareness, consideration, decision, retention, none_evident

Rules: persona is the economic role the ad sells to, never a story identity; business_owner runs the business, professional is an employed individual. Numeric evidence claims are statistic; peer adoption framing is social_proof. A permanent free tier is offer none_evident; free_trial must be time-limited. funnel_stage decision requires purchase mechanics in the ad itself (a price, a buy CTA, or a redeemable offer); evaluation content is consideration however commanding the CTA verb. Length is not evidence: a four-word ad can carry a claim and a forty-word ad can carry none. A claim asserted in four words is still bold_claim. Emoji, hashtags and capitalisation are formatting, not signals. Brand-mood copy that asserts nothing is hook none_evident, but its funnel_stage is usually awareness or consideration; funnel_stage none_evident is rare. direct_offer means the ad IS the deal; a confident tone alone is not an offer. A question mark does not make a question hook: "Tired of X?" is problem_callout."""


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


# Newer OpenAI models reject temperature 0 and permit only the default.
# We ask for 0 where it is allowed, because a benchmark wants determinism,
# and fall back where it is not. Which path a run took is recorded, since
# a non-deterministic entry is a weaker result and the card should say so.
OPENAI_TEMP_SUPPORTED = {}


def ask_openai(model: str, system: str, user: str, key: str) -> str:
    body = {"model": model, "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}]}
    if OPENAI_TEMP_SUPPORTED.get(model, True):
        body["temperature"] = 0
    try:
        data = post("https://api.openai.com/v1/chat/completions", body,
                    {"Authorization": f"Bearer {key}"})
    except SystemExit as e:
        if "temperature" not in str(e):
            raise
        OPENAI_TEMP_SUPPORTED[model] = False
        body.pop("temperature", None)
        print(f"note: {model} does not accept temperature 0, running at its default",
              file=sys.stderr)
        data = post("https://api.openai.com/v1/chat/completions", body,
                    {"Authorization": f"Bearer {key}"})
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


def ask_anthropic(model: str, system: str, user: str, key: str) -> str:
    data = post(
        "https://api.anthropic.com/v1/messages",
        {"model": model, "max_tokens": 1024, "temperature": 0, "system": system,
         "messages": [{"role": "user", "content": user}]},
        {"x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    return "".join(b.get("text", "") for b in data["content"])


def ask_local(base_url: str, model: str, system: str, user: str) -> str:
    """Score any OpenAI-compatible endpoint, which llama-server, vLLM, Ollama
    and LM Studio all expose. This is how a GGUF gets measured through the
    identical path the hosted models take: same prompt, same scorer, no
    special case for the model that happens to be ours."""
    data = post(
        base_url,
        {"model": model, "temperature": 0,
         "messages": [{"role": "system", "content": system},
                      {"role": "user", "content": user}]},
        {},
    )
    return data["choices"][0]["message"]["content"]


def main() -> None:
    load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["openai", "google", "anthropic", "local"])
    p.add_argument("--base-url", default=None,
                   help="OpenAI-compatible endpoint, for scoring a local model. "
                        "With llama-server: http://127.0.0.1:8080/v1/chat/completions")
    p.add_argument("--model", required=True, help="e.g. gpt-5.5 or gemini-3.6-flash")
    p.add_argument("--exam", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int, default=0, help="stop after N items, for pricing a run")
    p.add_argument("--spec", action="store_true", default=True,
                   help="give the model the taxonomy in-prompt (default: on). "
                        "Required for any model not trained on it, and disclosed on the card.")
    p.add_argument("--no-spec", dest="spec", action="store_false",
                   help="use the exam file's own system prompt verbatim")
    args = p.parse_args()

    if args.provider == "local":
        if not args.base_url:
            raise SystemExit("--provider local needs --base-url, e.g.\n"
                             "  llama-server -m model.gguf --port 8080\n"
                             "  --base-url http://127.0.0.1:8080/v1/chat/completions")
        key = "not-needed"
    else:
        env_var = {"openai": "OPENAI_API_KEY", "google": "GOOGLE_API_KEY",
                   "anthropic": "ANTHROPIC_API_KEY"}[args.provider]
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
            system = TASK_SPEC if args.spec else (
                msgs[0]["content"] if msgs[0]["role"] == "system" else "")
            user = next(m for m in msgs if m["role"] == "user")["content"]
            expected = msgs[2]["content"] if len(msgs) > 2 else None

            if args.provider == "local":
                got = ask_local(args.base_url, args.model, system, user)
            else:
                got = {"openai": ask_openai, "google": ask_google,
                       "anthropic": ask_anthropic}[args.provider](args.model, system, user, key)
            fh.write(json.dumps({"id": row.get("id"), "task": row.get("task"),
                                 "prompt": user, "expected": expected, "got": got}) + "\n")
            fh.flush()
            done += 1
            print(f"\r{done}/{len(rows)}", end="", file=sys.stderr)

    print(f"\nwrote {done} generations to {out}", file=sys.stderr)
    print(f"score with:  uv run python harness/score.py {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
