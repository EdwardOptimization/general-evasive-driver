# M917 V4 Public-Base Target Regeneration Implementation

## Purpose

M917 implements and runs the M916 no-training target regeneration step.

It is constrained to:

```text
no residual-head training
no actor parameter update
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Implementation

M917 adds:

```text
src/autodrift/public_base_target_regeneration.py
tests/test_public_base_target_regeneration.py
```

The tool reconstructs M399 features for selected low-tail rows, evaluates a
bounded local action-delta set around the M399 base action, and writes selected,
candidate, accepted, rejected, group, and summary artifacts.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_target_regeneration \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --group-deficit-summary runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv \
  --run-dir runs/m917_v4_public_base_target_regeneration \
  --device cpu
```

## Result

Summary:

```text
run_type: public_base_target_regeneration
low_tail_rows_input_count: 498
selected_sources: 67
selected_sources_reconstructed: 67
selected_sources_missing: 0
candidate_actions: 871
accepted_targets: 67
rejected_targets: 0
distinct_fault_family_pairs: 11
distinct_seeds: 19
max_fault_family_pair_fraction: 0.3582089552238806
metadata_missing_rows: 0
reconstruction_rejections: 0
actor_parameters_changed: false
training_started: false
m880_exact_used: false
replay_used: false
ppo_used: false
promoted: false
result_class: public_base_target_regeneration_too_few_targets
```

M917 fails the pre-registered diversity and acceptance gates:

```text
accepted_targets: 67 < 80
distinct_seeds: 19 < 24
max_fault_family_pair_fraction: 0.3582 > 0.25
```

The failure is not target-search rejection. All selected reconstructed sources
produced accepted local targets:

```text
accepted_targets / selected_sources_reconstructed = 67 / 67
```

The blocker is source coverage. The M912 low-tail input has only `21` distinct
seeds total, so the M917 `distinct_seeds >= 24` gate is impossible to satisfy
from this strict low-tail source alone.

## Source Coverage Audit

The M912 low-tail source pool contains:

```text
rows: 498
fault-family pairs: 17
seeds: 21
```

The M755 source corpus contains `27` seeds, but only `21` of those appear in
the strict M912 low-tail subset. Therefore the next step should expand the
target source pool from strict low-tail rows to a source-balanced near-tail
candidate set, rather than lowering the diversity gate or training on a
concentrated target file.

Cap sensitivity over the same strict low-tail input:

```text
per_seed_cap  selected  pairs  seeds  max_pair_fraction
4             67        11     19     0.358
6             88        12     19     0.273
8             107       13     18     0.224
12            141       14     18     0.170
unbounded     256       14     14     0.094
```

Relaxing caps alone can increase row count, but it cannot satisfy seed
coverage because the strict source pool does not contain enough seeds.

## Decision

Decision:

```text
public_base_target_regeneration_route_to_source_expansion_design
```

Next:

```text
m918-v4-public-base-target-source-expansion-design
```

M918 should design a no-training source expansion route that joins the M909
near-base objective rows with M912 strict low-tail membership, adds
source-balanced near-tail coverage from the full M755 corpus, and reruns target
generation only after the source pool can satisfy diversity gates.

## Supported Claims

M917 supports:

```text
1. The M399 reconstruction path works for selected source rows.
2. Bounded local action targets are available for all selected strict low-tail
   rows in this run.
3. The strict M912 low-tail source pool is too small and too concentrated for
   the M916 diversity gate.
4. Actor parameters remained unchanged, and no training, exact compatibility,
   replay, PPO, or promotion occurred.
```

## Unsupported Claims

M917 does not support:

```text
regenerated target corpus admission;
residual objective training;
M880 exact compatibility;
replay retention;
PPO safety;
driver improvement;
checkpoint promotion.
```
