# M2470 Paper-Route Current-Sim Dual-Axis Stable-AES Distribution-Support Repair Design

- status: completed
- decision: `stable_aes_distribution_support_design_route_to_materialization_preflight`
- manifest: `experiments/manifests/m2470-paper-route-current-sim-dual-axis-stable-aes-distribution-support-repair-design.json`
- parent audit: `docs/m2469-paper-route-current-sim-dual-axis-scenario-distribution-support-atlas-result-audit.md`
- parent summary: `runs/m2468_paper_route_current_sim_dual_axis_scenario_distribution_support_atlas/summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO in M2470: `false`
- ranking/winner selection in M2470: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Problem

M2469 accepted M2468 as clean reset-only distribution-support evidence, but
kept measured readiness blocked because stable AES is still seed-fragile at
distribution level:

```text
stable_aes_support: 14/24 reset success
stable_aes_broad_threshold_free: 5/8 success
stable_aes_threshold_band: 3/8 success
stable_aes_low_mu_near: 6/8 success
```

Stable-AES reset failures account for `10/11` total M2468 reset failures. The
branch must not return to the three fixed M2464 R1 rows; M2470 therefore
designs a distribution-level support contract covering all three partial
stable-AES atlas cells.

## Design Principle

M2470 is design-only. It defines bounded environment-support levers for later
materialization/preflight and does not execute those levers.

Allowed support levers:

```text
track_width
soft_offtrack_metric_enabled
soft_offtrack_tolerance_m
friction_limited_speed
speed_range
randomization_bucket_id
randomization copied from an existing M2468 bucket template
obstacle.enabled
obstacle.allowed_labels
obstacle.require_aeb_infeasible
obstacle.distance_range
obstacle.lateral_offset_range
obstacle.half_width_range
obstacle.max_threshold_score
obstacle.max_sample_attempts
obstacle.perception_reveal_step
obstacle.perception_reveal_distance
obstacle.finish_on_pass
obstacle.finish_pass_distance
```

Forbidden in M2470/M2471:

```text
mu, mass, tire, brake, or actuator features in actor input
slip, tire force, controller mode, TTC, path/reference, or oracle values
changing actor observation shape or contract
using AEB/AES/drift labels as actor features
retrying failed seeds
running reset, rollout, policy action, repair execution, training, replay, PPO
ranking cells or selecting winners
claiming actual-success, paper, FW-vs-GRU, self-ID, training-repair, or current-sim verdict evidence
```

Labels such as `aes_feasible` may remain environment-sampling metadata only.
Hidden-dynamics randomization may be copied into environment configs as
simulation variation, but it must remain outside actor input.

## Source Evidence Used

M2470 uses M2468 successful reset rows only to choose bounded support ranges,
not to rank cells or select a winner.

Stable-AES successful samples observed:

```text
broad threshold-free:
  speed_ref 11.98-14.87
  obstacle_distance 16.44-31.10
  lateral_offset -0.39 to 0.60
  half_width 0.46-0.88
  threshold_score 0.0002-0.3383

threshold band:
  speed_ref 13.91-14.36
  obstacle_distance 18.99-25.33
  lateral_offset -0.37 to -0.22
  half_width 0.47-0.79
  threshold_score 0.1098-0.2702

low-mu near:
  speed_ref 9.42-11.27
  obstacle_distance 14.58-18.11
  lateral_offset -0.70 to 0.61
  half_width 0.48-0.64
  threshold_score 0.0020-0.2234
```

The support contract deliberately spans beyond those observed successes so it
does not overfit a single successful seed. It also avoids the exact M2464 R1
signature:

```text
speed_range [10.0, 14.0]
distance_range [20.0, 34.0]
lateral_offset_range [-0.40, 0.40]
half_width_range [0.55, 0.80]
max_threshold_score 0.35
```

## Stable-AES Support Contract

M2471 should materialize exactly three stable-AES support-contract families.
Each family targets one M2468 partial stable-AES cell, but the contract is
distribution-level: no single failed seed or fixed M2464 row is retried.

### R1 AES Balanced Support

Purpose:

```text
core stable-AES support with moderate geometry and bounded threshold score
```

Source atlas cell:

```text
stable_aes_broad_threshold_free
```

Overlay:

```json
{
  "track_width": 7.5,
  "speed_range": [9.5, 14.5],
  "friction_limited_speed": false,
  "soft_offtrack_metric_enabled": true,
  "soft_offtrack_tolerance_m": 0.20,
  "randomization_bucket_id": "mixed",
  "obstacle": {
    "enabled": true,
    "distance_range": [18.0, 36.0],
    "lateral_offset_range": [-0.55, 0.55],
    "half_width_range": [0.50, 0.85],
    "allowed_labels": ["aes_feasible"],
    "require_aeb_infeasible": true,
    "max_threshold_score": 0.45,
    "max_sample_attempts": 20000,
    "perception_reveal_step": 0,
    "perception_reveal_distance": 60.0,
    "finish_on_pass": true,
    "finish_pass_distance": 1.0
  }
}
```

Rationale:

```text
This keeps stable-AES timing and geometry broad enough for distribution support
while avoiding the exact fixed M2464 R1 overlay. The threshold bound is above
the successful M2468 threshold scores but below the weakest threshold-band
filter, keeping the support target stable-AES rather than drift-required.
```

### R1 AES Threshold-Band Relief

Purpose:

```text
recover the weakest threshold-band support cell without selecting it as a winner
```

Source atlas cell:

```text
stable_aes_threshold_band
```

Overlay:

```json
{
  "track_width": 7.5,
  "speed_range": [10.0, 14.75],
  "friction_limited_speed": false,
  "soft_offtrack_metric_enabled": true,
  "soft_offtrack_tolerance_m": 0.20,
  "randomization_bucket_id": "mixed",
  "obstacle": {
    "enabled": true,
    "distance_range": [18.0, 38.0],
    "lateral_offset_range": [-0.55, 0.55],
    "half_width_range": [0.48, 0.82],
    "allowed_labels": ["aes_feasible"],
    "require_aeb_infeasible": true,
    "max_threshold_score": 0.45,
    "max_sample_attempts": 30000,
    "perception_reveal_step": 0,
    "perception_reveal_distance": 60.0,
    "finish_on_pass": true,
    "finish_pass_distance": 1.0
  }
}
```

Rationale:

```text
M2468 threshold-band successes had threshold_score <= 0.2703. A 0.45 cap keeps
the cell inside a stable-AES support band while widening sample attempts and
the geometry envelope. The design is still a support-materialization target,
not a measured controller-performance claim.
```

### R1 AES Low-Mu Reaction Support

Purpose:

```text
increase low-mu stable-AES reset support while preserving low-mu variation
```

Source atlas cell:

```text
stable_aes_low_mu_near
```

Overlay:

```json
{
  "track_width": 7.5,
  "speed_range": [8.0, 12.0],
  "friction_limited_speed": false,
  "soft_offtrack_metric_enabled": true,
  "soft_offtrack_tolerance_m": 0.20,
  "randomization_bucket_id": "low_mu",
  "obstacle": {
    "enabled": true,
    "distance_range": [16.0, 34.0],
    "lateral_offset_range": [-0.65, 0.65],
    "half_width_range": [0.45, 0.75],
    "allowed_labels": ["aes_feasible"],
    "require_aeb_infeasible": true,
    "max_threshold_score": 0.45,
    "max_sample_attempts": 30000,
    "perception_reveal_step": 0,
    "perception_reveal_distance": 60.0,
    "finish_on_pass": true,
    "finish_pass_distance": 1.0
  }
}
```

Rationale:

```text
This preserves the low-mu bucket rather than hiding the difficult dynamics. It
adds reaction distance over the M2468 low-mu near cell while keeping speeds and
obstacle widths in the stable-AES range.
```

## Guardrail Treatment

M2471 must preserve these non-target groups as guardrails:

```text
stable_feasibility_support:
  M2468 full support at 24/24 must remain an admission/monitoring guardrail.

handling_limit_guardrail:
  M2468 was 23/24; drift_required_nominal at 7/8 remains a monitor, not the
  primary repair target.

hidden_dynamics_guardrail:
  M2468 full support at 24/24 must not be weakened or converted into an actor
  hidden-feature dependency.

mitigation_guardrail:
  M2468 full support at 24/24 must remain out of stable-AES repair execution.
```

M2471 guardrails must fail if any support row:

```text
matches the exact M2464 R1 signature
omits one of the three stable-AES partial cells
uses labels or hidden dynamics as actor input
changes the P0 human-view actor contract
executes reset, rollout, policy action, repair, replay, PPO, or training
ranks rows or selects a winner
makes verdict or actual-success claims
```

## M2471 Materialization/Preflight Contract

M2471 should implement and run a materialization/preflight step that writes:

```text
runs/m2471_paper_route_current_sim_dual_axis_stable_aes_distribution_support_materialization_preflight/summary.json
runs/m2471_paper_route_current_sim_dual_axis_stable_aes_distribution_support_materialization_preflight/support_contract_rows.csv
runs/m2471_paper_route_current_sim_dual_axis_stable_aes_distribution_support_materialization_preflight/stable_aes_overlay_rows.csv
runs/m2471_paper_route_current_sim_dual_axis_stable_aes_distribution_support_materialization_preflight/guardrail_rows.csv
runs/m2471_paper_route_current_sim_dual_axis_stable_aes_distribution_support_materialization_preflight/claim_boundary.csv
runs/m2471_paper_route_current_sim_dual_axis_stable_aes_distribution_support_materialization_preflight/decision_rows.csv
```

Required `support_contract_rows.csv` fields:

```text
contract_id
source_atlas_cell_id
candidate_group
role_family
parameter_bin
randomization_bucket_id
support_lever_class
expected_materialized_overlay_count
no_fixed_m2464_r1_reuse
labels_metadata_only
actor_input_contract_changed
scenario_redesign_executed
policy_action_executed
repair_execution_started
training_started
ranking_admissible
winner_selected
```

Required `stable_aes_overlay_rows.csv` fields:

```text
overlay_id
contract_id
source_atlas_cell_id
candidate_group
role_family
parameter_bin
env_config_overlay_json
allowed_overlay_keys
labels_metadata_only
hidden_dynamics_metadata_only
matches_fixed_m2464_r1_signature
actor_input_contract_changed
environment_reset_started
policy_action_executed
repair_execution_started
training_started
ranking_admissible
winner_selected
```

Pass criteria:

```text
result_class == stable_aes_distribution_support_materialization_preflight_pass
support_contract_row_count == 3
stable_aes_overlay_row_count == 3
stable_aes_partial_cell_coverage_count == 3
fixed_m2464_r1_reuse_count == 0
labels_enter_actor_input_count == 0
actor_input_contract_changed_count == 0
environment_reset_started == false
policy_action_executed == false
repair_execution_started == false
training_started == false
ranking_admissible_count == 0
winner_selected_count == 0
guardrail_violation_count == 0
```

## Decision

Accepted next route:

```text
m2471-paper-route-current-sim-dual-axis-stable-aes-distribution-support-materialization-preflight
```

M2471 should materialize this design into static support-contract and overlay
artifacts. It must not reset the environment or execute repair. A later audit
must decide whether materialized support rows admit reset-readiness validation,
branch synthesis, or stop.
