# M1255 Paper-Route Capability-Separable Event-Timing Source Smoke

## Summary

M1255 implements source-timing overrides for the capability-separable source
constructor and runs the bounded no-training event-timing/source-state smoke
pre-registered by M1254.

Result:

```text
event_timing_source_smoke_infrastructure_pass_source_negative_route_to_result_audit
```

The infrastructure part passes: source timing is configurable from the CLI,
effective overrides are written to `summary.json`, trajectory proposals and
rollouts are produced, and no actor mutation, training, PPO, promotion, private
holdout, or actor-input expansion occurred.

The source result remains negative:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

## Implementation

M1255 adds source-collection overrides to
`autodrift.capability_separable_source_constructor`:

```text
--source-min-step
--source-max-steps
--source-snapshot-stride
--source-max-snapshots-per-scenario
--source-obstacle-longitudinal-min
--source-obstacle-longitudinal-max
```

The helper `source_collection_settings` reports both configured and effective
values so artifact readers can tell whether a run used config defaults or CLI
overrides.

Focused validation:

```text
tests/test_capability_separable_source_constructor.py
```

adds coverage for effective override reporting.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 124600 \
  --seed-count 4 \
  --max-pairs 8 \
  --max-pairs-per-seed 4 \
  --max-pairs-per-family-pair 8 \
  --source-min-step 18 \
  --source-snapshot-stride 2 \
  --source-max-snapshots-per-scenario 8 \
  --source-obstacle-longitudinal-min 4.0 \
  --source-obstacle-longitudinal-max 24.0 \
  --candidate-mode trajectory_proposal \
  --sequence-length 4 \
  --proposal-count-per-condition 24 \
  --proposal-seed 125500 \
  --proposal-steer-scale 0.45 \
  --proposal-brake-scale 0.45 \
  --proposal-throttle-scale 0.25 \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.002 \
  --target-max-best-margin 0.06 \
  --max-relocation-candidates 12 \
  --fine-relocation \
  --fine-parent-count 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1255_capability_separable_event_timing_source_smoke
```

## Evidence

Primary artifact:

```text
runs/m1255_capability_separable_event_timing_source_smoke/summary.json
```

Summary metrics:

```text
scenario_count: 52
snapshot_count: 299
candidate_pair_count: 276
matched_pair_count: 8
trajectory_proposals: 424
trajectory_proposal_rollouts: 848
relocation_candidates: 96
coarse_relocation_candidates: 64
fine_relocation_candidates: 32
near_boundary_viability_pairs: 1
best_actions_diverged_pairs: 2
low_regret_pairs: 8
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

Effective source timing:

```text
effective_min_step: 18
effective_max_steps: 220
effective_snapshot_stride: 2
effective_max_snapshots_per_scenario: 8
effective_obstacle_longitudinal_min: 4.0
effective_obstacle_longitudinal_max: 24.0
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
```

## Pair Diagnostics

M1255 found two pairs with branch-specific best-action divergence, but neither
passes the full acceptance criterion.

Pair 3:

```text
fault_family_pair: global_mu_drop->front_lateral_authority_drop
best_action_l2: 0.3338347673
cross_regret_A: 0.3354144041
cross_regret_B: 0.0017111134
pair_min_best_margin: -0.0004819446
rejection_reason: best_candidate_not_viable
```

Pair 7:

```text
fault_family_pair: global_mu_drop->brake_authority_drop
best_action_l2: 0.3316529095
cross_regret_A: 0.2090052680
cross_regret_B: 0.0161391286
pair_min_best_margin: -0.0004416509
rejection_reason: best_candidate_not_viable
```

Pair 4 is the only near-boundary viable row:

```text
near_boundary_viability: true
pair_min_best_margin: 0.0309116731
best_action_l2: 0.0
cross_regret_A: 0.0
cross_regret_B: 0.0
rejection_reason: best_actions_too_close
```

Interpretation:

```text
event timing found viable rows and action-divergent rows, but not the same rows.
```

The actionable gap remains the same as M1250-M1252: source mining can create
near-positive/nonviable action-divergent cases or viable/action-equivalent
cases, but not accepted capability-separable rows under the current simulator,
checkpoint, source family, and thresholds.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
event_timing_source_negative
```

Not classified as:

```text
contract_violation
training_instability
proof_washout
private_holdout_contamination
promotion_gate_failure
```

## Decision

Do not start another event-timing variant immediately.

M1254's fallback rule applies:

```text
if accepted rows remain zero, write event-timing source result audit before
another source run
```

Next milestone:

```text
m1256-paper-route-capability-separable-event-timing-source-result-audit
```

The audit should decide whether the capability-separable source-construction
branch needs a broader source-family/fidelity pivot, a branch synthesis, or one
new pre-registered source variable. It must not lower acceptance thresholds.
