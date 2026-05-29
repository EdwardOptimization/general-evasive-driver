# M1501 Paper-Route Decisive History Candidate Generation Design

## Summary

M1501 designs the no-training current-sim candidate-generation route that will
feed the M1500 T4/T5 decisive-history harness.

Decision:

```text
decisive_history_candidate_generation_design_admit_planner_implementation
```

This milestone does not run candidate generation, simulator replay, PPO,
training, promotion, private holdout, corpus export, actor-input changes, or
self-identification claims.

## Design Goal

The next evidence question is:

```text
Can current-sim public source families produce source-diverse T4/T5 candidates
where current frame and short recent windows are controlled, but older
command-response history changes terminal outcome or action choice?
```

M1501 only designs the route. It does not claim the candidates exist yet.

## Contract

Candidate generation may use privileged values for sampling and labels:

```text
hidden capability parameters;
terminal margins;
success/collision/road-departure labels;
intervention labels;
teacher/oracle action divergence diagnostics.
```

These values must not enter deployable actor input. Candidate artifacts must
carry:

```text
labels_enter_actor_input: false
actor_input_contract_changed: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
```

## Source Families

Use public development sources only.

### T4 Sources

T4 should prefer source families where older command-response evidence can be
different while current and recent windows are matched.

Initial sources:

```text
t4_staged_warmup_capability:
  Based on the staged warmup gate/source-wave route.
  Candidate configs include m1410, m1415, and m1419 style warmup source waves.
  Purpose: create older warmup evidence before obstacle reveal.

t4_capability_step_temporal:
  Based on capability-step and temporal sequence routes such as m991/m996/m998.
  Purpose: create hidden capability change or response evidence before the
  decision point.

t4_actuator_delay_response:
  Public current-sim variants with actuator delay/tau differences.
  Purpose: test whether older response latency evidence matters after current
  state is matched.
```

Current single-track proxy faults may be used for mining, but not described as
true one-wheel, tire-blowout, or half-shaft failures. Those belong to later
high-fidelity validation unless the simulator explicitly models asymmetry.

### T5 Sources

T5 should prefer source families where terminal outcome is close to a safety
constraint and can flip under wrong, delayed, reset, or current-tiled history.

Initial sources:

```text
t5_near_boundary_warmup:
  Based on clear near-boundary warmup retarget routes such as m1415/m1419.
  Purpose: combine older response evidence with terminal-boundary outcomes.

t5_high_speed_close_obstacle:
  Based on high-speed close-obstacle and extreme near-cliff routes such as
  m984/m985/m986.
  Purpose: stress late obstacle reveal, high speed, and narrow margin.

t5_boundary_axis_retarget:
  Based on v4 boundary-axis tracing and low-margin retarget routes.
  Purpose: find near-pass and near-fail brackets without treating old keys as
  the final proof surface.
```

M1502 should implement the source plan in a reusable format before any smoke.

## Public Seed Policy

Public development seeds:

```text
source_seed_base: 150100
source_seed_offsets: 0..31
geometry_seed_base: 150200
intervention_seed_base: 150300
eval_seed_base: 150400
```

M1502 implementation may use a smaller deterministic smoke subset, but the plan
must preserve these seed namespaces so later M1503/M1504 results are not
handpicked.

Private holdout seeds are not used in this branch until a public task family
stabilizes.

## Matching Tolerances

The T4/T5 harness thresholds from M1500 remain the public development defaults:

```text
max_current_distance: 0.05
max_recent_window_distance: 0.05
min_older_history_distance: 0.10
min_action_divergence: 0.03
min_margin_gap: 0.02
near_pass_margin_min: 0.0005
near_pass_margin_max: 0.03
```

M1502 should keep these as explicit config values, not hidden constants.

Distance definitions:

```text
current_distance:
  normalized distance over current ego response, actuator state, previous
  commands, and ego-frame road/obstacle geometry.

recent_window_distance:
  normalized distance over the most recent 13/25/50 frame command-response
  windows after optional tiling/matching.

older_history_distance:
  normalized distance over 0.5s-2.0s older command-response evidence, including
  command deltas, actuator response, acceleration/yaw response, and terminal
  warmup evidence.
```

These distances are diagnostics and selectors. They are not actor inputs.

## Intervention Plan

Every accepted public candidate must reserve enough metadata to evaluate:

```text
normal history;
current_tiled history;
reset recurrent state;
delayed history;
wrong older history from matched pair;
zero explicit response;
zero action-history fields.
```

T4 primary intervention:

```text
wrong older history under matched current/recent evidence.
```

T5 primary interventions:

```text
wrong older history;
delayed history;
reset;
current_tiled.
```

Reset-only evidence is never enough for level3 self-ID.

## Candidate Selection Gates

M1503 public smoke should report the following gates before any replay/training:

```text
generated_candidate_rows >= 64
accepted_rows >= 16
accepted_t4_rows >= 4
accepted_t5_rows >= 4
unique_seeds >= 4
unique_capability_pairs >= 4
unique_reveal_steps >= 4
unique_geometry_keys >= 4
max_source_share <= 0.35
labels_enter_actor_input == false
private_holdout_used == false
training/replay/PPO/promoted == false
```

These are smoke gates, not paper-level gates. The later source-diverse pilot
should raise the thresholds toward the M1499 design:

```text
accepted rows >= 80 before compact selection;
physical capability pairs >= 8;
seeds >= 5;
reveal/decision steps >= 4;
max single-source share <= 0.35;
mean wrong-history margin gap >= 0.02 or success-drop evidence present.
```

## Failure Classification

If candidate generation fails, classify it precisely:

```text
scenario_sampling_failure:
  sources do not produce matched current/recent but different older history.

metric_artifact:
  candidates pass distances but outcome gaps come from labels or bookkeeping.

contract_violation:
  actor input contract is changed or labels enter actor input.

private_holdout_contamination:
  private seeds are used for development repair.
```

If current-sim cannot honestly create T4/T5 candidates, the route should record
that as a simulator-scope negative result rather than forcing self-ID proof.

## Implementation Route

M1502 should implement no-training candidate-generation planner support:

```text
1. A source-plan schema for T4/T5 source families and seed namespaces.
2. A deterministic tiny smoke planner that produces candidate rows compatible
   with DecisiveHistoryTaskCandidate.
3. Configurable matching thresholds.
4. Source-diversity and acceptance summaries via the M1500 harness.
5. Focused tests that verify no training, replay, PPO, promotion, private
   holdout, corpus export, or actor-input change occurs.
```

M1502 should not yet use real simulator rollouts unless the implementation is
small and remains no-training. If current-sim hooks are needed, M1502 should
stop at planner scaffolding and route to an env-hook design.

M1503 should then run the first public no-training candidate-generation smoke.

## Guardrails

```text
candidate_generation_started: false
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
next: m1502-paper-route-decisive-history-candidate-planner-implementation
```
