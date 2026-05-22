# M168 Staged Boundary-Retention PPO Extension

M167 showed that the M166 1024-step anchor50 PPO micro recipe is repeatable
across seeds, but did not justify an unguarded longer PPO run. M168 tests one
short staged continuation from two already-passed parents and gates each stage
with the fixed M162 objective and M164 boundary replay before behavior checks.

This is a conditional positive result: one stage branch passes and one stage
branch fails. The passing branch may be used for the next guarded stage. The
failed branch must not be continued.

## Setup

Both candidates used the unchanged M166 micro config:

```text
configs/ppo_m166_boundary_retention_micro.json
```

Both kept the same M163 action anchor:

```text
runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt
```

The actor inputs and observation contract are unchanged.

## Stage 1 PPO Runs

| Candidate | Init checkpoint | Seed | Eval return | Eval termination | Checkpoint |
| --- | --- | ---: | ---: | ---: | --- |
| m168_from_m166 | `runs/ppo_m166_boundary_retention_micro_seed5166/checkpoint.pt` | 6166 | 70.024493 | 0.2 | `runs/ppo_m168_stage1_from_m166_seed6166/checkpoint.pt` |
| m168_from_m167_5168 | `runs/ppo_m167_boundary_retention_micro_seed5168/checkpoint.pt` | 6168 | 71.131161 | 0.2 | `runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt` |

Both smoke evals have nonzero termination rate, so rollout return alone is not
admissible evidence for continuation.

## Fixed Outcome Objective

Run:

```text
runs/m168_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m163_a100_s20 | 0.398315 |
| m166_1024 | 0.398266 |
| m167_5168 | 0.398195 |
| m168_from_m166 | 0.398426 |
| m168_from_m167_5168 | 0.397971 |

The M166 branch worsens the fixed objective versus M163. The M167_5168 branch
improves it.

## Boundary Replay Gate

Both candidates replayed the exact M162 boundary-outcome corpus under the M164
gate with M163 as the baseline.

| Candidate | Normal success | Wrong-history success | Success drops | Normal margin delta | Margin gap delta | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| m168_from_m166 | 0.681818 | 0.511364 | 15 | +0.000865 | +0.001572 | fail |
| m168_from_m167_5168 | 0.681818 | 0.500000 | 16 | +0.000325 | +0.000233 | pass |

The M166 branch repeats the M165 failure mode: it loses one wrong-history
success-drop row. The M167_5168 branch preserves the full count of `16`.

The lost row in the failed branch is:

```text
row_id=67
target=future_lateral_accel_response
physical_pair_key=9530:21:9540:24
relocated_obstacle_body_x=9.638490
relocated_obstacle_body_y=-0.970711
relocated_obstacle_half_width=0.726590
```

For row `67`, M163 and the passing M168 branch keep `normal_success=True` and
`wrong_history_success=False`. The failed M166 branch changes the wrong-history
rollout to `wrong_history_success=True`, so it is rejected.

## Behavior Retention

Only the replay-passing candidate was evaluated on behavior retention.

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.846266 |
| m168_from_m167_5168 | 0.8625 | 0.1375 | 1.846380 |
| m168_from_m167_5168_reset | 0.8500 | 0.1500 | 1.842043 |
| m168_from_m167_5168_zero_current | 0.8000 | 0.2000 | 1.856456 |
| m168_from_m167_5168_zero_all | 0.8000 | 0.2000 | 1.856456 |
| m168_from_m167_5168_noact | 0.8625 | 0.1375 | 1.847557 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.853828 |
| m168_from_m167_5168 | 0.8625 | 0.1375 | 1.853938 |
| m168_from_m167_5168_reset | 0.8500 | 0.1500 | 1.850184 |
| m168_from_m167_5168_zero_current | 0.8000 | 0.2000 | 1.868423 |
| m168_from_m167_5168_zero_all | 0.8000 | 0.2000 | 1.868423 |
| m168_from_m167_5168_noact | 0.8625 | 0.1375 | 1.856494 |

Behavior retention passes for the replay-passing branch. No-action history
remains behavior-neutral.

## Protected Critical Key

Run:

```text
runs/m168_from_m167_5168_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m163_a100_s20 | 1 / 1 | true |
| m168_from_m167_5168 | 1 / 1 | true |

The protected key passes for the admitted branch.

## Decision

M168 is conditionally positive.

What passed:

- one short continuation stage from M167_5168 improves the fixed objective;
- the admitted stage preserves M164 boundary replay success drops at `16`;
- behavior seeds `9503` and `9504` retain aggregate success and ablation gaps;
- the protected critical key remains accepted.

What failed:

- the same staged continuation from M166 loses row `67` and fails M164 replay;
- both stage smoke evals have termination rate `0.2`;
- no-action history remains behavior-neutral;
- this is not a self-ID proof and not a reason for unguarded long PPO.

Decision: admit only the M167_5168 stage branch for the next guarded step. The
next step must explicitly protect row `67` or audit stage sensitivity before any
further PPO extension.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.train_ppo ... --init-checkpoint runs/ppo_m166_boundary_retention_micro_seed5166/checkpoint.pt --seed 6166
PYTHONPATH=src python -m autodrift.train_ppo ... --init-checkpoint runs/ppo_m167_boundary_retention_micro_seed5168/checkpoint.pt --seed 6168
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ... m168_from_m166
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ... m168_from_m167_5168
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9503
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9504
PYTHONPATH=src python -m autodrift.critical_key_replay_guard ...
```
