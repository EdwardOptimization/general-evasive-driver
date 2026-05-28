# M1256 Paper-Route Capability-Separable Event-Timing Source Result Audit

## Summary

M1256 audits the M1255 event-timing/source-state source smoke before any further
source run.

Decision:

```text
event_timing_source_negative_stop_same_timing_variants_route_to_branch_synthesis
```

M1255 is an infrastructure pass but a source-negative result:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

The audit conclusion is that denser nearby source timing is not enough under
the current simulator, checkpoint, hidden-fault family, trajectory-proposal
budget, and unchanged capability-separable thresholds.

## Evidence

M1255 produced the intended artifacts:

```text
runs/m1255_capability_separable_event_timing_source_smoke/summary.json
runs/m1255_capability_separable_event_timing_source_smoke/matched_capability_pairs.csv
runs/m1255_capability_separable_event_timing_source_smoke/fault_family_pair_summary.csv
```

Run scope:

```text
scenario_count: 52
snapshot_count: 299
candidate_pair_count: 276
matched_pair_count: 8
trajectory_proposals: 424
trajectory_proposal_rollouts: 848
relocation_candidates: 96
fine_relocation_candidates: 32
```

Effective source timing:

```text
effective_min_step: 18
effective_snapshot_stride: 2
effective_max_snapshots_per_scenario: 8
effective_obstacle_longitudinal_min: 4.0
effective_obstacle_longitudinal_max: 24.0
```

Source result:

```text
accepted_separable_pairs: 0
near_boundary_viability_pairs: 1
best_actions_diverged_pairs: 2
low_regret_pairs: 8
unique_matched_fault_family_pairs: 2
unique_matched_seeds: 2
result_class: action_divergent_low_regret
```

Guardrails held:

```text
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

## Row Pattern

M1255 separated into two non-accepted patterns.

Pattern A: action-divergent but nonviable or one-sided.

```text
pair 3:
  fault_family_pair: global_mu_drop->front_lateral_authority_drop
  best_action_l2: 0.3338347673
  cross_regret_A: 0.3354144041
  cross_regret_B: 0.0017111134
  pair_min_best_margin: -0.0004819446
  rejection_reason: best_candidate_not_viable

pair 7:
  fault_family_pair: global_mu_drop->brake_authority_drop
  best_action_l2: 0.3316529095
  cross_regret_A: 0.2090052680
  cross_regret_B: 0.0161391286
  pair_min_best_margin: -0.0004416509
  rejection_reason: best_candidate_not_viable
```

Pattern B: viable but action-equivalent.

```text
pair 4:
  near_boundary_viability: true
  pair_min_best_margin: 0.0309116731
  best_action_l2: 0.0
  cross_regret_A: 0.0
  cross_regret_B: 0.0
  rejection_reason: best_actions_too_close
```

The desired accepted pattern did not appear:

```text
own-branch best margins >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

## Relation To Earlier Source Runs

M1242-M1255 now show a stable branch-level pattern:

```text
M1242 first-action lattice: accepted_separable_pairs=0
M1244 short-sequence lattice: accepted_separable_pairs=0
M1246 viability-band relocation: accepted_separable_pairs=0
M1247 fine relocation: accepted_separable_pairs=0
M1250 trajectory proposal: accepted_separable_pairs=0, near-miss
M1252 targeted margin restoration: accepted_separable_pairs=0, near-miss improved but still negative
M1255 event timing: accepted_separable_pairs=0, viable/action-equivalent and action-divergent/nonviable rows remain separate
```

The branch has repeatedly improved source diagnostics without producing an
accepted row. That is useful evidence, but it also means the current local
source-construction path is not yet yielding the paper-route source needed for
later history-necessity gates.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
event_timing_source_negative
```

More specific interpretation:

```text
capability_separable_source_family_gap
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

## Supported Claims

Supported:

```text
source timing overrides are implemented and traceable;
event timing alone did not create accepted capability-separable rows;
the current source branch repeatedly finds partial evidence but not accepted rows;
another immediate timing-window run would be local gate chasing.
```

Not supported:

```text
self-identification;
history necessity;
PPO readiness;
paper-level evidence;
real-vehicle claims;
overall project infeasibility.
```

## Decision

Stop same event-timing variants for now.

Do not proceed to:

```text
another source-min-step tweak
another source-snapshot-stride tweak
another obstacle longitudinal window tweak
another proposal-count increase
another local relocation budget increase
threshold relaxation
```

Next milestone:

```text
m1257-paper-route-capability-separable-source-construction-synthesis
```

M1257 should synthesize M1241-M1256 and choose the next branch explicitly. The
likely choices are:

```text
broader source family / scenario generator
model-fidelity or richer hidden-fault source
privileged teacher or optimizer-derived source
branch pause with a return to paper-route evidence planning
```

Any next source branch must be pre-registered with a new evidence variable and
must keep the same acceptance thresholds unless a separate threshold-policy
document justifies a change.
