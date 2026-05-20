# M8 RL Professional Driver

Last updated: 2026-05-21

## Purpose

M8 is the first implementation step toward the project goal of a true
driver-like RL operator. The historical M8 run extended the M7 contract with an
explicit temporal actor; the current project contract has since been cleaned and
requires a fresh M8-style retrain.

The target behavior is:

```text
deployable observation history + previous actions
  -> recurrent/latent RL actor
  -> steering and throttle/brake
  -> vehicle response
  -> updated history
```

The actor is still direct low-level control. It does not receive rule labels,
controller modes, true friction, mass, CG, tire stiffness, brake scale, or
actuator parameters.

## M8 Baseline

Tracked config:

- `configs/ppo_m8_temporal_gru_driver.json`
- `configs/ppo_m8b_temporal_sequence_driver.json`

Actor and observation interface:

- `actor_encoder="temporal_gru"`;
- `actor_history_length=4`;
- `history_length=4`;
- `action_history_mode="full"`;
- the original M8 run used a 19-value obstacle frame and a 76-value stacked
  observation;
- the current clean driver contract uses a 15-value obstacle frame and a
  60-value stacked observation;
- removed actor inputs are `aeb_stop_distance`, explicit sideslip `beta`,
  `speed_ref`, and `beta_target`;
- previous actions are ordered as `[previous_steer, previous_drive_brake]`.

The temporal actor encodes each history frame, reverses the current-first
history into chronological order, and feeds the encoded sequence through a GRU.
The final GRU hidden state is the actor/critic latent used for action, value,
sequence prediction, and latent probes.

The historical M8 checkpoint remains useful as a baseline, but it was trained
before the observation cleanup and cannot be loaded into the current clean
contract. Observation-contract changes require retraining; no checkpoint
compatibility shim is kept.

## Stable AES Reward Shaping

M8 adds optional `ObstacleTaskConfig` fields:

- `stable_aes_beta_limit`;
- `stable_aes_sideslip_penalty`;
- `stable_aes_drift_bonus_scale`.

These fields only affect `aes_feasible` scenarios. They reduce drift reward and
penalize excessive sideslip when stable steering should be enough. Policies
must be trained under the current clean observation/action contract; old
checkpoints are evidence baselines, not migration targets.

The M8 config enables this shaping because the M7 gate rejected both M7-A and
M7-B for using too much high sideslip on `aes_feasible` cases.

## Smoke Command

Short infrastructure check:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m8_temporal_gru_driver.json \
  --total-steps 512 \
  --rollout-steps 64 \
  --eval-episodes 2 \
  --device cpu \
  --run-dir runs/ppo_m8_temporal_gru_smoke
```

Historical pre-clean result:

| item | value |
| --- | --- |
| run dir | `runs/ppo_m8_temporal_gru_smoke` |
| init mode | pre-clean `new_temporal_encoder` |
| curriculum stage | `stable_aes_only` |
| reward mean | 1.132 |
| eval return mean | 2.529 |
| eval steps mean | 29.000 |
| eval termination rate | 1.000 |
| eval lateral RMSE mean | 0.367 |
| eval beta abs error mean | 0.086 |

Interpretation: this was an infrastructure pass only. Under the current clean
project policy, the same smoke should train from scratch or from a strict
same-contract checkpoint. It does not prove the policy is useful; the smoke
checkpoint terminates quickly and must not be used as a performance claim.

## Driver Gate Smoke

Historical M8 was wired into the existing M7 gate as an optional required driver
candidate. The current `m8-driver-gate` Makefile target requires
`M8_CHECKPOINT` to point at a same-contract clean checkpoint.

```bash
conda run -n autodrift python -m autodrift.m7_gate \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --seed-csv runs/scenario_corpus_m7_aes_weighted_seed1300/scenario_corpus.csv \
  --episodes 60 \
  --seed 900 \
  --probe-episodes 6 \
  --probe-seed 1200 \
  --probe-epochs 20 \
  --device cpu \
  --run-dir runs/m8_driver_gate_corpus_smoke \
  --skip-probes \
  --driver-checkpoint runs/ppo_m8_temporal_gru_smoke/checkpoint.pt \
  --driver-name m8
```

Result:

| check | result |
| --- | --- |
| `success_beats_m5` | fail |
| `ablation_drop_present` | fail |
| `aes_feasible_sideslip_ok` | pass |
| `probe_temporal_lift_present` | fail, probes skipped |

Overall status: `needs_iteration`.

Key metrics:

| metric | value |
| --- | ---: |
| `selected_policy` | `m8` |
| `selected_success_rate` | 0.600 |
| `selected_success_delta_vs_m5` | -0.100 |
| `selected_min_ablation_drop` | 0.000 |
| `selected_aes_feasible_high_sideslip` | 0.000 |
| `m5_success_rate` | 0.700 |
| `m7a_success_rate` | 0.700 |
| `m7b_success_rate` | 0.700 |

Label-bucket result:

| policy | `aes_feasible` success / high sideslip | `drift_required` success / high sideslip | `unavoidable` success |
| --- | --- | --- | ---: |
| M5 | 1.000 / 0.090 | 0.950 / 0.059 | 0.150 |
| M7-A | 1.000 / 0.292 | 0.950 / 0.079 | 0.150 |
| M7-B | 1.000 / 0.171 | 0.950 / 0.069 | 0.150 |
| M8 smoke | 1.000 / 0.000 | 0.750 / 0.018 | 0.050 |

Interpretation: the untrained M8 smoke checkpoint shows the intended stable-AES
direction, but it loses too much `drift_required` and `unavoidable` performance
and its ablations do not show a useful temporal mechanism. This is negative
evidence, not a driver-v1 result.

## Full Training Commands

Best M8-A seed:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m8_temporal_gru_driver.json \
  --seed 227 \
  --device cuda \
  --run-dir runs/ppo_m8_temporal_gru_driver_seed227
```

Sequence-head variant:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m8b_temporal_sequence_driver.json \
  --device cuda \
  --run-dir runs/ppo_m8b_temporal_sequence_driver_seed223
```

## Full Driver Gate Results

These results are historical pre-clean-contract evidence. They used the old
76-value M8 checkpoint and should not be compared as a current driver under the
60-value actor contract.

All rows use the same 60-seed label-balanced corpus:

```bash
conda run -n autodrift python -m autodrift.m7_gate \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --seed-csv runs/scenario_corpus_m7_aes_weighted_seed1300/scenario_corpus.csv \
  --episodes 60 \
  --seed 900 \
  --probe-episodes 100 \
  --probe-seed 1200 \
  --probe-epochs 160 \
  --device cpu \
  --run-dir runs/m8_driver_gate_seed227 \
  --driver-checkpoint runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt \
  --driver-name m8
```

| checkpoint | status | success | delta vs M5 | `aes_feasible` high sideslip | ablation drop | probe temporal lift |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M8-A seed211 | `needs_iteration` | 0.733 | 0.033 | 0.159 | 0.000 | 0.022 |
| M8-A seed227 | `needs_iteration` | 0.733 | 0.033 | 0.038 | 0.000 | 0.022 |
| M8-B sequence seed223 | `needs_iteration` | 0.733 | 0.033 | 0.165 | 0.000 | -0.005 |

Historical best: M8-A seed227.

Label-bucket comparison for M8-A seed227:

| policy | `aes_feasible` success / high sideslip | `drift_required` success / high sideslip | `unavoidable` success |
| --- | --- | --- | ---: |
| M5 | 1.000 / 0.090 | 0.950 / 0.059 | 0.150 |
| M7-A | 1.000 / 0.292 | 0.950 / 0.079 | 0.150 |
| M7-B | 1.000 / 0.171 | 0.950 / 0.069 | 0.150 |
| M8-A seed227 | 1.000 / 0.038 | 0.950 / 0.024 | 0.250 |

Interpretation:

- M8-A seed227 is a real improvement over M5/M7 on the current corpus:
  aggregate success improves from 0.700 to 0.733, `unavoidable` success improves
  from 0.150 to 0.250, and `aes_feasible` high-sideslip drops well below the
  0.150 threshold.
- The latent probe has temporal signal over shuffled history, so the GRU state
  is not empty.
- The policy still fails the driver gate because success is unchanged when
  action history is zeroed or history order is shuffled. This means the current
  benchmark does not yet prove behavior-level closed-loop self-identification.

M8-B is not the next direction. Adding a sequence head did not improve the gate:
stable-AES high-sideslip rose and temporal probe lift fell below threshold.

## Current Blocker

The remaining blocker is now the clean-contract retrain. The old M8 checkpoint
cannot be adapted into the 60-value actor frame, so the next result must be
trained under the new input/output contract before the gate can be interpreted
again.

The detailed blocker report is in `docs/m8-driver-gate-blocker-report.md`.

The next iteration should make the validation task more history-critical rather
than only training another similar policy. Candidate directions:

- train a clean 60-value temporal driver from scratch;
- add a driver-gate stress set with friction steps or actuator-lag changes close
  to obstacle approach;
- add training augmentation that sometimes degrades the current frame so the GRU
  must use response history;
- add a true online recurrent hidden-state actor and compare it against the
  fixed-window GRU.

## Next Work

- Retrain the best M8-A architecture under the clean 60-value driver contract.
- Add a history-critical stress subset to the driver gate.
- Only call the project driver-v1 complete when both aggregate success and
  behavior-level temporal ablations pass.
