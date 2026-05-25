# M766 V4 Residual Source-Holdout Replay Design

## Purpose

M766 designs the next step after M765 audited M764 as a clean public-corpus
closed-loop mechanism positive.

The question is:

```text
Can we build a fresh source-holdout corpus for the M761 residual head, rather
than reusing public M755/M761 rows and overclaiming generalization?
```

This milestone is design-only:

```text
no data wave run
no residual replay
no actor training
no residual retraining
no PPO
no checkpoint promotion
```

## Precheck

Existing M752/M755 artifacts do not contain a clean extra positive holdout for
the residual head:

```text
M752 non-sentinel outcome positives: 1213
M755 positives: 1213
M752 positives not exported to M755: 0

M752 source rows total: 512
M752 positive source rows: 452
M752 unused source rows: 60
```

M755 has an `assigned_split=heldout` label:

```text
train: 1109
heldout: 104
```

But M761 trained the residual head on all M755 positive rows. Therefore that
split is contaminated for residual-head generalization and must not be used as
an unbiased holdout.

## Design Decision

M766 decides not to run residual holdout replay directly from existing M752/M755
rows.

Instead, the next step should create a fresh source-holdout wave:

```text
M767:
  fresh v4 extreme-fault source wave
  fresh v4 reset-source sequence intervention
  fresh v4 sequence-outcome corpus export
```

Only after that fresh corpus is audited should the project run M761 residual
closed-loop replay on the holdout.

## Freshness Definition

Fresh relative to M761 means:

```text
1. disjoint seed range from M749/M752/M755/M761 public source rows;
2. source rows not present in M755 positive_sequence_outcomes.csv;
3. sequence outcome rows not used in M761 residual training;
4. no residual or actor retraining after seeing the fresh holdout;
5. alpha choice pre-registered before replay.
```

Recommended fresh seed range:

```text
seed_start: 76512
seed_count: 512
```

This follows the M749 range `76000..76511` without overlap.

## M767 Planned Pipeline

M767 should run three no-training steps.

### 1. Fresh v4 extreme-fault source wave

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 76512 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m767_v4_source_holdout_extreme_faults
```

### 2. Fresh v4 reset-source sequence intervention

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --reset-rows runs/m767_v4_source_holdout_extreme_faults/reset_only_rows.csv \
  --rejected-rows runs/m767_v4_source_holdout_extreme_faults/rejected_rows.csv \
  --seed-start 76512 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m767_v4_source_holdout_sequence_intervention
```

### 3. Fresh v4 sequence-outcome corpus export

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_outcome_corpus_export \
  --summary runs/m767_v4_source_holdout_sequence_intervention/summary.json \
  --rollouts runs/m767_v4_source_holdout_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m767_v4_source_holdout_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m767_v4_source_holdout_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m767_v4_source_holdout_corpus_export
```

## Minimum Fresh Corpus Gates

M767 should not proceed to residual replay unless the fresh corpus has:

```text
positive_rows >= 100
sentinel_positive_rows == 0
missing_normal_matches == 0
positive_rows_missing_v4_metadata == 0
positive_rows_missing_fidelity_metadata == 0
unique_positive_seeds >= 10
unique_positive_fault_family_pairs >= 6
max_positive_seed_share <= 0.25
claim_boundary_levels == [current_model_or_proxy]
```

If the fresh wave produces too few positives, classify it as
`scenario_sampling_failure` and audit before changing source generation.

## Residual Replay Plan After Fresh Corpus

If M767 succeeds and M768 audits it as a clean fresh corpus, the later residual
replay should use:

```text
primary alpha: 0.2
diagnostic alphas: 0.5, 1.0
base alpha: 0.0
```

Alpha `0.2` is primary because M765 found it conservative: it improves the
closed-loop intervention gap without creating intervention collisions on the
public corpus.

## Forbidden Shortcuts

M766 explicitly forbids:

```text
using M755 assigned_split=heldout as unbiased holdout;
retraining residual or actor on the fresh holdout;
tuning alpha after seeing holdout results and reporting the same result as
unbiased;
promoting a checkpoint from source-holdout replay;
claiming true per-wheel / tire blowout / axle-break physics from current
proxy faults.
```

## Next Step

Decision:

```text
admit_m767_v4_fresh_source_holdout_wave_implementation
```

M767 should implement the fresh no-training source-holdout wave and corpus
export. Residual replay, PPO, and checkpoint promotion remain blocked until
that fresh corpus is audited.
