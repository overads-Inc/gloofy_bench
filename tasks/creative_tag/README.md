# creative_tag

Closed-vocabulary ad tagging.

Given the text of an ad creative, the model must tag it along fixed
dimensions: hook, angle, persona, offer, and funnel stage. Every dimension
has a closed vocabulary; the model must pick from the allowed values and
return strict JSON.

## Planned item format

- **Input:** ad copy (text), plus the closed vocabulary for each dimension.
- **Expected output:** strict JSON with one value per dimension, drawn only
  from the allowed vocabulary.
- **Scoring:** exact-match per dimension against expert labels. Invalid
  JSON or out-of-vocabulary values score zero for the affected dimension.

## Status

Skeleton. No test items exist yet. The vocabulary, item schema, and test
set will be added and frozen before any model is scored.
