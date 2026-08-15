# lead_qualify

Signal-cited lead scoring.

Given a contact's profile and behavior signals, the model must produce a
score, a qualification band, and, critically, the specific signals that
drove the score. A number without cited evidence does not count.

## Planned item format

- **Input:** contact attributes and behavior signals (for example: role,
  company size, page views, email engagement, demo requests).
- **Expected output:** numeric score, qualification band, and the cited
  signals behind the score.
- **Scoring:** band accuracy against expert labels, plus a citation check:
  the cited signals must actually appear in the input and support the
  direction of the score.

## Status

Skeleton. No test items exist yet. The signal schema, banding rules, and
test set will be added and frozen before any model is scored.
