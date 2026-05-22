# M220 Guarded Stage2 PPO From M219

M220 runs exactly one short guarded stage2 from the best retained M219 repeat,
seed `5216`. It keeps the M217 seed `10054` action anchor through the M218
config and does not change actor inputs.

## Setup

Initial checkpoint:

```text
runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt
```

Training config:

```text
configs/ppo_m218_guarded_from_m217_smoke.json
```

The config still anchors actions to:

```text
runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
```

## Training

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m218_guarded_from_m217_smoke.json \
  --seed 5217 \
  --init-checkpoint runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt \
  --run-dir runs/ppo_m220_stage2_from_m219_seed5217
```

Artifact:

```text
runs/ppo_m220_stage2_from_m219_seed5217/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Training termination | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 67.017624 | 1.041547 | 11 | 0.181818 | 0.204682 | 0.000033147 |

Built-in eval:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 67.456082 | 69.8 | 0.0000 | 1.536786 | 0.150227 |

Training reward is not used for promotion.

## Fixed M212 Objective Eval

Artifact:

```text
runs/m220_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M212 loss |
| --- | ---: |
| m204_5209 | 0.205221 |
| m217_10054 | 0.204291 |
| m218_5214 | 0.204267 |
| m219_5216 | 0.204240 |
| m220_5217 | 0.204179 |

M220 improves the fixed M212 objective versus M219.

## Replay Gates

Replay gates compare M220 against the M219 seed `5216` source checkpoint.

| Corpus | Rows | M220 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.000127 | 0.000102 | true |
| M183 M170 | 17 | 17 / 17 | -0.000135 | 0.000103 | true |
| M193 M189 | 14 | 14 / 14 | -0.000128 | 0.000201 | true |
| M212 M204 | 17 | 17 / 17 | -0.000145 | 0.000193 | true |

Artifacts:

- `runs/m220_m183_m168_replay_gate_seed9510`
- `runs/m220_m183_m170_replay_gate_seed9510`
- `runs/m220_m193_m189_replay_gate_seed9630`
- `runs/m220_m212_m204_replay_gate_seed10040`

All replay gates pass. The normal-margin deltas are slightly negative but well
inside the pre-registered `0.005` regression tolerance.

## Behavior Retention

Artifacts:

- `runs/m220_behavior_gate_seed9505`
- `runs/m220_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_5209 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m219_5216 | 0.8625 | 0.1375 | 1.836432 |
| 9505 | m220_5217 | 0.8625 | 0.1375 | 1.836227 |
| 9505 | m220_5217_reset | 0.8500 | 0.1500 | 1.834356 |
| 9505 | m220_5217_zero_all | 0.8000 | 0.2000 | 1.851733 |
| 9506 | m204_5209 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m219_5216 | 0.8625 | 0.1375 | 1.854007 |
| 9506 | m220_5217 | 0.8625 | 0.1375 | 1.853784 |
| 9506 | m220_5217_reset | 0.8500 | 0.1500 | 1.850637 |
| 9506 | m220_5217_zero_all | 0.8000 | 0.2000 | 1.869673 |

Behavior success is retained. Reset-hidden and zero-all-response ablations still
degrade success.

## Protected Key

Artifact:

```text
runs/m220_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m204_5209 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m217_10054 | 1 / 1 | true | 0.176641 | 0.083504 | 0.093137 |
| m218_5214 | 1 / 1 | true | 0.199560 | 0.100863 | 0.098696 |
| m219_5215 | 0 / 1 | false | 0.200679 | 0.102143 | 0.098536 |
| m219_5216 | 1 / 1 | true | 0.199571 | 0.100774 | 0.098797 |
| m220_5217 | 0 / 1 | false | 0.214602 | 0.119100 | 0.095502 |
| m206_stage6 | 0 / 1 | false | 0.207450 | 0.109548 | 0.097903 |
| m208_retry | 0 / 1 | false | 0.208742 | 0.111262 | 0.097479 |

M220 fails the protected key. The failure is the same class as M206/M208 and
M219 seed `5215`: normal success remains true and the margin gap remains large,
but normal margin leaves the old `0.2` near-boundary acceptance window. M220 is
therefore rejected despite better fixed objective and passing replay/behavior.

## Decision

M220 is negative:

- fixed M212 objective improves to `0.204179`;
- old M183, refreshed M193, and current M212 replay gates pass;
- behavior success remains `0.8625` on both broad seeds;
- protected key `9944|perturbed|28|28` fails with normal margin `0.214602`;
- current best remains M219 seed `5216`.

Decision:

```text
reject_stage2_protected_key_failure
```

Next step:

```text
m221-stage2-protected-key-failure-audit
```

Do not repeat M220 and do not run longer PPO from M220. The next milestone must
audit the protected-key drift and design a continuation path that protects the
near-boundary proof surface without simply training the driver to reduce
clearance on the old key.
