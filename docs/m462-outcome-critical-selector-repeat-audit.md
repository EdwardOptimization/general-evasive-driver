# M462 Outcome-Critical Selector Repeat Audit

## Purpose

M462 repeats the M461 outcome-critical selector on fresh late-reveal artifacts.
The goal is not to train or promote a checkpoint. It tests whether the M461
selector finds robust outcome-critical evidence on a disjoint seed window and
whether wrong-history interventions become strong enough to justify a
wrong-history proof gate.

## Contract

- Actor contract unchanged: P0 human-view no-wheel 72-dim frame plus online GRU
  hidden state.
- No hidden dynamics, oracle feasibility labels, TTC, reference trajectory, or
  rule-mode inputs are added.
- Public-gate base remains:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

No checkpoint is promoted.

## Commands

Fresh matched-current mining:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --probe-seeds 10200,10300,10400 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m462_late_reveal_matched_current_fresh_seed10200
```

Action intervention gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m462_late_reveal_matched_current_fresh_seed10200/matched_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.05 \
  --max-pairs-per-checkpoint-target 80 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m462_late_reveal_matched_history_action_gate
```

Continuation outcome gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m462_late_reveal_matched_current_fresh_seed10200/matched_pairs.csv \
  --delay-steps 2 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 60 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m462_late_reveal_matched_history_outcome_gate
```

Outcome-critical selector:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_critical_matched_current_selector \
  --pairs-csv runs/m462_late_reveal_matched_current_fresh_seed10200/matched_pairs.csv \
  --action-interventions-csv runs/m462_late_reveal_matched_history_action_gate/action_interventions.csv \
  --outcome-interventions-csv runs/m462_late_reveal_matched_history_outcome_gate/outcome_interventions.csv \
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
  --run-dir runs/m462_outcome_critical_selector_fresh_seed10200
```

## Results

Matched-current repeat:

```text
candidate pairs:          73281
accepted pairs:             422
physical pairs:             422
left steps:                  31
obstacle buckets:            32
targets:
  future_braking_deceleration:   190
  future_yaw_response:           168
  future_lateral_accel_response:  64
```

Selector summary:

```text
candidate variant rows:        900
action prefilter pass:         376
action-only diagnostics:       306
outcome-critical rows:         140
accepted rows:                  70
compact rows:                   34
compact probe seeds:             3
compact obstacle labels:         3
compact targets:                 3
compact variants:                2
selector_pass:                True
```

Accepted rows by variant:

```text
reset_hidden:             31
zero_current_response:    31
wrong_matched_history:     8
```

Compact rows by variant:

```text
zero_current_response:    26
reset_hidden:              8
wrong_matched_history:     0
```

Compact outcome type:

```text
success_drop:                 6
collision_gap:                6
positive_margin_gap:         31
obstacle_completion_drop:    12
```

Wrong-history audit:

```text
wrong-history candidate rows:               180
wrong-history action-prefilter pass:        136
wrong-history outcome-critical rows:         10
wrong-history accepted raw rows:              8
wrong-history compact rows:                   0
accepted wrong-history success-drop rows:     0
accepted wrong-history collision-gap rows:    0
accepted wrong-history completion-drop rows:  1
accepted wrong-history positive-margin rows:  7
accepted wrong-history source labels:         aes_feasible only
accepted wrong-history probe seeds:           10300 only
max accepted wrong-history margin gap:        0.055137
```

Artifacts:

```text
runs/m462_late_reveal_matched_current_fresh_seed10200/summary.json
runs/m462_late_reveal_matched_history_action_gate/summary.json
runs/m462_late_reveal_matched_history_outcome_gate/summary.json
runs/m462_outcome_critical_selector_fresh_seed10200/summary.json
runs/m462_outcome_critical_selector_fresh_seed10200/wrong_history_audit.json
runs/m462_outcome_critical_selector_fresh_seed10200/wrong_history_accepted_rows.csv
```

## Interpretation

M462 confirms that the M461 selector is useful beyond the original M459 rows:
the fresh seed window produces a larger compact corpus than M461, including
success-drop and collision-gap rows. This is a positive repeat for the
reset/zero-current outcome-critical diagnostic.

It does not yet justify a wrong-history proof gate. Wrong-history produces
eight accepted raw rows, but those rows are weak and narrow: they do not enter
the compact corpus, have no success-drop or collision-gap rows, and are
concentrated in one probe seed and the `aes_feasible` label. One accepted row
has obstacle-completion drop, while the remaining accepted rows are positive
margin-gap evidence only.

## Decision

```text
fresh_repeat_pass_wrong_history_weak_admit_m463
```

M462 is completed as a repeat audit. The next step should redesign the
wrong-history outcome-critical task or selector instead of expanding a
wrong-history gate from this evidence.
