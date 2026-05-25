# M801 V4 Low-Margin Source-Diverse Corpus Refresh Implementation

## Purpose

M801 implements and runs the no-training corpus refresh designed in M800.

The question is:

```text
Can a boundary-retargeted public mining wave produce a source-diverse set of
normal-history rows whose alpha 0.2 residual-assisted branch succeeds with very
low clearance margin?
```

This milestone is data and tooling only:

```text
no actor update
no residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

Added:

```text
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
src/autodrift/v4_low_margin_guard_corpus_refresh.py
tests/test_v4_low_margin_guard_corpus_refresh.py
```

The new selector consumes a reference replay CSV and exports:

```text
low_margin_guard_candidates.csv
accepted_low_margin_guard_rows.csv
diagnostic_margin_bands.csv
summary.json
```

It treats `0.00005 m` as the primary low-margin threshold and reports wider
diagnostic bands only as diagnostics. Rows in wider bands cannot pass the
primary gate.

## Commands

### Source Wave

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 78048 \
  --seed-count 2048 \
  --device cpu \
  --run-dir runs/m801_v4_low_margin_refresh_extreme_faults
```

### Sequence Intervention

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --reset-rows runs/m801_v4_low_margin_refresh_extreme_faults/reset_only_rows.csv \
  --rejected-rows runs/m801_v4_low_margin_refresh_extreme_faults/rejected_rows.csv \
  --seed-start 78048 \
  --seed-count 2048 \
  --max-source-rows 2048 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m801_v4_low_margin_refresh_sequence_intervention
```

### Corpus Export

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_outcome_corpus_export \
  --summary runs/m801_v4_low_margin_refresh_sequence_intervention/summary.json \
  --rollouts runs/m801_v4_low_margin_refresh_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m801_v4_low_margin_refresh_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m801_v4_low_margin_refresh_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m801_v4_low_margin_refresh_corpus_export
```

### Reference Residual Replay

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m801_v4_low_margin_refresh_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m801_v4_low_margin_refresh_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m801_v4_low_margin_source_diverse_reference_replay \
  --device cpu \
  --alphas 0.0,0.125,0.15,0.2
```

### Low-Margin Selector

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_low_margin_guard_corpus_refresh \
  --reference-replay-rows runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv \
  --reference-replay-summary runs/m801_v4_low_margin_source_diverse_reference_replay/summary.json \
  --run-dir runs/m801_v4_low_margin_source_diverse_corpus_refresh \
  --alpha 0.2 \
  --primary-margin-threshold 0.00005 \
  --diagnostic-thresholds 0.00005,0.0001,0.0005,0.001,0.01,0.1,0.2 \
  --min-rows 80 \
  --min-seeds 8 \
  --min-source-indices 8 \
  --min-fault-pairs 4 \
  --max-seed-dominance 0.25 \
  --max-source-index-dominance 0.15 \
  --max-fault-pair-dominance 0.40
```

## Stage 1: Source Wave

Result:

```text
run_dir: runs/m801_v4_low_margin_refresh_extreme_faults
result_class: cross_fault_reset_only

seed_start: 78048
seed_count: 2048
scenario_count: 59392
snapshot_count: 400593
matched_pair_count: 49152

accepted_rows: 0
reset_only_rows: 3552
rejected_rows: 45600
normal_failed_rejected: 14041
history_insensitive_rejected: 31559
reset_history_action_critical_rows: 3552

actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Compared with M773, this roughly doubles matched pairs and substantially
increases reset-only rows:

```text
M773 reset_only_rows: 1389
M801 reset_only_rows: 3552
```

## Stage 2: Sequence Intervention

Result:

```text
run_dir: runs/m801_v4_low_margin_refresh_sequence_intervention
result_class: v4_reset_sequence_outcome_positive

source_candidate_rows: 2048
source_unique_seeds: 135
source_unique_fault_family_pairs: 22
source_max_seed_dominance: 0.046387
source_max_preferred_family_dominance: 0.140137
source_reset_rows: 1843
source_sentinel_rows: 205

rollout_rows: 49152
sequence_action_critical_rows: 21964
sequence_outcome_critical_rows: 4825
unique_sequence_outcome_seeds: 108
unique_sequence_outcome_fault_family_pairs: 18
max_sequence_outcome_seed_dominance: 0.086425

sentinel_false_positive_rows: 0
normal_history_retention_pass: true

actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

This is a coverage positive relative to M773:

```text
M773 sequence_outcome_critical_rows: 2652
M801 sequence_outcome_critical_rows: 4825
M773 unique_sequence_outcome_seeds: 49
M801 unique_sequence_outcome_seeds: 108
M773 unique_sequence_outcome_fault_family_pairs: 17
M801 unique_sequence_outcome_fault_family_pairs: 18
```

## Stage 3: Corpus Export

Result:

```text
run_dir: runs/m801_v4_low_margin_refresh_corpus_export
result_class: v4_sequence_outcome_corpus_hard_negative_sparse

positive_rows: 4825
normal_rows: 4825
positive_intervention_rows: 4825
contrast_groups: 4825
unique_positive_seeds: 108
unique_positive_fault_family_pairs: 18
max_positive_seed_dominance: 0.086425
max_positive_fault_family_pair_dominance: 0.137617

sentinel_positive_candidates: 0
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0
positive_corpus_gate_pass: true
v4_metadata_gate_pass: true

hard_negative_rows: 4145
positives_without_hard_negative: 1514
hard_negative_complete: false

training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

The broader corpus objective is successful. Hard negatives remain sparse, but
that is not the primary M801 gate.

## Stage 4: Reference Residual Replay

Result:

```text
run_dir: runs/m801_v4_low_margin_source_diverse_reference_replay
result_class: v4_residual_closed_loop_replay_normal_regression

positive_rows: 4825
reconstructed_rows: 4805
sample_reconstruction_success_rate: 0.995855
metadata_missing_rows: 0
rejected_rows: 20
replay_rows: 38440
objective_rows: 19220

actor_backbone_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Alpha summary:

| alpha | normal success | normal collision | intervention gap mean | candidate |
| ---: | ---: | ---: | ---: | --- |
| 0.0 | 1.000000 | 0.000000 | 0.041962 | false |
| 0.125 | 0.987513 | 0.012487 | 0.045748 | false |
| 0.15 | 0.987513 | 0.012487 | 0.046519 | false |
| 0.2 | 0.987513 | 0.012487 | 0.048074 | false |

The frozen residual head produces stronger intervention separation but also
normal regression on the refreshed corpus. This is diagnostic only; no
checkpoint is promoted.

## Stage 5: Low-Margin Guard Selection

Result:

```text
run_dir: runs/m801_v4_low_margin_source_diverse_corpus_refresh
result_class: v4_low_margin_guard_refresh_diagnostic_band_only

reference_replay_row_count: 38440
candidate_row_count: 76
fresh_candidate_row_count: 76

accepted_low_margin_guard_row_count: 0
fresh_accepted_low_margin_guard_row_count: 0
low_margin_corpus_pass: false

reference_contract_ok: true
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Diagnostic bands for collision-free successful normal alpha `0.2` rows:

| margin band | rows | seeds | source indices | fault pairs | max seed dominance |
| ---: | ---: | ---: | ---: | ---: | ---: |
| <= 0.00005 | 0 | 0 | 0 | 0 | 0.000000 |
| <= 0.00010 | 0 | 0 | 0 | 0 | 0.000000 |
| <= 0.00050 | 0 | 0 | 0 | 0 | 0.000000 |
| <= 0.00100 | 0 | 0 | 0 | 0 | 0.000000 |
| <= 0.01000 | 24 | 1 | 4 | 3 | 1.000000 |
| <= 0.10000 | 39 | 5 | 12 | 4 | 0.615385 |
| <= 0.20000 | 76 | 9 | 41 | 11 | 0.618421 |

Additional margin check on all normal alpha `0.2` rows:

```text
normal rows: 4805
success rate: 0.987513
collision rate: 0.012487

rows with margin <= 0.001: 60
  success: 0
  collision: 60
  seeds: 2
  fault-family pairs: 1

smallest collision-free successful margin: about 0.005243 m
```

So M801 found a useful wider diagnostic band, but not the requested
source-diverse primary low-margin guard corpus. There is still a gap between
colliding rows and the nearest collision-free success rows.

## Interpretation

M801 strongly supports the broad coverage part of M800:

```text
4825 positives
108 positive seeds
18 positive fault-family pairs
max positive seed dominance 0.086425
```

But M801 does not support the active-steer guard training precondition:

```text
0 rows in the primary <= 0.00005 successful non-collision band
0 rows through <= 0.001
only diagnostic rows starting around 0.005 m
diagnostic rows remain seed-dominated
```

This is a clean negative:

```text
v4_low_margin_guard_refresh_diagnostic_band_only
```

The likely blocker is not ordinary source count anymore. The new issue is a
boundary-window miss: the refreshed distribution produces either collisions or
safe-enough rows, but not many collision-free rows inside the very low margin
window required for active-steer guard training.

## Supported Claims

M801 supports:

```text
1. The source mining expansion worked: sequence-outcome coverage increased
   materially over M773 while preserving sentinel and metadata gates.

2. The low-margin guard corpus blocker is not solved by simply doubling the
   public v4 source wave.

3. The strict primary low-margin band remains empty for successful
   collision-free normal alpha 0.2 rows on the refreshed corpus.

4. The next step should audit the boundary-window miss before another
   calibrator objective.
```

## Falsified Claims

M801 falsifies:

```text
1. The M798 blocker was only caused by too few broad v4 positives.

2. A larger source wave alone is enough to produce source-diverse primary
   low-margin guard rows.

3. M801 admits active-steer guard calibration, PPO, or checkpoint promotion.
```

## Workflow Note

The source wave took materially longer than typical design/audit milestones and
writes artifacts only at completion. A future harness improvement should add
progress reporting or source-wave sharding for long public mining waves. That is
a workflow improvement, not a change to the scientific result.

## Decision

M801 admits audit only:

```text
m802-v4-low-margin-source-diverse-corpus-refresh-audit
```

Residual calibration, PPO, and checkpoint promotion remain blocked.
