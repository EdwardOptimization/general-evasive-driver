# M1269 Paper-Route Four-Wheel Fault Source-Shape Result Audit

## Summary

M1269 audits the M1268 no-policy four-wheel fault source-shape smoke.

Decision:

```text
four_wheel_source_shape_audit_admit_viability_calibration_design
```

M1268 is infrastructure-valid and source-negative:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
source_positive: false
```

But it changes the source blocker:

```text
old blocker: action-divergent but low-regret
new blocker: high-regret but own-branch nonviable / collision dominated
```

Therefore the next variable should target own-branch viability, not regret.

## Evidence

Primary artifacts:

```text
runs/m1268_four_wheel_fault_source_shape_smoke/summary.json
runs/m1268_four_wheel_fault_source_shape_smoke/matched_capability_pairs.csv
runs/m1268_four_wheel_fault_source_shape_smoke/action_rollouts.csv
```

Summary:

```text
sequence_length: 72
matched_pair_count: 108
action_rollouts: 2376
accepted_separable_pairs: 0
best_actions_diverged_pairs: 27
low_regret_pairs: 92
own_branch_viability_fail_count: 103
all_four_rollouts_collision_count: 103
unique_fault_family_pairs: 4
```

Terminal distribution:

```text
collision: 2360
obstacle_completed: 16
safe_stop: 0
```

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Metric Artifact Correction

M1268 initially found two accepted rows, but both were horizon-only rows:

```text
terminal_reason: horizon
obstacle not completed
vehicle had not safely stopped
```

This was correctly rejected as a metric artifact.

Final success semantics:

```text
success = no collision and (obstacle_completed or safe_stop)
```

After rerun:

```text
accepted_separable_pairs: 0
```

This correction should be preserved in later four-wheel source code.

## Positive Signal

The new four-wheel source is not equivalent to the old single-track source. It
creates much stronger outcome regret.

Example:

```text
pair_id: 28
fault_family_pair: left_right_split_mu->left_right_split_mu
best_action_l2: 1.5000001192
cross_regret_A: 0.1793146044
cross_regret_B: 0.1793146044
margin_A_best_A: -0.5693411345
margin_B_best_B: -0.5693411345
rejection_reason: best_candidate_not_viable
```

Compared with M1262:

```text
M1262 max min_cross_regret: 0.0043813964
M1268 top min_cross_regret: 0.1793146044
```

So the fidelity-source branch is directionally useful. The missing piece is
finding states/action sequences where each branch has a viable own action.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
four_wheel_source_collision_dominated
```

Process issue fixed:

```text
metric_artifact:
  horizon-only success was rejected and corrected.
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

Do not promote.

Do not lower thresholds.

Do not claim source-positive evidence.

Admit one design milestone:

```text
m1270-paper-route-four-wheel-source-viability-calibration-design
```

M1270 should design a bounded viability calibration branch over:

```text
obstacle distance / half-width / lateral offset
speed range
sequence horizon
candidate action amplitudes
brake actuator established versus partial
safe-stop versus pass-around success modes
```

The goal is to preserve the new high-regret signal while restoring own-branch
viability under unchanged strict source acceptance.
