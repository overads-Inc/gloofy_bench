# marketing-bench leaderboard

Measured 17 August 2026. Every number is reproducible with the harness
in this repo. Frontier entries beyond Claude are pending API keys.

## creative_tag, exact facet accuracy

| model | exam v2 (synthetic, stratified) | exam v3 (REAL ads) |
|---|---|---|
| human ceiling (3 blind annotators) | 0.938 | 0.911 |
| **Claude** | **0.860** | **0.904** |
| gloofy-1-nano r7e (1.7B) | 0.710 | 0.600 |
| Qwen3-1.7B untrained | 0.000 | 0.000 |

## lead_qualify, band accuracy (exam v2)

| model | band |
|---|---|
| Claude | 0.972 |
| gloofy-1-nano r7e | 0.720 |
| Qwen3-1.7B untrained | 0.000 |

The untrained base scores zero because it does not perform the task at
all: 3 to 4 percent vocabulary closure means it invents its own labels
rather than using the required ones.

## What these numbers actually say

**Claude is far more accurate than gloofy, and pretending otherwise
would be dishonest.** On real ads Claude sits at 0.904 against a human
ceiling of 0.911, which is effectively human-level. gloofy-1-nano, at
1.7 billion parameters, scores 0.600. A model 1/500th the size does not
match a frontier model on judgment, and the gap is not close.

**Claude scores HIGHER on real ads (0.904) than on our synthetic exam
(0.860).** That is worth publishing loudly, because it means our
authored exam is harder and stranger than reality. Some of what exam v2
measures is our own taxonomy edge cases rather than the actual job.
Anyone building a synthetic benchmark should assume the same until they
check.

**One stratum inverts the ranking.** On deliberately ambiguous ads,
where the honest answer is often none_evident:

| model | ambiguous stratum |
|---|---|
| gloofy-1-nano | 0.72 |
| Claude | 0.44 |

gloofy was trained explicitly to decline when an ad carries no evidence
for a facet. Claude, absent that training, interprets confidently and is
wrong more often. This is the one place a small tuned model beats a
frontier one, and it is not an accident: it is the single behaviour our
training data drilled hardest.

## The honest positioning that follows

gloofy-1-nano is not competitive with frontier models on accuracy and
this leaderboard says so permanently. Its case rests on four other
things, each measurable:

1. **Cost.** Roughly three orders of magnitude cheaper per call at
   volume, since it runs locally with no API charge at all.
2. **Latency.** Milliseconds on a laptop rather than a network round
   trip.
3. **Privacy.** The data never leaves the machine.
4. **Calibrated honesty.** It says none_evident when an ad says nothing,
   which the frontier baseline does not.

If your task is tagging a thousand ads a day and you can accept 0.60
against a human ceiling of 0.911, gloofy is free forever and yours. If
you need 0.90, use Claude and pay for it. Publishing both numbers is the
point of this benchmark.
