# M1527 Paper-Route Fresh Ambiguity Source-Mining Design

## Summary

M1527 designs a fresh ambiguity/source-mining route after M1526 closed the
current four-row T5 wrong-history route.

Decision:

```text
fresh_ambiguity_source_mining_design_admit_bounded_planner_implementation
```

The goal is to stop tuning the same T5 rows and instead search for public,
source-diverse scenarios where:

```text
scene context is similar;
current ego/actuator state is similar;
hidden dynamics or older command-response history imply a different preferred
action or terminal safety outcome.
```

This is design only. It does not materialize candidates, export a corpus, train,
run PPO, promote a checkpoint, use private holdout, change actor inputs, or
claim level3 self-identification.

## Why This Branch Exists

M1521-M1525 showed a clear split:

```text
timing/reset/zero-current interventions can reduce terminal margin;
donor hidden and donor response/action mismatch remained near-null on the
current four-row T5 subset.
```

The most likely explanation is not yet "history is useless." It may be that the
current subset does not contain enough ambiguity. The next branch should mine
fresh sources before changing objectives or training.

The core question is:

```text
Can public source generation find matched-current, matched-scene rows where
different hidden dynamics require meaningfully different evasive actions?
```

If not, that should become a simulator/task-design negative result, not a reason
to weaken the self-ID evidence standard.

## Source Families

Use public development sources only. Privileged simulator values may be used for
sampling, pairing, labels, and diagnostics, but never as actor inputs.

### Existing Decisive-History Families

Start from the source families that already have hook/spec scaffolding:

```text
t4_staged_warmup_capability
t4_capability_step_temporal
t4_actuator_delay_response
t5_near_boundary_warmup
t5_high_speed_close_obstacle
t5_boundary_axis_retarget
```

These sources remain useful, but the closed four-row T5 subset must not dominate
the new branch.

### Fresh Ambiguity Families

Add source plans that explicitly target hidden capability ambiguity:

```text
capability_step_down:
  sudden drop in mu, brake_scale, tire_stiffness, or steering authority before
  the emergency decision window.

capability_step_up:
  same scene and current state, but hidden capability improves or recovers after
  warmup, creating a different safe maneuver envelope.

actuator_delay_step:
  same obstacle geometry with fast vs slow steering/brake actuator response.

brake_fade_or_loss_proxy:
  lower brake_scale or delayed brake response after similar speed/current state.

drive_loss_proxy:
  lower drive authority or throttle response in scenarios where yaw recovery or
  post-maneuver stabilization matters.

grip_loss_proxy:
  symmetric low-mu or lateral-stiffness drop near reveal/decision.

late_reveal_boundary:
  obstacle appears late enough that stable braking/AES margins are small.

curved_boundary_obstacle:
  obstacle or free-space constraint in a turn, where yaw authority matters more
  than straight-line braking.
```

Current single-track dynamics must not be described as true one-wheel blowout,
split-mu, half-shaft failure, or individual-wheel drive failure unless the
simulator explicitly models those asymmetries. In this branch, those ideas are
allowed only as symmetric capability proxies. High-fidelity asymmetric faults
belong to a later simulator-validation branch.

## Pairing Target

The miner should search for pairs or small bundles with:

```text
same or near-same road/free-space/obstacle context;
same or near-same current ego response;
same or near-same actuator state and previous command;
different hidden capability or older command-response evidence;
different action preference, margin sensitivity, or recovery feasibility.
```

This separates two questions:

```text
Is the scene hard?
Is the scene ambiguous unless history/capability belief is known?
```

The new branch is only valuable if it finds the second kind.

## Matching Metrics

Every measured pair should report these distances.

### Scene Context Distance

Use only deployable context fields:

```text
road boundary points;
free-space/corridor geometry when available;
obstacle present/x/y/size;
obstacle rel_vx/rel_vy only as part of the current profile, with a flag if used.
```

Forbidden:

```text
obstacle label;
oracle feasibility;
TTC;
required clearance;
terminal margin;
success/collision labels;
hidden parameters.
```

### Current Ego Distance

Use current-frame deployable ego/action-response fields:

```text
vx, vy, yaw_rate;
ax, ay;
steer angle/rate;
throttle/brake actuator state;
previous steer/throttle/brake commands.
```

### Older Evidence Distance

Use older command-response windows before the current/recent window:

```text
command deltas;
actuator tracking errors;
acceleration/yaw response;
braking response;
steering/yaw response;
warmup or pre-emergency response evidence.
```

Older evidence should be different enough to make a recurrent belief useful.

## Action-Divergence Metrics

Fresh ambiguity requires action or outcome divergence. The implementation should
measure at least:

```text
first_action_l2;
steer_action_delta;
brake_action_delta;
throttle_action_delta;
prefix_action_l2 over 8/16/32 continuation steps;
terminal_margin_gap;
success_drop;
collision/road-departure/spin reason changes;
recovery_margin or post-obstacle stability change.
```

Useful ambiguity rows are those where the safe action is not merely delayed by a
few frames but materially different:

```text
earlier/harder braking vs steer-yaw maneuver;
stable AES vs drift-like yaw rotation;
brake-release/yaw recovery vs continued braking;
conservative avoidance vs mitigation when avoidance is impossible.
```

## Mining Pipeline

The follow-up implementation should be a bounded public planner/runner, for
example:

```text
src/autodrift/fresh_ambiguity_source_mining.py
```

Pipeline:

```text
1. Generate public source specs across old and fresh ambiguity families.
2. Run or dry-run bounded fixed-policy traces only after the spec layer passes.
3. Snapshot reveal, reveal_plus_4, decision_minus_8, decision, and
   post_decision_plus_8 windows.
4. Pair rows by scene/context and current ego distance.
5. Require hidden-capability or older-history diversity.
6. Measure action divergence and terminal-margin sensitivity.
7. Write accepted and rejected source-pair artifacts.
8. Do not materialize DecisiveHistoryTaskCandidate rows until a later audit
   admits it.
```

The first implementation may be metadata/spec-level plus tiny bounded smoke.
Measured rollout materialization must remain explicit and separately audited.

## Thresholds

Initial public development thresholds:

```text
max_scene_context_distance: 0.08
max_current_ego_distance: 0.08
max_recent_window_distance: 0.08
min_older_evidence_distance: 0.12
min_hidden_capability_distance: 0.15
min_first_action_l2: 0.04
min_prefix_action_l2: 0.08
min_terminal_margin_gap: 0.02
near_boundary_margin_min: -0.02
near_boundary_margin_max: 0.10
```

The thresholds are public-development gates. They can be tightened after the
branch proves source diversity, but they must not be silently adjusted after
seeing private holdout results.

## Diversity Gates

The first measured public source-mining smoke should target:

```text
generated_source_specs >= 96
attempted_source_families >= 8
accepted_pair_candidates >= 24
unique_source_families >= 6
unique_hidden_capability_pairs >= 8
unique_geometry_keys >= 8
unique_decision_steps >= 4
max_single_source_family_share <= 0.30
max_closed_t5_subset_share <= 0.20
proxy_fault_family_count >= 3
guardrail_violation_count == 0
```

For a smaller first implementation smoke, it is acceptable to use lower runtime
counts, but the artifacts must include the full target gates and explain which
ones were only dry checked.

## Artifact Contract

The implementation should write:

```text
fresh_ambiguity_source_specs.csv
fresh_ambiguity_trace_snapshots.csv
fresh_ambiguity_pair_candidates.csv
fresh_ambiguity_action_divergence.csv
fresh_ambiguity_rejected_pairs.csv
fresh_ambiguity_source_family_summary.csv
fresh_ambiguity_guardrail_summary.csv
summary.json
```

Every artifact should include:

```text
labels_enter_actor_input: false
actor_input_contract_changed: false
candidate_materialized: false
training_corpus_exported: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

## Acceptance and Stop Rules

The branch may proceed to a bounded implementation if M1527 design is complete.

The next measured smoke should stop and audit if:

```text
accepted_pair_candidates < 8;
max_closed_t5_subset_share > 0.20;
all accepted pairs come from one source family;
action divergence is below threshold despite near-boundary margins;
positive results come only from zero-current/reset controls;
candidate materialization would require actor-input or simulator-contract
changes.
```

If no fresh ambiguous rows are found, the correct next step is synthesis and
task/simulator redesign, not training.

## Failure Taxonomy

Use:

```text
scenario_sampling_failure:
  source families do not produce matched-current matched-scene ambiguous rows.

metric_artifact:
  divergence comes from bookkeeping, labels, impossible matching, or zeroing
  current response rather than meaningful history/capability ambiguity.

contract_violation:
  labels, hidden parameters, TTC, required clearance, or oracle feasibility
  enter actor input.

private_holdout_contamination:
  private scenarios are used to repair public source mining.
```

## Next Milestone

Next:

```text
m1528-paper-route-fresh-ambiguity-source-planner-implementation
```

M1528 should implement the source-spec and pair-candidate planner with a bounded
public smoke. It should still block candidate materialization, training corpus
export, replay, PPO, promotion, private holdout, actor-input changes, and
self-identification claims.
