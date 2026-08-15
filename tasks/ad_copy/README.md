# ad_copy

Platform-constrained ad copy generation.

Given a brief, a target platform, and an angle, the model must produce a
headline, primary text, and CTA that respect the platform's character
limits and format rules.

## Planned item format

- **Input:** brief (product, audience, goal), platform, angle.
- **Expected output:** structured copy fields (headline, primary text, CTA)
  respecting the stated platform constraints.
- **Scoring:** hard constraints (character limits, required fields, format
  validity) checked programmatically; copy quality scored against a rubric.

## Status

Skeleton. No test items exist yet. The platform constraint table, rubric,
and test set will be added and frozen before any model is scored.
