# marketing-bench

An open evaluation benchmark for marketing AI tasks.

Part of the gloofy project (gloofy.ai) by overads Inc.

> **Status: skeleton. No test items exist yet. Nothing is scored yet.**

## Why this exists

Every serious professional domain has an open benchmark that lets you check
a model's claims against expert-defined ground truth:

- Medicine has HealthBench: 48,562 rubric criteria written by 262 physicians.
- Law has LegalBench-RAG: 6,858 expert-annotated pairs.
- Marketing has nothing comparable.

Marketing is one of the largest discretionary spend categories in business,
and the tools that serve it increasingly run on language models, yet there is
no open, reproducible way to measure whether a model is actually good at
marketing work. marketing-bench exists to fill that gap.

## Task categories

Five initial tasks, chosen because they are high-volume jobs that real
marketing tools run constantly, each with a well-defined output shape:

| task | what it measures |
|---|---|
| `creative_tag` | Closed-vocabulary ad tagging: hook, angle, persona, offer, funnel stage from ad copy |
| `ad_copy` | Platform-constrained generation: headline, primary text, CTA within platform character limits |
| `metric_diagnosis` | Campaign metrics to diagnosis: what is wrong, the highest-leverage action, and the reasoning |
| `lead_qualify` | Signal-cited lead scoring: score, band, and the specific signals that drove it |
| `chat` | Open marketing QA: consistent, numerate, direct marketing conversation |

Each task lives in `tasks/<task_name>/` with its own README describing the
planned item format and scoring approach.

## Design principles

1. **Published before the model it was built alongside.** marketing-bench
   ships before gloofy-1 is fine-tuned. The test sets are frozen first, so
   the model cannot be tuned against them after the fact and baseline
   numbers are recorded honestly.
2. **Frontier models on the leaderboard, including where gloofy loses.**
   A benchmark that only shows its sponsor winning is marketing, not
   measurement. Baselines from frontier models are first-class results,
   and losses are published alongside wins.
3. **Broader than any one model.** The benchmark covers marketing work in
   general, not the subset any particular model happens to be good at.
   Task coverage is decided by what marketing tools actually need, not by
   what gloofy-1 can do.
4. **Reproducible by a stranger.** Frozen, versioned test sets plus public
   scoring code in this repo. Anyone can rerun any claimed number without
   asking permission or trusting us.

## Repository layout

```
tasks/     one directory per task: item format, rubric, frozen test sets
harness/   scoring code and evaluation runner
results/   published, versioned results and leaderboard data
docs/      methodology, versioning policy, contribution notes
```

## License

Apache 2.0. See [LICENSE](LICENSE).
