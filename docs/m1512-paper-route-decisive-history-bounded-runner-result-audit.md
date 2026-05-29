# M1512 Paper-Route Decisive History Bounded Runner Result Audit

## Summary

M1512 audits the M1511 bounded fixed-policy source trace artifacts before any
candidate materialization.

Decision:

```text
bounded_runner_trace_audit_plumbing_pass_margin_uninformative_route_to_source_retarget
```

The runner plumbing passed, but the traces are not yet admissible for measured
T4/T5 candidate materialization. The next step should retarget source families
toward near-boundary and outcome-relevant traces, not train or export a corpus.

This milestone does not materialize candidates, export a training corpus, run
replay, run PPO, train, promote, use private holdout, change actor inputs, or
claim level3 self-identification.

## Audit Inputs

M1511 run:

```text
runs/m1511_decisive_history_bounded_runner_smoke
```

Input artifacts:

```text
summary.json
source_trace_rows.csv
source_snapshot_rows.csv
source_family_summary.csv
runner_guardrail_summary.csv
```

Checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

## Trace Quality Verdict

Trace plumbing verdict:

```text
pass
```

Evidence:

```text
spec_count: 6
source_family_count: 6
trace_row_count: 525
snapshot_row_count: 30
rollout_success_count: 6
rollout_failure_count: 0
source_families_reached_reveal: 6
source_families_reached_decision: 6
source_families_reached_post_decision: 6
guardrail_violation_count: 0
```

All six source families produced bounded trace rows through the reveal,
decision, and post-decision windows.

## Source-Family Audit

```text
source_family                         rows  terminal_reason     label           min_trace_margin
t4_staged_warmup_capability             96  max_rollout_steps  aeb_feasible    8.669
t4_capability_step_temporal             93  terminated         aeb_feasible   23.939
t4_actuator_delay_response              88  terminated         aeb_feasible   14.878
t5_near_boundary_warmup                 95  obstacle_completed aeb_feasible   17.119
t5_high_speed_close_obstacle            57  obstacle_completed drift_required  4.170
t5_boundary_axis_retarget               96  max_rollout_steps  aeb_feasible   17.061
```

The best source-family label diversity is the high-speed close-obstacle source,
which sampled `drift_required`. The other five source families sampled
`aeb_feasible`.

## Candidate Materialization Verdict

Materialization verdict:

```text
not_admissible_yet
```

Reasons:

```text
1. No wrong-history, delayed-history, current-tiled, reset, zero-response, or
   zero-action intervention continuation margins were measured.
2. T5 near-pass criteria are not close. The public default T5 near-pass band is
   0.0005 <= normal_margin <= 0.03, but the smallest observed trace margin is
   4.170.
3. T4 same-current / same-recent / different-older matching distances were not
   computed from paired source traces.
4. Most source families are currently too easy and AEB-feasible, so a first
   materialization attempt would mostly reject rows for margin or outcome
   irrelevance.
```

This is not a negative result for the whole direction. It says the M1511 runner
is working, but the current hook specs are source-trace plumbing configs rather
than decisive near-boundary configs.

## Guardrails

M1511 guardrails remained clean:

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

M1512 did not introduce new actor inputs or use any private holdout.

## Failure Taxonomy

```text
none:
  Runner mechanics passed; no reset or rollout failure occurred.

metric_artifact:
  Candidate materialization would be a metric artifact if done now, because
  trace reachability and high positive margins do not imply history necessity.

scenario_sampling_failure:
  Not a runtime failure in M1511, but the current source scenarios are not
  near-boundary enough for decisive-history materialization.
```

## Decision

The next route is source retargeting:

```text
m1513-paper-route-decisive-history-source-retarget-design
```

M1513 should design a bounded public retarget route that adjusts source-family
axes such as obstacle distance, obstacle width, reveal timing, speed, friction,
and lateral offset to produce near-boundary and label-diverse traces. It should
remain no-training, no-PPO, no-promotion, no-private-holdout, and should not
materialize candidates until the retargeted runner evidence is audited.
