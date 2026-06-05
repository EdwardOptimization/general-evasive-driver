# M2752 Engineering Controller Route A Cross-Axis Stress Generalization Bounded Execution Design

## Metadata

- status: completed
- decision: `admit_route_a_cross_axis_stress_generalization_bounded_execution_preflight`
- manifest: `experiments/manifests/m2752-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-design.json`
- design doc: `docs/m2752-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-design.md`
- parent synthesis: `docs/m2751-engineering-controller-route-a-baseline-readiness-after-role-panel-diagnostic-branch-synthesis.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2753-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-preflight.json`
- next: `m2753-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-preflight`

## Design Premise

M2751 closes the M2748-M2750 readiness-after-role-panel branch as complete and
claim-safe process evidence only. It explicitly says that M2749/M2750 changed
the readiness/admission state, not driver capability evidence. The M2746
diagnostic remains weak row accounting:

```text
M2746 execution rows: 14
diagnostic success: 1/14
collision: 1/14
off_track: 9/14
speed_too_low: 3/14
unset_or_completed: 1/14
```

M2752 is design-only. It does not reset, step, run policy actions, rollout,
replay, validate, train, run PPO, build source, probe adapters, run external
simulation, tune profiles, rank rows, select winners, promote checkpoints,
compute success-rate verdicts, or claim repair success, driver performance,
paper evidence, current-sim validation, high-fidelity validation, full ideal
driver completion, or level3 self-identification.

The design purpose is to admit one bounded M2753 diagnostic execution preflight
that changes the Route A evidence axis from readiness/role-panel accounting to
a fresh non-same-panel cross-axis stress surface.

## Source Criteria

M2753 may consume only these source artifacts for candidate selection and
guardrails:

```text
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/execution_candidate_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_index/next_action_admission_rows.csv
runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_index/blocker_matrix.csv
docs/m2751-engineering-controller-route-a-baseline-readiness-after-role-panel-diagnostic-branch-synthesis.md
```

The executable source must be `L3_online_gru` rows from the M1690 workload
matrix. This is a single recurrent policy-under-test protocol, not a profile
winner selection. M2753 must not compare L0/L1/L2/L3_reset rows, rank profile
families, or substitute another profile if a selected L3 row is missing.

Candidate rows must satisfy:

```text
profile_name: L3_online_gru
config_exists: True
checkpoint_exists: True
environment_rollout_scheduled: False in source matrix
training_scheduled: False in source matrix
profile_specific_tuning: False
actor input change required: false
hidden/oracle actor input required: false
private holdout used: false
```

## Non-Same-Panel Exclusion Rules

M2753 must build a prior-panel exclusion set from:

```text
M2746 execution_candidate_rows.csv task_source_id
M2746 candidate_execution_rows.csv task_source_id
M2737 candidate_execution_rows.csv task_source_id
```

The exact task-source ids observed in those prior panels include:

```text
m1680-spec-0000
m1680-spec-0002
m1680-spec-0004
m1680-spec-0005
m1680-spec-0006
m1680-spec-0036
m1680-spec-0038
m1680-spec-0040
m1680-spec-0041
```

M2753 must not execute any row whose `task_source_id` is in that exclusion set.
If a selected task-source id is unexpectedly found in the exclusion set, M2753
must write a failure row and not substitute a nearby same-axis row.

The non-same-panel rule is exact task-source exclusion. M2753 may still include
a repeated stress-axis family if the source task is a fresh task-source id,
because the purpose is cross-axis generalization, not source-edge ranking.

## Candidate Surface

M2753 admits exactly 12 fixed L3 task-source ids from M1690:

```text
m1680-spec-0001  T4  actuator_delay_step|t4_capability_step_temporal
m1680-spec-0003  T4  t4_actuator_delay_response|actuator_delay_step
m1680-spec-0008  T4  actuator_delay_step|t4_capability_step_temporal
m1680-spec-0010  T4  t4_actuator_delay_response|actuator_delay_step
m1680-spec-0037  T5  brake_fade_or_loss_proxy|late_reveal_boundary
m1680-spec-0039  T5  curved_boundary_obstacle|drive_loss_proxy
m1680-spec-0042  T5  t5_boundary_axis_retarget|drive_loss_proxy
m1680-spec-0043  T5  t5_near_boundary_warmup|t5_boundary_axis_retarget
m1680-spec-0044  T5  actuator_delay_step|t5_near_boundary_warmup
m1680-spec-0045  T5  brake_fade_or_loss_proxy|late_reveal_boundary
m1680-spec-0046  T5  capability_step_down|t5_near_boundary_warmup
m1680-spec-0047  T5  curved_boundary_obstacle|drive_loss_proxy
```

Stress-axis grouping for diagnostic aggregate rows:

```text
actuator_delay_or_response:
  m1680-spec-0001
  m1680-spec-0003
  m1680-spec-0008
  m1680-spec-0010
  m1680-spec-0044

brake_or_drive_authority:
  m1680-spec-0037
  m1680-spec-0039
  m1680-spec-0042
  m1680-spec-0045
  m1680-spec-0047

late_boundary_or_near_boundary:
  m1680-spec-0037
  m1680-spec-0043
  m1680-spec-0044
  m1680-spec-0045
  m1680-spec-0046

curved_or_retargeted_obstacle:
  m1680-spec-0039
  m1680-spec-0042
  m1680-spec-0043
  m1680-spec-0047
```

These groups are diagnostic tags for artifact accounting only. They are not
actor inputs, reward inputs, controller-family labels, scenario-role labels,
ranking groups, progress labels, or verdict labels.

## Seed And Execution Policy

M2753 must use the selected M1690 workload rows as the fixed corpus policy. It
must not mine additional rows, resample until success, alter active configs, or
tune per-axis parameters. The runner may execute one diagnostic rollout per
resolved candidate row using the row's preserved `profile_config_path`,
`checkpoint_path`, and workload identity.

If M2753 cannot resolve or execute a selected row without actor-contract
changes, hidden/oracle labels, profile-specific tuning, or active config
overwrites, it must write that row to `candidate_execution_failure_rows.csv`
and keep artifact accounting complete.

## Actor Contract Guard

M2753 must preserve:

```text
P0 observation shape: 72
action shape: 3
hidden_oracle_actor_input_detected: false
actor_input_changed: false
deployed action contract changed: false
```

The actor may use only deployable human-view signals already admitted by Route
A: ego response, actuator state, previous physical commands, ego-frame
road/free-space/obstacle geometry, and recurrent/history state.

M2753 must not add any of these to actor input:

```text
mu
mass
center-of-gravity
tire stiffness
brake scale
drive scale
steering delay
drive delay
sensor-noise labels
actuator-delay labels
source-edge labels
stress-axis labels
scenario-role labels
oracle feasibility
AEB/AES/drift labels
TTC
reference trajectory
path error
heading error
path curvature
required clearance
precomputed success or progress labels
verdict labels
```

## Exclusion And Blocker Surface

M2753 must carry the following as guardrails, not execution candidates:

```text
M2746 weak diagnostic rows
M2737 prior source-diverse diagnostic rows
M2749 same-panel and same-surface rejection rows
M2667 protected mitigation blocker
M2638 HF3 source dependency blocker
```

Guardrail rules:

```text
prior-panel rows remain non-ranking context
same-panel role execution remains rejected
same-surface repair loop remains rejected
protected mitigation rows remain outside ordinary success denominators
HF3 selected-platform execution remains not admitted
blocker labels remain actor-invisible
stress-axis tags remain actor-invisible
guardrail outcomes are not ordinary success denominators
```

Any candidate resolution that overlaps a prior-panel, protected, or HF3
blocker row must be rejected into `candidate_execution_failure_rows.csv`.

## Output Artifacts

M2753 should write:

```text
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/summary.json
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/cross_axis_candidate_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/execution_candidate_resolution_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/candidate_execution_failure_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/stress_axis_aggregate_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/prior_panel_exclusion_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/blocker_guard_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/actor_contract_guard_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/claim_boundary_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/gate_matrix.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/run_state.json
docs/m2753-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-preflight.md
```

Execution rows may record diagnostic metrics:

```text
termination_reason
collision
offtrack
obstacle_completed
minimum clearance
episode length
return
speed_too_low
finite metric checks
```

These fields are diagnostic only. They must not become ranking, validation,
success-rate verdict, repair-success, driver-performance, paper, current-sim,
high-fidelity, full-driver, or self-ID claims.

## Gate Matrix

M2753 passes as a bounded execution preflight only if all of these hold:

```text
M2752 design doc exists
M1690 workload matrix loaded
12 fixed L3_online_gru candidate rows selected
12 selected task_source_ids resolved or accounted by failure rows
M2746/M2737 prior-panel task_source_ids loaded as exclusion rows
prior-panel task_source_ids executed false
same-panel role execution admitted false
same-surface repair loop admitted false
protected rows executed false
protected rows in success denominator false
HF3 execution started false
actor 72/action 3 preserved
hidden_oracle_actor_input_detected false
actor input changed false
stress-axis labels actor-visible false
taxonomy, scenario-role, target, blocker, route-decision, success/progress, and verdict labels actor-visible false
profile_specific_tuning false
active_config_overwritten false
ranking_run false
winner_selected false
checkpoint_promoted false
success_rate_verdict_claim_made false
driver_performance_claim_made false
validation_readiness_claim_made false
paper_claim_made false
current_sim_verdict_claim_made false
high_fidelity_validation_claim_made false
full_ideal_driver_gate_passed false
one result-audit follow-up manifest registered
```

Behavioral failure rows may still pass the artifact gate if every selected
candidate is accounted for and all claim/actor/blocker boundaries are clean. A
pass does not mean the driver succeeded.

## Follow-Up

M2752 admits:

```text
m2753-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-preflight
```

M2753 must register a separate M2754 result audit before any interpretation,
repair design, validation route, ranking, packaging, or performance claim.

## Claim Boundary

Allowed M2752 claim:

```text
M2752 defines and admits a bounded non-same-panel Route A cross-axis stress
generalization execution preflight over 12 fixed L3_online_gru M1690 workload
rows while preserving actor, blocker, and claim boundaries.
```

Forbidden M2752 claims:

```text
driver performance
repair success
validation readiness
validation result
success-rate verdict
source-family ranking
task-family ranking
stress-axis ranking
profile ranking
winner selection
checkpoint promotion
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
