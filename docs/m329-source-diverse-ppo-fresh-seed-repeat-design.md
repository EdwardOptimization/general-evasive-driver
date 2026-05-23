# M329 Source-Diverse PPO Fresh-Seed Repeat Design

M329 designs a fresh-seed repeat of the M327/M328 source-diverse protected PPO
smoke process. No PPO, repair, replay, promotion, or actor-input change was
performed.

## Motivation

M328 promoted one positive smoke PPO result from the source-diverse protected
workflow. Before any longer PPO escalation, the workflow needs a fresh seed
repeat to check seed fragility:

```text
M328 base
  -> fresh PPO seed
  -> exact repair
  -> source-diverse protected gates
  -> old-key diagnostic
  -> first replay gates
```

This prevents treating a single smoke PPO seed as a stable continuation recipe.

## M330 PPO Repeat

Config:

```text
configs/ppo_m330_source_diverse_protected_repeat_smoke.json
```

Initial checkpoint and PPO anchors:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

Fresh-seed settings:

| Field | M327 | M330 |
| --- | ---: | ---: |
| total_steps | 1024 | 1024 |
| rollout_steps | 128 | 128 |
| num_envs | 8 | 8 |
| learning_rate | 5e-7 | 5e-7 |
| PPO seed | 5236 | 5237 |
| exact repair seed | 10097 | 10098 |

Proposed PPO command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m330_source_diverse_protected_repeat_smoke.json \
  --init-checkpoint runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt \
  --run-dir runs/ppo_m330_source_diverse_protected_repeat_seed5237 \
  --save runs/ppo_m330_source_diverse_protected_repeat_seed5237/checkpoint.pt \
  --device cpu
```

## Mandatory Exact Repair

The raw PPO checkpoint remains proposal-only:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt \
  --raw-checkpoint runs/ppo_m330_source_diverse_protected_repeat_seed5237/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-param-raw 0.05 \
  --lambda-param-base 1.0 \
  --lambda-action-anchor 100.0 \
  --run-dir runs/m330_exact_repair_from_raw_s40_seed10098 \
  --seed 10098
```

Exact acceptance starts with:

```text
exact_M297(candidate) <= exact_M297(M328)
exact_M270(candidate) <= exact_M270(M328)
```

## Source-Diverse Protected Gates

M330 should use the same three-corpus source-diverse bundle as M327, with
M328 as the current-base baseline:

| Gate | Corpus | Baseline |
| --- | --- | --- |
| current_m328_surface | `runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M328 base |
| m325_continuity_surface | `runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M325 base |
| m317_continuity_surface | `runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M317 base |
| m314_continuity_surface | `runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M314 base |

Because the first two use the same corpus but different baselines, the gate
labels must stay distinct. The wrapper already rejects true self-gates.

## Old-Key Diagnostic

M330 must run `9944` as a diagnostic. If the candidate fails the old
normal-margin window while retaining `margin_gap >= 0.09`, classify:

```text
single_key_window_saturation
```

If the old-key gap collapses below the diagnostic floor, stop before first
replay and classify protected-key failure.

## First Replay Gates

If exact and source-diverse gates pass, run:

```text
M183/M170 boundary replay versus M328
M267/M264 boundary replay versus M328
```

M330 remains a no-promotion milestone. If first gates pass, admit a separate
full public gate.

## Decision

Admit:

```text
m330-source-diverse-ppo-fresh-seed-repeat
```

Decision:

```text
admit_m330_source_diverse_ppo_fresh_seed_repeat
```
