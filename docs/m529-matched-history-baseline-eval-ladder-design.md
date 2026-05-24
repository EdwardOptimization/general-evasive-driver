# M529 Matched History Baseline Eval Ladder Design

## Purpose

M529 pre-registers the evaluation ladder for trained matched-history baselines.
The goal is to compare history value without letting each baseline get a
separate training recipe, seed choice, or evaluation surface.

No training is run in M529. No checkpoint is promoted.

## Baseline Family

The baseline levels are:

```text
L0_current_observation:
  feedforward MLP over the current P0 frame.

L1_one_step_feedback:
  feedforward current P0 frame with previous physical commands and current
  actuator/IMU-like response. In the current canonical frame this is close to
  L0, so it should remain an annotation until a stricter frame split exists.

L2_finite_window:
  temporal_gru over a fixed P0 command-response window, no online hidden state.

L3_online_gru:
  mainline human_view_online_gru recurrent belief actor.
```

All levels must keep:

```text
P0 human-view no-wheel no-oracle contract
same task/curriculum distribution
same train seeds where practical
same PPO budget
same eval seeds
same public proof/generalization gates
same artifact retention
```

## Ladder

Use staged escalation:

```text
Stage 0: plumbing smoke
  One tiny run only checks config/checkpoint metadata and route validity.

Stage 1: repeat smoke
  Run 2-3 seeds for the same level with the same config budget.
  Purpose: detect routing or seed-specific crashes, not performance.

Stage 2: matched short train
  Train L0, L2, and L3 with the same short budget and frozen config family.
  Do not tune one level after seeing its result.

Stage 3: natural history-value eval
  Evaluate on M524/M526 natural event surfaces and recent mechanism surfaces.
  Keep projected surfaces separate from natural surfaces.

Stage 4: scenario-distribution eval
  Evaluate fresh randomized scenarios only after Stage 2/3 routes are stable.

Stage 5: promotion-level evidence
  Only after proof and generalization are stable, add private holdout discipline.
```

## Reliability Rules

Do not treat M528 smoke return as evidence. It used only `64` PPO steps and is
not a trained baseline.

Do not tune each baseline independently before comparison. If one config is
invalid or unstable for a level, record the failure first, then pre-register a
new shared recipe.

Do not use M526 natural event rows as a private holdout. They are public
diagnostic surfaces and may guide debugging. Promotion or paper-level claims
need a rotated/fresh holdout.

Keep all artifacts:

```text
config.json
checkpoint.pt
train_metrics.csv
eval_summary.json
stdout command line
history_baseline metadata
natural surface eval tables
scenario distribution summaries
```

## Next Executable Smoke

M530 should repeat the L0 current-observation smoke across fresh seeds using
the M528 config family and verify that artifact metadata is stable.

Suggested command family:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m528_l0_current_observation_smoke.json \
  --device cpu \
  --seed <seed> \
  --run-dir runs/m530_l0_current_observation_smoke_seed<seed>
```

Admission criteria for M530:

```text
all smoke runs complete
history_baseline metadata matches L0/P0 contract
no checkpoint is promoted
no performance claim is made
```

## Decision

```text
admit_m530_l0_baseline_smoke_repeat
```
