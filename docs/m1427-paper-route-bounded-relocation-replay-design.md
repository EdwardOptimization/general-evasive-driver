# M1427 Paper-Route Bounded Relocation Replay Design

## Summary

M1427 designs the bounded no-training replay probe admitted by M1426.

Decision:

```text
bounded_relocation_replay_design_admit_implementation
```

M1427 does not implement the replay tool, run replay, train, run PPO, promote,
use private holdout, export a training corpus, or change actor inputs.

## Problem

M1425 produced:

```text
candidate_rows: 256
outcome_pressure_rows: 846
history_positive_rows: 0
```

The negative is meaningful but not final. M1425 used a shared-margin proxy:

```text
proxy_normal_margin = normal_margin - pressure
proxy_variant_margin = variant_margin - pressure
```

That proxy preserves `margin_gap`, so it cannot discover cases where obstacle
relocation changes the geometry of two different closed-loop trajectories in
different ways.

## Design Goal

Build a no-training replay probe that answers:

```text
When the same matched-current source row is replayed under bounded relocated
obstacle geometry, do history variants become terminal-margin-sensitive in
actual rollout?
```

This is still public diagnostic evidence only. A positive replay result would
admit a later audit or corpus design; it would not directly admit training.

## Inputs

The replay probe should consume:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

config:
  configs/m1419_warmup_gate_invasiveness_retune_source_wave.json

candidate rows:
  runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv
```

Each candidate row supplies:

```text
seed
preferred_fault
wrong_fault
reveal_step
variant
body_longitudinal_offset
body_lateral_offset
half_width_inflation
matched_current_pass / bucketed_current_pass
capability_pair
preferred_reveal_bucket
```

## Mechanics

For each selected row:

```text
1. Reconstruct preferred and wrong traces with collect_fault_trace_window.
2. Build warmup variant hiddens with build_warmup_variant_hiddens.
3. Convert the preferred current TracePoint to a relocatable snapshot.
4. Compute the current active obstacle body geometry from the preferred snapshot.
5. Apply bounded relocation:
     relocated_x = max(min_body_x, source_body_x + body_longitudinal_offset)
     relocated_y = source_body_y + body_lateral_offset
     relocated_half_width = source_half_width + half_width_inflation
6. Replay normal first under relocated geometry.
7. Replay the requested history variant under the same relocated geometry.
8. Replay reset_hidden and zero_current_response controls separately.
9. Write actual rollout rows and summaries.
```

Implementation can reuse these existing pieces:

```text
collect_fault_trace_window
build_warmup_variant_hiddens
replay_probe_variant
TracePoint
OutcomeSnapshot
relocate_outcome_snapshot
response_feature_dim_for_model
```

If the relocation helper returns an `OutcomeSnapshot`, the implementation should
convert it back to a `TracePoint` with the same seed, fault, step, relocated
observation, hidden, env, and info before using `replay_probe_variant`.

## Candidate Selection

First implementation should be small and deterministic:

```text
max_candidate_rows: 128
per_capability_pair_cap: 12
prefer proxy_preferred_normal_margin rows
prefer rows with larger sequence_action_l2_mean
prefer rows with nonnegative original margin_gap
prefer source diversity across seeds, capability pairs, and reveal buckets
```

Controls:

```text
reset_hidden
zero_current_response
```

Controls must be replayed for diagnostics but cannot count as history-positive.

History variants:

```text
delayed_warmup_history_8
delayed_warmup_history_16
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
warmup_removed
warmup_shortened_8
```

Only these can enter actual `history_positive_rows`.

## Actual Replay Criteria

A history row is positive only if actual replay satisfies:

```text
normal_success == true
normal_margin >= 0.0
sequence_action_l2_mean >= 0.025
and (
  success_drop == true
  or margin_gap >= 0.02
)
variant in history variants
```

Proxy fields may be copied for traceability, but they cannot satisfy the gate.

## First Public Replay Gates

The first no-training run after implementation should use conservative gates:

```text
selected_candidate_rows >= 64
actual_replay_rows >= 192
history_positive_rows >= 8
history_positive_unique_source_seeds >= 3
history_positive_unique_capability_pairs >= 3
history_positive_unique_reveal_buckets >= 2
control_positive_rows reported separately
normal_failed_rows <= 40% of actual_replay_rows
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
training_corpus_exported == false
actor_input_contract_changed == false
```

These gates are intentionally diagnostic, not promotion or paper-level gates.

## Required Outputs

The replay implementation should write:

```text
summary.json
selected_candidate_rows.csv
actual_replay_rows.csv
history_positive_rows.csv
control_positive_rows.csv
variant_summary.csv
source_diversity_summary.csv
relocation_summary.csv
rejected_rows.csv
```

The summary must report:

```text
selected candidates
actual replay rows
normal failed rows
history positive rows
control positive rows
success drops
margin gap distribution
source diversity
relocation bounds used
actor/checkpoint contract flags
```

## Guardrails

M1427 and the next implementation must not:

```text
train
run PPO
promote
use private holdout
export training corpus
change actor inputs
count proxy rows as replay evidence
count reset or zero-current as history-positive
lower M1425 thresholds after seeing the result
```

Relocation is allowed only as scenario generation. It must not become actor
input.

## Next

Next milestone:

```text
m1428-paper-route-bounded-relocation-replay-implementation
```

M1428 should implement the replay tool and focused tests only. It should not run
the public replay probe until a separate manifest is active.
