# M718 Temporal Action-Response Mismatch Design

## Purpose

M718 designs the next no-training diagnostic after M717 pivoted away from more
current-model fault coverage.

The key question changes from:

```text
Can a different hidden fault history mislead the actor?
```

to:

```text
Does the actor depend on the temporal consistency between its own commands and
the sensed vehicle response?
```

This milestone is design-only:

```text
no implementation
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Background

M716 broadened extreme-fault coverage:

```text
scenario_count: 16896
matched_pair_count: 4096
reset_only_rows: 58
wrong_history_action_critical_rows: 0
result_class: cross_fault_reset_only
```

That means:

```text
resetting history can matter,
but cross-fault hidden injection still does not produce action/outcome-critical
wrong-history evidence.
```

M713 also showed:

```text
wrong-history feature directions are not actor-head-null;
164 rows cross the action threshold by alpha <= 4 under feature-line-search.
```

So M718 should test a different intervention axis before training:

```text
temporal action-response consistency
```

## Source Rows

M719 should build sources from three pools.

### Pool A: M716 Reset-Only Rows

Use:

```text
runs/m716_extreme_fault_coverage_refresh/reset_only_rows.csv
```

Purpose:

```text
rows where history clearly matters under reset, but cross-fault hidden did not
mislead the actor.
```

These rows are not source-positive yet. They are diagnostic candidates.

### Pool B: M713 Low-Alpha Actor-Head Rows

Use:

```text
runs/m713_actor_head_history_signal_coupling/row_actor_head_coupling.csv
```

Filter:

```text
variant == normal_vs_wrong_history
alpha_to_action_threshold <= 4
```

Purpose:

```text
rows where the actor head can respond to wrong-history feature directions if
the feature delta is amplified.
```

### Pool C: Sentinel Rows

Sample from M716 rejected rows:

```text
runs/m716_extreme_fault_coverage_refresh/rejected_rows.csv
```

Purpose:

```text
verify the diagnostic does not report source-positive rows everywhere.
```

## Required Implementation Boundary

M719 should rerun or reuse the scenario generator in memory rather than trying
to reconstruct hidden tensors from CSV files.

Reason:

```text
CSV artifacts store row metadata and rollout results, but not enough hidden
state and environment state to synthesize new temporal interventions reliably.
```

Implementation should reuse the existing M716 config and snapshot collection:

```text
configs/extreme_fault_coverage_v2_scenarios.json
```

but add new intervention variants before writing rows.

## Intervention Variants

M719 should evaluate at least these variants for each selected current snapshot:

```text
normal:
  current observation + current recurrent hidden.

reset_hidden:
  current observation + zero recurrent hidden.

cross_fault_wrong_hidden:
  current observation + matched cross-fault hidden, same as M716 baseline.

delayed_same_episode_hidden_k:
  current observation + same-scenario hidden from k steps earlier.
  k in {5, 10, 20} if available.

pre_fault_stale_hidden:
  for surprise faults, current post-fault observation + hidden from before fault
  activation.

severity_stale_hidden:
  current observation + same-family different-severity hidden when a matched
  visible state exists.

action_response_mismatch_hidden:
  hidden produced by replaying the response/history stream with mismatched
  previous-command fields or shifted command-response timing.
```

The last variant is the most important. It is closer to the human-driver claim:

```text
I know what I commanded, I sensed what the car did, and the mismatch changes my
belief about the car.
```

## Action-Response Mismatch Construction

M719 should implement the mismatch conservatively.

Preferred implementation:

```text
1. Record a short history window before the current snapshot.
2. Recompute recurrent hidden from the same observations with one controlled
   corruption:
   - shift previous steer/throttle/brake command fields by +1 or -1 frame;
   - zero previous command fields while keeping ego response;
   - keep previous commands but delay ego response fields by k frames;
   - pair high-command response history with low-command fields from another
     same-fault snippet.
3. Feed the resulting hidden into the unchanged actor at the current
   observation.
```

The actor observation at the decision step remains unchanged. Only the hidden
state is intervened on.

Forbidden shortcut:

```text
do not add fault labels, hidden parameters, slip, or oracle feasibility to the
actor input.
```

## Metrics

For each variant, write:

```text
first_steer
first_throttle
first_brake
first_action_distance_from_normal
trajectory_l2_mean
trajectory_l2_max
min_clearance_margin
margin_gap_from_normal
success_drop_from_normal
terminal_reason
```

Also write source metadata:

```text
source_pool
fault_family
fault_name
fault_severity
activation_step
intervention_type
history_offset_steps
match_distance
assigned_split
```

## Acceptance Criteria

M719 should classify results as:

```text
temporal_mismatch_positive:
  temporal/history-mismatch rows are action-critical or outcome-critical with
  source diversity.

temporal_reset_only:
  reset remains disruptive, but delayed/stale/mismatch variants do not pass.

temporal_neutral:
  even reset rows do not reproduce under this diagnostic.

temporal_artifact:
  results depend on impossible reconstruction, hidden tensor mismatch, or
  actor-input contract violation.
```

Positive thresholds:

```text
temporal_action_critical_rows >= 30
temporal_outcome_critical_rows >= 10
unique_fault_families >= 4
unique_seeds >= 20
normal_history_retention_pass == true
```

Row-level action-critical:

```text
normal succeeds or has nonnegative margin
variant first_action_l2 >= 0.015
```

Row-level outcome-critical:

```text
normal succeeds or has nonnegative margin
and one of:
  success_drop_from_normal == true
  margin_gap_from_normal >= 0.02
```

## Output Artifacts

M719 should write:

```text
runs/m719_temporal_action_response_mismatch/summary.json
runs/m719_temporal_action_response_mismatch/source_rows.csv
runs/m719_temporal_action_response_mismatch/intervention_rollouts.csv
runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv
runs/m719_temporal_action_response_mismatch/variant_summary.csv
runs/m719_temporal_action_response_mismatch/fault_family_summary.csv
runs/m719_temporal_action_response_mismatch/rejected_rows.csv
docs/m719-temporal-action-response-mismatch-implementation.md
```

## M719 Command

M719 should implement a new no-training runner:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_response_mismatch \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m719_temporal_action_response_mismatch
```

A smaller smoke is acceptable for debugging, but capability conclusions require
the full registered run or a separately registered scale change.

## Supported Claims

M718 supports:

```text
1. The next evidence axis should test temporal command-response consistency,
   not just more fault-family coverage.

2. M716 reset-only rows and M713 low-alpha rows are useful diagnostics but must
   not be called source-positive until temporal interventions pass action or
   outcome gates.

3. The actor-input contract can remain unchanged because all interventions are
   hidden-state interventions at the current observation.
```

## Falsified Claims

M718 falsifies:

```text
1. The only next choices are more current-model fault mining or immediate actor
   training.

2. Reset-hidden degradation is sufficient evidence for the self-ID claim.

3. A temporal intervention runner can be built by reading only the existing CSV
   row artifacts.
```

## Next Step

M719 should implement the no-training temporal intervention runner and classify
the result before any actor objective design, PPO, or model-fidelity upgrade.
