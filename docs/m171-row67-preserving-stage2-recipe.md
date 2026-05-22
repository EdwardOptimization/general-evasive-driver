# M171 Row67-Preserving Stage2 Recipe

M170 improved the fixed M162 objective but lost boundary replay row `67`. M171
tries a more conservative stage2 recipe from the M168 admitted checkpoint:
shorter PPO stage and stronger action anchoring.

This is a negative result. Row `67` is retained, but the candidate loses other
boundary replay rows and fails normal-success retention.

## Config

Added:

```text
configs/ppo_m171_row67_stage2_s512_anchor100.json
```

Differences from M170/M166 micro config:

| Parameter | M170 | M171 |
| --- | ---: | ---: |
| total steps | 1024 | 512 |
| rollout steps | 128 | 64 |
| minibatch size | 512 | 256 |
| action anchor coef | 50.0 | 100.0 |
| init checkpoint | M168 admitted branch | M168 admitted branch |

The actor inputs and observation contract are unchanged.

## PPO Run

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m171_row67_stage2_s512_anchor100.json \
  --init-checkpoint runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --seed 7171 \
  --run-dir runs/ppo_m171_row67_stage2_s512_anchor100_seed7171
```

Training result:

```text
step=512 update=1 stage=base rollout_return_mean=34.88 reward_mean=0.989 episode_count=2
saved=runs/ppo_m171_row67_stage2_s512_anchor100_seed7171/checkpoint.pt
```

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 68.094879 |
| steps mean | 69.4 |
| termination rate | 0.2 |
| lateral RMSE mean | 0.926035 |
| beta abs error mean | 0.104078 |

## Fixed Outcome Objective

Run:

```text
runs/m171_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m163_a100_s20 | 0.398315 |
| m168_from_m167_5168 | 0.397971 |
| m170_stage2 | 0.397740 |
| m171_s512_a100 | 0.397869 |

The fixed objective improves versus M168, but not as much as M170. As with M170,
the fixed objective is not sufficient evidence.

## Full M164 Boundary Replay

Run:

```text
runs/m171_boundary_outcome_replay_gate_seed9510
```

| Metric | M163 | M171 | Delta |
| --- | ---: | ---: | ---: |
| normal success rate | 0.681818 | 0.659091 | -0.022727 |
| wrong-history success rate | 0.500000 | 0.500000 | 0.000000 |
| success-drop count | 16 | 14 | -2 |
| normal margin mean delta | | | -0.000158 |
| margin gap mean delta | | | +0.000367 |

Gate checks:

| Gate | Pass |
| --- | --- |
| normal success retention | false |
| normal margin retention | true |
| wrong-history gap retention | true |
| success-drop count retention | false |

The full M164 replay gate fails. This is worse than M170 because M171 also loses
normal success.

## Fragile Row Guard

Run:

```text
runs/m171_fragile_row_guard_seed9510
```

| Metric | Value |
| --- | --- |
| required rows | `[67]` |
| baseline success-drop count | 16 |
| candidate success-drop count | 14 |
| lost success-drop rows | `[70, 77]` |
| changed success-drop rows | `[70, 77]` |
| required row67 retained | true |
| gate pass | false |

M171 preserves row `67` but loses rows `70` and `77`. The problem is therefore
not a single-row issue; the fixed objective can improve while actual replay
retention degrades on different rows.

## Decision

M171 is rejected.

What passed:

- a more conservative PPO stage was run from the M168 admitted checkpoint;
- row `67` was retained;
- fixed objective improved versus M168.

What failed:

- full M164 replay normal success regressed;
- success-drop count dropped from `16` to `14`;
- fragile row guard found lost rows `70` and `77`;
- behavior retention and protected key were skipped because replay gates failed.

Decision: stop trying stage2 PPO variants until we audit why fixed objective
improvement is not aligned with full boundary replay retention.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.train_ppo ...
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ...
PYTHONPATH=src python -m autodrift.boundary_fragile_row_guard ... --required-row-id 67
```
