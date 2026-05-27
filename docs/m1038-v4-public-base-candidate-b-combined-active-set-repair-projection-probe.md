# M1038 V4 Public Base Candidate B Combined Active-Set Repair Projection Probe

## Purpose

M1038 runs the no-PPO combined active-set repair/projection probe admitted by
M1037.

It uses the M1037 `row16x4` combined trajectory anchor, runs exact repair
endpoints, then applies temporal-safe projection before first replay. It does
not run PPO, promote, use private holdout, or change actor inputs.

## Command

```bash
rm -rf runs/m1038_candidate_b_combined_active_set_repair_projection_probe && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.candidate_b_combined_active_set_repair_projection_probe \
  --run-dir runs/m1038_candidate_b_combined_active_set_repair_projection_probe \
  --device auto
```

## Inputs

Base checkpoint:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Raw PPO proposal:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

Combined active-set anchor:

```text
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
```

Exact/projection corpora:

```text
M297 rejected-history preference
M270 outcome intervention
M393 current-family row15 conflict
M997 temporal sequence corpus
M267/M264 boundary replay corpus
M183/M170 boundary replay corpus
```

## Exact Repair Endpoints

M1038 creates three no-PPO exact repair endpoints:

| Label | Start mode | Exact pass | M297 delta | M270 delta | Anchor loss |
| --- | --- | --- | ---: | ---: | ---: |
| `raw_row16x4_s40` | `repair_from_raw` | true | -0.000358105 | -0.000007987 | 0.000250261 |
| `base_row16x4_s40` | `repair_from_base` | true | -0.000131607 | -0.000006437 | 0.000049676 |
| `line_row16x4_s40` | `line_search_boundary` | true | -0.000131607 | -0.000006437 | 0.000049676 |

All three exact repair endpoints preserve the actor-input contract and do not
use PPO or promotion.

## Temporal Projection Result

Temporal-safe projection over the repair endpoints produced:

```text
candidate_count: 39
temporal_exact_pass_count: 34
temporal_and_exact_pass_count: 34
eligible_candidate_count: 31
first_replay_attempted_candidate_count: 27
first_replay_pass_candidate_found: true
```

Selected candidate:

```text
label: m1031_base_row16x4_s40_a0_15
source: base_row16x4_s40
alpha: 0.15
checkpoint:
  runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Selected temporal/exact metrics:

```text
candidate_action_l2_mean: 0.002198
candidate_action_l2_max: 0.002520
M297 delta vs base: -0.000020
M270 delta vs base: -0.000001
exact_gate_pass: true
m297_m270_exact_pass: true
movement_retained_pass: true
```

Selected combined-anchor losses:

```text
combined_anchor_total_loss: 0.000006485
combined_anchor_m267_loss: 0.000028552
combined_anchor_m183_row16_loss: 0.000000968
```

## First Replay

M267/M264 first replay:

```text
gate_pass: true
candidate_success_drop_count: 17
baseline_success_drop_count: 17
row15_retained: true
candidate_normal_success_rate: 1.0
candidate_wrong_history_success_rate: 0.0
```

M267/M264 row15:

```text
normal_success: true
wrong_history_success: false
normal_margin: 0.005303
wrong_history_margin: -0.001181
```

M183/M170 first replay:

```text
gate_pass: true
candidate_success_drop_count: 17
baseline_success_drop_count: 17
candidate_normal_success_rate: 1.0
candidate_wrong_history_success_rate: 0.0
```

M183/M170 row16:

```text
normal_success: true
wrong_history_success: false
normal_margin: 0.000163
wrong_history_margin: -0.006258
```

This is the first candidate in this branch that simultaneously retains:

```text
M997 temporal exact retention
M297/M270 exact no-regression
M267/M264 row15 rejected-history failure
M183/M170 row16 normal success
```

## Result

```text
result_class: candidate_b_combined_active_set_projection_first_replay_candidate
failure_types: none
ppo_used: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

## Limits

This is a first-replay candidate, not a full public-gate promotion.

M1038 does not prove:

```text
six-surface full public replay pass
fresh public / OOD generalization pass
behavior seed retention
promotion readiness
paper-level evidence
private holdout performance
```

## Next Route

The next milestone should design the full public proof/generalization/behavior
gate for the selected candidate:

```text
m1039-v4-public-base-candidate-b-combined-active-set-full-public-gate-design
```

That gate should use the selected checkpoint above, keep Candidate B as the
baseline, and still block promotion until the full gate result is known.

## Decision

```text
candidate_b_combined_active_set_projection_first_replay_candidate_route_to_full_public_gate_design
```
