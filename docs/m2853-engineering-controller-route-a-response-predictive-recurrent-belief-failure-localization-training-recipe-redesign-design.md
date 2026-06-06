# M2853 Engineering Controller Route A Response-Predictive Recurrent-Belief Failure Localization Training Recipe Redesign Design

## Metadata

- status: completed
- decision: `admit_existing_artifact_failure_localization_materialization_preflight`
- manifest: `experiments/manifests/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design.json`
- design artifact: `docs/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design.md`
- parent synthesis: `docs/m2852-engineering-controller-route-a-response-predictive-recurrent-belief-closed-loop-delta-result-synthesis.md`
- parent paired panel: `runs/m2850_engineering_controller_route_a_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel/summary.json`
- follow-up manifest: `experiments/manifests/m2854-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-preflight.json`
- next: `m2854-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-preflight`

## Design Decision

M2853 admits a bounded existing-artifact failure-localization materialization
preflight:

```text
existing_artifact_failure_localization_materialization_preflight
```

The purpose is to convert the M2850 paired closed-loop diagnostic panel into
machine-auditable row-level localization artifacts before changing training
recipe, continuing PPO, or running another paired delta panel.

This is still not a driver-performance milestone. M2853 does not run reset,
step, rollout, replay, validation, training, PPO, private holdout, source build,
adapter probe, external simulation, ranking, winner selection, promotion, or
success-rate verdict computation.

## Evidence Used

M2852 closed the direct M2843-M2851 continuation/delta loop as complete but weak
diagnostic evidence:

```text
M2846 implementation preflight:
  status_pass: true
  8-step CPU PPO smoke
  response_prediction_loss_mean: 0.3585260510444641
  changed non-actor-head groups:
    response_encoder, online_gru_cell, response_context_fusion,
    response_prediction_head

M2848 bounded continuation:
  status_pass: true
  strict source load
  32-step CPU PPO continuation
  response_prediction_loss_mean: 0.32993096113204956
  changed groups:
    response_encoder, online_gru_cell, response_context_fusion,
    actor_mean, critic, log_std, response_prediction_head

M2850 paired diagnostic delta panel:
  selected pairs: 16
  paired execution rows: 32
  paired delta rows: 16
  gate matrix: 27/27 pass
  diagnostic success count: 0
  diagnostic collision count: 0
  termination counts: {"": 30, "speed_too_low": 2}
  min-clearance-margin delta positive rows: 16/16
  return delta positive rows: 1/16
  speed_mean delta positive rows: 1/16
  termination pair changed: 0/16
  collision pair changed: 0/16
```

M2850's paired execution rows are rollout-level rows. They contain summary
metrics such as termination reason, outcome bucket, clearance, return, mean
speed, sideslip fraction, and action summary norms. They do not contain per-step
state/action traces, per-step response-prediction error, or recurrent hidden
state probes. M2853 therefore must not claim temporal onset localization from
M2850 alone.

## Localization Questions

M2854 should answer only first-layer row-level localization questions that are
supported by existing M2850 artifacts:

```text
1. Is the candidate's all-positive clearance delta paired with progress loss?
2. Is speed degradation present on the same rows where clearance improves?
3. Are the two speed_too_low rows attributable to one subject or both subjects?
4. Do termination outcomes remain invariant despite metric deltas?
5. Are action summary deltas large enough to suggest action-shaping drift, or
   are behavior changes too small to explain task outcome changes?
6. Are high-sideslip changes absent, making drift-style recovery unsupported by
   this row surface?
7. Which rows require a future per-step telemetry panel because rollout-level
   metrics cannot localize the onset?
```

M2854 must not answer:

```text
validated driver capability
checkpoint ranking
winner selection
repair success
success-rate verdict
paper-level self-ID
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness
full ideal driver completion
```

## Localization Artifact Schema

M2854 should materialize the following artifacts under:

```text
runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/
```

Required artifacts:

```text
summary.json
row_failure_localization_rows.csv
localization_taxonomy_rows.csv
training_recipe_redesign_rows.csv
public_row_overfit_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
```

### row_failure_localization_rows.csv

One row per M2850 pair:

```text
pair_id
task_source_id
profile_name
task_family
source_family_tag
scenario_role_primary
baseline_outcome_bucket
candidate_outcome_bucket
baseline_termination_reason
candidate_termination_reason
baseline_success_diagnostic
candidate_success_diagnostic
baseline_collision_diagnostic
candidate_collision_diagnostic
clearance_delta
return_delta
speed_mean_delta
action_rate_delta
previous_command_norm_delta
current_action_norm_delta
action_trace_delta_delta
high_sideslip_fraction_delta
clearance_improved
return_degraded
speed_degraded
termination_invariant
collision_invariant
both_non_success
both_non_collision
speed_too_low_subject_count
requires_step_trace
localization_bucket
training_recipe_signal
diagnostic_only
ranking_admissible
ordinary_success_denominator_allowed
```

Allowed localization buckets:

```text
clearance_progress_tradeoff
low_speed_invariant_noncompletion
weak_action_delta_outcome_invariant
sideslip_not_activated
step_trace_required
mixed_or_unclassified
```

### localization_taxonomy_rows.csv

Aggregate counts by localization bucket and source family:

```text
taxonomy_id
localization_bucket
row_count
clearance_improved_count
return_degraded_count
speed_degraded_count
termination_invariant_count
speed_too_low_subject_count
requires_step_trace_count
diagnostic_interpretation
forbidden_interpretation
```

### training_recipe_redesign_rows.csv

Design-level recommendations, not training execution:

```text
recipe_signal_id
signal_name
trigger_condition
observed_count
allowed_next_use
blocked_shortcut
claim_boundary
```

Candidate signals:

```text
progress_preserving_clearance_objective:
  trigger: clearance improves while return or speed degrades and termination is
  invariant.
  allowed next use: design a bounded training objective that preserves progress
  and speed while keeping clearance guardrails.

low_speed_guard_and_recovery_loss:
  trigger: speed_too_low appears in either subject or speed_mean degrades on most
  rows.
  allowed next use: design a low-speed onset/recovery diagnostic or training
  guard.

action_response_temporal_trace_requirement:
  trigger: row-level metrics cannot localize when clearance and progress diverge.
  allowed next use: design a fresh per-step telemetry panel before another
  training continuation.

fresh_non_public_localization_panel:
  trigger: existing rows are fixed public M2850 diagnostic rows.
  allowed next use: require disjoint fresh diagnostic rows before optimization or
  promotion gates.
```

### public_row_overfit_guard_rows.csv

The follow-up must explicitly preserve:

```text
M2850 rows are public diagnostic rows
M2850 rows are not ordinary success denominators
M2850 rows cannot be the only optimization target
positive clearance deltas cannot be rebranded as repair success
future proof/generalization rows must be disjoint or separately registered
future training recipe must not introduce hidden/oracle actor inputs
```

## Public-Row Overfit Guard

M2854 is allowed to read M2850 artifacts and create a derived localization
panel. It is not allowed to use M2850 as a training target or ranking surface.
Any later training recipe must include at least one of:

```text
fresh diagnostic panel disjoint from M2850
guardrail-only use of M2850 with separate proof/generalization rows
per-step telemetry materialization that is explicitly diagnostic-only
objective preflight that reports public-row overfit risk before PPO
```

## Actor And Claim Boundary

All follow-up work must preserve:

```text
actor observation shape: 72
action shape: 3
actor_encoder: human_view_online_gru
hidden/oracle actor input required: false
actor-visible source/stress/scenario/outcome/route/verdict labels: false
ordinary_success_denominator_allowed: false for M2838 and M2850 rows
ranking_admissible: false for M2850-derived rows
```

M2853 and M2854 do not change actor inputs, action outputs, active configs,
checkpoint promotion state, or evaluator labels visible to the actor.

## Follow-Up Route

M2853 registers:

```text
m2854-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-preflight
```

M2854 should be an infrastructure materialization preflight. It should read
existing M2850 artifacts and write the localization artifacts listed above. It
should also register an M2855 result-audit manifest.

If M2854 finds that row-level artifacts are insufficient to localize the failure
mechanism, the correct next route is a per-step telemetry design or materialized
diagnostic panel, not another direct response-predictive recurrent-belief PPO
continuation.

## Claim Boundary

Allowed M2853 claim:

```text
M2853 defines a bounded existing-artifact failure-localization materialization
route and registers M2854.
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
