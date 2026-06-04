# M2646 Engineering Controller Route A Source-Only Gap-Targeted Repair Design

- status: completed
- decision: `route_to_source_only_gap_targeted_repair_branch_synthesis_before_materialization`
- manifest: `experiments/manifests/m2646-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-design.json`
- parent audit: `docs/m2645-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-result-audit.md`
- parent summary: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/summary.json`
- parent repair-target map: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/repair_target_admission_rows.csv`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2647-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-branch-synthesis.json`
- next: `m2647-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-branch-synthesis`

## Purpose

M2645 accepted M2644 only as source-only behavior-gap taxonomy evidence for
repair-design planning. M2646 converts that accepted taxonomy into a bounded
Route A repair objective and intervention plan.

This is a design milestone. It does not execute reset, step, rollout, replay,
validation, training, PPO, source build, adapter probe, external simulation,
ranking, winner selection, promotion, success-rate computation, or any driver
performance verdict.

The route constraint from `docs/post-m2470-route-plan.md` is still active:
Route A should freeze a usable actuator-level engineering controller baseline
without relying on hidden dynamics, oracle labels, TTC, reference trajectory,
precomputed progress, or self-ID shortcuts as actor inputs.

## Accepted Source Evidence

M2646 admits these M2644/M2645 facts:

```text
M2644 status_pass: true
result_class: engineering_controller_route_a_source_only_behavior_gap_taxonomy_preflight_pass
source measured behavior rows: 160
role gap rows: 4
subject-role gap rows: 20
dynamics-axis gap rows: 8
repair-target admission rows: 4
claim-boundary rows: 13
gate rows: 15
gate_matrix_pass: true
actor_contract_shape_72_action_3: true
taxonomy_labels_actor_visible: false
all_rows_diagnostic_only_no_ranking_claim: true

M2645 decision:
accept_m2644_route_to_source_only_gap_targeted_repair_design
```

These rows are admitted as artifact-level planning evidence only. They are not
ranking, promotion, validation, success-rate, driver-performance, paper,
current-sim, high-fidelity validation, finite-window-vs-GRU, or self-ID
evidence.

## Repair Targets

M2646 admits exactly two repair-design targets:

```text
road_departure_dominant_gap:
  source rows: 80
  source roles: stable_aes, stable_avoidable
  target scope: road_boundary_margin_control
  design objective: reduce road-boundary departure pressure while preserving
    obstacle-clearance and actuator-contract diagnostics

drift_recovery_mixed_gap:
  source rows: 40
  source role: drift_required_recovery
  target scope: drift_collision_recovery_tradeoff
  design objective: improve recovery-shaped tradeoff between collision
    avoidance, road margin, yaw/lateral velocity recovery, and command
    smoothness
```

The repair objective is gap-targeted, not subject-ranking targeted. Source
subjects can be used only as diagnostic row provenance for the plan; they must
not become a leaderboard, winner field, promotion trigger, or actor-visible
label.

## Protected Reference Rows

M2646 preserves two M2644 rows as non-target references:

```text
mitigation_collision_saturated_reference:
  source rows: 40
  source role: unavoidable_mitigation
  disposition: reference_only
  use in repair plan: mitigation-reference guard only
  not allowed: ordinary success denominator, repair target, winner evidence

axis_sensitivity_not_yet_decisive:
  source rows: 160
  source roles: stable_avoidable, stable_aes, drift_required_recovery,
    unavoidable_mitigation
  disposition: diagnostic axis monitoring only
  use in repair plan: axis-coverage monitor and overfit guard only
  not allowed: robust-fault verdict, validated delay/noise physics verdict,
    repair target, actor input
```

These rows prevent two common overclaims: treating unavoidable mitigation as a
normal pass/fail task, and treating the source-only fault/delay/noise axis as a
validated robustness result.

## Actor Boundary

The repair design preserves the deployed P0 contract:

```text
observation_shape: 72
action_shape: 3
action_contract: [steer_command, throttle_command, brake_command]
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
route_decisions_actor_visible: false
source_only_outcomes_actor_visible: false
hidden_oracle_actor_inputs_allowed: false
```

Forbidden actor inputs include behavior-gap labels, repair-target labels,
source-only diagnostic outcomes, route decisions, hidden friction/dynamics,
slip, tire force, TTC, reference trajectory, path error, heading error, path
curvature, oracle feasibility, stopping distance, required clearance,
precomputed success/progress labels, validation outcomes, and high-fidelity
backend status.

Objective terms may exist in training or plan metadata later only after an
audit admits them. They must not be appended to the actor observation.

## Bounded Objective Design

A post-synthesis materialization milestone may materialize these objective
families as rows, not execute them:

```text
road_boundary_margin_control:
  admitted gap: road_departure_dominant_gap
  source roles: stable_avoidable, stable_aes
  source rows: 80
  objective terms:
    minimum_road_margin_floor_proxy
    road_departure_event_penalty_proxy
    final_road_margin_recovery_proxy
    obstacle_clearance_preservation_proxy
    command_delta_l1_smoothness_guard
  guard terms:
    no collision-regression claim
    no success-rate verdict
    no controller ranking
    no actor-visible labels

drift_collision_recovery_tradeoff:
  admitted gap: drift_recovery_mixed_gap
  source roles: drift_required_recovery
  source rows: 40
  objective terms:
    minimum_obstacle_clearance_proxy
    collision_event_penalty_proxy
    minimum_road_margin_floor_proxy
    final_lateral_velocity_recovery_proxy
    final_yaw_rate_recovery_proxy
    command_delta_l1_smoothness_guard
  guard terms:
    no mitigation-row normalization
    no robust-fault or delay/noise verdict
    no winner selection
    no actor-visible labels
```

The objective is intentionally proxy-level because M2646 is source-only and
pre-repair. M2647 may define row schemas and gate checks. It must not run PPO,
modify a checkpoint, generate repaired weights, or evaluate the objective.

## Intervention Plan

If M2647 synthesis admits materialization, the follow-up materialization should
write a repair-plan artifact bundle with these row groups:

```text
repair_objective_rows:
  one row per admitted repair objective family
  records gap family, target scope, source role family, source row count,
  objective terms, guard terms, and claim boundary

source_row_selection_rows:
  records which accepted M2644 repair-target rows are admitted or excluded
  admits road_departure_dominant_gap and drift_recovery_mixed_gap only
  excludes mitigation_collision_saturated_reference and
  axis_sensitivity_not_yet_decisive from repair targets

protected_reference_rows:
  records mitigation and axis rows as protected references
  forbids using protected rows as ordinary success denominators or robust
  validation verdicts

actor_contract_guard_rows:
  proves P0 observation 72 and action 3 are preserved
  proves taxonomy labels and repair-target labels remain actor-invisible

intervention_boundary_rows:
  records what later repair execution may be allowed to change
  allowed later after audit: objective weights, sampling admission, loss rows,
  repair-run config fields
  not allowed later without a separate contract repair: actor observation,
  action contract, hidden/oracle input channels

claim_boundary_rows:
  states that M2647 is a plan materialization only
  rejects ranking, validation, performance, paper, current-sim, high-fidelity,
  finite-window-vs-GRU, and self-ID claims

gate_matrix:
  records pass/fail rows for source artifacts, target admission, protected
  references, actor boundary, forbidden execution, and follow-up routing
```

The candidate materialization artifact bundle should be small and
deterministic. It is a repair plan preflight, not a training run. M2647 itself
should synthesize the branch before admitting or rejecting that materialization.

## Candidate Repair-Plan Artifact Contract

Required artifacts for a candidate post-synthesis materialization:

```text
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/summary.json
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/repair_objective_rows.csv
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/source_row_selection_rows.csv
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/protected_reference_rows.csv
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/actor_contract_guard_rows.csv
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/intervention_boundary_rows.csv
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/claim_boundary_rows.csv
runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_plan/gate_matrix.csv
docs/m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-plan-materialization-preflight.md
```

Expected summary keys:

```text
status_pass
result_class
source_artifacts_exist
repair_objective_row_count
source_row_selection_row_count
protected_reference_row_count
actor_contract_guard_row_count
intervention_boundary_row_count
claim_boundary_row_count
gate_matrix_row_count
gate_matrix_pass
actor_contract_shape_72_action_3
taxonomy_labels_actor_visible
repair_target_labels_actor_visible
hidden_oracle_actor_input_detected
ranking_run
winner_selected
checkpoint_promoted
success_rate_computed
validation_run
training_run
ppo_run
driver_performance_claim_made
paper_claim_made
finite_window_vs_gru_claim_made
current_sim_verdict_claim_made
high_fidelity_validation_claim_made
level3_self_id_claim_made
next_audit_manifest_registered
```

## Pass/Fail Gates

A post-synthesis materialization should pass only if:

```text
source_artifacts_exist: true
accepted_repair_target_count: 2
protected_reference_count: 2
road_departure_dominant_gap_targeted: true
drift_recovery_mixed_gap_targeted: true
mitigation_collision_saturated_reference_targeted: false
axis_sensitivity_not_yet_decisive_targeted: false
actor_contract_shape_72_action_3: true
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
hidden_oracle_actor_input_detected: false
all_rows_plan_only_no_execution_claim: true
reset_run: false
step_run: false
rollout_run: false
replay_run: false
validation_run: false
training_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
driver_performance_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
level3_self_id_claim_made: false
next_audit_manifest_registered: true
```

A post-synthesis materialization should fail if it needs to change the actor
observation, expose taxonomy metadata to the actor, use protected references
as repair targets, execute a repair or rollout, or make any performance or
paper-level claim.

## Stop And Fallback Rules

Stop rather than materialize M2647 if:

```text
1. The repair objective cannot be expressed without actor-contract changes.
2. Mitigation rows must be converted into ordinary success denominators.
3. Axis rows must be interpreted as robust fault/delay/noise verdicts.
4. The next step would train or rank before the repair plan is audited.
5. The next step would claim driver performance from source-only taxonomy rows.
```

Fallback routes:

```text
actor contract inconsistency -> contract repair or branch synthesis
missing M2644/M2645 artifacts -> artifact repair
protected-reference conflict -> branch synthesis or stop
M2647 synthesis admits materialization -> M2648 materialization preflight
M2647 synthesis rejects materialization -> measured-evidence design pivot or stop
post-synthesis materialization pass -> result audit
post-synthesis materialization fail -> repair-plan artifact audit or synthesis
```

## Claim Boundary

Supported operational claim:

```text
M2646 designs a bounded Route A source-only gap-targeted repair objective and
intervention plan from accepted M2644/M2645 taxonomy evidence.
```

Rejected claims:

```text
no reset step rollout replay validation training PPO source build adapter probe
no external high-fidelity simulation
no ranking winner selection checkpoint promotion or success-rate verdict
no driver-performance claim
no paper-level evidence
no finite-window-vs-GRU conclusion
no current-sim verdict
no high-fidelity validation readiness or result
no full ideal driver completion
no level3 self-identification result
```

## Decision

Route to M2647 source-only gap-targeted repair branch synthesis before
materialization. M2647 should decide whether to admit M2648 repair-plan
materialization, pivot to measured-evidence design, or stop. It must not
execute repair, train, validate, rank, promote, compute success rates, or claim
driver performance.
