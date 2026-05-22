# M219 Guarded PPO Smoke Repeat From M217

M219 repeats the M218 tiny guarded PPO smoke from the same M217 seed `10054`
source checkpoint on fresh PPO seeds. The repeats are not chained from M218.

Actor inputs are unchanged.

## Setup

Initial checkpoint for both repeats:

```text
runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
```

Training config:

```text
configs/ppo_m218_guarded_from_m217_smoke.json
```

The config keeps the M217 checkpoint as the strong action anchor and uses the
M212 M204 boundary corpus as the outcome-intervention auxiliary objective.

## Training

Artifacts:

- `runs/ppo_m219_guarded_from_m217_seed5215/checkpoint.pt`
- `runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt`

| Seed | Rollout return mean | Reward mean | Training termination | Outcome aux loss | Anchor loss | Built-in eval return | Built-in eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5215 | 77.742570 | 1.078217 | 0.100000 | 0.200085 | 0.000005026 | 75.526753 | 0.0000 |
| 5216 | 68.096465 | 1.049170 | 0.166667 | 0.199095 | 0.000004969 | 73.776193 | 0.0000 |

Training reward is not used for promotion. Promotion depends on fixed objective
and retention gates below.

## Fixed M212 Objective Eval

Artifact:

```text
runs/m219_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M212 loss |
| --- | ---: |
| m204_5209 | 0.205221 |
| m217_10054 | 0.204291 |
| m218_5214 | 0.204267 |
| m219_5215 | 0.204423 |
| m219_5216 | 0.204240 |

Both repeats remain improved versus M204. Seed `5216` is the best fixed-loss
repeat; seed `5215` is worse than M218 but still better than M204.

## Replay Gates

Replay gates compare each M219 repeat against the M217 seed `10054` source
checkpoint.

| Candidate | Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m219_5215 | M183 M168 | 16 | 16 / 16 | 0.000854 | 0.000114 | true |
| m219_5215 | M183 M170 | 17 | 17 / 17 | 0.000846 | 0.000114 | true |
| m219_5215 | M193 M189 | 14 | 14 / 14 | 0.000750 | 0.000212 | true |
| m219_5215 | M212 M204 | 17 | 17 / 17 | 0.000757 | 0.000203 | true |
| m219_5216 | M183 M168 | 16 | 16 / 16 | 0.000575 | 0.000123 | true |
| m219_5216 | M183 M170 | 17 | 17 / 17 | 0.000566 | 0.000123 | true |
| m219_5216 | M193 M189 | 14 | 14 / 14 | 0.000479 | 0.000219 | true |
| m219_5216 | M212 M204 | 17 | 17 / 17 | 0.000481 | 0.000210 | true |

Both repeats preserve old M183, refreshed M193, and current M212 replay drops.

## Behavior Retention

Artifacts:

- `runs/m219_behavior_gate_seed9505`
- `runs/m219_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_5209 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m217_10054 | 0.8625 | 0.1375 | 1.836247 |
| 9505 | m218_5214 | 0.8625 | 0.1375 | 1.836438 |
| 9505 | m219_5215 | 0.8625 | 0.1375 | 1.836588 |
| 9505 | m219_5216 | 0.8625 | 0.1375 | 1.836432 |
| 9505 | m219_5216_reset | 0.8500 | 0.1500 | 1.834539 |
| 9505 | m219_5216_zero_all | 0.8000 | 0.2000 | 1.851892 |
| 9506 | m204_5209 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m217_10054 | 0.8625 | 0.1375 | 1.853820 |
| 9506 | m218_5214 | 0.8625 | 0.1375 | 1.854010 |
| 9506 | m219_5215 | 0.8625 | 0.1375 | 1.854163 |
| 9506 | m219_5216 | 0.8625 | 0.1375 | 1.854007 |
| 9506 | m219_5216_reset | 0.8500 | 0.1500 | 1.850824 |
| 9506 | m219_5216_zero_all | 0.8000 | 0.2000 | 1.869845 |

Behavior success is retained. Reset-hidden and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m219_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m204_5209 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m217_10054 | 1 / 1 | true | 0.176641 | 0.083504 | 0.093137 |
| m218_5214 | 1 / 1 | true | 0.199560 | 0.100863 | 0.098696 |
| m219_5215 | 0 / 1 | false | 0.200679 | 0.102143 | 0.098536 |
| m219_5216 | 1 / 1 | true | 0.199571 | 0.100774 | 0.098797 |
| m206_stage6 | 0 / 1 | false | 0.207450 | 0.109548 | 0.097903 |
| m208_retry | 0 / 1 | false | 0.208742 | 0.111262 | 0.097479 |

Seed `5215` fails only the protected-key acceptance window: normal success and
wrong-history gap remain large, but normal margin moves to `0.200679`, just
above the old `0.2` max-normal-margin boundary. Seed `5216` stays inside the
protected-key window and is the only promotable M219 repeat.

## Decision

M219 is positive only for seed `5216`:

- both repeats keep fixed M212 loss improved versus M204;
- both repeats preserve old M183, refreshed M193, and current M212 replay
  drops;
- both repeats preserve broad behavior success;
- seed `5215` fails the protected key by leaving the near-boundary margin
  window;
- seed `5216` passes the protected key and has the best fixed M212 loss.

Decision:

```text
admit_guarded_stage2_from_m219_seed5216
```

Next step:

```text
m220-guarded-stage2-ppo-from-m219
```

M220 should run exactly one short guarded stage2 from M219 seed `5216`, keeping
the M217 action anchor in the same config. Do not chain from M218 or M219 seed
`5215`.
