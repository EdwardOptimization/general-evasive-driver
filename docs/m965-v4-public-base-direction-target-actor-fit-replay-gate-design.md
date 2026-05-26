# M965 V4 Public Base Direction Target Actor-Fit Replay Gate Design

## Purpose

M965 designs the no-training replay/proof gate for the M964 objective-level
actor-fit candidates.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote.

M964 produced five objective-level candidates:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_05.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_1.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_2.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_5.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

All five improve direction-target fit, pass active M267/M264 preflight, and
retain proof/retention anchors. That is not enough for a driver claim. The next
step must replay closed-loop surfaces.

## Candidate Order

Primary candidate:

```text
alpha_1_0
```

Reason:

```text
best direction-target weighted MSE among evaluated alphas
M267/M264 active preflight passed
retention/proof anchors passed
only actor_mean changed
```

Backup candidates in order:

```text
alpha_0_5
alpha_0_2
alpha_0_1
alpha_0_05
```

M966 should evaluate all candidates through a cheap M267/M264 full-surface
preflight first. It should only run the full public replay stack on the highest
ranked candidate that passes the preflight.

## Baseline

Baseline remains the public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

No candidate is promoted by M966. A pass only routes to a broader
generalization/promotion design.

## Replay Gate Scope

M966 should run these public replay surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Required public behavior seeds:

```text
9505
9506
```

Required ablations for the selected candidate:

```text
normal checkpoint
reset_recurrent_state
zero_all_response
```

Behavior ordering should remain:

```text
normal success >= reset success >= zero_all success
```

Diagnostics:

```text
source-diverse protected surfaces if compatible
old key 9944 diagnostic-only, not a singleton veto
actor-input contract signature
```

## Acceptance Criteria

M966 may classify a candidate as replay-gate pass only if:

```text
actor_input_contract_changed == false
training_started == false
ppo_used == false
promoted == false
selected candidate passed M964 exact/objective reference
selected candidate passed full M267/M264 surface with success_drop_count 17 / 17
all six public replay surfaces pass
behavior seeds 9505 and 9506 do not regress materially
reset/zero-all ordering is retained
source-diverse diagnostic is pass or explicitly diagnostic-only
old key 9944 is documented diagnostic-only
```

M966 must not claim promotion. Passing replay gates should route to:

```text
promotion/generalization gate design
```

Failing replay gates should route to the relevant audit:

```text
M267/M264 failure -> proof_washout audit
other replay surface failure -> replay surface failure audit
behavior seed failure -> behavior_regression audit
contract signature mismatch -> contract_violation audit
```

## Required Artifacts For M966

M966 should write:

```text
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/summary.json
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/candidate_preflight_summary.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/public_replay_gate_summary.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/behavior_summary.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/behavior_comparison.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/route_decision.csv
```

Optional but useful:

```text
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/full_gates/
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/source_diverse_protected_diagnostic/
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/old_key_neighborhood_diagnostic/
```

Summary fields:

```text
baseline_checkpoint
primary_checkpoint
selected_candidate
candidate_preflight_pass_count
selected_candidate_preflight_pass
six_public_replay_gates_pass
public_replay_gates_passed
failed_public_replay_surfaces
behavior_pass
behavior_seed9505_success_delta
behavior_seed9506_success_delta
reset_zero_all_ordering_retained
source_diverse_protected_status
old_key_9944_status
actor_inputs_changed
training_started
replay_used
ppo_used
promoted
result_class
failure_types
next_blocker
```

## Decision

M965 routes to:

```text
m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation
```

M966 should implement the no-training replay gate. It must not train, run PPO,
change actor inputs, use private holdout, or promote.
