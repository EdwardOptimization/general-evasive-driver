# M540 Matched-History Training-Variance Design

## Purpose

M540 turns the M537-M539 evidence into a fair next training plan.

The key finding is not simply "L3 wins". The public diagnostics now say:

```text
L3 beats L0 robustly on public paired natural surfaces.
L3 beats L2 on aggregate, but L2 seed 3531 is a broad counterexample.
```

Therefore the next step must measure matched training variance before making a
strong recurrent-belief claim.

This milestone is design-only. It does not train or promote any checkpoint.

## Existing Baseline Recipe

The short-train configs are:

```text
configs/ppo_m531_matched_l0_short_train.json
configs/ppo_m531_matched_l2_short_train.json
configs/ppo_m531_matched_l3_short_train.json
```

Their shared budget:

```text
total_steps = 1024
rollout_steps = 64
num_envs = 4
update_epochs = 2
minibatch_size = 128
hidden_size = 64
learning_rate = 0.0003
log_std_init = -1.0
log_std_max = -0.5
```

The intended history-level differences are only:

| Level | Actor Encoder | Actor History Length | Env History Length | Recurrent Sequence Training |
| --- | --- | ---: | ---: | --- |
| L0 | `mlp` | `1` | `1` | no |
| L2 | `temporal_gru` | `4` | `4` | no |
| L3 | `human_view_online_gru` | `1` | `1` | yes |

The next configs must preserve this same fairness boundary. No history level may
receive a custom learning rate, task distribution, obstacle sampler, reward, or
randomization range unless the same change is applied to all levels.

## Training-Variance Ladder

Use a staged escalation. Do not jump from 1024-step short training to long
training or fresh-holdout claims.

| Stage | Purpose | Budget | Seeds | Action |
| --- | --- | ---: | --- | --- |
| V0 | config implementation | none | none | generate machine-checkable matched configs |
| V1 | route pilot | `4096` steps | `3540` | run L0/L2/L3 once; check metadata and route health |
| V2 | variance pilot | `4096` steps | `3540,3541,3542` | run all three levels; public frozen-source eval |
| V3 | variance repeat | `4096` steps | `3540-3544` | expand only if V2 has no route failures |
| V4 | budget repeat | `8192` or `16384` steps | frozen before launch | only after V3 shows interpretable variance |
| V5 | fresh holdout | no training | newly mined natural rows | only after recipe is frozen |

The immediate next milestone should be V0: create `ppo_m541_matched_*` configs
and tests. Training starts only after the config family is validated.

## Public Diagnostic Gates

Every trained checkpoint family must be evaluated in this order:

1. metadata and route eval from training output;
2. M537 frozen public natural surfaces;
3. M538 paired source-key audit;
4. M539-style seed/counterexample audit if L3-L2 is mixed;
5. only then a fresh natural holdout, with the recipe frozen.

M537/M538/M539 remain public diagnostics. They can guide debugging, but they are
not private evidence.

## Pass/Fail Rules

Evaluate L3 against L0 and L2 separately.

### L3 Versus L0

L3 can be called stronger than L0 on public diagnostics only if:

```text
paired success delta > +0.010
paired clearance margin delta > +0.050
CI lower bound for margin delta > 0
positive margin seeds >= 4 / 5 on V3
positive margin surfaces = 4 / 4
```

If this fails, classify as `seed_fragility` or `training_instability`, and do
not claim history-value beyond L0.

### L3 Versus L2

L2 is now a serious finite-window baseline. L3 can be called stronger than L2
only if:

```text
paired success delta > +0.005
paired clearance margin delta > +0.050
CI lower bound for margin delta > 0
positive margin seeds >= 4 / 5 on V3
positive success seeds >= 4 / 5 on V3
no seed has a broad M539-style L2-over-L3 counterexample
```

If L3 beats L0 but not L2, the correct conclusion is:

```text
history helps, but finite-window history remains competitive.
```

That result would still be useful. It would mean the current public surfaces do
not yet require online recurrent belief beyond a short command-response window.

## Failure Classification

Use structured outcomes:

| Condition | Classification | Next Step |
| --- | --- | --- |
| L3 beats L0 but not L2 | `finite_window_competitive` | improve recurrent training or mine longer-history surfaces |
| L3 loses to L0 or L2 in most seeds | `training_instability` | inspect PPO recipe and actor optimization |
| One seed flips result broadly | `seed_fragility` | repeat seeds before architecture claims |
| Public diagnostics pass but fresh holdout fails | `public_surface_overfit` | rotate holdout and revise scenario distribution |
| Metadata/input contract differs | `contract_violation` | reject run |

If `finite_window_competitive` becomes common, the research story should shift:
the evidence supports command-response history, but not necessarily unbounded
online memory under the current tasks.

## Fresh Holdout Boundary

Do not mine a fresh holdout until the matched training recipe is frozen.

When ready, the holdout should:

- use source seeds not present in M487/M497/M537/M538/M539;
- keep natural, non-projected source states;
- preserve the same P0 no-wheel/no-oracle actor contract;
- include both event-like and ordinary rows;
- be evaluated once for promotion-level evidence;
- be rotated if its failures are used for repair.

## Next Milestone

M541 should implement the V0 config family:

```text
configs/ppo_m541_matched_l0_variance_4096.json
configs/ppo_m541_matched_l2_variance_4096.json
configs/ppo_m541_matched_l3_variance_4096.json
```

Required tests should verify:

- shared PPO budget and task distribution;
- only approved history-level differences;
- P0 input contract;
- seed override path for V1/V2/V3 runs;
- no per-level hidden tuning.

## Decision

```text
matched_training_variance_design_admit_m541_variance_config_family
```
