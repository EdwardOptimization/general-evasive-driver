# M1507 Paper-Route Decisive History Rollout Candidate Design

## Summary

M1507 designs how reset-viable M1506 env-hook specs become measured T4/T5
rollout candidates.

Decision:

```text
decisive_history_rollout_candidate_design_admit_probe_implementation
```

This milestone is design only. It does not run rollout candidate generation,
replay, PPO, training, promotion, private holdout, corpus export, actor-input
changes, candidate materialization, or level3 self-ID claims.

## Why This Design Exists

M1506 proved only reset/runtime viability:

```text
AutoDriftEnv(spec.env_config).reset(seed=spec.seed) works for all six source
families.
```

That is plumbing evidence, not self-ID evidence. The next branch needs measured
rollout evidence:

```text
same-current / same-recent / different-older-history;
terminal margins under normal and history-intervention variants;
candidate rows materialized only from measured rollout diagnostics.
```

## Fixed Inputs

The rollout candidate probe should use public development inputs only:

```text
hook specs:
  from M1505/M1506 `default_hook_specs`

policy:
  fixed public-gate base only, initially M1362 alpha 0.1
  no training, no PPO, no promotion

seeds:
  M1501 public seed namespaces only
  no private holdout
```

The probe may use privileged simulator `info` fields for labels, filtering, and
diagnostics. It must not append those fields to actor observation.

## Pipeline

The implementation should be a separate no-training module, for example:

```text
src/autodrift/decisive_history_rollout_candidates.py
```

Pipeline:

```text
1. load hook specs
2. run fixed-policy source rollouts
3. collect trace windows around reveal/decision steps
4. compute current/recent/older-history distances
5. form T4 same-current same-recent older-different pairs
6. form T5 near-terminal-boundary rows
7. run bounded intervention continuations
8. materialize DecisiveHistoryTaskCandidate rows only if measured gates pass
9. write rejected rows and summaries for all failures
```

## Trace Windows

Every source rollout should emit a compact trace schema:

```text
trace_id
source_family
task_family
seed
candidate_id
step
observation_0..observation_71
action_steer
action_throttle
action_brake
hidden_checksum or hidden_path
info subset:
  obstacle_label
  obstacle_distance
  obstacle_lateral_offset
  active_obstacle_body_x/y
  min_clearance_margin
  collision
  obstacle_completed
  warmup_gate_visible
  warmup_gate_clearance_margin
  friction_step_at
  friction_step_applied
  mu / capability fields for diagnostics only
```

The actor still receives only the normal P0 observation and hidden state.
Privileged fields stay in metadata.

## Matching Metrics

Candidate materialization requires measured distances, not source-plan
placeholders.

### Current Distance

Computed at the decision step over deployable current-frame features:

```text
ego response;
actuator state;
previous commands;
ego-frame road/free-space/obstacle geometry.
```

Forbidden in current-distance feature vector:

```text
mu, capability labels, obstacle label, success, collision, terminal margin,
TTC, required clearance, oracle feasibility.
```

### Recent-Window Distance

Computed over short windows ending at the decision step:

```text
13 frames;
25 frames;
50 frames if available.
```

The first public implementation may select one window, but the artifact must
record which one was used:

```text
recent_window_length
recent_window_distance
recent_window_feature_schema
```

### Older-History Distance

Computed over the older command-response window before the recent window:

```text
commands;
actuator state;
vx/vy/yaw_rate;
ax/ay;
steer rate;
warmup gate response;
friction-step response diagnostics.
```

Older history should be materially different:

```text
older_history_distance >= M1500 min_older_history_distance
```

## T4 Candidate Rule

T4 materializes only when:

```text
current_distance <= max_current_distance
recent_window_distance <= max_recent_window_distance
older_history_distance >= min_older_history_distance
action_divergence >= min_action_divergence
wrong-history or delayed-history intervention creates margin gap >= min_margin_gap
or creates a success drop
labels_enter_actor_input == false
```

The decisive test is not reset alone. The strongest T4 row is:

```text
same current;
same recent;
wrong older history from a matched source;
normal history does better than wrong history.
```

## T5 Candidate Rule

T5 materializes only when:

```text
normal terminal margin is inside near-pass band;
at least one history intervention reduces margin by min_margin_gap or crosses
  success/collision boundary;
source family and geometry remain public;
labels do not enter actor input.
```

Useful T5 variants:

```text
wrong older history;
delayed history;
current-tiled history;
reset hidden;
zero current response;
zero action history.
```

T5 may include unavoidable-collision mitigation later, but first implementation
should focus on near-pass/near-fail clearance margin.

## Intervention Continuations

Use bounded continuation horizons:

```text
max_continuation_steps: 64 initially
stop on termination/truncation/obstacle_completed
no training or PPO
```

Required variants:

```text
normal
reset_hidden
delayed_history
wrong_history
current_tiled_history
zero_current_response
zero_action_history
```

Each intervention row must report:

```text
variant
terminal_success
terminal_reason
collision
obstacle_completed
min_clearance_margin
first_action
first_action_l2_vs_normal
prefix_action_l2_vs_normal
margin_gap_from_normal
success_drop_from_normal
```

## Artifact Contract

The first implementation should write:

```text
source_trace_rows.csv
decision_snapshot_rows.csv
pair_candidate_rows.csv
intervention_rows.csv
materialized_candidate_rows.csv
rejected_candidate_rows.csv
source_family_summary.csv
matching_summary.csv
intervention_summary.csv
summary.json
```

`materialized_candidate_rows.csv` may be empty. An empty output is a valid
negative result if rejection reasons are complete.

## Public Smoke Gates

The first implementation smoke should be small and public:

```text
source families attempted >= 6
reset/runtime failures == 0
decision snapshots >= 6
intervention rows may be zero in implementation smoke
materialized candidates may be zero in implementation smoke
labels_enter_actor_input == false
private_holdout_used == false
training/replay/PPO/promoted == false
candidate_materialized_from_reset_only == false
```

The later candidate-generation smoke should require measured candidate evidence:

```text
accepted rows >= 4
accepted T4 rows >= 1
accepted T5 rows >= 1
unique source families >= 2
unique seeds >= 2
all materialized candidates have measured intervention margins
```

## Failure Taxonomy

Use structured rejection reasons:

```text
scenario_sampling_failure:
  no usable source rollout or obstacle/runtime failure.

current_match_failure:
  current distance too large.

recent_match_failure:
  recent window distance too large.

older_history_not_distinct:
  older history distance too small.

action_not_divergent:
  action divergence too small.

terminal_margin_not_decisive:
  intervention does not change terminal margin or success enough.

contract_violation:
  forbidden labels or hidden parameters enter actor input.

metric_artifact:
  candidate passes due to bookkeeping or reset-only evidence rather than
  measured rollout/intervention data.
```

## Guardrails

The rollout candidate probe must report:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
candidate_materialized_from_reset_only: false
level3_self_id_claim_made: false
```

Candidate generation may use a fixed policy checkpoint to collect behavior, but
that is still evaluation/probing, not training or promotion.

## M1508 Implementation Scope

M1508 should implement only the scaffolding and a tiny public implementation
smoke:

```text
1. trace/distance/intervention dataclasses;
2. source rollout runner using fixed public policy;
3. candidate/rejection schema writers;
4. distance helper tests on synthetic arrays;
5. no-training public smoke that may produce zero materialized candidates.
```

If policy-runner integration is too large, M1508 may implement schemas and
synthetic tests first, then route to a bounded runner milestone. It should not
export a training corpus.

## Next Route

Route to:

```text
m1508-paper-route-decisive-history-rollout-candidate-probe-implementation
```
