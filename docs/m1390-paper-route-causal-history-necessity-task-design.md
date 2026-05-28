# M1390 Paper-Route Causal History-Necessity Task Design

## Summary

M1390 designs the next paper-route task/gate family after M1389 found that
standard fixed-budget profile comparison does not expose history necessity.

Decision:

```text
causal_history_necessity_task_design_admit_source_miner_implementation
```

M1390 performs no training, PPO, new evaluation, promotion, private holdout,
corpus export, actor-input expansion, profile-ranking claim, paper-level claim,
or level3 self-identification claim.

## Blocker

M1388/M1389 established this negative result:

```text
L2 finite-window profiles are near parity with current-tiled controls.
L3 online GRU underperforms corrected reset-control.
Blind fixed-budget profile scaling is unlikely to prove history necessity.
```

The next evidence unit must therefore stop asking:

```text
Which temporal architecture has higher aggregate return?
```

and ask the causal question directly:

```text
When current observation and immediate scene are matched, does older
command-response history change the action or closed-loop outcome?
```

## Design Principle

The core failure mode to eliminate is current-frame substitution. A task or
gate can only count as history-necessity evidence if current ego response,
current actuator state, current previous-command slots, and current scene
geometry are not enough to explain the result.

M1390 therefore requires all later causal-history gates to include:

```text
1. matched-current or same-current controls;
2. current-tiled controls where finite-window profiles are compared;
3. corrected reset-control for online recurrent policies;
4. delayed, wrong, or older-history interventions;
5. outcome-grounded metrics, not action distance alone;
6. source-diversity thresholds before corpus export or training.
```

## Task Families

### Task A: Matched-Current Older-History Ambiguity

Purpose:

```text
Find states that look the same now but arrived through different
command-response histories.
```

Candidate construction:

```text
source: public capability-step or obstacle avoidance rollouts
match: current P0 human-view observation, current actuator state, current
       previous-command slots, road geometry, obstacle geometry
diverge: older response/action history before the recent window
```

Required controls:

```text
normal_history
reset_hidden
delayed_history_4 / 8 / 12
wrong_same_current_history
same_recent_window_wrong_older_history
zero_action_history
zero_current_response_positive_control
```

This is the primary task family because it makes current frame and immediate
recent frame information insufficient by construction.

### Task B: Warmup-Latched Capability Identification

Purpose:

```text
Give the driver a harmless warmup response history before the emergency, then
make the emergency current frame ambiguous.
```

Episode sketch:

```text
0.0s to 1.0s: mild steering/braking/throttle warmup under randomized hidden
              capability.
1.0s onward: obstacle or boundary-critical event appears.
current frame at reveal: matched or bucketed across hidden capability families.
```

The useful history is not the current obstacle geometry. It is the earlier
command-response evidence about braking authority, yaw authority, actuator
delay, and lateral grip.

Allowed hidden-capability proxies in the current simulator:

```text
mu / friction schedules for simulator only
brake_scale
drive_scale
tire_stiffness_scale
steering actuator lag
yaw/lateral authority proxy faults
capability-step drops
```

These remain simulator labels for sampling, logging, teacher diagnostics, or
source mining. They must not enter actor input.

### Task C: Tail-Aligned Critical-Window Wrong History

Purpose:

```text
Test whether wrong belief at the critical instant changes outcome when the
wrong history is temporally aligned rather than stale.
```

Candidate construction:

```text
left_tail_snapshot  = left rollout at source_step + S
right_tail_snapshot = right rollout at matched source_step + S
wrong_tail_once     = inject right hidden only for first tail action
wrong_tail_hold     = diagnostic clamped variant, not natural proof
S                   = 4, 8, 12, 16
```

This is a continuation of the earlier critical-window lesson: one-shot wrong
history can be too easy to recover from unless the injection is close to the
terminal boundary and tail-aligned.

### Task D: Source-Rich Temporal Sequence Diagnostics

Purpose:

```text
Reuse M1377/M1379 temporal positives, but fix the seed-thin limitation before
corpus export or training.
```

M1379 evidence:

```text
accepted_temporal_sequence_rows: 224
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 10
accepted_cross_fault_sequence_rows: 0
```

M1390 interpretation:

```text
temporal rows are useful public diagnostics;
seed diversity is still below threshold;
cross-fault self-identification is unsupported;
no training or corpus export should use these rows without a source-diversity
refresh.
```

## Matching Requirements

A candidate row is eligible only if all visible current-frame quantities are
matched closely enough that a memoryless or current-tiled policy cannot explain
the effect by obvious current-state differences.

Initial public thresholds:

```text
ego_response_l2 <= 0.08
actuator_state_l2 <= 0.05
previous_command_l2 <= 0.05
scene_context_l2 <= 0.10
obstacle_slot_presence_match == true
obstacle_position_l2 <= 0.10
road_boundary_l2 <= 0.12
```

For same-recent-window tests:

```text
recent_window_length: 1 or 2 actor frames
recent_window_l2 <= 0.10
older_history_l2 >= 0.20
or hidden-capability family differs
```

These thresholds are public starting points. They may be audited after a smoke,
but must not be relaxed after seeing private holdout.

## Intervention Requirements

Each implementation should record the following variants when applicable:

```text
normal
reset_hidden
delayed_history_4
delayed_history_8
delayed_history_12
wrong_same_current_history
same_recent_wrong_older_history
tail_aligned_wrong_once
tail_aligned_wrong_hold_4_diagnostic
zero_action_history
zero_current_response_positive_control
```

Interpretation order:

```text
1. normal must be successful or safely near-boundary.
2. wrong/delayed/older-history variants are the self-ID-relevant tests.
3. zero_current_response is a positive control for current feedback dependence.
4. reset_hidden is useful but can be weak because the current frame is still
   available.
5. held/clamped variants are diagnostic unless a natural one-shot or delayed
   variant also produces outcome degradation.
```

## Outcome Metrics

Action distance is a screen, not proof. M1390 requires outcome-grounded metrics:

```text
success_drop
collision_gap
road_departure_gap
obstacle_completion_drop
min_clearance_margin_gap
terminal_margin_gap
return_gap
recovery_time_gap
first_action_l2
sequence_action_l2
termination_reason_histogram
```

A row is causal-history positive if:

```text
current/recent matching passes;
normal rollout succeeds or is near-boundary with positive margin;
history-only intervention causes success drop, collision gap, completion drop,
or min_clearance_margin_gap >= 0.02;
first_action_l2 >= 0.015 or sequence_action_l2 >= 0.025;
the effect is not counted solely from zero_current_response;
the row passes source-diversity caps.
```

## Source-Diversity Thresholds

Structural smoke threshold:

```text
candidate_rows >= 200
matched_current_pairs >= 80
unique_source_seeds >= 12
unique_fault_or_capability_pairs >= 6
normal_failed_rows reported separately
all metrics finite
```

Public diagnostic positive threshold:

```text
causal_history_positive_rows >= 48
accepted_seeds >= 12
accepted_fault_or_capability_pairs >= 8
accepted_scenario_buckets >= 4
accepted_intervention_families >= 2
max_single_seed_share <= 0.25
max_single_fault_pair_share <= 0.35
```

Corpus-export threshold:

```text
causal_history_positive_rows >= 128
accepted_seeds >= 24
accepted_fault_or_capability_pairs >= 10
accepted_scenario_buckets >= 6
train_eval_split_by_seed_possible == true
private_holdout_not_used == true
```

If rows and fault pairs pass but seed diversity fails, the result is
temporal-positive seed-thin evidence. It may guide source redesign, not
training.

## Failure Taxonomy

Pre-registered classifications:

```text
no_matched_current_surface:
  matching thresholds produce too few source-diverse pairs.
  route to broader source sampling or task redesign.

current_feedback_only_signal:
  zero_current_response or zero_action_history is sensitive, but wrong/delayed
  older history is not.
  route to stronger same-current warmup task.

action_only_history_signal:
  wrong/delayed history changes actions but not outcomes.
  route to near-boundary source mining.

source_narrow_history_signal:
  outcome signal exists but is dominated by a few seeds or fault pairs.
  route to source-diversity refresh.

history_positive_public_diagnostic:
  source-diverse history-only interventions degrade outcome on public rows.
  route to corpus design, not direct training.

metric_artifact:
  positive result disappears under current-tiled, reset-control, or
  same-recent-window controls.
  route to gate repair before any claim.
```

## Claim Boundary

Allowed after a passing public diagnostic:

```text
level2 history-encoded reactive evidence on public diagnostic rows;
matched-current or same-current history intervention changes outcome;
source-diverse public task/gate is ready for corpus design.
```

Forbidden:

```text
level3 anticipatory self-identification;
private-holdout or paper-level evidence;
architecture ranking;
checkpoint promotion;
real-vehicle readiness;
true per-wheel fault or high-fidelity dynamics claims;
training from public rows without a separate corpus design.
```

Level3 remains reserved for later evidence where the policy uses pre-emergency
history to choose a safer action before current-frame evidence alone can reveal
the hidden capability.

## Next Route

Admit:

```text
m1391-paper-route-causal-history-source-miner-implementation
```

M1391 should implement a no-training public source miner/smoke that materializes
Task A candidates first:

```text
input:  M1362 public-base checkpoint and public M1375/M1379 source artifacts
output: matched-current older-history candidate rows plus intervention plan
checks: finite metrics, matching-distance histograms, source-diversity summary,
        and guardrails showing no training/PPO/private/promote/input changes
```

M1391 should not export a training corpus. It should only prove that the causal
history-necessity source selection path can be materialized cleanly.

## Decision

```text
causal_history_necessity_task_design_admit_source_miner_implementation
```

Next:

```text
m1391-paper-route-causal-history-source-miner-implementation
```
