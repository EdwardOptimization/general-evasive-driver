# M326 Source-Diverse Protected PPO Proposal Design

M326 designs the next smoke PPO proposal after M325 promoted the M316 repaired
endpoint under the source-diverse protected policy. No PPO, repair, replay, or
actor-input change was performed.

## Current Base

M325 public-gate base:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

M325 matters because it removes the M317 micro-alpha bottleneck. The old
`9944` key remains diagnostic, but the M320 source-diverse protected bundle is
now the first-class protected gate.

## M327 PPO Proposal

Config:

```text
configs/ppo_m327_source_diverse_protected_proposal_smoke.json
```

Initial checkpoint and PPO anchors:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

Smoke-scale settings:

| Field | Value |
| --- | ---: |
| total_steps | 1024 |
| rollout_steps | 128 |
| num_envs | 8 |
| learning_rate | 5e-7 |
| seed | 5236 |
| rejected_history_preference_aux_coef | 0.03 |
| outcome_intervention_aux_coef | 0.06 |
| baseline_action_anchor_coef | 100.0 |
| snippet_action_anchor_coef | 100.0 |
| trajectory_action_anchor_coef | 100.0 |

Proposed PPO command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m327_source_diverse_protected_proposal_smoke.json \
  --init-checkpoint runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt \
  --run-dir runs/ppo_m327_source_diverse_protected_proposal_smoke_seed5236 \
  --save runs/ppo_m327_source_diverse_protected_proposal_smoke_seed5236/checkpoint.pt \
  --device cpu
```

## Mandatory Exact Repair

The raw PPO checkpoint is a proposal only. It is not promotable. M327 must run
exact repair before replay gates:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt \
  --raw-checkpoint runs/ppo_m327_source_diverse_protected_proposal_smoke_seed5236/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-param-raw 0.05 \
  --lambda-param-base 1.0 \
  --lambda-action-anchor 100.0 \
  --run-dir runs/m327_exact_repair_from_raw_s40_seed10097 \
  --seed 10097
```

Exact acceptance starts with:

```text
exact_M297(candidate) <= exact_M297(M325)
exact_M270(candidate) <= exact_M270(M325)
```

If either exact objective regresses, stop before replay and classify the result
as `objective_overfit` or `metric_artifact`, depending on whether the PPO
training metrics looked good.

## Source-Diverse Protected Acceptance

M327 should evaluate the repaired candidate against all three M320 compact
protected corpora:

| Gate | Corpus | Baseline |
| --- | --- | --- |
| current_repaired_surface | `runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M325 base |
| m317_continuity_surface | `runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M317 base |
| m314_continuity_surface | `runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M314 base |

The candidate must retain all wrong-history success drops on the source-diverse
bundle. This gate replaces old-key alpha clipping as the first-class protected
surface.

The source-diverse wrapper command should include:

```text
--checkpoint-policy m325_base=runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
--checkpoint-policy m317_base=runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
--checkpoint-policy m314_base=runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
--checkpoint-policy m327_repaired=runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

and the three replay gates listed above.

## Old-Key Diagnostic

M327 must still run or ingest `9944`:

```text
9944 is diagnostic, not deleted.
```

If `9944` fails only by the normal-margin singleton window while retaining
`margin_gap >= 0.09`, classify it as:

```text
single_key_window_saturation
```

If the old-key gap collapses or the wrong-history branch becomes safe, classify
it as `protected_key_window_failure` and stop.

## First Replay Gates

Only exact-passing and source-diverse-passing candidates should run first replay
gates versus M325:

```text
M183/M170 boundary replay
M267/M264 boundary replay
```

Both must retain all success drops and stay within public margin tolerances.

## Promotion Escalation

M327 cannot promote directly. If exact repair, source-diverse protected gate,
old-key diagnostic classification, and first replay gates pass, it may admit a
separate full public-gate milestone:

```text
m328-full-public-gate-for-m327-source-diverse-repaired
```

That later milestone must run all six replay surfaces, behavior seeds 9505/9506,
old-key diagnostic reporting, and research validation.

## Decision

Admit:

```text
m327-source-diverse-protected-ppo-proposal-smoke
```

Decision:

```text
admit_m327_source_diverse_protected_ppo_proposal_smoke
```
