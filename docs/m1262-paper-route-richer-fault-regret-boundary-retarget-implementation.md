# M1262 Paper-Route Richer-Fault Regret-Boundary Retarget Implementation

## Summary

M1262 implements and runs the bounded fixed-action obstacle-geometry retarget
smoke admitted by M1261.

Decision:

```text
regret_boundary_retarget_infrastructure_pass_source_negative_route_to_result_audit
```

The infrastructure part passes:

```text
source_reconstruction_reliable: true
source_reconstructed_snapshot_count: 812
retarget_candidate_count: 441
retarget_rollouts: 1764
```

The source result remains negative:

```text
strict_accepted_count: 0
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
source_positive: false
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, self-identification claim, paper-level claim, or true
high-fidelity physical fault claim occurred.

## Implementation

Added:

```text
src/autodrift/capability_separable_regret_retarget.py
tests/test_capability_separable_regret_retarget.py
```

The tool:

1. Reads the M1259 source run and selects regret-boundary target rows.
2. Reconstructs M1259 snapshots deterministically from the same config,
   seeds, faults, collection window, and snapshot ids.
3. Loads the fixed best-A and best-B trajectory-proposal sequences from M1259.
4. Scans a bounded obstacle-geometry grid around the target pair.
5. Replays four rollouts per geometry:

```text
condition A with best-A sequence
condition A with best-B sequence
condition B with best-B sequence
condition B with best-A sequence
```

6. Reuses strict `evaluate_action_separability`.
7. Reports anti-collision-dominance diagnostics.

Strict acceptance remains:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

`asymmetric_success_drop` is not accepted source-positive evidence.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_separable_regret_retarget \
  --source-run-dir runs/m1259_richer_fault_capability_source_smoke \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --target-pair-id 5 \
  --max-target-pairs 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1262_richer_fault_regret_boundary_retarget_smoke
```

## Evidence

Primary artifact:

```text
runs/m1262_richer_fault_regret_boundary_retarget_smoke/summary.json
```

Summary metrics:

```text
selected_target_pairs: 1
selected_pair_ids: [5]
source_reconstructed_snapshot_count: 812
retarget_candidate_count: 441
retarget_rollouts: 1764
strict_accepted_count: 0
rejected_retarget_rows: 441
all_four_rollouts_collision_count: 193
own_branch_viability_fail_count: 207
wrong_branch_collision_count: 208
low_regret_count: 441
best_actions_diverged_pairs: 438
result_class: action_divergent_low_regret
```

Guardrails:

```text
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
source_reconstruction_reliable: true
```

Snapshot reconstruction check:

```text
pair_id,condition,snapshot_id,seed,fault,step,status
5,A,212,78049,mu_drop_extreme_preexisting,27,matched
5,B,277,78049,brake_fade_extreme_pre_emergency,33,matched
```

## Regret Distribution

The geometry scan did not amplify two-sided regret.

Observed:

```text
own-branch viable rows: 234 / 441
action-diverged rows: 438 / 441
min_cross_regret >= 0.004: 298 / 441
min_cross_regret >= 0.005: 0 / 441
min_cross_regret >= 0.020: 0 / 441
max min_cross_regret: 0.0043813964
```

Best min-regret row:

```text
retarget_id: 423
relocated_obstacle_body_x: 10.9230481481
relocated_obstacle_body_y: -1.8976139516
relocated_obstacle_half_width: 1.1668958958
best_action_l2: 0.7001441121
margin_A_best_A: 1.1236772413
margin_A_best_B: 1.1192958449
margin_B_best_B: 1.0689311680
margin_B_best_A: 1.0645472562
cross_regret_A: 0.0043813964
cross_regret_B: 0.0043839118
rejection_reason: insufficient_cross_regret
```

The nearest strict-regret cases are far from the `0.02` threshold. Geometry
retargeting preserved action divergence but did not make either fixed sequence
meaningfully worse in the wrong hidden branch.

## Anti-Collision Diagnostics

M1262 explicitly prevents a false positive from making all actions fail:

```text
all_four_rollouts_collision_count: 193
own_branch_viability_fail_count: 207
wrong_branch_collision_count: 208
```

Interpretation:

```text
Some obstacle geometries are too hard and collapse into collision-dominated
rows, but the viable rows still remain low-regret.
```

Therefore M1262 should not be followed by a larger same-axis geometry grid
without a result audit.

## Validation

```bash
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_capability_separable_regret_retarget.py \
  tests/test_capability_separable_source_constructor.py
```

Result:

```text
13 passed in 2.09s
```

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
regret_boundary_geometry_retarget_negative
```

Not classified as:

```text
contract_violation
training_instability
proof_washout
private_holdout_contamination
promotion_gate_failure
metric_artifact
```

## Decision

M1262 passes as infrastructure but fails as source-positive evidence.

Do not train.

Do not run PPO.

Do not promote.

Do not expand the same geometry grid immediately.

Next:

```text
m1263-paper-route-richer-fault-regret-boundary-retarget-result-audit
```

The audit should decide whether the richer-fault branch should:

```text
stop geometry-only retargeting,
try source-step/fault-severity retargeting,
refresh source families,
or synthesize/pivot toward high-fidelity fault simulation.
```
