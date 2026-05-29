# M1685 Paper-Route Controller-Family Measured Execution Design

## Summary

M1685 designs the first measured execution route after the M1683 no-rollout
protocol passed M1684 audit.

Decision:

```text
measured_execution_design_admit_small_public_routing_smoke
```

This milestone is design-only. It does not run environment rollout, train,
replay, run PPO, use private holdout, promote, change actor inputs, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Strategy

Choose a staged route:

```text
Stage A: small public routing smoke
Stage B: audit smoke results
Stage C: full 864-cell public rollout design or protocol repair
```

Do not jump directly to the full 864-cell rollout. The protocol layer is
complete, but the executable mapping from protocol specs to simulator hook specs
and the 12-profile checkpoint plumbing still need one bounded execution smoke.

## M1686 Routing Smoke Scope

M1686 should execute a small public routing smoke only:

```text
profiles: 12 corrected controller-family profiles
profile checkpoints: M1674 one-seed public pilot checkpoints
task specs: source-diverse executable subset mapped from M1680/M1683 protocol
target executable specs: 4
target episodes: 4 specs x 12 profiles = 48 episodes
strata reported: all_routing_smoke_specs, explicit_window_subset where present, task_family_T4, task_family_T5
```

The smoke should use public/local checkpoints only for plumbing and should not
promote or rank them. It should record metrics but label interpretation as
`routing_smoke_only`.

## Required Runner Behavior

The M1686 runner should:

```text
load M1674 profile configs and checkpoints;
derive a small executable source-diverse hook subset;
wrap each env with the matching profile mask/reset behavior;
run one episode per profile/spec pair;
write per-episode rows, aggregate rows, and summary;
keep actor contract P0 human-view no-wheel/no-oracle;
not train, replay, run PPO, use private holdout, or promote.
```

Required artifacts:

```text
runs/m1686_controller_family_measured_routing_smoke/summary.json
runs/m1686_controller_family_measured_routing_smoke/episode_rows.csv
runs/m1686_controller_family_measured_routing_smoke/profile_aggregate.csv
runs/m1686_controller_family_measured_routing_smoke/spec_aggregate.csv
```

## Success Criteria

M1686 passes as routing smoke if:

```text
episode_count == 48
profile_count == 12
spec_count >= 4
all episodes complete without runner exceptions
selected metrics are finite
guardrail_violation_count == 0
training_started == false
ppo_used == false
private_holdout_used == false
promoted == false
actor_input_contract_changed == false
```

Performance metrics are diagnostic only. A high or low success rate does not
rank controller families in M1686.

## Stop Rules

Stop before full rollout if:

```text
profile checkpoints/configs are missing;
executable spec mapping cannot preserve P0 actor contract;
any profile needs profile-specific tuning;
episode metrics are non-finite;
the smoke uses private holdout or hidden/oracle actor inputs;
the runner cannot preserve L1/L2-current-tiled/L3-reset controls.
```

## Next Step

Admit exactly one measured execution smoke:

```text
m1686-paper-route-controller-family-measured-routing-smoke
```

M1686 may run bounded public environment rollout, but only for routing-smoke
plumbing. It must not train, PPO, promote, use private holdout, change actor
inputs, or make controller-family ranking/self-ID claims.

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
next: m1686-paper-route-controller-family-measured-routing-smoke
```
