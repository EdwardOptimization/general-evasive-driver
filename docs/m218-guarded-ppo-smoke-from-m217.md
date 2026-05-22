# M218 Guarded PPO Smoke From M217

M218 runs one tiny guarded PPO smoke from the best M217 fresh-repeat actor-update
candidate. It does not run a repeat or longer continuation.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
```

Config:

```text
configs/ppo_m218_guarded_from_m217_smoke.json
```

Run:

```text
runs/ppo_m218_guarded_from_m217_seed5214/checkpoint.pt
```

The config keeps the M217 checkpoint as the baseline action anchor and uses the
M212 M204 boundary corpus as the outcome-intervention auxiliary objective.

## Training Smoke

Artifact:

```text
runs/ppo_m218_guarded_from_m217_seed5214
```

| Metric | Value |
| --- | ---: |
| total PPO steps | 1024 |
| rollout return mean | 70.143231 |
| reward mean | 1.006434 |
| training termination rate | 0.2000 |
| response prediction loss mean | 0.054342 |
| outcome intervention loss mean | 0.204019 |
| baseline action anchor loss mean | 0.000003389 |
| built-in eval return mean | 79.512170 |
| built-in eval termination rate | 0.0000 |

The training smoke is only a routing check. Promotion depends on fixed objective
and retention gates below.

## Fixed Batch Eval

Artifact:

```text
runs/m218_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M212 loss |
| --- | ---: |
| m204_5209 | 0.205221 |
| m216_10051 | 0.204291 |
| m217_10054 | 0.204291 |
| m218_5214 | 0.204267 |

M218 keeps the small M212 improvement and is slightly better than the M217
source checkpoint on this fixed batch.

## Replay Gates

Replay gates compare M218 against the M217 seed `10054` source checkpoint.

| Corpus | Rows | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | 0.000632 | 0.000125 | true |
| M183 M170 | 17 | 17 / 17 | 0.000624 | 0.000126 | true |
| M193 M189 | 14 | 14 / 14 | 0.000534 | 0.000221 | true |
| M212 M204 | 17 | 17 / 17 | 0.000537 | 0.000211 | true |

M218 does not wash out the proof rows. Normal margins improve slightly on all
four replay surfaces.

## Behavior Retention

Artifacts:

- `runs/m218_behavior_gate_seed9505`
- `runs/m218_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_5209 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m217_10054 | 0.8625 | 0.1375 | 1.836247 |
| 9505 | m218_5214 | 0.8625 | 0.1375 | 1.836438 |
| 9505 | m218_5214_reset | 0.8500 | 0.1500 | 1.834523 |
| 9505 | m218_5214_zero_all | 0.8000 | 0.2000 | 1.851880 |
| 9506 | m204_5209 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m217_10054 | 0.8625 | 0.1375 | 1.853820 |
| 9506 | m218_5214 | 0.8625 | 0.1375 | 1.854010 |
| 9506 | m218_5214_reset | 0.8500 | 0.1500 | 1.850807 |
| 9506 | m218_5214_zero_all | 0.8000 | 0.2000 | 1.869832 |

Behavior success is retained. Reset and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m218_critical_key_seed9944
```

| Policy | Accepted cases | Normal margin | Wrong-history margin | Margin gap | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| m204_5209 | 1 / 1 | 0.189607 | 0.094102 | 0.095505 | true |
| m217_10054 | 1 / 1 | 0.176641 | 0.083504 | 0.093137 | true |
| m218_5214 | 1 / 1 | 0.199560 | 0.100863 | 0.098696 | true |
| m206_stage6 | 0 / 1 | 0.207450 | 0.109548 | 0.097903 | false |
| m208_retry | 0 / 1 | 0.208742 | 0.111262 | 0.097479 | false |

M218 remains inside the protected-key acceptance window while rejected M206/M208
controls remain rejected.

## Decision

M218 is positive as a single guarded PPO smoke:

- fixed M212 objective remains improved versus M204 and slightly improves versus
  M217;
- old M183, refreshed M193, and current M212 replay gates pass;
- broad behavior and protected key pass.

Do not chain a longer PPO continuation from M218 yet. Repeat the exact M218
smoke recipe from the same M217 seed `10054` source checkpoint on fresh PPO seeds
before any longer stage.

Decision:

```text
admit_guarded_ppo_smoke_repeat_from_m217
```

Next step:

```text
m219-guarded-ppo-smoke-repeat-from-m217
```
