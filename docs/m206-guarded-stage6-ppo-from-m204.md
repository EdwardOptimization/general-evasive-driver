# M206 Guarded Stage6 PPO From M204

M206 runs one short guarded stage6 from the best fixed-loss retained stage5
checkpoint.

This milestone tests one additional 1024-step continuation only. It does not
run stage6 repeats or a longer PPO continuation.

## Setup

Initial checkpoint:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Training config:

```text
configs/ppo_m196_guarded_from_m194_smoke.json
```

The config still anchors actions to M194. Actor inputs are unchanged.

## Training

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5212 \
  --init-checkpoint runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt \
  --run-dir runs/ppo_m206_stage6_from_m204_seed5212
```

Artifact:

```text
runs/ppo_m206_stage6_from_m204_seed5212/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Outcome aux loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 77.822020 | 1.116533 | 10 | 0.156299 | 0.000427196 |

Smoke eval summary:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 80.117704 | 68.8 | 0.00 | 0.682196 | 0.154480 |

The smoke eval termination rate is `0.00`.

## Fixed M193 Objective Eval

Artifact:

```text
runs/m206_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean | Delta vs M204 |
| --- | ---: | ---: |
| m204_stage5 | 0.158475 | 0.000000 |
| m205_5210 | 0.158520 | 0.000045 |
| m205_5211 | 0.158503 | 0.000028 |
| m206_stage6 | 0.158420 | -0.000055 |

M206 improves the fixed M193 objective beyond M204.

## Replay Gates

All replay gates use M204 as the direct-parent retention baseline.

| Corpus | Rows | Baseline drops | M206 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | 0.000006 | 0.000096 | true |
| M183 M170 | 17 | 17 | 17 | 0.000000 | 0.000097 | true |
| M193 M189 | 14 | 14 | 14 | 0.000009 | 0.000179 | true |

Artifacts:

- `runs/m206_m183_m168_replay_gate_seed9510`
- `runs/m206_m183_m170_replay_gate_seed9510`
- `runs/m206_m193_m189_replay_gate_seed9630`

M206 preserves the old M183 replay surfaces and the refreshed M193 replay
surface relative to its direct parent.

## Behavior Retention

Artifacts:

- `runs/m206_behavior_gate_seed9505`
- `runs/m206_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m204_stage5 | 0.8625 | 0.1375 | 1.836804 |
| 9505 | m205_5211 | 0.8625 | 0.1375 | 1.836665 |
| 9505 | m206_stage6 | 0.8625 | 0.1375 | 1.836698 |
| 9505 | m206_stage6_noact | 0.8625 | 0.1375 | 1.840742 |
| 9505 | m206_stage6_reset | 0.8500 | 0.1250 | 1.834663 |
| 9505 | m206_stage6_zero_all | 0.8000 | 0.1250 | 1.852031 |
| 9506 | m204_stage5 | 0.8625 | 0.1375 | 1.854415 |
| 9506 | m205_5211 | 0.8625 | 0.1375 | 1.854271 |
| 9506 | m206_stage6 | 0.8625 | 0.1375 | 1.854295 |
| 9506 | m206_stage6_noact | 0.8625 | 0.1375 | 1.858224 |
| 9506 | m206_stage6_reset | 0.8500 | 0.1250 | 1.850952 |
| 9506 | m206_stage6_zero_all | 0.8000 | 0.1250 | 1.870003 |

Behavior success is retained. Reset-hidden and zero-all-response ablations
still degrade success. Zero-action-history remains behavior-neutral.

## Protected Key

Artifact:

```text
runs/m206_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m204_stage5 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m206_stage6 | 0 / 1 | false | 0.207450 | 0.109548 | 0.097903 |

M206 fails the protected key `9944|perturbed|28|28`.

The reference manifest uses `max_normal_margin = 0.2`. M206's selected
protected-key row has normal margin `0.207450`, which moves it outside the
pre-registered boundary acceptance window even though normal success remains
true and the wrong-history margin gap remains large.

## Decision

M206 is rejected:

- fixed M193 objective improves versus M204;
- smoke eval termination is `0.00`;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay drops `16/16` and `17/17` are retained;
- refreshed M193 replay drops `14/14` are retained;
- protected key fails with `0/1` accepted cases.

Decision:

```text
reject_stage6_protected_key_failure
```

Next step:

```text
m207-stage6-protected-key-failure-audit
```

Do not run stage6 repeats or longer PPO continuation until the protected-key
failure is audited and a guarded retry/design is pre-registered.
