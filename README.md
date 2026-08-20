# marketing-bench

An open evaluation suite for marketing tasks. Medicine has HealthBench,
48,562 rubric criteria written by 262 physicians. Law has LegalBench-RAG,
6,858 expert-annotated pairs. Marketing had nothing comparable, so this
exists.

**Status: v1.0, public, with four models measured.** Every entry was run
through one harness with one specification and graded by one scorer,
because a leaderboard whose rows were scored by different paths is not a
leaderboard.

| model | 150 real published ads |
|---|---|
| Claude | 0.916 |
| annotator agreement ceiling | 0.911 |
| Gemini 3.6 Flash | 0.817 |
| GPT-5.5 | 0.792 |
| gloofy-1-nano (4B, ours) | 0.780 |
| Qwen3-4B untrained | 0.000 |

**Our own model places fifth and we published it anyway.** That is the
point of releasing the benchmark before the model: we could not tune the
questions to suit our answers, because the questions were frozen and
public first.

Read [results/LEADERBOARD.md](results/LEADERBOARD.md) for the caveats
that matter, including why Claude clears the ceiling (it is graded
against a key its own model family wrote) and why gloofy's number is
lower than an earlier one we reported (we found it was inflated by
prompt familiarity and corrected it).

## What it measures

Five tasks a marketing tool actually runs at volume. `creative_tag` and
`lead_qualify` are scored mechanically and are the load-bearing ones; the
prose tasks are judged blind in both orders and reported separately.

| task | what it asks | how it is scored |
|---|---|---|
| `creative_tag` | tag an ad with hook, angle, persona, offer and funnel stage from a closed vocabulary | exact facet accuracy, vocabulary closure, strict JSON |
| `lead_qualify` | band and score a lead, citing only signals present in the prompt | band accuracy, score within 15, JSON validity |
| `ad_copy` | write platform-shaped copy that respects character limits | blind pairwise judging |
| `metric_diagnosis` | read campaign metrics, name the problem and the highest-leverage action | blind pairwise judging |
| `chat` | answer an open marketing question | blind pairwise judging |

## Five exams, and why every version ships

587 items across five files. Nothing is ever deleted or quietly
rewritten: when a key changes, both versions stay.

**`tasks/exam-v1.jsonl`** (95 items) is the continuity series. It was
frozen early and has never been edited, so scores stay comparable across
every model and every date. It is not representative of the whole domain
and does not claim to be.

**`tasks/exam-v3.1.jsonl`** (150 items) is the one to use. Every item is
a REAL published ad, collected verbatim from the Meta Ad Library and
brand galleries, so it measures the job rather than our idea of the job.
Its predecessor `exam-v3.jsonl` (110 items) is kept for continuity.

**`tasks/exam-v2.1.jsonl`** (126 items) re-keys one stratum of v2 under
taxonomy v2.1 after we found our labelling rules had improved and the
answer key had never followed. The original `exam-v2.jsonl` ships
unchanged beside it. The same model scores 0.46 on the old key and 0.64
on the corrected one, which is exactly why both are here.

**`tasks/exam-v2.jsonl`** (126 items) is the original stratified
benchmark.
Every item was authored fresh as an exam item, verified to have zero
overlap with any training corpus, and stratified so each cell is
separately measurable:

- creative_tag: 10 each of awareness, consideration, decision, retention,
  deliberately ambiguous, and hard boundary cases
- lead_qualify: 12 each of should-be-hot, should-be-warm, should-be-cold
- prose: 10 each of ad_copy, metric_diagnosis and chat

Reporting both is the point. Benchmarks commonly swap their test set and
publish only the new number, which destroys comparability and hides
whether the model improved or the exam got easier.

## Human ceilings, published per set

**What the annotators are, stated plainly:** three independent Claude
agents, each shown the item alone with the taxonomy and no sight of the
others' answers, with a majority required. They are NOT human. Earlier
versions of this file called the resulting figure a "human ceiling",
which was wrong, and it has been corrected throughout.

This has a consequence for the leaderboard that we have to state
ourselves: **Claude's entry is graded against a key its own model family
produced.** That is a self-agreement advantage no other entry gets, and
it is the most likely explanation for Claude scoring above the ceiling.
Read its number with that in mind, and read the gap between it and GPT
or Gemini as smaller than it appears.

Labels come from three blind annotators with a majority required. Items
without a majority are discarded rather than guessed.

| set | annotator agreement | reading |
|---|---|---|
| exam v1 tags | 0.954 | the practical ceiling for tagging |
| exam v2 tags | 0.938 | stratified, so harder on average |
| boundary leads | 0.871 | three blind annotators disagree on one in eight |

A model reaching 0.87 on boundary leads has hit annotator consistency, not a
shortfall. A single project-wide ceiling would have hidden that.

## Running it

```bash
python harness/score.py --exam v2 --adapter <path-or-omit-for-base>
```

Mechanically scored tasks print per-stratum results. Prose is judged
pairwise:

```bash
python harness/judge.py pairs A.jsonl B.jsonl --both-orders
python harness/judge.py score verdicts.json
```

**Both-order judging is mandatory.** Every item is presented twice, once
each way, and a verdict counts only when the same answer wins both times.
Anything that flips with position is discarded. The judge prompt is
frozen and versioned inside `harness/judge.py`; changing it bumps the
version.

## Method notes, including the mistakes

Published because benchmarks usually hide exactly this.

1. **A frozen exam silently grew.** Hash-based splitting pulled fresh
   data into what was supposed to be a fixed test set, which would have
   made cross-round scores incomparable. Fixed by pinning ids to disk.
2. **The first position-bias check was wrong.** It compared raw slot win
   shares, which is confounded by which model landed in which slot. The
   corrected check measures one model's win rate by position, and it then
   flagged a bias that both-order judging proved was small-sample noise.
3. **The first answer key was only 0.893 aligned with expert consensus.**
   Twenty-two facets were re-keyed after a three-annotator study. An exam
   is only as good as its labels, and these were not good at first.

## Licence

Apache 2.0. Copyright 2026 overads Inc.
