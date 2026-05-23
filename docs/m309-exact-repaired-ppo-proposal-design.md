# M309 Exact Repaired PPO Proposal Design

M309 designs the next PPO step after M307 promoted the exact-repaired M306
candidate and M308 showed the repair optimizer seed is not the current
fragility source. No PPO was run, no repair was run, and actor inputs are
unchanged.

## Design Decision

The next PPO run must be treated as a proposal generator, not as a promotable
checkpoint by itself. The acceptance path is:

```text
M307 public-gate base
  -> fresh smoke PPO proposal
  -> exact full-corpus M297/M270 repair projection
  -> exact no-regression gates versus M307
  -> M183/M170 and M267/M264 first replay gates
  -> later full public gate only if first gates pass
```

The key change from M302 is that the exact gates are no longer post-hoc
diagnostics. They are the first acceptance layer after PPO, and replay is not
run for exact-regressing proposals.

## M310 PPO Proposal

Config:

```text
configs/ppo_m310_exact_repaired_proposal_smoke.json
```

Initial checkpoint and PPO anchors:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Smoke-scale settings:

| Field | Value |
| --- | ---: |
| total_steps | 1024 |
| rollout_steps | 128 |
| num_envs | 8 |
| learning_rate | 5e-7 |
| seed | 5234 |
| rejected_history_preference_aux_coef | 0.03 |
| outcome_intervention_aux_coef | 0.06 |
| baseline_action_anchor_coef | 100.0 |
| snippet_action_anchor_coef | 100.0 |
| trajectory_action_anchor_coef | 100.0 |

The proposed PPO command is:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m310_exact_repaired_proposal_smoke.json \
  --init-checkpoint runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt \
  --run-dir runs/ppo_m310_exact_repaired_proposal_smoke_seed5234 \
  --save runs/ppo_m310_exact_repaired_proposal_smoke_seed5234/checkpoint.pt \
  --device cpu
```

## Mandatory Exact Repair

The raw PPO checkpoint is not promotable. It must be routed through exact
repair:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt \
  --raw-checkpoint runs/ppo_m310_exact_repaired_proposal_smoke_seed5234/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-param-raw 0.05 \
  --lambda-param-base 1.0 \
  --lambda-action-anchor 100.0 \
  --run-dir runs/m310_exact_repair_from_raw_s40_seed10095 \
  --seed 10095
```

Acceptance begins with exact objectives versus M307:

```text
exact_M297(candidate) <= exact_M297(M307)
exact_M270(candidate) <= exact_M270(M307)
```

If either exact gate regresses, M310 should stop before replay and be classified
as `objective_overfit` or `metric_artifact`, depending on the PPO train metric.

## First Replay Gates

Only exact-passing candidates should run the two first replay gates. The
baseline policy for both is the M307 public-gate base:

```text
m307_base=runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Candidate:

```text
m310_repaired=runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
```

First gate order:

```text
1. M183/M170 boundary replay
2. M267/M264 boundary replay
```

Both gates must retain all success drops and avoid normal-history margin
regression beyond existing public-gate tolerances.

## Promotion Escalation

M310 is not allowed to promote directly after first gates. If it passes exact
and first replay gates, it should admit a separate full public-gate milestone:

```text
m311-full-public-gate-for-m310-repaired-ppo-proposal
```

That later gate must include:

```text
all six replay surfaces
protected-key diagnostic
behavior seeds 9505 and 9506
scoreboard update
```

## Failure Classification

Use these classifications:

| Failure | Classification |
| --- | --- |
| PPO raw or repaired candidate regresses exact M297/M270 | `objective_overfit` |
| PPO train metric looks good but exact full-corpus gates regress | `metric_artifact` |
| Exact gates pass but replay drops are lost | `proof_washout` |
| First gates pass but full public gate fails later | `promotion_gate_failure` |
| No usable movement beyond M307 | `training_instability` only if optimizer failed; otherwise archive as no-op |

## Decision

Admit:

```text
m310-fresh-ppo-proposal-exact-repair-smoke
```

Decision:

```text
admit_m310_fresh_ppo_proposal_exact_repair_smoke
```
