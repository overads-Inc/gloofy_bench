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
