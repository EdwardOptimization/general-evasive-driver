# M982 V4 Public Base Post Repair OOD Pocket Expansion Audit

## Purpose

M982 audits whether the M980 accepted OOD pocket was caused by insufficient
candidate coverage. It returns to the same OOD seed range from M980 and raises
candidate/snapshot limits while keeping all acceptance thresholds unchanged.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M982 does not train, run PPO, promote, use private holdout, change actor inputs,
or lower thresholds.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --surface-seed-range ood=98100:98179 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 35.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 160 \
  --max-candidate-pairs-per-surface 8000 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 1600 \
  --max-snapshots-per-seed 12 \
  --sample-stride 3 \
  --max-continuation-steps 9 \
  --device auto \
  --run-dir runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit
```

## Result

```text
corpus_passed: false
accepted_rows: 30
accepted_physical_pairs: 2
accepted_left_seeds: 1
accepted_right_seeds: 2
near_boundary_preferred_snapshots: 161
candidate_pairs: 8000
candidate_rows: 24000
actor_parameters_changed: false
ppo_used: false
promoted: false
```

M982 reproduces the M980 pocket but does not expand it.

## Window Coverage

| Surface | Window class | Rows | Seeds | Targets | Mean normal margin |
| --- | --- | ---: | ---: | ---: | ---: |
| ood | near_boundary_preferred | 161 | 55 | 3 | 0.520081 |
| ood | early_safe_diagnostic | 158 | 47 | 3 | 2.510001 |
| ood | already_failed_diagnostic | 87 | 29 | 2 | -0.097919 |

The OOD range has enough near-boundary preferred windows for the audit.

## Accepted Rows

Accepted rows:

```text
accepted_rows: 30
accepted_success_drop_rate: 1.0
mean_preferred_vs_rejected_action_mean_l2: 0.138704
mean_margin_gap: 0.000333
```

Source diversity remains exactly the same shape as M980:

```text
surface: ood only
target: unavoidable only
left_seed: 98107 only
right_seeds: 98108, 98139
physical_pairs: 2
sources: 10
```

Rejection reasons:

```text
accepted: 30
no_success_drop_or_margin_gap: 23677
preferred_rejected_action_mean_l2_below_threshold;no_success_drop_or_margin_gap: 230
wrong_action_sequence_mean_l2_below_threshold;preferred_rejected_action_mean_l2_below_threshold;no_success_drop_or_margin_gap: 57
wrong_first_action_l2_below_threshold;wrong_action_sequence_mean_l2_below_threshold;preferred_rejected_action_mean_l2_below_threshold;no_success_drop_or_margin_gap: 6
```

Even with `8000` candidate pairs, accepted rows remain attached to one left seed.
Candidate coverage was not the limiting factor.

## Interpretation

M982 rules out the simple candidate-limit explanation for M980. The current
M974 public-base surface refresh has a real, repeatable, but isolated
wrong-history outcome-sensitive OOD pocket.

Supported:

```text
M980 pocket is deterministic and reproducible.
M980 pocket is not a broad source-diverse proof surface.
Increasing candidate-pair coverage on the same OOD range does not expand source diversity.
```

Not supported:

```text
The current fresh/OOD scenario family contains a source-diverse post-repair proof surface.
The project should train on the M980/M982 rows as a durable corpus.
Another same-family seed expansion is likely to be high leverage.
```

Classification:

```text
post_repair_ood_pocket_isolated_repeatable
```

Failure taxonomy:

```text
scenario_sampling_failure
```

## Decision

Do not train from the M980/M982 rows. Do not lower thresholds. Do not run PPO.

Route to branch synthesis and then scenario-family expansion:

```text
m983-v4-public-base-post-repair-surface-refresh-synthesis
```

The next scientific question is no longer "did we mine enough candidate pairs
inside the same public scenario family?" It is "does a broader hidden-dynamics
and emergency-scenario family expose source-diverse outcome-sensitive
wrong-history rows?"

## Artifacts

```text
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/summary.json
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/snapshot_bank_summary.csv
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/normal_window_summary.csv
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/candidate_scores.csv
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/normal_success_boundary_rows.csv
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/normal_success_boundary_corpus.npz
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/source_summary.csv
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/split_summary.csv
runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/target_summary.csv
```
