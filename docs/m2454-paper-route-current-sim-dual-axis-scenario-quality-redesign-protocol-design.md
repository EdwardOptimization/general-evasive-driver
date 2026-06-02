# M2454 Paper-Route Current-Sim Dual-Axis Scenario-Quality Redesign Protocol Design

- status: completed
- decision: `scenario_quality_redesign_protocol_route_to_materialization_preflight`
- manifest: `experiments/manifests/m2454-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-design.json`
- parent audit: `docs/m2453-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel-result-audit.md`
- audited panel: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/summary.json`
- new rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Problem

M2453 accepted M2452 and blocked direct repair/training because ordinary stable
cases are still road-boundary dominated:

```text
R0_stable_avoidable / aeb_feasible:
  actual_success_rate: 0.06111111111111111
  hard_offtrack_rate: 0.9333333333333333
  collision_rate: 0.0

R1_aeb_infeasible_stable_aes / aes_feasible:
  actual_success_rate: 0.3288888888888889
  hard_offtrack_rate: 0.66
  collision_rate: 0.011111111111111112
```

This means the next route should repair task/scenario quality before any driver
repair, training, controller comparison, self-ID claim, or current-sim verdict.

## Design Principle

The protocol must make the stable and AES tasks interpretable without deleting
the hard cases the project needs later.

Allowed design levers:

```text
scenario geometry:
  define role-specific obstacle distance, lateral offset, half-width, road
  containment, and post-obstacle recovery corridor bands.

boundary semantics:
  keep actual success as obstacle pass plus collision-free road containment;
  keep soft-boundary tolerance diagnostic unless fresh execution proves
  completion under the selected metric.

source selection:
  split scenario candidates into stable-feasibility, AES-feasibility,
  handling-limit guardrail, hidden-dynamics guardrail, and mitigation guardrail
  groups.

preflight:
  require reset/static validation before measured rollout;
  require no policy action and no training in the first materialization step.
```

Forbidden design levers:

```text
actor input changes;
hidden/oracle actor features;
controller-specific scenario filters;
profile-specific tuning;
rankings or winner selection;
turning off road-boundary failure;
counting old diagnostic soft success as actual success;
erasing drift-required or unavoidable roles to make stable rows look better;
executing scenario redesign before materialization/preflight.
```

## Role-Specific Protocol

### R0 Stable Avoidable / AEB-Feasible

Purpose:

```text
basic road-contained obstacle avoidance support
```

Admission rule:

```text
collision feasibility: obstacle can be cleared without impact under a stable
avoidance maneuver;
road feasibility: road/recovery corridor allows a stable avoidance path without
hard offtrack;
timing feasibility: obstacle reveal and initial speed leave enough steering or
braking time for a non-handling-limit response;
diagnostic target: reduce hard_offtrack saturation without reducing collision
safety.
```

M2455 should materialize R0 candidates with explicit geometry metadata and
guardrails. It must not label a candidate as success-ready from metadata alone.

### R1 AEB-Infeasible Stable AES

Purpose:

```text
AEB cannot stop in time, but stable steering avoidance should be feasible.
```

Admission rule:

```text
AEB infeasible metadata may exist for task construction, but it must not enter
actor input;
stable road-contained avoidance should be geometrically plausible;
collision risk must remain a guardrail;
hard offtrack should not be saturated by centerline or recovery-corridor design.
```

### R2/R3/R5 Handling-Limit And Hidden-Dynamics Roles

Purpose:

```text
preserve drift-required, recovery-after-limit, and hidden-dynamics stress cases.
```

Admission rule:

```text
do not use these rows to tune stable task quality;
keep them as guardrail and later repair-plan candidates;
preserve low_mu, weak_brake, slow_steer_actuator, tire_stiffness_shift, and
other hidden-dynamics stress metadata as evaluation/training diagnostics only;
do not add hidden dynamics to actor input.
```

### R4 Unavoidable Mitigation

Purpose:

```text
separate mitigation from success ranking.
```

Admission rule:

```text
unavoidable rows must not be used as offtrack repair success targets;
metrics should focus on collision mitigation, impact speed, delta-v, yaw/risk,
and post-event road containment;
collision guardrails must stay explicit when stable/AES geometry changes.
```

## Candidate Groups For Materialization

M2455 should produce deterministic candidate specs, not measured rollouts:

```text
stable_feasibility_support:
  R0/aeb_feasible rows with bounded geometry and recovery-corridor support.

stable_aes_support:
  R1/aes_feasible rows with AEB-infeasible metadata and stable road-contained
  avoidance support.

handling_limit_guardrail:
  R2/R3/R5 and drift_required rows preserved from M2452 as guardrails and later
  repair-plan candidates.

hidden_dynamics_guardrail:
  low_mu, weak_brake, slow_steer_actuator, tire_stiffness_shift, nominal_neighbor
  and related stress buckets preserved as metadata-only conditions.

mitigation_guardrail:
  R4/unavoidable rows isolated from success ranking and tracked with collision
  mitigation metrics.
```

Initial materialization should use public-debug/public-gate splits only. No
private holdout is admitted until the scenario-quality protocol has reset and
measured evidence.

## M2455 Output Contract

M2455 should write:

```text
summary.json
candidate_rows.csv
role_protocol_rows.csv
geometry_lever_rows.csv
guardrail_rows.csv
claim_boundary.csv
decision_rows.csv
```

Required candidate fields:

```text
candidate_id
candidate_group
source_panel_class
source_panel_scope
role_family
sampled_obstacle_label
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
geometry_lever_class
boundary_protocol_class
split
labels_enter_actor_input=false
actor_input_contract_changed=false
scenario_redesign_executed=false
policy_action_executed=false
ranking_admissible=false
winner_selected=false
```

Required guardrail fields:

```text
guardrail_id
guardrail_class
source_role_or_axis
failure_mode_to_preserve
metric_to_watch
violation
reason
```

## M2455 Pass Gates

M2455 may pass only if:

```text
candidate_rows.csv exists;
stable_feasibility_support_count > 0;
stable_aes_support_count > 0;
handling_limit_guardrail_count > 0;
hidden_dynamics_guardrail_count > 0;
mitigation_guardrail_count > 0;
labels_enter_actor_input_count == 0;
actor_input_contract_changed == false;
scenario_redesign_executed == false;
policy_action_executed == false;
repair_execution_started == false;
training_started == false;
ranking_admissible_count == 0;
winner_selected_count == 0;
guardrail_violation_count == 0;
```

If M2455 cannot produce nonempty stable and AES support groups while preserving
handling-limit and mitigation guardrails, it should fail closed and route to
branch synthesis or stop.

## Claim Boundary

M2454 supports only:

```text
a bounded scenario-quality redesign protocol is defined.
```

It does not support:

```text
scenario redesign was executed;
driver performance improved;
actual success improved;
repair or training is ready;
controller/profile/pack/checkpoint ranking;
candidate-family ranking;
winner selection;
paper-level result;
finite-window-vs-GRU result;
level3 self-identification;
current-sim verdict.
```

## Next Route

Next milestone:

```text
m2455-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-materialization-preflight
```

M2455 should materialize the protocol artifacts and static/reset-preflight
checks if needed. It must not execute measured rollout, scenario redesign,
repair, training, ranking, winner selection, or verdict claims.
