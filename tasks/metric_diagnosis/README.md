# metric_diagnosis

Campaign metrics to diagnosis.

Given a table of campaign metrics, the model must identify what is wrong,
name the highest-leverage corrective action, and show the reasoning that
connects the numbers to the conclusion.

## Planned item format

- **Input:** a campaign metrics table (spend, impressions, clicks,
  conversions, and derived rates), possibly with context such as objective
  and time window.
- **Expected output:** the diagnosis, the single highest-leverage action,
  and the reasoning.
- **Scoring:** rubric-based, checking that the diagnosis matches the
  planted issue, the action addresses it, and the reasoning is numerate
  (correct arithmetic, correct metric relationships).

## Status

Skeleton. No test items exist yet. The metric schema, rubric, and test set
will be added and frozen before any model is scored.
