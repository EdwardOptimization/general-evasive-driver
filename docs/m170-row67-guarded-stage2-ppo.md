# M170 Row67-Guarded Stage2 PPO

M169 added a row-level fragile boundary replay guard for row `67`. M170 tests
one more short PPO stage from the M168 admitted branch and requires fixed
objective, full M164 replay, and row67 guard before any behavior or protected
key checks.

This is a negative result. The candidate improves the fixed objective but fails
full boundary replay and the row67 guard.

## Setup

Stage2 starts only from the M168 admitted branch:

```text
runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt
```

It uses the unchanged M166 micro config and the same M163 action anchor:

```text
configs/ppo_m166_boundary_retention_micro.json
runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt
```

The actor inputs and observation contract are unchanged.

## PPO Run

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m166_boundary_retention_micro.json \
  --init-checkpoint runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --seed 7170 \
  --run-dir runs/ppo_m170_row67_guarded_stage2_seed7170
```

Training result:

```text
step=1024 update=1 stage=base rollout_return_mean=75.07 reward_mean=1.102 episode_count=11
saved=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt
```

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 68.562053 |
| steps mean | 69.0 |
| termination rate | 0.2 |
| lateral RMSE mean | 0.962101 |
| beta abs error mean | 0.083898 |

The smoke eval still has nonzero termination, so gates are decisive.

## Fixed Outcome Objective

Run:

```text
runs/m170_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m163_a100_s20 | 0.398315 |
| m168_from_m167_5168 | 0.397971 |
| m170_stage2 | 0.397740 |

The fixed objective improves. This is not sufficient because M170 must also
preserve actual boundary replay outcomes.

## Full M164 Boundary Replay

Run:

```text
runs/m170_boundary_outcome_replay_gate_seed9510
```

| Metric | M163 | M170 | Delta |
| --- | ---: | ---: | ---: |
| normal success rate | 0.681818 | 0.681818 | 0.000000 |
| wrong-history success rate | 0.500000 | 0.511364 | +0.011364 |
| success-drop count | 16 | 15 | -1 |
| normal margin mean delta | | | +0.000734 |
| margin gap mean delta | | | +0.001703 |

Gate checks:

| Gate | Pass |
| --- | --- |
| normal success retention | true |
| normal margin retention | true |
| wrong-history gap retention | true |
| success-drop count retention | false |

The full M164 replay gate fails because the candidate loses one success-drop row.

## Row67 Guard

Run:

```text
runs/m170_fragile_row_guard_seed9510
```

| Metric | Value |
| --- | --- |
| required rows | `[67]` |
| baseline success-drop count | 16 |
| candidate success-drop count | 15 |
| lost success-drop rows | `[67]` |
| changed success-drop rows | `[67]` |
| gate pass | false |

The lost row is the known fragile row `67`, so the M169 guard catches the
failure directly.

## Decision

M170 is rejected.

What passed:

- stage2 training completed;
- fixed M162 objective improved from M168 `0.397971` to M170 `0.397740`;
- normal boundary success and normal margin were retained.

What failed:

- full M164 boundary replay lost one success-drop row;
- row67 guard failed with lost row `[67]`;
- behavior retention and protected key were not run because the earlier gates
  already rejected the candidate.

Decision: do not continue from `runs/ppo_m170_row67_guarded_stage2_seed7170`.
The next step should test a more conservative row67-preserving stage2 recipe
from the M168 admitted checkpoint, not from this failed M170 checkpoint.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.train_ppo ...
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ...
PYTHONPATH=src python -m autodrift.boundary_fragile_row_guard ... --required-row-id 67
```
