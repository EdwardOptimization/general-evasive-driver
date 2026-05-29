# M1514 Paper-Route Decisive History Source Retarget Implementation

## Summary

M1514 implements the bounded public source-retarget smoke designed in M1513.

Decision:

```text
decisive_history_source_retarget_smoke_pass_route_to_retarget_audit
```

The retarget smoke moved the source traces much closer to the boundary, but it
also produced reset failures and one pre-decision collision. The next step is a
retarget result audit, not candidate materialization or training.

This milestone does not materialize candidates, export a training corpus, run
replay, run PPO, train, promote, use private holdout, change actor inputs, or
claim level3 self-identification.

## Implementation

New code:

```text
src/autodrift/decisive_history_source_retarget.py
tests/test_decisive_history_source_retarget.py
```

The implementation builds deterministic retarget modes on top of the M1505
hook specs and reuses the M1511 bounded runner.

Retarget modes used in the smoke:

```text
close_wide
low_mu_close
late_reveal_high_speed
drift_required_focus
```

The mode `wide_low_brake` is defined but not used in this first capped smoke.

## Smoke Command

```bash
PYTHONPATH=src python -m autodrift.decisive_history_source_retarget \
  --run-dir runs/m1514_decisive_history_source_retarget_smoke \
  --max-rollout-steps 128 \
  --seed-count 1 \
  --source-family-cap 4 \
  --device cpu
```

## Result

Run directory:

```text
runs/m1514_decisive_history_source_retarget_smoke
```

Summary:

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
guardrail_violation_count: 0
```

Margin movement:

```text
M1511 global min margin: 4.170293752717424
M1514 global min margin: -0.042059208331689746
near_boundary_proxy_count: 39
non_aeb_label_source_family_count: 2
```

Per-source minimum margins:

```text
source_family                     M1511_min   M1514_min   reduction
t4_staged_warmup_capability          8.669       2.254       6.415
t4_capability_step_temporal         23.939      11.733      12.206
t4_actuator_delay_response          14.878       6.293       8.585
t5_near_boundary_warmup             17.119       8.365       8.753
t5_high_speed_close_obstacle         4.170       0.234       3.936
t5_boundary_axis_retarget           17.061      -0.042      17.103
```

Label movement:

```text
t5_high_speed_close_obstacle: unavoidable
t5_boundary_axis_retarget: aeb_feasible + unavoidable
other source families: aeb_feasible
```

Failures:

```text
reset_failure:
  drift_required_focus failed to sample matching scenarios for:
    t4_staged_warmup_capability
    t4_capability_step_temporal
    t4_actuator_delay_response
    t5_near_boundary_warmup

did_not_reach_decision_step:
  t5_boundary_axis_retarget drift_required_focus collided before decision.
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_decisive_history_source_retarget.py -q
5 passed
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

## Interpretation

M1514 is positive retarget evidence:

```text
retargeting can move the public fixed-policy traces toward near-boundary and
non-AEB scenarios under bounded caps.
```

It is not yet candidate evidence:

```text
no intervention continuations were measured;
no T4 current/recent/older matching distances were computed;
one retarget is too hard before the decision step;
four drift_required_focus specs failed sampling.
```

The next step must audit which source families and modes are suitable for
measured intervention design, and which need retarget repair.

## Next

```text
m1515-paper-route-decisive-history-source-retarget-result-audit
```
