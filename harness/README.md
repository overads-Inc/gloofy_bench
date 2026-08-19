# harness/

Scoring code and the evaluation runner.

This directory will contain everything needed for a stranger to reproduce
any published number: loading a frozen test set, running a model against
it, scoring the outputs, and emitting a results file.

Planned contents (none of this exists yet):

- an evaluation runner with a model-agnostic interface, so frontier APIs
  and local open-weights models are scored by the exact same code path
- per-task scorers matching the format described in each `tasks/<name>/README.md`
- deterministic output: same test set version plus same model outputs
  yields the same score

Status: skeleton. No scoring code exists yet.


## Adding the frontier baselines

The leaderboard has two empty rows, GPT and Gemini. Filling them needs
API keys, which live in a `.env` file in the repo root and never leave
your machine.

1. Copy the template:

       cp .env.example .env

2. Paste your keys into it:

       OPENAI_API_KEY=sk-...
       GOOGLE_API_KEY=...

   Get them at platform.openai.com/api-keys and
   aistudio.google.com/apikey.

3. Price the run before committing to it. Ten items first:

       uv run python harness/run_frontier.py --provider openai \
         --model gpt-5.5 --exam tasks/exam-v3.1.jsonl \
         --out results/v31-gpt55.jsonl --limit 10

4. Then the full 150-item exam, and score it through the same scorer
   every other entry uses:

       uv run python harness/run_frontier.py --provider openai \
         --model gpt-5.5 --exam tasks/exam-v3.1.jsonl \
         --out results/v31-gpt55.jsonl
       uv run python harness/score.py results/v31-gpt55.jsonl

   Repeat with `--provider google --model gemini-3.6-flash`.

`.env` is gitignored. Keys are read at run time, never written into a
generations file, and never printed.
