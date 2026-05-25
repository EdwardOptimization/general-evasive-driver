# M867 V4 Generated Boundary Pair-Delta Refresh Implementation

## Purpose

M867 implements the no-training M866 design:

```text
Convert M864 pairability projection into actual pair-delta sequence outcome
evidence over M864 combined generated-boundary rows.
```

M867 is not a training or promotion milestone:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

Added:

```text
src/autodrift/v4_generated_boundary_pair_delta_refresh.py
tests/test_v4_generated_boundary_pair_delta_refresh.py
```

The runner:

1. reads M864 combined generated-boundary rows;
2. treats blank `accepted_primary` values from M864 as accepted generated rows;
3. assigns stable synthetic candidate IDs for M864 rows whose original
   `candidate_id` field is blank;
4. builds source-aware left/right generated-boundary pair candidates;
5. selects replay pairs with source/seed/fault/axis caps and seed-aware
   balancing;
6. reconstructs temporal snapshots from M825 source rows;
7. replays only `pair_delta_positive` and `pair_delta_negative` first;
8. writes raw accepted and balanced pair-delta artifacts;
9. replays component-control directions only after accepted pair-delta rows
   exist, and only as diagnostics.

Pairability projection remains a candidate filter. M867's evidence is actual
closed-loop sequence replay.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_generated_boundary_pair_delta_refresh \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --combined-boundary-rows runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv \
  --pairability-projection-rows runs/m864_v4_generated_boundary_refinement/pairability_projection_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m867_v4_generated_boundary_pair_delta_refresh \
  --device cpu
```

## Artifacts

```text
runs/m867_v4_generated_boundary_pair_delta_refresh/summary.json
runs/m867_v4_generated_boundary_pair_delta_refresh/pair_candidate_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/replay_pair_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/reconstructed_pair_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/reconstructed_snapshot_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/accepted_pair_delta_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/balanced_pair_delta_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/component_control_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/train_public_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/eval_public_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/source_holdout_public_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/diversity_summary.json
runs/m867_v4_generated_boundary_pair_delta_refresh/gate_summary.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/rejected_rows.csv
```

## Result

M867 completed with frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Candidate selection passed the M866 candidate gates:

```text
pair_candidate_rows: 1332 >= 120
selected_replay_pairs: 118 >= 80
selected_unique_left_source_group_count: 27 >= 16
selected_unique_left_seed_count: 5 >= 5
selected_unique_left_fault_family_count: 9 >= 8
```

Pair-delta replay produced real outcome signal:

```text
reconstructed_pair_rows: 118
reconstructed_snapshot_rows: 27
pair_delta_sequence_rows: 1416
accepted_pair_delta_rows: 234
accepted_pair_delta_degradation_rows: 156
accepted_pair_delta_improvement_rows: 78
pair_delta_success_flip_rows: 97
pair_delta_collision_flip_rows: 97
max_abs_margin_delta: 0.04554687977030536
```

The balanced corpus is sparse but source-limited:

```text
balanced_pair_delta_rows: 32
balanced_unique_left_source_group_count: 5
balanced_unique_left_seed_count: 2
balanced_unique_left_fault_family_count: 5
balanced_unique_fault_family_pair_count: 11
balanced_unique_hold_steps_count: 2
balanced_unique_direction_count: 2
balanced_max_left_source_group_dominance: 0.25
balanced_max_left_seed_dominance: 0.5
balanced_max_direction_dominance: 0.75
balanced_max_axis_pair_dominance: 0.96875
```

Result class:

```text
v4_generated_boundary_pair_delta_refresh_source_limited
```

## Distribution

Raw accepted pair-delta rows are concentrated:

```text
left_seed:
  78058: 192
  78050: 42

direction:
  pair_delta_negative: 154
  pair_delta_positive: 80

left_boundary_axis:
  obstacle_lateral_offset: 162
  obstacle_timing: 72
```

Balanced rows remain concentrated:

```text
left_seed:
  78058: 16
  78050: 16

direction:
  pair_delta_negative: 24
  pair_delta_positive: 8

left_boundary_axis:
  obstacle_lateral_offset: 31
  obstacle_timing: 1
```

Component controls are diagnostic only:

```text
component_control_rows: 396
component-control rows cannot satisfy primary M867 gates
```

## Interpretation

Supported claims:

```text
M867 successfully converts M864 pairability projection into actual
pair-delta sequence outcome evidence.
Candidate selection is now source/seed/fault diverse.
There is real pair-delta sensitivity on M864 generated-boundary rows.
Actor and M761 residual-head checksums are unchanged.
```

Unsupported claims:

```text
M867 is a strong pair-delta corpus.
M867 is objective-ready without audit.
M867 proves learned self-identification.
M867 admits PPO or checkpoint promotion.
Component controls are primary pair-delta evidence.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  balanced accepted pair-delta rows are concentrated in two left seeds and one
  dominant left-axis family.

metric_artifact:
  component-control rows are diagnostic only and cannot satisfy primary gates.

contract_violation:
  not observed.
```

## Decision

M867 should route to audit before objective design:

```text
generated_boundary_pair_delta_refresh_source_limited_audit_required
```

The next milestone should audit whether this source-limited but real pair-delta
surface is enough for a limited objective/replay corpus, or whether the branch
must generate additional boundary rows targeting the missing accepted seeds,
directions, and axes.
