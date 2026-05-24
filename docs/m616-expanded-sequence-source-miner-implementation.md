# M616 Expanded Sequence Source Miner Implementation

## Purpose

M616 implements the no-training source expansion step designed by M615.

Goal:

```text
turn M609 rollout-backed source rows into a larger sequence-target source table
before repeating sequence target mining
```

Scope:

```text
no actor training
no PPO
no checkpoint promotion
no optimizer admission
no actor input change
```

## Implementation

New module:

```text
src/autodrift/expanded_sequence_source_miner.py
```

New focused tests:

```text
tests/test_expanded_sequence_source_miner.py
```

The miner reads:

```text
runs/m609_boundary_conditioned_source_miner/source_rollouts.csv
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
runs/m613_sequence_target_miner/accepted_sequences.csv
```

It writes:

```text
runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv
runs/m616_expanded_sequence_source_miner/rejected_sequence_source_rows.csv
runs/m616_expanded_sequence_source_miner/summary.json
```

## Source Tiers

M616 keeps only deterministic supported history variants:

```text
wrong_matched_history
delayed_history
```

Rows are accepted into these tiers:

```text
core_boundary:
  baseline_collision == true
  or baseline_margin <= 0.50

near_boundary:
  0.50 < baseline_margin <= 1.00

support_boundary:
  1.00 < baseline_margin <= 2.00
```

Rows are rejected when:

```text
baseline_off_road == true
baseline_spin_out == true
baseline_margin is non-finite
variant is unsupported
baseline_margin > 2.00
```

Every accepted/rejected row preserves hidden provenance:

```text
source_index
coupling_row_index
surface
target
variant
left_seed / right_seed
left_step / right_step
capability_z_distance
action_distance
coupling_gap
base action
baseline rollout fields
source_tier
expansion_reason
original_m609_boundary
m613_accepted_sequence
```

## Command

Executed:

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

## Results

Summary:

| Metric | Value |
| --- | ---: |
| source rollout rows | `33` |
| expanded source rows | `30` |
| rejected source rows | `3` |
| original M609 boundary rows included | `17` |
| M613 accepted sequence rows included | `1` |
| diversity pass | `true` |

Diversity:

| Metric | Value |
| --- | ---: |
| rows | `30` |
| physical pairs | `27` |
| left seeds | `15` |
| surfaces | `2` |
| variants | `2` |
| targets | `3` |
| max physical-pair dominance | `0.066667` |

Tier counts:

| Tier | Rows |
| --- | ---: |
| core_boundary | `17` |
| near_boundary | `6` |
| support_boundary | `7` |

Expansion reasons:

| Reason | Rows |
| --- | ---: |
| baseline_collision | `9` |
| core_margin_window | `8` |
| near_margin_window | `6` |
| support_margin_window | `7` |

Rejected rows:

```text
3 rows rejected as baseline_outside_support_window
```

## Interpretation

M616 passes its infrastructure gate.

The source pool is now broad enough to repeat sequence target mining:

```text
M609 boundary rows: 17
M616 expanded rows: 30
```

The expansion did not lower sequence target acceptance thresholds. It only
increased the rollout-backed source rows that the unchanged M613 sequence miner
can evaluate.

This still does not prove driver improvement. The next step is another
diagnostic sequence mining run on the expanded source rows.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_expanded_sequence_source_miner.py \
  tests/test_boundary_conditioned_source_miner.py
```

Result:

```text
11 passed
```

Contract checks:

```text
target_acceptance_thresholds_changed: false
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
```

## Decision

Decision:

```text
expanded_sequence_source_miner_pass_admit_m617
```

Next blocker:

```text
m617-expanded-sequence-target-miner
```
