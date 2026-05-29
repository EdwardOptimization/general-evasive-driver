# M1515 Paper-Route Decisive History Source Retarget Result Audit

## Summary

M1515 audits the M1514 bounded source-retarget smoke.

Decision:

```text
source_retarget_audit_admit_t5_high_speed_intervention_design_repair_others
```

M1514 successfully moved the public source traces toward near-boundary and
non-AEB conditions. It does not justify candidate materialization yet. It does
justify a bounded measured-intervention design for the best T5 high-speed
close-obstacle subset, while routing the remaining weak or failed retargets to
repair later.

This milestone does not materialize candidates, export a training corpus, run
replay, run PPO, train, promote, use private holdout, change actor inputs, or
claim level3 self-identification.

## Audit Inputs

Run directory:

```text
runs/m1514_decisive_history_source_retarget_smoke
```

Artifacts:

```text
summary.json
retarget_spec_rows.csv
retarget_trace_rows.csv
retarget_snapshot_rows.csv
retarget_source_family_summary.csv
retarget_guardrail_summary.csv
```

## Result Summary

```text
spec_count: 24
source_family_count: 6
retarget_mode_count: 4
trace_row_count: 1576
snapshot_row_count: 95
rollout_success_count: 19
rollout_failure_count: 5
failure_type_counts:
  reset_failure: 4
  did_not_reach_decision_step: 1
global_min_margin: -0.042059208331689746
near_boundary_proxy_count: 39
non_aeb_label_source_family_count: 2
guardrail_violation_count: 0
```

M1514 met the M1513 evidence-quality direction:

```text
global margin moved from 4.170 m to -0.042 m;
at least two source families reduced margin by >= 50%;
two source families sampled non-aeb labels;
all guardrails stayed false.
```

## Eligible Subset

Measured-intervention design is admissible for this subset:

```text
t5_high_speed_close_obstacle
```

Candidate rows:

```text
mode                    min_margin  label        reached_decision  reached_post_decision
close_wide                 0.513    unavoidable true              true
low_mu_close               1.347    unavoidable true              true
late_reveal_high_speed     0.234    unavoidable true              true
drift_required_focus       0.567    unavoidable true              true
```

Rationale:

```text
all four rows reached decision and post-decision;
all four rows are non-aeb;
three rows are under 0.6 m margin;
the subset is source-consistent and suitable for first measured intervention
continuations.
```

This is not candidate materialization. It only admits designing a measured
intervention probe.

## Not Yet Eligible

These are not admissible for measured candidate materialization:

```text
T4 source families:
  still aeb_feasible and high-margin; not useful for T4 current/recent/older
  matching yet.

t5_near_boundary_warmup:
  still aeb_feasible and high-margin.

t5_boundary_axis_retarget:
  close_wide / low_mu_close / late_reveal_high_speed are still high-margin;
  drift_required_focus is near-boundary but collided before the decision step,
  so it is too hard for decision-step interventions.
```

Failure details:

```text
drift_required_focus reset_failure:
  t4_staged_warmup_capability
  t4_capability_step_temporal
  t4_actuator_delay_response
  t5_near_boundary_warmup

did_not_reach_decision_step:
  t5_boundary_axis_retarget drift_required_focus collided before decision.
```

## Candidate Materialization Verdict

```text
blocked
```

Reasons:

```text
no intervention continuation margins were measured;
no T4 current/recent/older distances were computed;
some retarget rows are too hard or failed sampling;
near-boundary scenario hardness alone is not self-identification evidence.
```

## Next Route

Next milestone:

```text
m1516-paper-route-decisive-history-t5-intervention-design
```

M1516 should design a bounded measured-intervention probe for the
`t5_high_speed_close_obstacle` subset only. It should measure normal,
reset-hidden, zero-response, zero-action-history, delayed-history, and
eventually wrong-history continuations where implementable.

M1516 should still block:

```text
candidate materialization;
training;
PPO;
promotion;
private holdout;
actor-input changes;
level3 self-ID claims.
```

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```
