# M2758 Engineering Controller Route A Post-Cross-Axis Negative Action-Response Containment Probe Design

## Metadata

- status: completed
- decision: `admit_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight`
- manifest: `experiments/manifests/m2758-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-design.json`
- design doc: `docs/m2758-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-design.md`
- parent audit: `docs/m2757-engineering-controller-route-a-post-cross-axis-negative-failure-localization-panel-materialization-result-audit.md`
- parent summary: `runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/summary.json`
- follow-up manifest: `experiments/manifests/m2759-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-preflight.json`
- next: `m2759-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-preflight`

## Design Premise

M2757 accepts M2756 as a complete and claim-safe localization panel. The
accepted panel separates M2753's 12 negative diagnostic rows into:

```text
collision_negative_clearance: 3 rows
offtrack_positive_clearance: 9 rows
diagnostic_success: 0 rows
stress-axis context rows: 4
source-edge context rows: 8
guardrail context rows: 31
```

M2758 is design-only. It does not reset, step, run policy actions, rollout,
replay, validate, train, run PPO, build source, probe adapters, start external
simulation, rank rows, select winners, promote checkpoints, compute
success-rate verdicts, or claim repair success, driver performance, paper
evidence, current-sim validation, high-fidelity validation, full ideal driver
completion, or self-identification.

The design purpose is to admit one bounded M2759 diagnostic execution preflight
that tests mechanism signals on the localized negative rows before any repair
design. The probe asks whether the current driver failure is better explained
by action-response mismatch, track-containment failure, obstacle-clearance
timing, impact severity, or mixed behavior.

## Candidate Input Surface

M2759 may consume only these M2756 artifacts as the execution input surface:

```text
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/summary.json
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/failure_localization_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/outcome_bucket_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/stress_axis_context_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/source_edge_context_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/guardrail_context_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/actor_contract_guard_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/claim_boundary_rows.csv
runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel/gate_matrix.csv
```

The candidate rows are exactly the 12 rows in
`failure_localization_rows.csv`. M2759 must preserve the localized strata:

```text
collision_negative_clearance rows: 3
offtrack_positive_clearance rows: 9
profile: L3_online_gru
candidate_admitted: true
prior_panel_excluded: false
diagnostic_only_no_verdict: true
hidden_oracle_actor_input_required: false
actor_visible_allowed: false
```

The fixed candidate surface is:

```text
m1680-spec-0001  m2753-cross-axis-candidate-0001  collision_negative_clearance
m1680-spec-0003  m2753-cross-axis-candidate-0002  offtrack_positive_clearance
m1680-spec-0008  m2753-cross-axis-candidate-0003  offtrack_positive_clearance
m1680-spec-0010  m2753-cross-axis-candidate-0004  offtrack_positive_clearance
m1680-spec-0037  m2753-cross-axis-candidate-0005  offtrack_positive_clearance
m1680-spec-0039  m2753-cross-axis-candidate-0006  offtrack_positive_clearance
m1680-spec-0042  m2753-cross-axis-candidate-0007  offtrack_positive_clearance
m1680-spec-0043  m2753-cross-axis-candidate-0008  collision_negative_clearance
m1680-spec-0044  m2753-cross-axis-candidate-0009  collision_negative_clearance
m1680-spec-0045  m2753-cross-axis-candidate-0010  offtrack_positive_clearance
m1680-spec-0046  m2753-cross-axis-candidate-0011  offtrack_positive_clearance
m1680-spec-0047  m2753-cross-axis-candidate-0012  offtrack_positive_clearance
```

M2759 must not add or substitute nearby rows, mine extra rows, resample until a
desired outcome occurs, or use source-edge or stress-axis labels as ranking
groups.

## Guardrail Surface

M2759 must carry all 31 M2756 guardrail context rows as guardrails, not
execution candidates:

```text
prior-panel exclusion rows: 25
blocker guard rows: 6
execution_run: false
ordinary_success_denominator_allowed: false
protected_rows_in_success_denominator: false
actor_visible_allowed: false
```

Guardrails remain visible in artifacts because they constrain interpretation.
They must not enter the 12-row execution denominator and must not become actor
inputs.

## Actor Contract

M2759 must preserve:

```text
P0 observation shape: 72
action shape: 3
actor_input_contract_changed: false
hidden_oracle_actor_input_detected: false
localization labels actor-visible: false
action-response labels actor-visible: false
containment labels actor-visible: false
stress-axis labels actor-visible: false
source-edge labels actor-visible: false
success/progress labels actor-visible: false
verdict labels actor-visible: false
```

The actor may use only the deployed Route A human-view observation contract:
ego response, actuator state, previous physical commands, ego-frame road,
free-space and obstacle geometry, and recurrent/history state. Evaluator
telemetry may use richer diagnostic fields after the rollout, but none of those
fields may be fed into actor input or policy routing.

## Probe Execution Protocol

M2759 may execute reset, step, policy action, and rollout only for the 12
localized candidate rows. It must not execute replay, validation, training,
PPO, source build, adapter probe, external simulation, private holdout, ranking,
winner selection, checkpoint promotion, success-rate verdict computation, or
profile-specific tuning.

Execution rules:

```text
one diagnostic rollout per localized candidate row
fixed L3_online_gru policy and checkpoint from each M2756 row
fixed row config path from each M2756 row
no active config overwrite
no repair overlay
no row replacement
no per-row tuning
no hidden or oracle actor feature
```

If a row cannot be resolved or executed without actor-contract changes,
profile-specific tuning, active config overwrite, or hidden/oracle labels,
M2759 must write the row to `probe_execution_failure_rows.csv` and keep the
artifact set complete.

## Evaluator-Only Telemetry

M2759 should write evaluator-only telemetry rows that help separate mechanisms:

```text
action_response_probe_rows.csv:
  candidate_id
  failure_family
  previous_command
  current_action
  actuator_lag_proxy
  actuator_error_proxy
  action_rate_mean
  action_rate_peak
  command_response_phase_lag_proxy
  speed_response_proxy
  yaw_response_proxy
  beta_response_proxy
  plan_first_action_error_proxy
  finite_metric

containment_probe_rows.csv:
  candidate_id
  failure_family
  termination_reason
  min_clearance_margin
  max_off_track_overshoot
  time_to_first_off_track_s
  off_track_severity_proxy
  impact_speed_proxy
  impact_severity_proxy
  recoverability_window_success
  post_event_speed_proxy
  post_event_yaw_proxy
  post_event_offtrack_proxy
  containment_failure_flag
  collision_risk_flag

mechanism_context_rows.csv:
  candidate_id
  mechanism_tag
  mechanism_tag_actor_visible
  tag_scope
```

These fields are diagnostic outputs only. They may support a future repair
design after result audit, but M2759 itself must not call them proof of repair,
validation readiness, performance, paper evidence, or self-identification.
Allowed mechanism tags are
`collision_negative_clearance`, `offtrack_positive_clearance`,
`action_response_mismatch_context`, `track_containment_context`,
`obstacle_timing_context`, and `mixed_mechanism_context`. They are artifact
labels only and must never be actor input.

## Output Artifacts

M2759 should write:

```text
runs/m2759_engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight/summary.json
probe_candidate_resolution_rows.csv
probe_execution_rows.csv
probe_execution_failure_rows.csv
action_response_probe_rows.csv
containment_probe_rows.csv
mechanism_context_rows.csv
guardrail_context_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2759-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-preflight.md
```

Expected candidate accounting:

```text
localized candidate rows: 12
collision negative-clearance strata: 3
offtrack positive-clearance strata: 9
guardrail rows: 31
```

## Gate Matrix

M2759 passes as an execution preflight only if all of these hold:

```text
M2756 summary status_pass true
M2758 design doc present
M2757 audit doc present
12 localized candidate rows loaded
12 localized candidate rows resolved or accounted by failure rows
3 collision negative-clearance rows preserved
9 offtrack positive-clearance rows preserved
31 guardrail context rows carried
guardrail execution false
protected rows in success denominator false
actor 72/action 3 preserved
hidden_oracle_actor_input_detected false
actor_input_contract_changed false
localization/action-response/containment labels actor-visible false
profile_specific_tuning false
active_config_overwritten false
replay/validation/training/PPO/source/adapters/external sim false
ranking_run false
winner_selected false
checkpoint_promoted false
success_rate_verdict_claim_made false
driver_performance_claim_made false
all required artifacts present
follow-up result-audit manifest registered
```

## Follow-Up

If M2759 executes and writes a complete claim-safe probe artifact set, it must
register an M2760 result audit before any repair design, execution extension,
ranking, validation, performance, paper, current-sim, high-fidelity,
full-driver, or self-ID interpretation.
