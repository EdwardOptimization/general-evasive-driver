# M2856 Engineering Controller Route A Response-Predictive Recurrent-Belief Per-Step Telemetry Panel Design

## Metadata

- status: completed
- decision: `admit_m2857_per_step_telemetry_panel_materialization_preflight`
- manifest: `experiments/manifests/m2856-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-design.json`
- design artifact: `docs/m2856-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-design.md`
- parent audit: `docs/m2855-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-result-audit.md`
- parent localization summary: `runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/summary.json`
- follow-up manifest: `experiments/manifests/m2857-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-materialization-preflight.json`
- next: `m2857-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-materialization-preflight`

## Design Decision

M2856 admits a bounded per-step telemetry panel materialization preflight:

```text
response_predictive_recurrent_belief_per_step_telemetry_panel_materialization
```

The panel is diagnostic only. It is intended to localize the M2854
clearance/progress tradeoff and low-speed invariant noncompletion surfaces before
any reward change, PPO continuation, checkpoint ranking, or promotion decision.

M2856 itself does not run reset, step, rollout, replay, validation, training,
PPO, ranking, winner selection, promotion, success-rate verdict computation, or
driver-performance evaluation.

## Evidence Used

M2854 materialized existing-artifact localization from M2850:

```text
row failure localization rows: 16
localization taxonomy rows: 6
training recipe rows: 4
public row overfit guards: 5
clearance improved rows: 16/16
return degraded rows: 15/16
speed degraded rows: 15/16
termination invariant rows: 16/16
requires step trace rows: 16/16
localization buckets:
  clearance_progress_tradeoff: 15
  low_speed_invariant_noncompletion: 1
```

M2855 accepted those artifacts as complete and claim-safe, but concluded that
rollout-level rows cannot localize temporal onset. The next evidence-changing
step is therefore a per-step telemetry panel, not another direct continuation or
another aggregate paired delta panel.

## Telemetry Surfaces

M2857 should materialize two bounded surfaces.

### Surface A: M2850 Explanatory Trace Surface

Purpose:

```text
explain the existing M2850/M2854 diagnostic rows at per-step resolution
```

Rows:

```text
the 16 M2850 task_source_id/profile pairs
baseline subject: M2846 checkpoint
candidate subject: M2848 checkpoint
horizon_steps: 96 unless an audited design changes it
```

Interpretation:

```text
diagnostic explanation only
not validation
not ranking
not a success-rate denominator
not an optimization target
not a promotion surface
```

### Surface B: Fresh/Disjoint Telemetry Surface

Purpose:

```text
avoid optimizing only the fixed public M2850 row surface
```

Selection rule:

```text
prefer M1690 L3_online_gru task_source_ids disjoint from:
  M2850 selected task sources
  M2838 selected task sources
  M2828 selected task sources
  M2816/M2807/M2759/M2737 protected diagnostic surfaces when available
```

If a fully disjoint panel cannot be formed, M2857 must write a guard row that
marks the overlap as public guardrail-only and rejects ranking, validation, and
optimization claims.

Recommended size:

```text
fresh/disjoint row count: 8 to 16
subject count per row: baseline and candidate
horizon_steps: 96
eval_seed_base: 285700
```

## Per-Step Telemetry Schema

M2857 should write:

```text
per_step_trace_rows.csv
episode_trace_summary_rows.csv
telemetry_surface_rows.csv
telemetry_localization_rows.csv
public_row_overfit_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
summary.json
run_state.json
```

### per_step_trace_rows.csv

One row per subject per environment step:

```text
trace_id
surface_id
pair_id
task_source_id
profile_name
checkpoint_subject
checkpoint_path
eval_seed
step_index
horizon_steps
terminated
truncated
termination_reason
success_diagnostic
collision_diagnostic
obstacle_completed_diagnostic
ego_vx
ego_vy
yaw_rate
ax
ay
steer_actuator
steer_rate
throttle_actuator
brake_actuator
previous_steer_command
previous_throttle_command
previous_brake_command
current_steer_command
current_throttle_command
current_brake_command
action_delta_norm
speed_scalar
speed_delta_from_previous
min_obstacle_clearance
clearance_margin
clearance_delta_from_previous
return_increment
cumulative_return
offtrack_margin_proxy
high_sideslip_proxy
response_prediction_available
response_prediction_error_norm
response_prediction_error_source
diagnostic_only
actor_visible_allowed
hidden_oracle_actor_input_required
```

Allowed actor-visible values are the same deployable observation and action
history channels used by the deployed actor. Evaluator-only diagnostics such as
clearance margin, return increments, termination flags, localization labels, and
response-prediction error annotations must remain actor-invisible.

### episode_trace_summary_rows.csv

One row per subject episode:

```text
surface_id
pair_id
task_source_id
checkpoint_subject
steps
success_diagnostic
collision_diagnostic
termination_reason
outcome_bucket
first_clearance_improvement_step
first_speed_drop_step
first_progress_loss_step
first_large_action_delta_step
first_low_speed_step
clearance_improvement_before_speed_drop
speed_drop_before_clearance_improvement
low_speed_recovery_window_available
candidate_minus_baseline_clearance_improvement_step_delta
candidate_minus_baseline_speed_drop_step_delta
candidate_minus_baseline_progress_loss_step_delta
requires_training_recipe_redesign
requires_fresh_panel_audit
diagnostic_only
ranking_admissible
ordinary_success_denominator_allowed
```

### telemetry_localization_rows.csv

One row per pair:

```text
surface_id
pair_id
task_source_id
localization_bucket_from_m2854
per_step_localization_bucket
clearance_progress_order
low_speed_onset_subject
action_response_lag_detected
response_prediction_timing_issue_detected
termination_invariant
candidate_behavior_change_before_failure
training_recipe_signal
requires_recipe_design
requires_additional_trace
diagnostic_interpretation
forbidden_interpretation
```

Candidate per-step localization buckets:

```text
late_clearance_after_progress_loss
early_clearance_with_speed_collapse
low_speed_unrecovered
weak_action_change_outcome_invariant
response_prediction_timing_unresolved
fresh_surface_mismatch
step_trace_inconclusive
```

## Response-Prediction Trace Boundary

The M2846/M2848 branch uses a training-only next-response prediction head with
target indices 0..8 and horizon 4. M2857 may record evaluator-side
response-prediction availability and error summaries only if they can be
computed without exposing future labels to the actor at action time.

Hard boundary:

```text
actor input stays 72 values
deployed action stays [steer, throttle, brake]
response-prediction targets remain evaluator/training diagnostics
future response labels are not actor-visible at action time
hidden dynamics and oracle labels remain forbidden
```

If response-prediction error cannot be computed cleanly from the current
checkpoint/runtime API, M2857 should write `response_prediction_available=false`
and route that gap to a later instrumentation repair instead of inventing
unverified values.

## Gate Design

M2857 should separate gate tiers:

```text
proof gates:
  required artifacts present
  per_step_trace_rows written
  episode_trace_summary_rows written
  M2850 explanatory surface accounting preserved
  fresh/disjoint surface accounting or overlap guard written
  M2850 zero-success diagnostics preserved
  M2854 requires-step-trace result preserved

generalization gates:
  fresh/disjoint surface contains the selected number of rows
  per-step telemetry finite for core deployable response/action channels
  termination and outcome rows remain diagnostic only
  localization rows written for both surfaces

promotion guards:
  ranking_admissible=false
  ordinary_success_denominator_allowed=false for public diagnostic rows
  checkpoint_promoted=false
  success_rate_verdict_computed=false
  no driver-performance claim
```

## Public-Row Overfit Guard

M2857 must explicitly distinguish:

```text
M2850 explanatory trace surface:
  public diagnostic explanation only

fresh/disjoint telemetry surface:
  diagnostic evidence expansion, still not validation or promotion
```

M2857 must not:

```text
optimize on M2850 explanatory rows
rank checkpoints from telemetry rows
select a winner
compute a success-rate verdict
promote M2848 or any checkpoint
claim repair success or driver performance
```

## Actor And Claim Boundary

All M2857 execution must preserve:

```text
actor observation shape: 72
action shape: 3
actor_encoder: human_view_online_gru
hidden/oracle actor input required: false
actor-visible source/stress/scenario/outcome/route/verdict labels: false
ordinary_success_denominator_allowed: false for M2838/M2850-derived public rows
ranking_admissible: false
```

Evaluator-only labels may be written to artifacts after execution, but they must
not be fed to the actor.

## Follow-Up Route

M2856 registers:

```text
m2857-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-materialization-preflight
```

M2857 should implement and run the bounded telemetry materialization. It should
also register an M2858 result-audit manifest. If M2857 cannot implement clean
per-step response/action telemetry without changing actor inputs or mixing
diagnostic labels into actor observations, it should fail closed and write a
blocker or artifact-repair route.

## Claim Boundary

Allowed M2856 claim:

```text
M2856 defines a bounded per-step telemetry panel design and registers M2857.
```

Rejected claims:

```text
checkpoint_promoted=false
validation_run=false
ranking_run=false
success_rate_computed=false
repair_success_claim_made=false
driver_performance_claim_made=false
paper_claim_made=false
current_sim_verdict_claim_made=false
high_fidelity_validation_claim_made=false
full_ideal_driver_gate_passed=false
level3_self_id_claim_made=false
```
