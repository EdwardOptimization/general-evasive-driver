# M919 V4 Public-Base Expanded Target Regeneration Implementation

## Purpose

M919 implements and runs the M918 source-expansion design.

It remains a no-training data-generation milestone:

```text
no residual-head training
no actor update
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Implementation

M919 adds:

```text
src/autodrift/public_base_expanded_target_regeneration.py
tests/test_public_base_expanded_target_regeneration.py
```

The tool joins M909 near-base objective rows with M912 strict low-tail labels,
expands source coverage with near-tail rows from underrepresented seeds and
fault-family pairs, then reuses the M917 bounded local action target search.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_expanded_target_regeneration \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --objective-rows runs/m909_v4_public_base_residual_head_probe/objective_rows.csv \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m919_v4_public_base_expanded_target_regeneration \
  --device cpu
```

## Result

Summary:

```text
run_type: public_base_expanded_target_regeneration
near_base_alpha: 0.02
near_tail_deficit_threshold: 0.012
near_tail_gap_threshold: 0.03
strict_low_tail_input_rows: 498
source_candidate_rows: 678
rejected_source_candidate_rows: 535
selected_sources: 122
selected_strict_low_tail_sources: 103
selected_near_tail_sources: 19
selected_sources_reconstructed: 122
selected_sources_missing: 0
candidate_actions: 1586
accepted_targets: 122
strict_low_tail_accepted_targets: 103
near_tail_accepted_targets: 19
rejected_targets: 0
distinct_fault_family_pairs: 14
distinct_seeds: 26
accepted_horizon_values: 4, 6, 8
max_fault_family_pair_fraction: 0.19672131147540983
metadata_missing_rows: 0
reconstruction_rejections: 0
actor_parameters_changed: false
training_started: false
m880_exact_used: false
replay_used: false
ppo_used: false
promoted: false
result_class: public_base_expanded_target_regeneration_pass
```

M919 passes the pre-registered source and target gates:

```text
accepted_targets: 122 >= 96
strict_low_tail_accepted_targets: 103 >= 60
distinct_fault_family_pairs: 14 >= 10
distinct_seeds: 26 >= 24
max_fault_family_pair_fraction: 0.19672131147540983 <= 0.25
```

The accepted target split is:

```text
strict_low_tail: 103
near_tail_coverage: 19
```

The largest accepted group remains below the dominance cap:

```text
front_lateral_authority_drop->combined_fault:
  accepted_targets: 24
  accepted_fraction: 0.19672131147540983
```

## Interpretation

M919 resolves the M917 source-coverage blocker. The strict low-tail-only pool
was too sparse, but a coverage-first near-tail expansion gives a source-diverse
target corpus while preserving the M399 actor checksum and without starting
training.

This does not prove residual-head usefulness. It only admits the next design
step: train a frozen-M399 residual head against the regenerated target rows and
evaluate exact objective metrics before any replay, PPO, or promotion.

## Decision

Decision:

```text
public_base_expanded_target_regeneration_pass_route_to_residual_objective_design
```

Next:

```text
m920-v4-public-base-regenerated-target-residual-objective-design
```

## Supported Claims

M919 supports:

```text
1. Expanded near-tail source coverage can provide a source-diverse M399-rooted
   regenerated target corpus.
2. The regenerated target corpus contains enough strict low-tail rows to remain
   tied to the original M912 low-tail blocker.
3. Actor parameters remained unchanged, and no training, exact compatibility,
   replay, PPO, or promotion occurred.
```

## Unsupported Claims

M919 does not support:

```text
residual-head candidate quality;
M880 exact compatibility;
replay retention;
PPO safety;
driver improvement;
checkpoint promotion.
```
