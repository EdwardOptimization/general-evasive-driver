# M460 Outcome-Critical Matched-Current Selector Design

## Purpose

M459 found a useful matched-current response/action ambiguity surface, but the
continuation outcome gate was weak:

- `503` accepted matched-current pairs;
- reset and zero-current interventions strongly changed actions;
- wrong matched history moved toward the right-pair action in `0.630252` of
  weighted rows;
- continuation success-drop was `0.0` for every intervention.

The problem is the selector. M459 selected pairs by future response-envelope
target z-delta, then checked outcomes afterward. M460 changes the selection
objective: a row is useful only if it is matched-current and outcome-critical
under at least one history intervention.

This milestone is design only. It does not train or promote a checkpoint.

## Selector Contract

The selector must preserve the human-view contract:

- actor inputs remain P0 72-dim no-wheel human-view observations;
- hidden params and oracle labels are used only for logging/mining;
- no hidden params, labels, TTC, required clearance, reference trajectory, or
  feasibility answers enter the actor.

The selector operates on rollout snapshots and matched-current pair rows. It can
use privileged simulator fields for offline scoring, but selected rows must be
replayable through the deployable actor interface.

## Pipeline

### Stage 1: Matched-Current Candidate Pool

Start from `matched_current_response_ambiguity` or an equivalent collector:

```text
match_feature_set: current_response_context
probe_seeds: >= 3 seed windows
episodes: >= 40 per seed window
sample_stride: 3
max_samples: >= 1200 per seed
nearest_k: 12
max_visible_quantile: 0.05
min_target_z_delta: 0.75-1.0
```

Keep the existing source-diverse caps:

```text
max_pairs_per_physical_pair: 1
max_pairs_per_left_step: 20
max_pairs_per_source_obstacle_bucket: 40
obstacle_distance_bucket_width: 5.0
obstacle_lateral_bucket_width: 1.0
```

The matched-current constraints are hard. Do not accept an outcome-critical row
if current response/context similarity is poor.

### Stage 2: Action Intervention Prefilter

For each pair, evaluate:

```text
normal
reset_hidden
delayed_history
wrong_matched_history
zero_current_response
zero_action_history
```

Action prefilter metrics:

```text
normal_pair_action_distance
intervention_action_distance
variant_to_right_action_distance
wrong_history_closer_to_right_action
first-action component deltas
```

Use action signals as a prefilter, not proof. Suggested thresholds:

```text
normal_pair_action_distance <= 0.08
any_intervention_action_distance >= 0.05
wrong_history_closer_to_right_action == true for wrong-history rows
```

If these thresholds are too strict, relax only after documenting the accepted
pair counts and source diversity.

### Stage 3: Outcome Continuation Score

Run continuation rollouts from the matched-current snapshot for each
intervention. Compute:

```text
normal_success
variant_success
success_drop = normal_success and not variant_success
normal_margin
variant_margin
margin_gap = normal_margin - variant_margin
return_gap = normal_return - variant_return
collision_gap
obstacle_completion_gap
trajectory_action_distance
```

The primary outcome-critical conditions are:

```text
normal_success == true
and (
  success_drop == true
  or margin_gap >= 0.02
  or collision_gap > 0
  or obstacle_completion_gap > 0
)
```

Secondary diagnostic conditions can be recorded but should not be sufficient for
proof:

```text
return_gap >= 2.0
trajectory_action_distance >= 0.10
first_action_distance >= 0.05
```

This distinction is important. M459 already showed action/trajectory changes
without outcome degradation, so M461 must not select action-only rows as
outcome-critical.

### Stage 4: Outcome-Critical Score

For ranking, use a lexicographic score:

```text
score tuple =
  success_drop
  clipped_positive_margin_gap
  collision_gap
  obstacle_completion_gap
  source_diversity_bonus
  wrong_history_closer_to_right_action
  action_distance
  target_z_delta
  -visible_distance
```

Where:

```text
clipped_positive_margin_gap = min(max(margin_gap, 0.0), 0.50)
```

Do not let `target_z_delta` outrank outcome terms. Future response-envelope
difference is useful only after outcome sensitivity is established.

### Stage 5: Compact Corpus Selection

Export:

```text
candidates.csv
compact_corpus.csv
summary.json
variant_summary.csv
```

Compact corpus rules:

```text
target accepted rows: 32-96
min seed windows: 3
min obstacle labels: 2
min mu buckets: 2
max per physical pair: 1
max per seed window: 16
max per obstacle bucket: 8
must include at least one true outcome-critical intervention class
```

Preferred intervention classes:

```text
wrong_history_outcome_critical
reset_hidden_outcome_critical
zero_current_outcome_critical
delayed_history_outcome_critical
```

Rows that only pass action-distance thresholds should be kept as diagnostics,
not in the compact outcome-critical corpus.

## Pass And Redirect Criteria

M461 passes if:

```text
accepted outcome-critical rows >= 16
compact corpus rows >= 16
source windows >= 3
obstacle labels >= 2
at least one intervention has success_drop rows or mean margin_gap >= 0.02
no actor contract change
no checkpoint promotion
```

If accepted outcome-critical rows are between `1` and `15`:

```text
archive as sparse evidence,
admit a task-family redesign or larger mining run,
do not train.
```

If accepted rows are `0`:

```text
reject M457 late-reveal as an outcome-critical self-ID task family,
redesign the environment with longer warm-up, active probing, or tighter
matched-current relocation.
```

If action-distance rows are many but outcome rows remain zero:

```text
classify as action_only_surface,
do not admit wrong-history proof gate,
do not train PPO.
```

## M461 Implementation Plan

M461 should implement or extend a CLI, likely:

```text
autodrift.outcome_critical_matched_current_selector
```

Inputs:

```text
--env-config
--checkpoint-policy
--pairs-csv
--delay-steps
--max-continuation-steps
--min-margin-gap
--min-action-distance
--max-selected-per-seed
--max-selected-per-obstacle-bucket
--run-dir
```

It can reuse:

- `matched_history_intervention_gate` action-distance logic;
- `matched_history_outcome_gate` continuation logic;
- source-diverse selection helpers from `matched_current_response_ambiguity`;
- CSV/JSON artifact writers.

Focused tests should cover:

- margin-gap scoring;
- success-drop scoring;
- action-only rows are not accepted as outcome-critical;
- source-diverse compact selection caps;
- no-update smoke with empty and non-empty candidate rows.

M461 should not train or promote. It should only produce an outcome-critical
corpus or reject the task family with a structured negative result.

## Decision

M460 admits:

```text
m461-outcome-critical-matched-current-selector-implementation
```

No checkpoint is promoted.
