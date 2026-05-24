# M535 Frozen Source-Surface Eval Implementation

## Purpose

M535 implements the evaluator designed in M534. The goal is to compare trained
L0/L2/L3 baselines on the same M399 natural source states instead of letting
each baseline reconstruct a different trajectory.

No checkpoint is promoted.

## Implementation

Added:

```text
src/autodrift/frozen_source_surface_eval.py
tests/test_frozen_source_surface_eval.py
```

The evaluator supports:

```text
source checkpoint:
  online recurrent source policy used to reconstruct frozen natural states

baseline checkpoint specs:
  label=history_level:path

baseline levels:
  L0_current_observation
  L2_finite_window
  L3_online_gru
```

Key semantics:

```text
1. M399 rolls the source environment and deep-copies frozen env states.
2. L0 receives the current 72-value P0 frame.
3. L2 receives a current-first stacked P0 history window.
4. L3 builds hidden state by replaying the source observation prefix through
   the target actor, then continues from the frozen source env.
5. All checkpoints must declare matching history_baseline metadata and P0 input
   contract.
```

This is a frozen off-policy surface evaluator. It is not a replacement for
closed-loop scenario-distribution evaluation.

## Focused Tests

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_frozen_source_surface_eval.py
```

Result:

```text
7 passed
```

The tests cover:

```text
baseline checkpoint spec parsing;
metadata mismatch rejection;
validated baseline loading;
temporal GRU current-first history stacking;
off-policy recurrent hidden construction;
frozen snapshot replay for feedforward and temporal-GRU actors;
source snapshot collection with history prefixes.
```

## Real Smoke

Command:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.frozen_source_surface_eval \
  --source-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --baseline-checkpoint l0_s3530=L0_current_observation:runs/m532_matched_l0_short_train_seed3530/checkpoint.pt \
  --baseline-checkpoint l2_s3530=L2_finite_window:runs/m532_matched_l2_short_train_seed3530/checkpoint.pt \
  --baseline-checkpoint l3_s3530=L3_online_gru:runs/m532_matched_l3_short_train_seed3530/checkpoint.pt \
  --env-config configs/m494_natural_belief_short_reveal_zero_relvel.json \
  --pairs-csv runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv \
  --tail-offsets 0 \
  --max-continuation-steps 20 \
  --max-pairs 2 \
  --device cpu \
  --run-dir runs/m535_frozen_source_surface_eval_smoke
```

Result:

```text
input_pair_count = 2
source_snapshot_count = 2
outcome_row_count = 6
invalid_row_count = 0
```

Artifacts:

```text
runs/m535_frozen_source_surface_eval_smoke/surface_outcomes.csv
runs/m535_frozen_source_surface_eval_smoke/surface_summary.csv
runs/m535_frozen_source_surface_eval_smoke/baseline_metadata.csv
runs/m535_frozen_source_surface_eval_smoke/summary.json
```

All three baseline checkpoints passed metadata validation:

```text
L0_current_observation
L2_finite_window
L3_online_gru
P0_human_view_no_wheel_no_oracle
```

## Interpretation

M535 passes the implementation gate. The evaluator can now compare trained
baselines on matched frozen source states. The smoke is too small for any
performance claim.

## Decision

```text
frozen_source_surface_eval_implementation_pass_admit_m536_matrix_smoke
```

Next blocker:

```text
m536-frozen-source-natural-surface-matrix-smoke
```
