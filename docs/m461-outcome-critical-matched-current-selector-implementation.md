# M461 Outcome-Critical Matched-Current Selector Implementation

## Purpose

M460 designed an outcome-critical selector because M459 found action-level
matched-current ambiguity without closed-loop outcome proof. M461 implements the
selector and smokes it on M459 artifacts.

No checkpoint is trained or promoted.

## Implementation

Added:

```text
src/autodrift/outcome_critical_matched_current_selector.py
tests/test_outcome_critical_matched_current_selector.py
```

The selector consumes:

```text
matched_pairs.csv
action_interventions.csv
outcome_interventions.csv
```

It writes:

```text
candidates.csv
compact_corpus.csv
summary.json
```

The key rule is strict:

```text
accepted =
  matched_current_pass
  and action_prefilter_pass
  and outcome_critical
```

Where `outcome_critical` requires normal success and at least one of:

```text
success_drop
margin_gap >= min_margin_gap
collision_gap
obstacle_completion_drop
```

Action-only rows are diagnostic and are not accepted.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_critical_matched_current_selector \
  --pairs-csv runs/m459_late_reveal_matched_current_seed9600/matched_pairs.csv \
  --action-interventions-csv runs/m459_late_reveal_matched_history_action_gate/action_interventions.csv \
  --outcome-interventions-csv runs/m459_late_reveal_matched_history_outcome_gate/outcome_interventions.csv \
  --max-pairs-per-checkpoint-target 60 \
  --min-margin-gap 0.02 \
  --min-action-distance 0.05 \
  --max-normal-pair-action-distance 0.08 \
  --min-target-z-delta 1.0 \
  --max-rows 96 \
  --max-per-probe-seed 16 \
  --max-per-target 32 \
  --max-per-variant 32 \
  --max-per-obstacle-bucket 8 \
  --min-accepted-rows 16 \
  --run-dir runs/m461_outcome_critical_selector_m459_pairs
```

Artifacts:

```text
runs/m461_outcome_critical_selector_m459_pairs/summary.json
runs/m461_outcome_critical_selector_m459_pairs/candidates.csv
runs/m461_outcome_critical_selector_m459_pairs/compact_corpus.csv
```

## Results

| metric | value |
| --- | ---: |
| candidate rows | 900 |
| matched-current pass | 900 |
| action-prefilter pass | 441 |
| action-only rows | 418 |
| outcome-critical rows | 56 |
| accepted rows | 23 |
| compact rows | 20 |
| compact probe seeds | 3 |
| compact obstacle labels | 2 |
| compact targets | 2 |
| compact variants | 2 |

Compact rows by variant and target:

| variant | target | rows |
| --- | --- | ---: |
| reset hidden | future lateral accel response | 6 |
| reset hidden | future yaw response | 6 |
| zero current response | future lateral accel response | 5 |
| zero current response | future yaw response | 3 |

Outcome-critical triggers in the compact corpus:

| trigger | rows |
| --- | ---: |
| success drop | 0 |
| positive margin gap | 18 |
| collision gap | 0 |
| obstacle-completion drop | 2 |

Source coverage:

| probe seed | label | rows |
| --- | --- | ---: |
| `9600` | drift_required | 4 |
| `9900` | drift_required | 6 |
| `10150` | drift_required | 6 |
| `10150` | unavoidable | 4 |

## Interpretation

M461 is a positive infrastructure result: the selector works, rejects action-only
rows, and extracts a compact outcome-critical corpus from M459 artifacts.

But it is not yet a full self-ID proof:

- no wrong-history rows are selected;
- no success-drop rows are selected;
- accepted rows are reset-hidden and zero-current-response;
- most evidence is margin-gap based rather than collision/success based.

This means M457/M459 are useful for response-history sensitivity, but not yet
for wrong-history belief proof. The next step should repeat the selector on
fresh matched-current/action/outcome artifacts and explicitly audit wrong-history
coverage.

## Decision

Decision:

```text
selector_pass_admit_m462_fresh_repeat_wrong_history_audit
```

No checkpoint is promoted.
