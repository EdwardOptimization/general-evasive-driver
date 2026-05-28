# M1260 Paper-Route Richer-Fault Capability Source Result Audit

## Summary

M1260 audits the strict M1259 richer-fault source smoke before any further
source run.

Decision:

```text
richer_fault_source_low_regret_audit_admit_regret_boundary_retarget_design
```

M1259 is an infrastructure pass and a strict source-negative result:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

It is not source-positive, but it does produce a better repair target than the
previous branch: pair 5 is viable in both hidden branches and has large best
action separation, but two-sided cross regret is below threshold.

## Acceptance Correction

M1259 exposed and fixed a metric artifact:

```text
old behavior:
  accepted = symmetric_margin_accept or asymmetric_success_drop

strict behavior:
  accepted = symmetric_margin_accept
```

The strict source-positive criterion remains:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

`asymmetric_success_drop` remains a diagnostic signal, not accepted source
evidence.

## Evidence

Primary artifacts:

```text
runs/m1259_richer_fault_capability_source_smoke/summary.json
runs/m1259_richer_fault_capability_source_smoke/matched_capability_pairs.csv
runs/m1259_richer_fault_capability_source_smoke/fault_family_pair_summary.csv
```

Strict rerun summary:

```text
scenario_count: 116
snapshot_count: 812
candidate_pair_count: 784
matched_pair_count: 12
trajectory_proposals: 642
trajectory_proposal_rollouts: 1284
relocation_candidates: 144
near_boundary_viability_pairs: 8
best_actions_diverged_pairs: 4
asymmetric_success_drop_pairs: 0
low_regret_pairs: 12
accepted_separable_pairs: 0
unique_matched_fault_family_pairs: 3
unique_matched_seeds: 3
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

## Key Row

Pair 5:

```text
seed: 78049
fault_family_pair: global_mu_drop->brake_authority_drop
condition_A_fault: mu_drop_extreme_preexisting
condition_B_fault: brake_fade_extreme_pre_emergency
best_action_l2: 0.7001441121
margin_A_best_A: 0.0799886482
margin_A_best_B: 0.0747198233
margin_B_best_B: 0.0337841324
margin_B_best_A: 0.0295662466
cross_regret_A: 0.0052688249
cross_regret_B: 0.0042178858
rejection_reason: insufficient_cross_regret
```

Interpretation:

```text
viable + action-divergent + low-regret
```

This is a better repair target than the M1250-M1252 near-positive rows because
both own-branch best candidates are viable. The missing piece is not viability;
it is cross-regret amplification.

## Dominant Row Patterns

Observed in M1259:

```text
global_mu_drop->brake_authority_drop:
  action divergence exists, but min two-sided regret is below threshold or
  own-branch viability fails.

global_mu_drop->front_lateral_authority_drop:
  mostly viable/action-equivalent or tiny-regret rows.

global_mu_drop->rear_lateral_authority_drop:
  viable/action-equivalent rows dominate.
```

Compared with M1255:

```text
near_boundary_viability_pairs: 1 -> 8
best_actions_diverged_pairs: 2 -> 4
```

So richer faults improve source shape, but not enough for strict source-positive
rows.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
richer_fault_source_low_regret
```

Process issue found and fixed:

```text
metric_artifact:
  asymmetric_success_drop was previously counted as accepted.
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

Do not train.

Do not run PPO.

Do not treat M1259 as source-positive.

Admit one design milestone:

```text
m1261-paper-route-richer-fault-regret-boundary-retarget-design
```

The repair variable should be:

```text
regret-boundary retargeting around viable action-divergent low-regret rows
```

This is distinct from earlier local source tweaks. Earlier relocation targeted
own-branch viability. M1261 should target two-sided cross-regret while
preserving strict own-branch viability.

Allowed retarget axes for design:

```text
obstacle body_x / timing
obstacle body_y / lateral offset
obstacle half-width
small fault severity scale around the same public proxy-fault families
source step neighbor around the same matched snapshot pair
```

Required acceptance remains:

```text
own-branch best margins >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

M1261 should be design-only. Any later run must be bounded and must report
whether it is increasing true cross-regret or merely making scenarios
collision-dominated.
