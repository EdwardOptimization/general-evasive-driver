# M798 V4 Active Steer Guard Calibration Implementation

## Purpose

M798 implements the no-PPO active/source-diverse low-margin steer guard
diagnostic designed by M797.

The question is:

```text
Can we build a source-diverse low-margin normal guard corpus before training an
active-steer guard calibrator?
```

This milestone is diagnostic only:

```text
no actor update
no residual-head update
no calibrator training if corpus gate fails
no PPO
no checkpoint promotion
```

## Tooling Added

M798 extends:

```text
src/autodrift/v4_normal_margin_residual_calibration.py
tests/test_v4_normal_margin_residual_calibration.py
```

New mode:

```text
--objective-mode active_steer_guard
```

New artifacts:

```text
low_margin_guard_rows.csv
separability_metrics.csv
```

The implementation adds a pre-training guard-corpus gate. It selects normal
rows from the parent replay artifact when:

```text
alpha == 0.2
and branch == normal
and (
  min_clearance_margin <= 0.00005
  or row is the known active boundary source
)
```

It then requires:

```text
min unique seeds: 8
min unique source_index values: 8
min unique fault-family pairs: 4
max single seed dominance: 0.25
```

If this source-diversity gate fails, M798 stops before training and writes the
blocker artifacts.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_normal_margin_residual_calibration \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --parent-replay-rows runs/m795_v4_steer_attributed_residual_calibration/replay_rows.csv \
  --run-dir runs/m798_v4_active_steer_guard_calibration \
  --device cpu \
  --epochs 60 \
  --seed 7980 \
  --lr 0.001 \
  --alpha-train 0.2 \
  --objective-mode active_steer_guard \
  --initial-gate 0.85 \
  --gap-lift 0.003 \
  --active-normal-gate-max 0.45 \
  --intervention-gate-floor 0.75 \
  --alphas 0.0,0.125,0.15,0.2
```

## Result

M798 stops at the guard-corpus stage:

```text
result_class: v4_active_steer_guard_low_margin_corpus_blocked

low_margin_guard_row_count: 12
low_margin_unique_source_count: 1
low_margin_unique_seed_count: 1
low_margin_unique_source_index_count: 1
low_margin_unique_fault_pair_count: 1
low_margin_max_seed_dominance: 1.0

required unique seeds: 8
required unique source_index values: 8
required unique fault-family pairs: 4
required max seed dominance: 0.25
```

All selected guard rows come from the same public active source:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
normal margin: +0.000003618
```

M798 therefore does not run the separability probe, does not train the
calibrator, and does not run closed-loop replay.

## Invariants

```text
actor_backbone_changed: false
base_residual_head_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
```

The created calibrator file is only the initialized 2146-parameter
steer/brake gate artifact for reproducibility. It is not trained.

## Interpretation

M798 supports:

```text
1. The M797 guard-corpus gate is working: it prevents training on a single
   public active source.

2. The current M795/M773 parent replay evidence has only one low-margin normal
   source under the registered threshold.

3. Another active-steer guard objective would be under-supported unless we
   first mine a source-diverse low-margin normal corpus.
```

M798 falsifies:

```text
1. Current artifacts already contain enough source-diverse low-margin normal
   rows for active-steer guard training.

2. M798 can fairly test deployable feature separability now.

3. The next step should be another gate-objective coefficient tweak.
```

## Decision

M798 is a clean process-positive blocker:

```text
v4_active_steer_guard_low_margin_corpus_blocked
```

It admits only an audit:

```text
next: m799-v4-active-steer-guard-calibration-audit
```

M799 should decide whether to design a source-diverse low-margin corpus refresh
or stop the residual-calibration branch and return to broader scenario/corpus
evidence.

PPO and checkpoint promotion remain blocked.
