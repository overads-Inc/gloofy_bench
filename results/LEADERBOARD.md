# marketing-bench leaderboard

Measured 19 August 2026. Every number is reproducible with the harness
in this repo. Frontier entries beyond Claude are pending API keys.

Exams v2.1 and v3.1 correct a documented answer-key drift and a
coverage gap; the original v2 and v3 keys ship unchanged alongside
them. See TAXONOMY.md and the drift note below. Claude's entries were
measured on v2/v3 and are re-sat on the corrected exams next baseline
run.

## creative_tag, exact facet accuracy

| model | exam v2 (synthetic) | exam v2.1 (re-keyed) | exam v3 (110 REAL ads) | exam v3.1 (150 REAL ads) |
|---|---|---|---|---|
| human ceiling (3 blind annotators) | 0.938 | 0.933 on re-keyed items | 0.911 | 0.92 on new items |
| **Claude** | **0.860** | pending | **0.904** | pending |
| gloofy-1-nano r14 (4B, tag specialist) | 0.680 | 0.710 | 0.770 | 0.770 |
| gloofy-1-nano r7e (1.7B, retired entry) | 0.710 | | 0.600 | |
| Qwen3 base untrained | 0.000 | 0.000 | 0.000 | 0.000 |

gloofy's real-ad score improved from 0.600 to 0.770 across rounds 8 to
14 (real ads in training, specialist adapters, a measured scaling curve
that chose 4B, and a targeted round of mood-led real ads). The gap to
Claude remains large and is stated plainly below.

## lead_qualify (exam v2)

| model | band | score within 15 |
|---|---|---|
| Claude | 0.972 | |
| gloofy-1-nano r14 (4B, lead specialist) | 0.830 | 0.810 |
| gloofy-1-nano r7e (retired entry) | 0.720 | |
| Qwen3 base untrained | 0.000 | 0.000 |

The untrained base scores zero because it does not perform the task at
all: 3 to 4 percent vocabulary closure means it invents its own labels
rather than using the required ones.

## prose tasks, blind pairwise judging (exam v2)

Every item presented twice, once in each order, three judges per
presentation, majority per presentation, and an item counts only if the
same answer wins both ways. Consistency was 30 of 30, so nothing was
discarded.

| task | gloofy-1-nano r7e vs untrained base |
|---|---|
| ad_copy | gloofy 7 of 10 |
| chat | gloofy 7 of 10 |
| metric_diagnosis | base 8 of 10 |
| overall | gloofy 16 of 30 (53%) |

**Caveat that matters:** the model measured here predates the training
round that added mandatory computation blocks for numeric answers.
Campaign diagnosis is lost on arithmetic errors, which is exactly what
that round targeted, so this row should be read as a pre-fix baseline
and will be re-measured.

## What these numbers actually say

**Claude is far more accurate than gloofy, and pretending otherwise
would be dishonest.** On real ads Claude sits at 0.904 against a human
ceiling of 0.911, which is effectively human-level. gloofy-1-nano, at 4
billion parameters, scores 0.770. A model a fraction of the size does
not match a frontier model on judgment, and the gap is not close. What
gloofy offers instead is stated on the site: zero marginal cost, local
inference, and calibrated honesty about exactly this gap.

**A drift note every benchmark should have to write.** Between rounds
our labelling rules improved (documented in TAXONOMY.md, versioned).
One stratum's answer key silently predated the change, and the model
was being marked wrong for agreeing with current annotators: the same
model scored 0.46 on the stale key and 0.64 on the re-keyed one. Both
keys ship. Benchmarks that quietly update their answers are worthless,
and benchmarks that never re-examine their keys are quietly wrong.

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
