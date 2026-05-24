# M615 Sequence Source Expansion Design

## Purpose

M615 designs the next no-training step after M614 audited the M613
diagnostic-positive sequence target result.

M613 result:

```text
17 boundary source rows
5916 sequence candidates
2 accepted candidate rows
1 selected accepted sequence
accepted diversity = one source / pair / surface / variant / target
```

Conclusion:

```text
sequence targets have signal, but the source set is too narrow for optimizer
admission
```

M615 is design-only:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
```

## Design Choice

The next step should not lower the M613 target acceptance thresholds.

Keep:

```text
margin_improvement >= 0.02
or risk_improvement >= 0.05
```

Instead, expand the source rows that sequence mining is allowed to test.

Lowering `min_capability_z_distance` does not help on the current corpus:

```text
M604 grounding candidates for wrong/delayed variants: 101 rows
deduplicated source pool at z >= 0.10: 33 rows
deduplicated source pool at z >= 0.05: 33 rows
```

So M616 should not spend effort on capability-threshold tuning first. The
better source of expansion is the baseline boundary window.

M609 already rolled out `33` unique source rows:

| Window | Rows Included | Physical Pairs | Left Seeds |
| --- | ---: | ---: | ---: |
| collision or margin <= `0.50` | `17` | `16` | `9` |
| collision or margin <= `0.75` | `20` | `18` | `11` |
| collision or margin <= `1.00` | `23` | `21` | `12` |
| collision or margin <= `2.00` | `30` | `27` | `15` |

M616 should therefore build an expanded source table from the existing M609
`source_rollouts.csv`, without rerunning training or changing the actor.

## Source Tiers

M616 should write an expanded sequence-source table with a `source_tier` field.

### Core Boundary

```text
baseline_collision == true
or baseline_margin <= 0.50
```

This is the original M609 boundary set and must remain included.

### Near Boundary

```text
0.50 < baseline_margin <= 1.00
```

These rows are close enough that bounded short sequence prefixes may create a
measurable safety-margin change, while still being less saturated than collision
rows.

### Support Boundary

```text
1.00 < baseline_margin <= 2.00
```

These rows are less fragile. They should be included only as diagnostic source
diversity, not as proof that the policy is unsafe or near collision.

The expanded source table should exclude rows with:

```text
baseline_off_road == true
baseline_spin_out == true
non-finite baseline_margin
```

## Provenance Rules

Each expanded row must preserve deterministic hidden provenance:

```text
source_index
coupling_row_index
surface
target
variant
left_seed
right_seed
left_step
right_step
capability_z_distance
action_distance
coupling_gap
base_steer / base_throttle / base_brake
baseline terminal fields
source_tier
expansion_reason
```

M616 should initially keep only the currently supported history variants:

```text
wrong_matched_history
delayed_history
```

Do not add `shuffled_history` yet. It may be useful later, but M616 should not
introduce a history variant unless the hidden-state provenance can be recorded
and reconstructed as deterministically as the current paired variants.

Do not add neighboring left steps in M616. Neighbor rows are plausible, but the
paired hidden provenance would need to be rebuilt rather than inferred from the
original row. That is a separate design step if M616/M617 still lacks diversity.

## M616 Implementation Scope

M616 should implement a small source-expansion utility, not a training script.

Input:

```text
runs/m609_boundary_conditioned_source_miner/source_rollouts.csv
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
runs/m613_sequence_target_miner/accepted_sequences.csv
```

Output:

```text
runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv
runs/m616_expanded_sequence_source_miner/rejected_sequence_source_rows.csv
runs/m616_expanded_sequence_source_miner/summary.json
```

M616 should prefer a deterministic command such as:

```bash
PYTHONPATH=src python -m autodrift.expanded_sequence_source_miner \
  --source-rollouts runs/m609_boundary_conditioned_source_miner/source_rollouts.csv \
  --original-boundary-source-rows runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv \
  --accepted-sequences runs/m613_sequence_target_miner/accepted_sequences.csv \
  --core-margin-window 0.50 \
  --near-margin-window 1.00 \
  --support-margin-window 2.00 \
  --run-dir runs/m616_expanded_sequence_source_miner
```

## Diversity Targets

M616 should require at least:

```text
expanded source rows >= 24
unique physical pairs >= 16
unique left seeds >= 10
surfaces >= 2
variants >= 2
targets >= 2
max physical-pair dominance <= 0.20
```

These thresholds are for admitting a repeat sequence-mining run, not for
training.

If M616 only reaches the support tier by going out to `margin <= 2.00`, the
summary must say that later accepted sequence targets should be stratified by
source tier. A target found only on support rows is weaker evidence than one
found on core or near rows.

## M617 Repeat Sequence Mining

If M616 passes source diversity, M617 should rerun the M613 sequence miner with
the expanded source table and unchanged target acceptance thresholds.

M617 should not change:

```text
sequence lengths: K in {3, 5}
candidate families: constant_delta, decay_pulse, brake_release_then_steer, steer_then_brake
per-step L2 <= 0.10
sequence mean L2 <= 0.08
sequence max L2 <= 0.10
max delta-delta L2 <= 0.08
margin improvement threshold: 0.02
risk improvement threshold: 0.05
```

Before any optimizer or sequence-head design, M617 should aim for:

```text
accepted sequences >= 8
accepted physical pairs >= 6
accepted left seeds >= 6
accepted surfaces >= 2 where available
accepted variants >= 2 where available
```

If M617 still finds only one or two accepted sequences, the next decision should
be another audit, not optimizer design.

## Contract Checks

```text
actor_input_changed: false
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
```

## Decision

Decision:

```text
sequence_source_expansion_design_admit_m616
```

Next blocker:

```text
m616-expanded-sequence-source-miner-implementation
```
