# M864 V4 Generated Boundary Refinement Implementation

## Purpose

M864 implements the M862/M863 no-training generated-boundary refinement route.

The implementation question is:

```text
Can M860 generated wide/negative brackets be refined into enough accepted
boundary-new-to-M844 rows to pass sparse combined generated-boundary coverage?
```

M864 is not a training milestone:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Implementation

Added:

```text
src/autodrift/v4_generated_boundary_refinement.py
tests/test_v4_generated_boundary_refinement.py
```

The runner:

1. reads M860 generated replay rows and accepted rows;
2. selects same-source same-step same-axis `all_safe_closer_obstacle`
   wide/negative brackets;
3. prioritizes brackets with no M860 accepted boundary row;
4. reconstructs the original M825 temporal snapshots;
5. replays bounded normal closed-loop bisection/refinement between endpoint
   parameters;
6. reports refined-only and combined M860+refined coverage.

Pairability projection remains a cheap filter only. M864 does not execute
pair-delta sequence replay.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_generated_boundary_refinement \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --m860-generation-plan-rows runs/m860_v4_closer_obstacle_source_generation/generation_plan_rows.csv \
  --m860-generated-replay-rows runs/m860_v4_closer_obstacle_source_generation/generated_replay_rows.csv \
  --m860-accepted-boundary-rows runs/m860_v4_closer_obstacle_source_generation/accepted_generated_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m864_v4_generated_boundary_refinement \
  --device cpu
```

## Artifacts

```text
runs/m864_v4_generated_boundary_refinement/summary.json
runs/m864_v4_generated_boundary_refinement/bracket_seed_rows.csv
runs/m864_v4_generated_boundary_refinement/reconstructed_snapshot_rows.csv
runs/m864_v4_generated_boundary_refinement/refinement_rows.csv
runs/m864_v4_generated_boundary_refinement/accepted_refined_boundary_rows.csv
runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv
runs/m864_v4_generated_boundary_refinement/pairability_projection_rows.csv
runs/m864_v4_generated_boundary_refinement/refinement_summary.csv
runs/m864_v4_generated_boundary_refinement/gate_summary.csv
runs/m864_v4_generated_boundary_refinement/rejected_rows.csv
```

## Result

M864 completed and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
checkpoint_promoted: false
```

Bracket and reconstruction coverage passed:

```text
bracket_seed_rows: 25
no_m860_boundary_bracket_seed_rows: 13
unique_bracket_source_group_count: 25
unique_bracket_seed_count: 5
unique_bracket_fault_family_count: 9
reconstructed_snapshot_rows: 25
snapshot_rejection_rows: 0
```

Refinement was strongly positive:

```text
refinement_rows: 120
accepted_refined_boundary_rows: 42
accepted_no_m860_boundary_rows: 33
unique_refined_source_group_count: 20
unique_refined_seed_count: 4
unique_refined_fault_family_count: 9
```

Combined M860+M864 coverage passed sparse gate:

```text
combined_generated_boundary_rows: 59 >= 32
combined_boundary_new_to_m844_rows: 59 >= 24
combined_unique_source_group_count: 27 >= 20
combined_unique_seed_count: 5 >= 5
combined_unique_fault_family_count: 9 >= 8
combined_pairability_projection_rows: 365 >= 40
```

It did not pass strong gate:

```text
combined_generated_boundary_rows: 59 < 60
combined_unique_source_group_count: 27 < 32
combined_unique_seed_count: 5 < 8
```

Result class:

```text
v4_generated_boundary_refinement_sparse_useful
```

## Distribution

Combined rows:

```text
combined rows: 59
m860_generated: 17
m864_refined: 42
```

By bracket source class:

```text
no_m860_boundary: 33
m860_boundary_already_present: 9
M860 original rows: 17
```

By boundary axis:

```text
obstacle_lateral_offset: 56
obstacle_timing: 3
```

By seed:

```text
78050: 16
78057: 14
78048: 13
78058: 11
78055: 5
```

By fault family:

```text
brake_authority_drop: 10
rear_lateral_authority_drop: 9
drive_authority_drop: 9
combined_fault: 6
global_mu_drop: 6
front_lateral_authority_drop: 5
mass_cg_shift: 5
delay_noise_fault: 5
steering_fault: 4
```

The main residual limitation is axis/seed concentration. The result is sparse
useful, not strong.

## Gate Summary

Passed:

```text
actor checksum unchanged
residual-head checksum unchanged
bracket_seed_rows: 25 >= 10
accepted_refined_boundary_rows: 42 >= 8
combined_generated_boundary_rows: 59 >= 32
combined_pairability_projection_rows: 365 >= 40
pair_delta_sequence_replay_blocked: true
ppo_blocked: true
```

Failed strong criteria:

```text
combined_generated_boundary_rows: 59 < 60
combined_unique_source_group_count: 27 < 32
combined_unique_seed_count: 5 < 8
```

## Interpretation

Supported claims:

```text
M860 generated brackets were refinement-ready.
No-training generated-boundary refinement works.
Combined M860+M864 coverage passes sparse generated-boundary gates.
Actor and M761 contracts remain clean.
```

Unsupported claims:

```text
pair-delta outcome evidence
objective-ready self-ID corpus
learned policy improvement
PPO admission
checkpoint promotion
```

M864 is a real positive data-route result, but it still requires audit before
pair-delta mining. The audit should decide whether sparse generated-boundary
coverage is enough for a limited pair-delta refresh, or whether axis/seed
concentration requires another boundary-generation pass first.

## Tests

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_v4_generated_boundary_refinement.py
```

Result:

```text
2 passed
```

Compile check:

```bash
python -m compileall -q src/autodrift/v4_generated_boundary_refinement.py \
  tests/test_v4_generated_boundary_refinement.py
```

Result:

```text
passed
```

## Decision

Decision:

```text
v4_generated_boundary_refinement_sparse_useful
```

Next:

```text
m865-v4-generated-boundary-refinement-audit
```
