# M60 Constrained Baseline Anchor

Last updated: 2026-05-21

## Motivation

M59 showed that direct interpolation from M37_102 toward M56_028 is
behaviorally conservative but not positive-margin: all alphas retained success,
yet every nonzero alpha reduced mean clearance margin. M60 therefore moves away
from more reward-scale tuning and adds a constrained update mechanism:

- keep M37_102 as a frozen behavior anchor;
- allow PPO and margin reward to improve high-value states;
- penalize deterministic action drift back toward M37 on negative-advantage
  states;
- keep actor observations unchanged and deployable.

This is a training-only constraint. It does not add hidden vehicle parameters,
controller labels, oracle fields, or reference actions to the actor input.

## Implementation

M60 adds three PPO config fields:

- `baseline_action_anchor_coef`;
- `baseline_action_anchor_checkpoint`;
- `baseline_action_anchor_negative_advantage_only`.

When enabled, training loads a frozen reference `ActorCritic` with the same
architecture as the active actor. During rollout, the reference actor observes
the same deployable observation stream and carries its own recurrent hidden
state. The trainer stores the reference deterministic action mean for each
sample. During PPO update, it adds:

```text
mean_square(tanh(current_mean) - tanh(reference_mean))
```

If `baseline_action_anchor_negative_advantage_only` is true, the loss is
weighted only by negative normalized advantages. This makes the anchor act as a
retention term on low-value/non-improving samples rather than a blanket freeze.

## Config

Full-run config:

- `configs/ppo_m60_constrained_baseline_anchor_driver.json`
- init checkpoint: `m37_102`
- anchor checkpoint: `m37_102`
- margin reward: terminal clearance-margin scale `2.0`, matching M56
- learning rate: `5e-6`
- action anchor coefficient: `0.25`
- negative-advantage-only anchor: enabled

Full run command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m60_constrained_baseline_anchor_driver.json \
  --seed 2760 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m60_constrained_baseline_anchor_seed2760
```

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m60_constrained_baseline_anchor_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 2760 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m60_anchor_smoke_seed2760
```

Result:

- smoke completed successfully;
- run dir: `runs/ppo_m60_anchor_smoke_seed2760`;
- eval return mean: `65.0278`;
- eval termination rate: `0.100`;
- metrics include `response_prediction_loss_mean`;
- metrics include `baseline_action_anchor_loss_mean`.

Focused tests:

```bash
conda run -n autodrift pytest -q tests/test_checkpoints.py
```

Result: `28 passed`.

## Next Step

Run the full M60 continuation, sweep dense checkpoints through the unchanged
M38/broad/fresh margin-retention benchmark, then apply the strict gate. Promote
only if a checkpoint has no binary regressions, no near-margin regressions, and
non-negative mean margin delta versus M37_102.
