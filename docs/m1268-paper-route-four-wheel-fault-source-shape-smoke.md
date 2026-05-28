# M1268 Paper-Route Four-Wheel Fault Source-Shape Smoke

## Summary

M1268 implements and runs the no-policy four-wheel fault source-shape smoke
admitted by M1267.

Decision:

```text
four_wheel_fault_source_shape_smoke_infrastructure_pass_source_negative_route_to_result_audit
```

Infrastructure passes:

```text
scenario_count: 27
fault_pair_count: 4
matched_pair_count: 108
action_lattice_rows: 11
action_rollouts: 2376
```

Strict source result remains negative:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
source_positive: false
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, self-ID claim, or
paper-level claim occurred.

## Implementation

Added:

```text
src/autodrift/four_wheel_fault_source_shape.py
tests/test_four_wheel_fault_source_shape.py
```

The runner:

1. Builds matched-current source scenarios with the same visible state and
   obstacle geometry.
2. Varies only simulator-internal four-wheel fault scales.
3. Maps each source state to a 72-value human-view-compatible observation.
4. Rolls out short open-loop steer/throttle/brake sequences.
5. Reuses strict `evaluate_action_separability`.
6. Writes source-shape artifacts and guardrail flags.

## Important Correction

An initial M1268 smoke produced `accepted_separable_pairs=2`, but audit showed
both rows ended with:

```text
terminal_reason: horizon
obstacle not yet passed
margin dominated by remaining longitudinal gap
```

That was a metric artifact, not source-positive evidence.

Fix:

```text
success = no collision and (obstacle_completed or safe_stop)
```

and the default sequence horizon was increased:

```text
sequence_length: 24 -> 72
```

After this correction, the run was rerun and the final strict result is:

```text
accepted_separable_pairs: 0
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape \
  --run-dir runs/m1268_four_wheel_fault_source_shape_smoke
```

## Evidence

Primary artifact:

```text
runs/m1268_four_wheel_fault_source_shape_smoke/summary.json
```

Summary:

```text
sequence_length: 72
dt: 0.02
scenario_count: 27
fault_count: 8
fault_pair_count: 4
matched_pair_count: 108
action_lattice_rows: 11
action_rollouts: 2376
accepted_separable_pairs: 0
rejected_pairs: 108
best_actions_diverged_pairs: 27
low_regret_pairs: 92
own_branch_viability_fail_count: 103
all_four_rollouts_collision_count: 103
unique_fault_family_pairs: 4
accepted_fault_family_pairs: 0
result_class: action_divergent_low_regret
```

Guardrails:

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

Validation:

```bash
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_four_wheel_fault_source_shape.py \
  tests/test_four_wheel_dynamics.py
```

Result:

```text
9 passed in 0.90s
```

## Negative Shape

Most rollouts collide:

```text
terminal_reason collision: 2360
terminal_reason obstacle_completed: 16
safe_stop: 0
```

Most matched pairs fail own-branch viability:

```text
own_branch_viability_fail_count: 103 / 108
all_four_rollouts_collision_count: 103 / 108
```

The strongest regret rows show that the four-wheel faults do create branch
differences, but the candidate actions do not keep their own branches viable:

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

Pattern:

```text
four-wheel faults create stronger outcome-regret signal than M1259/M1262,
but the first no-policy scenario/action set is too collision-dominated.
```

## Comparison

Previous branch:

```text
M1259 accepted_separable_pairs: 0
M1262 accepted_separable_pairs: 0
M1262 max min_cross_regret: 0.0043813964
```

M1268:

```text
accepted_separable_pairs: 0
top min_cross_regret: 0.1793146044
```

This is a meaningful source-shape change. The blocker moved from low-regret to
own-branch viability.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
four_wheel_source_collision_dominated
```

Process issue found and fixed:

```text
metric_artifact:
  horizon-only rows were initially counted as success.
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

M1268 passes as infrastructure but is not source-positive evidence.

Do not train.

Do not run PPO.

Do not promote.

Do not lower thresholds.

Next:

```text
m1269-paper-route-four-wheel-fault-source-shape-result-audit
```

The audit should decide whether the next variable is:

```text
viability calibration,
longer/different candidate sequences,
obstacle geometry retargeting,
fault timing / actuator-state sampling,
or model-source synthesis.
```
