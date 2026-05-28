# M1279 Paper-Route Four-Wheel Source Response-History Materialization Design

## Summary

M1279 designs branch-specific command-response history artifacts for the M1277
source interventions.

Decision:

```text
four_wheel_source_response_history_materialization_design_admit_implementation
```

Admit next bounded no-training implementation:

```text
m1280-paper-route-four-wheel-source-response-history-materialization
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, accepted-threshold relaxation, high-fidelity validation
claim, paper-level claim, driver-performance claim, or self-identification claim
occurs in M1279.

## Why This Is Needed

M1277 materialized preferred/rejected intervention rows, but M1278 showed that
direct policy training is blocked:

```text
same current human-view observation
hidden branch A prefers action A
hidden branch B prefers action B
```

Without branch-specific response history, the actor cannot know which action is
preferred. Feeding branch/fault labels would violate the human-view contract.

Therefore the next artifact must provide:

```text
past command-response evidence
```

that can later be used by a recurrent policy or history encoder.

## Design Principle

Separate three concepts:

```text
source intervention:
  current source observation + preferred/rejected action/outcome relation

response history:
  branch-specific past command-response frames generated under fixed probe
  commands

history intervention:
  pairing a current source intervention with either the matching branch history
  or the wrong branch history
```

The current source observation remains branch-ambiguous. The history artifact is
what carries branch-specific evidence.

## Scope

M1280 should materialize response histories for the M1277 primary subset:

```text
source_subset: near_high_union
source pairs: 38
branch-conditioned interventions: 76
```

Use two fixed probe prefixes:

```text
left_brake_probe:
  24 steps at dt=0.02
  steer command +0.25
  throttle -1.0
  brake +1.0

right_brake_probe:
  24 steps at dt=0.02
  steer command -0.25
  throttle -1.0
  brake +1.0
```

Rationale:

```text
split-mu, brake-pull, and grip-collapse faults should produce branch-specific
yaw/lateral response under mild steering plus established brake.
```

This prefix is an artifact-level response-history probe, not a closed-loop
driver policy and not a physical continuity claim with the later source
snapshot.

## Expected Counts

For the primary subset:

```text
source pairs: 38
conditions per pair: 2
probe templates: 2
history length: 24
```

Expected artifacts:

```text
history_prefix_rows: 38 * 2 * 2 = 152
history_frame_rows: 152 * 24 = 3648
history_intervention_rows: 76 * 2 = 152
wrong_history_pair_rows: 76 * 2 = 152
```

Each intervention has:

```text
correct history: same pair, same condition, same probe template
wrong history: same pair, opposite condition, same probe template
```

## History Frame Schema

`history_frame_rows.csv` should contain:

```text
history_id
pair_id
condition
probe_template
step
cmd_steer
cmd_throttle
cmd_brake
vx
vy
yaw_rate
ax
ay
steer_state
steer_rate
drive_state
brake_state
prev_cmd_steer
prev_cmd_throttle
prev_cmd_brake
```

These are deployable response/history fields. They do not include fault labels,
per-wheel forces, per-wheel scales, branch labels in actor-view tensors, success
labels, or preferred/rejected labels.

Branch/fault metadata may exist in separate source metadata columns, but not in
actor-view history tensors.

## History Prefix Schema

`history_prefix_rows.csv` should contain one row per history:

```text
history_id
pair_id
condition
fault_name
fault_family
probe_template
history_length
dt
final_vx
final_vy
final_yaw_rate
final_yaw_delta_from_start
response_l2_from_opposite_branch
```

`condition`, `fault_name`, and `fault_family` are source metadata only.

## History-Intervention Schema

`history_intervention_rows.csv` should link histories to M1277 interventions:

```text
history_intervention_id
intervention_id
pair_id
condition
probe_template
correct_history_id
preferred_candidate_id
rejected_candidate_id
preferred_margin
rejected_margin
margin_gap
```

`wrong_history_pair_rows.csv` should define the counterfactual swap:

```text
history_intervention_id
intervention_id
pair_id
condition
probe_template
correct_history_id
wrong_history_id
wrong_condition
preferred_candidate_id
rejected_candidate_id
margin_gap
```

This gives later policy-side gates a clean way to test:

```text
same current intervention observation;
same preferred/rejected action relation;
correct branch history versus wrong branch history.
```

## Distinguishability Diagnostics

M1280 should report simple no-training diagnostics:

```text
mean response_l2_from_opposite_branch
min response_l2_from_opposite_branch
history pairs with response_l2 >= 0.01
history pairs with yaw_rate final difference >= 0.01
history pairs with vy final difference >= 0.01
```

These do not prove self-identification. They only check whether the history
artifact carries a measurable branch response signal.

## Guardrails

M1280 must not:

```text
train;
run PPO;
promote;
use private holdout;
add branch/fault labels to actor-view history tensors;
use per-wheel force/scale/slip as actor-view history;
claim self-identification;
claim driver performance;
claim high-fidelity validation.
```

The actor-view history columns are command-response fields only.

## Acceptance Criteria

M1280 passes if:

```text
summary.json exists;
history_prefix_rows == 152;
history_frame_rows == 3648;
history_intervention_rows == 152;
wrong_history_pair_rows == 152;
history_frame actor-view columns are finite;
wrong_history rows always swap to the opposite condition within the same pair;
response_l2 diagnostics are reported;
guardrails report false for training/PPO/promotion/private holdout/input change.
```

If response distinguishability is weak, route to audit and prefix repair rather
than actor training.

## Next Step

Pre-register and run:

```text
experiments/manifests/m1280-paper-route-four-wheel-source-response-history-materialization.json
```
