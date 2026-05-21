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

## Full Run

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m60_constrained_baseline_anchor_driver.json \
  --seed 2760 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m60_constrained_baseline_anchor_seed2760
```

Training completed with 8 dense checkpoints:

- `m60_004` through `m60_032`;
- final eval return mean: `65.6985`;
- final eval termination rate: `0.100`;
- metrics include `baseline_action_anchor_loss_mean`.

Validation artifacts:

- `runs/m60_m38_margin_benchmark_seed4300`;
- `runs/m60_broad_margin_benchmark_seed3000`;
- `runs/m60_fresh_margin_benchmark_seed5200`;
- `runs/m60_margin_critical_corpus`;
- `runs/m60_margin_retention_gate_strict`.

Strict gate result: `needs_iteration`; passed candidates: none.

| Candidate | Success Delta | Binary Regressions | Near-Margin Regressions | Mean Margin Delta | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| `m60_004` | 0.000000 | 0 | 1 | -0.000118 | false |
| `m60_008` | 0.000000 | 0 | 2 | -0.000870 | false |
| `m60_012` | -0.012500 | 2 | 4 | 0.000092 | false |
| `m60_016` | 0.000000 | 0 | 4 | 0.000062 | false |
| `m60_020` | -0.006250 | 1 | 4 | 0.000361 | false |
| `m60_024` | -0.012500 | 2 | 8 | -0.000643 | false |
| `m60_028` | -0.012500 | 2 | 8 | -0.000001 | false |
| `m60_032` | -0.012500 | 2 | 8 | -0.000395 | false |

M60 is not promotable, but it is the first continuation in this margin series
to produce non-negative combined mean-margin deltas on some checkpoints. The
blocker moved from aggregate mean margin to specific near-boundary regressions.

Key regression seeds:

| Seed | Source | Candidate | Outcome | Notes |
| ---: | --- | --- | --- | --- |
| 4413 | M38 | `m60_004`, `m60_016`, `m60_020` | unchanged failure | drift-required, medium-mu, heavy, slow steering; failure becomes much deeper |
| 4378 | M38 | `m60_016`, `m60_020` | unchanged failure | drift-required, low-mu, light, weak brake, slow steering |
| 4457 | M38 | `m60_016`, `m60_020` | success margin loss / binary regression | unavoidable, low-mu, heavy, strong brake |
| 3019 | broad | `m60_016`, `m60_020` | unchanged failure | unavoidable, high-mu, strong brake, slow steering |

## Conclusion

M60 validates the baseline-anchor direction but not this coefficient/sampling
choice. The anchor prevents broad drift compared with unconstrained reward
continuations, and some checkpoints improve mean margin, but the strict gate
correctly rejects them because near-boundary failures get worse.

## Next Step

M61 should replay the M60 regression seeds explicitly and strengthen retention
on near-boundary states:

- increase or schedule the baseline action anchor;
- oversample seeds `4413`, `4378`, `4457`, and `3019`;
- add a near-boundary floor criterion before accepting mean-margin gains;
- keep the strict gate unchanged.
