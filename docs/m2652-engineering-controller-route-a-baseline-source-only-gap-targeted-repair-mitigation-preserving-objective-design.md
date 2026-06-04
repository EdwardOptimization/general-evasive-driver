# M2652 Engineering Controller Route A Source-Only Gap-Targeted Repair Mitigation-Preserving Objective Design

- status: completed
- decision: `route_to_mitigation_preserving_objective_materialization_preflight`
- manifest: `experiments/manifests/m2652-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-design.json`
- parent synthesis: `docs/m2651-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-synthesis.md`
- parent localization summary: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/summary.json`
- parent localization findings: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/localization_findings.json`
- parent regression rows: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/mitigation_regression_rows.csv`
- follow-up manifest: `experiments/manifests/m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-preflight.json`
- next: `m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-preflight`

## Purpose

M2652 designs a bounded mitigation-preserving objective and gate matrix before
any second Route A source-only repair execution. It exists because M2648
improved admitted target gates but M2650 localized one real protected
mitigation regression.

This is design-only. It does not execute repair, training, reset, step,
rollout, replay, validation, PPO, source build, adapter probe, high-fidelity
simulation, ranking, winner selection, promotion, success-rate computation, or
driver-performance evaluation.

## Accepted Evidence

M2652 accepts these current Route A facts:

```text
Route A purpose:
  freeze a usable actuator-level active-safety controller baseline

M2648 target_road_boundary_margin_control:
  evaluated rows: 16
  improved rows: 16
  regressed rows: 0
  gate_pass: true

M2648 target_drift_collision_recovery_tradeoff:
  evaluated rows: 8
  improved rows: 8
  regressed rows: 0
  gate_pass: true

M2648 protected_mitigation_reference:
  evaluated rows: 8
  improved rows: 7
  regressed rows: 1
  gate_pass: false
  failure_type: behavior_regression

M2650 localization:
  matched protected mitigation pairs: 8
  regressed rows: 1
  metric_artifact_detected: false
  localized class: real_behavior_regression_likely_obstacle_penetration_deepened
```

The single localized protected mitigation regression is:

```text
subject: m2537_mitigation_preserving_policy
role: unavoidable_mitigation
seed: 267101
dynamics_axis_id: fresh_fault_delay_noise
severity_proxy: 3.953864 -> 3.987916
severity_delta: +0.034052
minimum_obstacle_clearance_m: -1.436872 -> -1.477159
obstacle_penetration_proxy_m: 1.436872 -> 1.477159
collision_speed_proxy: 3.359023 -> 3.322625
impact_angle_proxy: 0.452959 -> 0.443488
minimum_road_margin_m: 0.899620 -> 0.949128
```

This evidence says the next repair objective must not be target-only. It must
keep the target gains while explicitly protecting mitigation severity and
obstacle penetration.

## Objective Families

M2652 admits three objective families for materialization:

```text
road_boundary_margin_target:
  source gap family: road_departure_dominant_gap
  source roles: stable_avoidable, stable_aes
  objective role: target
  desired direction:
    increase minimum_road_margin_m
    reduce road_departure_event
    preserve minimum_obstacle_clearance_m
    preserve command_delta_l1_mean

drift_collision_recovery_target:
  source gap family: drift_recovery_mixed_gap
  source role: drift_required_recovery
  objective role: target
  desired direction:
    improve drift_tradeoff_proxy
    preserve minimum_obstacle_clearance_m
    preserve minimum_road_margin_m
    reduce final_abs_lateral_velocity
    reduce final_abs_yaw_rate
    preserve command_delta_l1_mean

mitigation_non_regression_protected:
  source family: mitigation_collision_saturated_reference
  source role: unavoidable_mitigation
  objective role: protected_reference
  desired direction:
    no increase in severity_proxy
    no increase in obstacle_penetration_proxy_m
    no decrease in minimum_obstacle_clearance_m on collision rows
    no new collision_event transition from false to true
    no road_margin sacrifice used to hide deeper obstacle penetration
```

The protected mitigation family is not a normal success denominator. It is a
blocking non-regression gate for any later repair execution.

## Protected Components

M2652 defines these protected components for the mitigation reference:

```text
severity_proxy_non_regression:
  baseline source: M2641 repaired subject row
  post-repair source: future repair candidate row
  pass condition: post severity_proxy <= baseline severity_proxy + tolerance
  default tolerance: 0.0
  blocks promotion/performance claims: true

obstacle_penetration_non_regression:
  baseline source: max(0, -minimum_obstacle_clearance_m)
  post-repair source: max(0, -minimum_obstacle_clearance_m)
  pass condition: post obstacle_penetration_proxy_m <= baseline obstacle_penetration_proxy_m + tolerance
  default tolerance: 0.0
  blocks promotion/performance claims: true

minimum_obstacle_clearance_preservation:
  baseline source: minimum_obstacle_clearance_m
  post-repair source: minimum_obstacle_clearance_m
  pass condition: post minimum_obstacle_clearance_m >= baseline minimum_obstacle_clearance_m - tolerance
  default tolerance: 0.0
  blocks promotion/performance claims: true

event_transition_guard:
  pass condition:
    no collision_event false -> true transition
    no road_departure_event false -> true transition
  blocks promotion/performance claims: true
```

M2650 shows collision speed and impact angle improved on the failing row while
obstacle penetration deepened. Therefore collision speed or impact angle
improvement cannot by itself pass the protected mitigation gate.

## Target Preservation Gates

A future repair execution candidate must retain the two M2648 target gains:

```text
target_road_boundary_margin_control:
  source role families: stable_avoidable, stable_aes
  evaluated repaired-subject rows: 16
  pass condition: no regression against M2641 baseline and at least one target improvement
  preferred stronger condition: preserve M2648 16/16 no-regression result

target_drift_collision_recovery_tradeoff:
  source role family: drift_required_recovery
  evaluated repaired-subject rows: 8
  pass condition: no regression against M2641 baseline and at least one target improvement
  preferred stronger condition: preserve M2648 8/8 no-regression result
```

These are target gates, not promotion gates. They remain insufficient without
the protected mitigation gates.

## Abort Rules

Any later repair execution should abort or route to artifact repair if:

```text
protected_mitigation_reference has any regressed row
obstacle_penetration_proxy_m increases on any unavoidable_mitigation protected row
severity_proxy increases on any unavoidable_mitigation protected row
taxonomy labels or repair-target labels become actor-visible
actor observation shape changes from 72
action shape changes from 3
hidden/oracle actor inputs are required
ranking winner success-rate validation or promotion fields are emitted
source-only axis rows are interpreted as robust delay/noise validation
```

If the future executor cannot represent protected component gates, the route is
implementation repair or artifact repair, not target-only repair execution.

## Actor Boundary

The objective design preserves the P0 contract:

```text
observation_shape: 72
action_shape: 3
actor_input_leak_flags: none
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
route_decisions_actor_visible: false
source_only_outcomes_actor_visible: false
hidden_oracle_actor_inputs_allowed: false
```

Objective metadata, protected component labels, gate outcomes, scenario roles,
repair families, and source-only localization outcomes are artifact metadata
only. They must not be appended to actor observations or used as a policy-side
mode switch.

## Materialization Contract

M2653 should materialize a deterministic objective artifact bundle, not run a
repair. The expected artifact rows are:

```text
objective_family_rows:
  road_boundary_margin_target
  drift_collision_recovery_target
  mitigation_non_regression_protected

protected_component_gate_rows:
  severity_proxy_non_regression
  obstacle_penetration_non_regression
  minimum_obstacle_clearance_preservation
  event_transition_guard

target_preservation_gate_rows:
  target_road_boundary_margin_control
  target_drift_collision_recovery_tradeoff

abort_rule_rows:
  one row per abort rule above

actor_contract_guard_rows:
  P0 72/3 contract and no-oracle actor-visible checks

claim_boundary_rows:
  no repair execution, training, ranking, validation, promotion, performance,
  paper, finite-window-vs-GRU, current-sim, high-fidelity, or self-ID claim

gate_matrix:
  source artifacts, objective completeness, protected components, target
  preservation, actor contract, forbidden execution, and follow-up routing
```

Required M2653 outputs:

```text
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/summary.json
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/objective_family_rows.csv
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/protected_component_gate_rows.csv
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/target_preservation_gate_rows.csv
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/abort_rule_rows.csv
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/actor_contract_guard_rows.csv
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/claim_boundary_rows.csv
runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/gate_matrix.csv
docs/m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-preflight.md
```

## Decision

Route to M2653 mitigation-preserving objective materialization preflight.

M2653 should produce the objective/gate artifact bundle and then route to one
of:

```text
implementation repair if the repair executor must be extended for protected gates
bounded repair execution preflight if the artifact bundle is complete
artifact repair if source rows or gate definitions are inconsistent
synthesis or stop if the branch is becoming target-gate local search
```

## Rejected Claims

M2652 rejects these claims:

```text
M2652 executes a repair or changes policy behavior.
M2652 proves driver performance.
M2652 permits promotion of M2648 or any later checkpoint.
M2652 ranks controller families, selects a winner, or computes success rate.
M2652 is validation or high-fidelity validation readiness.
M2652 is paper-level finite-window-vs-GRU or self-ID evidence.
M2652 treats protected mitigation rows as ordinary success denominators.
```
