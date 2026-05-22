# M178 Dual-Checkpoint Outcome Proof Surface

M177 found a small action-level self-identification sensitivity lift for
`m170_split` over `m168_strict`. M178 asks the harder question: does that action
difference already produce outcome-level dependence on response history under
the raw matched-current continuation surface?

Result: raw continuation outcome is neutral. M168 and M170 are effectively
identical on this gate, and wrong-history intervention does not create success
drops or meaningful clearance-margin degradation.

## Harness Update

`matched_history_outcome_gate` now supports the same `--pair-label-mode all`
option as `matched_history_intervention_gate`. This is required for fair
checkpoint comparison on a shared matched-pair surface whose original
`checkpoint_label` values came from older source checkpoints.

Default behavior remains `--pair-label-mode matching`.

## Setup

Run:

```text
runs/m178_dual_checkpoint_outcome_proof_surface_seed9510
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m159_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --pair-label-mode all \
  --device cpu \
  --run-dir runs/m178_dual_checkpoint_outcome_proof_surface_seed9510
```

Artifacts:

```text
summary.json
outcome_interventions.csv
outcome_summary.csv
```

The run evaluates `480` matched-current pairs per checkpoint and `5760`
continuation rows total.

## Aggregate Results

| Checkpoint | Variant | Pairs | Normal success | Variant success | Success drops | Normal better | Normal margin | Variant margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| m168_strict | delayed_history | 480 | 0.870833 | 0.870833 | 0.000000 | 0.060417 | 0.725276 | 0.723679 | 0.001598 |
| m168_strict | normal | 480 | 0.870833 | 0.870833 | 0.000000 | 0.000000 | 0.725276 | 0.725276 | 0.000000 |
| m168_strict | reset_hidden | 480 | 0.870833 | 0.870833 | 0.000000 | 0.372917 | 0.725276 | 0.713674 | 0.011602 |
| m168_strict | wrong_matched_history | 480 | 0.870833 | 0.870833 | 0.000000 | 0.000000 | 0.725276 | 0.724736 | 0.000540 |
| m168_strict | zero_action_history | 480 | 0.870833 | 0.870833 | 0.000000 | 0.000000 | 0.725276 | 0.726809 | -0.001532 |
| m168_strict | zero_current_response | 480 | 0.870833 | 0.870833 | 0.000000 | 0.216667 | 0.725276 | 0.716909 | 0.008367 |
| m170_split | delayed_history | 480 | 0.870833 | 0.870833 | 0.000000 | 0.060417 | 0.725600 | 0.723956 | 0.001644 |
| m170_split | normal | 480 | 0.870833 | 0.870833 | 0.000000 | 0.000000 | 0.725600 | 0.725600 | 0.000000 |
| m170_split | reset_hidden | 480 | 0.870833 | 0.870833 | 0.000000 | 0.372917 | 0.725600 | 0.713945 | 0.011656 |
| m170_split | wrong_matched_history | 480 | 0.870833 | 0.870833 | 0.000000 | 0.000000 | 0.725600 | 0.725096 | 0.000504 |
| m170_split | zero_action_history | 480 | 0.870833 | 0.870833 | 0.000000 | 0.000000 | 0.725600 | 0.727155 | -0.001554 |
| m170_split | zero_current_response | 480 | 0.870833 | 0.870833 | 0.000000 | 0.216667 | 0.725600 | 0.717180 | 0.008420 |

## Target-Level Signal

The only substantial raw outcome degradation comes from `reset_hidden` and
`zero_current_response` on lateral/yaw targets. This affects clearance margin
and obstacle completion, but not success rate.

| Checkpoint | Target | Variant | Normal success | Variant success | Normal better | Margin gap | Obstacle completed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| m168_strict | future_lateral_accel_response | reset_hidden | 0.643750 | 0.643750 | 0.487500 | 0.014653 | 0.543750 |
| m168_strict | future_lateral_accel_response | zero_current_response | 0.643750 | 0.643750 | 0.650000 | 0.023643 | 0.493750 |
| m168_strict | future_yaw_response | reset_hidden | 0.968750 | 0.968750 | 0.631250 | 0.018724 | 0.900000 |
| m168_strict | future_yaw_response | zero_current_response | 0.968750 | 0.968750 | 0.000000 | 0.000634 | 0.900000 |
| m170_split | future_lateral_accel_response | reset_hidden | 0.643750 | 0.643750 | 0.487500 | 0.014822 | 0.543750 |
| m170_split | future_lateral_accel_response | zero_current_response | 0.643750 | 0.643750 | 0.650000 | 0.023788 | 0.493750 |
| m170_split | future_yaw_response | reset_hidden | 0.968750 | 0.968750 | 0.631250 | 0.018739 | 0.900000 |
| m170_split | future_yaw_response | zero_current_response | 0.968750 | 0.968750 | 0.000000 | 0.000660 | 0.900000 |

Wrong-history remains outcome-neutral:

| Checkpoint | Wrong-history success drops | Wrong-history margin gap |
| --- | ---: | ---: |
| m168_strict | 0 / 480 | 0.000540 |
| m170_split | 0 / 480 | 0.000504 |

## M170 Minus M168

| Variant | Delta normal margin | Delta variant margin | Delta margin gap | Delta normal better |
| --- | ---: | ---: | ---: | ---: |
| delayed_history | 0.000324 | 0.000278 | 0.000046 | 0.000000 |
| normal | 0.000324 | 0.000324 | 0.000000 | 0.000000 |
| reset_hidden | 0.000324 | 0.000271 | 0.000053 | 0.000000 |
| wrong_matched_history | 0.000324 | 0.000360 | -0.000036 | 0.000000 |
| zero_action_history | 0.000324 | 0.000346 | -0.000022 | 0.000000 |
| zero_current_response | 0.000324 | 0.000271 | 0.000053 | 0.000000 |

The M170 raw-outcome improvement is negligible. The M177 action-level
wrong-history lift does not translate into raw continuation outcome sensitivity.

## Interpretation

What M178 supports:

- M168 and M170 are behaviorally equivalent on raw matched-current continuation
  outcome.
- Raw `wrong_matched_history` is too weak as an outcome proof surface.
- `reset_hidden` and `zero_current_response` do produce meaningful margin
  degradation on some targets, but not success drops.
- M170 should not replace M168 as the main checkpoint based on this gate.

What M178 does not support:

- no outcome-level proof that the policy must use matched command-response
  history;
- no evidence that M170's small action-level gain is outcome-critical;
- no reason to run more PPO before strengthening the outcome proof surface.

## Decision

Keep the dual-track status:

- M168 remains the strict full-replay checkpoint and outcome-retention anchor.
- M170 remains the split-aware branch with slightly stronger action-level
  self-ID sensitivity.
- The next step should use boundary relocation / near-boundary outcome mining,
  not more PPO.

This matches the earlier M160 to M161 lesson: the raw matched-current surface can
be action-sensitive but outcome-neutral; a near-boundary relocation surface is
needed to test whether changed actions are actually safety-critical.

## Validation

Targeted tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest \
  tests/test_matched_history_outcome_gate.py \
  tests/test_matched_history_intervention_gate.py -q
```

Result:

```text
7 passed
```
