# M1204 Paper-Route Profile Control Repair Smoke Run

## Summary

M1204 runs the no-training smoke for corrected profile controls.

Decision:

```text
profile_control_repair_smoke_pass_route_to_corrected_pilot_design
```

Artifacts:

```text
runs/m1204_profile_control_repair_smoke/summary.json
runs/m1204_profile_control_repair_smoke/m1204_l2_window_25_current_tiled_smoke.json
```

## Smoke Result

```text
result_class: profile_control_repair_smoke_pass
all_smoke_checks_passed: true
single_env_reset_tiled: true
single_env_step_tiled: true
raw_step_was_not_tiled: true
vector_env_reset_tiled: true
vector_env_step_tiled: true
reset_policy_honored: true
l3_reset_runtime_policy: every_step_control
```

Guardrails:

```text
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
```

## Interpretation

The corrected diagnostic controls are ready for a small corrected public pilot
design:

```text
current-tiled L2 control works in single env reset/step;
current-tiled L2 control works in sync vector env reset/step;
raw L2 observations remain non-tiled before wrapping;
every-step reset policy is honored by the evaluation policy.
```

This is infrastructure evidence only. It is not a performance comparison and
does not support history-necessity or self-identification claims.

## Next Milestone

```text
experiments/manifests/m1205-paper-route-finite-window-gru-evidence-synthesis.json
```

The branch cadence has fired. M1205 must synthesize the M1195-M1204 evidence
before any corrected public pilot design. If synthesis continues the branch,
the following corrected pilot should be designed afterward:

```text
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```
