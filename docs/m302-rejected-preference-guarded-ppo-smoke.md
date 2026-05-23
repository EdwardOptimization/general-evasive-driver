# M302 Rejected-Preference Guarded PPO Smoke

M302 runs one smoke-scale PPO continuation from the M299 public-gate base using
the M301 rejected-history preference auxiliary loss. Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Config:

```text
configs/ppo_m302_rejected_preference_guarded_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
```

M302 remains smoke-scale:

```text
total_steps = 1024
learning_rate = 5e-7
rejected_history_preference_aux_coef = 0.03
```

The PPO run completed and wrote the new metric:

```text
rejected_history_preference_loss_mean = 1.1774653842051823
```

## Exact Objective Gates

M302 fails before replay promotion. Both exact gates regress on the raw PPO
checkpoint:

| Policy | Exact M297 preference | Exact M270 |
| --- | ---: | ---: |
| m298pref_a020 | 1.189609528 | 0.677945912 |
| m302raw | 1.190309286 | 0.678388774 |
| delta | +0.000699759 | +0.000442863 |

Because the exact gates regress, M302 does not run replay, protected-key, or
behavior promotion gates.

## Interpolation Check

A small interpolation sweep confirms the PPO direction is not usable under the
pre-registered exact gates.

| Alpha | Exact M297 preference | Exact M270 |
| ---: | ---: | ---: |
| 0.000 | 1.189609528 | 0.677945912 |
| 0.001 | 1.189610243 | 0.677946329 |
| 0.005 | 1.189612985 | 0.677948177 |
| 0.010 | 1.189616561 | 0.677950382 |
| 0.020 | 1.189623594 | 0.677954793 |
| 0.050 | 1.189644337 | 0.677968025 |
| 0.100 | 1.189679503 | 0.677990079 |
| 0.200 | 1.189749241 | 0.678034067 |
| 0.500 | 1.189959049 | 0.678166509 |
| 1.000 | 1.190309286 | 0.678388774 |

Every nonzero alpha worsens both exact M297 and exact M270.

## Interpretation

M302 is a negative result. The training-time auxiliary loss is wired and active,
but a small coefficient does not enforce the exact full-corpus M297 gate. The
sampled training metric is not sufficient evidence of retained rejected-history
preference.

The next step should audit the mismatch between sampled PPO training loss and
exact post-PPO gates before another PPO run. A likely repair is to make exact
M297/M270 retention lexicographic, or to add post-PPO projection/repair, rather
than relying only on a small scalar PPO auxiliary coefficient.

## Decision

Reject M302.

Failure types:

```text
objective_overfit
```

Decision:

```text
reject_m302_exact_objective_regression
```

Next step:

```text
m303-m302-preference-guard-failure-audit
```
