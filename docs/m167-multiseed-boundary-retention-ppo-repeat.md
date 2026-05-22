# M167 Multiseed Boundary-Retention PPO Repeat

M166 was a positive single-seed PPO micro-smoke: it fixed the M165 blocker by
preserving the fixed M164 boundary replay success-drop count. M167 repeats the
same 1024-step anchor50 recipe across two more seeds before allowing any longer
PPO continuation.

This is a positive repeat result. It admits staged PPO extension, not an
unguarded long PPO run.

## Setup

All repeats start from M163, not from the failed M165 checkpoint.

```text
configs/ppo_m166_boundary_retention_micro.json
runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt
```

The actor inputs and observation contract are unchanged.

## PPO Repeats

| Seed | Run | Rollout return | Eval return | Eval termination | Checkpoint |
| ---: | --- | ---: | ---: | ---: | --- |
| 5167 | `runs/ppo_m167_boundary_retention_micro_seed5167` | 63.057249 | 80.618552 | 0.0 | `checkpoint.pt` |
| 5168 | `runs/ppo_m167_boundary_retention_micro_seed5168` | 63.947151 | 69.247821 | 0.2 | `checkpoint.pt` |

Seed `5167` has the cleaner short eval termination rate. Seed `5168` has the
better fixed outcome objective below. This means M167 should be treated as a
recipe-stability result rather than a single clear checkpoint win.

## Fixed Outcome Objective

Run:

```text
runs/m167_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m163_a100_s20 | 0.398315 |
| m166_1024 | 0.398266 |
| m167_5167 | 0.398423 |
| m167_5168 | 0.398195 |

Seed `5167` slightly worsens the fixed objective versus M163. Seed `5168`
improves it. This is why M167 does not justify selecting a candidate purely by
training rollout reward or by one fixed objective metric.

## Boundary Replay Gate

Both repeats replayed the exact M162 boundary-outcome corpus under the M164
gate, using M163 as the baseline.

| Candidate | Normal success | Wrong-history success | Success drops | Normal margin delta | Margin gap delta | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| m167_5167 | 0.681818 | 0.500000 | 16 | -0.000064 | +0.000121 | pass |
| m167_5168 | 0.681818 | 0.500000 | 16 | +0.000234 | +0.000131 | pass |

The important M165 failure mode does not recur: neither repeat loses the 16
wrong-history success-drop rows.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.846266 |
| m167_5167 | 0.8625 | 0.1375 | 1.846209 |
| m167_5167_reset | 0.8500 | 0.1500 | 1.842022 |
| m167_5167_zero_current | 0.8000 | 0.2000 | 1.856481 |
| m167_5167_zero_all | 0.8000 | 0.2000 | 1.856481 |
| m167_5167_noact | 0.8625 | 0.1375 | 1.847271 |
| m167_5168 | 0.8625 | 0.1375 | 1.846281 |
| m167_5168_reset | 0.8500 | 0.1500 | 1.842109 |
| m167_5168_zero_current | 0.8000 | 0.2000 | 1.856535 |
| m167_5168_zero_all | 0.8000 | 0.2000 | 1.856535 |
| m167_5168_noact | 0.8625 | 0.1375 | 1.847313 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.853828 |
| m167_5167 | 0.8625 | 0.1375 | 1.853758 |
| m167_5167_reset | 0.8500 | 0.1500 | 1.850156 |
| m167_5167_zero_current | 0.8000 | 0.2000 | 1.868445 |
| m167_5167_zero_all | 0.8000 | 0.2000 | 1.868445 |
| m167_5167_noact | 0.8625 | 0.1375 | 1.856224 |
| m167_5168 | 0.8625 | 0.1375 | 1.853840 |
| m167_5168_reset | 0.8500 | 0.1500 | 1.850248 |
| m167_5168_zero_current | 0.8000 | 0.2000 | 1.868507 |
| m167_5168_zero_all | 0.8000 | 0.2000 | 1.868507 |
| m167_5168_noact | 0.8625 | 0.1375 | 1.856276 |

Both repeats preserve the same behavior and response-ablation pattern as M166.
No-action history remains behavior-neutral.

## Protected Critical Key

Protected key:

```text
9944|perturbed|28|28
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m163_a100_s20 | 1 / 1 | true |
| m167_5167 | 1 / 1 | true |
| m167_5168 | 1 / 1 | true |

The protected key passes for both repeats.

## Decision

M167 is positive as a multiseed recipe repeat.

What passed:

- two additional M166-style micro seeds were trained from M163;
- both repeats preserve the M164 boundary replay success-drop count at `16`;
- both repeats pass behavior retention on seeds `9503` and `9504`;
- both repeats pass the protected critical key;
- one repeat improves the fixed M162 outcome objective and one slight regression
  remains harmless under the actual boundary replay gate.

What remains weak:

- this is still only 1024 PPO steps per seed;
- no-action history remains behavior-neutral;
- no single M167 repeat strictly dominates M166 on every metric;
- M167 is not a self-ID proof and not a reason to run unguarded long PPO.

Decision: admit M168 staged boundary-retention PPO extension. Each stage must
rerun the fixed objective and M164 boundary replay gate before continuing.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.train_ppo ... --seed 5167
PYTHONPATH=src python -m autodrift.train_ppo ... --seed 5168
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ... m167_5167
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ... m167_5168
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9503
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9504
PYTHONPATH=src python -m autodrift.critical_key_replay_guard ...
```
