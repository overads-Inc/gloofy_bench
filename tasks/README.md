# tasks/

One directory per benchmark task. Each task directory contains its own
README describing the planned item format, output shape, and scoring
approach for that task.

Planned contents per task (none of this exists yet):

- `README.md`: task definition, item format, scoring approach
- a frozen, versioned test set of items
- a rubric or answer key, depending on the task type

Current tasks:

- `creative_tag/`: closed-vocabulary ad tagging
- `ad_copy/`: platform-constrained ad copy generation
- `metric_diagnosis/`: campaign metrics to diagnosis
- `lead_qualify/`: signal-cited lead scoring
- `chat/`: open marketing QA

Status: skeleton. No test items exist yet.
