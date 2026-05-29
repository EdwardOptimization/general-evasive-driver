# M1682 Paper-Route Controller-Family Bounded Task-Source Rollout Design

## Summary

M1682 designs a bounded public rollout protocol over the M1680 task-source
specs. It does not execute rollout.

Decision:

```text
bounded_task_source_rollout_design_admit_no_rollout_protocol_preflight
```

This milestone is design-only. It does not run environment rollout, train,
replay, run PPO, use private holdout, promote, change actor inputs, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Inputs

Primary spec source:

```text
runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json
```

M1680 produced:

```text
72 total specs
T4=36, T5=36
12 source families
15 source edges
4 window tags
0 hidden/action key violations
all controller profiles covered
```

## Required Strata

The first rollout protocol must keep two reporting strata:

```text
all_72_specs: 72 specs
explicit_window_subset: 33 specs
```

The same rollout executions can feed both strata by filtering metrics, so the
explicit-window subset should not duplicate rollout work. It is a diagnostic
cross-check for the M1680 caveat that `mapping_window_unspecified` covers
`39 / 72` specs.

The protocol should also report:

```text
mapping_window_unspecified: 39 specs
metadata_role strata
task_family strata: T4 and T5
source_edge strata
```

## Controller Matrix

The protocol must include the full corrected controller-family matrix:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Mandatory comparisons:

```text
L1 versus best L2/L3
L2 normal minus matched L2 current-tiled
L3 online minus L3 reset-control corrected
T4 versus T5 behavior
all_72_specs versus explicit_window_subset
```

No profile-specific tuning is allowed. Any later training or checkpoint
instantiation must use one frozen recipe across profiles and must be
pre-registered separately.

## Future Rollout Metrics

The protocol preflight should define these metric columns for later execution:

```text
success_rate
collision_rate
road_departure_rate
spin_rate
clearance_margin_mean
clearance_margin_p10
termination_reason_histogram
control_smoothness
L2_normal_minus_current_tiled_success_delta
L2_normal_minus_current_tiled_margin_delta
L3_online_minus_reset_success_delta
L3_online_minus_reset_margin_delta
```

These metrics are not computed in M1682.

## M1683 No-Rollout Preflight Contract

M1683 should write:

```text
runs/m1683_controller_family_bounded_rollout_protocol_preflight/summary.json
runs/m1683_controller_family_bounded_rollout_protocol_preflight/rollout_protocol.json
runs/m1683_controller_family_bounded_rollout_protocol_preflight/workload_matrix.csv
```

The preflight should verify:

```text
all required specs are readable
all required profiles are present
all_72_specs and explicit_window_subset strata are present
workload matrix has 72 specs x 12 profiles
explicit-window rows are identifiable
no hidden/action target keys are present
private holdout is not used
environment rollout count is 0
training count is 0
profile-specific tuning is false
```

## Stop Rules

Stop before measured execution if:

```text
the workload matrix omits any controller profile;
the explicit-window subset cannot be recovered;
hidden/action target keys appear in protocol artifacts;
the protocol requires profile-specific tuning;
private holdout is needed to debug the public protocol;
the workload cannot be represented without actor-input contract changes.
```

## Next Step

Admit exactly one no-rollout protocol preflight:

```text
m1683-paper-route-controller-family-bounded-rollout-protocol-preflight
```

M1683 should materialize the protocol and workload matrix only. It must not
execute rollout, train, replay, run PPO, use private holdout, promote, change
actor inputs, or claim controller-family ranking.

## Guardrails

```text
environment_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1683-paper-route-controller-family-bounded-rollout-protocol-preflight
```
