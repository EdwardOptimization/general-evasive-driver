# M298 Rejected-Preference Objective-Only Probe

M298 probes whether the M297 rejected-history preference loss has a useful
no-PPO update direction from the current M290 public-gate base. No PPO was run,
actor inputs were unchanged, and no checkpoint is promoted by this milestone.

## Setup

Base checkpoint:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Preference corpus:

```text
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
```

The objective-only optimizer updates only the actor-coupling train scope:

```text
steps = 40
batch_size = 17
learning_rate = 1e-5
seed = 10080
train_scope = actor_coupling
```

## Raw Objective Update

The raw update strongly improves the fixed objectives:

| Policy | M297 preference loss | Exact M270 loss |
| --- | ---: | ---: |
| m290x64_a500 | 1.191800 | 0.679278 |
| m298pref raw | 1.087123 | 0.615473 |

But the raw checkpoint destroys closed-loop replay behavior:

| Surface | Gate pass | Normal success | Success drops |
| --- | --- | ---: | ---: |
| M183/M170 | false | 0 / 17 | 0 / 17 |
| M267/M264 | false | 0 / 17 | 0 / 17 |

So the raw direction is useful as a gradient signal, not as a deployable
checkpoint.

## Interpolation Probe

M298 interpolates from M290 toward the raw objective checkpoint.

| Alpha | M297 preference loss | Exact M270 loss | M183/M170 pass |
| ---: | ---: | ---: | --- |
| 0.000 | 1.191800 | 0.679278 | true |
| 0.001 | 1.191690 | 0.679212 | true |
| 0.005 | 1.191252 | 0.678945 | true |
| 0.010 | 1.190704 | 0.678612 | true |
| 0.020 | 1.189610 | 0.677946 | true |
| 0.050 | 1.186331 | 0.675951 | false |
| 0.100 | 1.180887 | 0.672638 | false |
| 0.200 | 1.170074 | 0.666055 | not run |
| 0.500 | 1.138227 | 0.646648 | not run |
| 1.000 | 1.087123 | 0.615473 | false as raw |

The largest checked alpha that preserves M183/M170 is `0.02`. At `0.05`,
normal success drops to `16 / 17`, so the safety boundary is between `0.02`
and `0.05`.

## Selected Alpha

Selected diagnostic candidate:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Against M290:

| Metric | Delta |
| --- | ---: |
| M297 preference loss | -0.002190 |
| Exact M270 loss | -0.001332 |
| M183/M170 normal success | 0.000000 |
| M183/M170 normal margin mean | -0.000440 |
| M183/M170 margin gap mean | -0.000019 |
| M267/M264 normal success | 0.000000 |
| M267/M264 normal margin mean | -0.000406 |
| M267/M264 margin gap mean | -0.000033 |

Both required replay surfaces retain all `17 / 17` success drops.

## Interpretation

M298 is positive, but narrow. The M297 rejected-history preference objective
does provide a non-PPO direction that improves exact objectives and can be
interpolated without immediately losing M183/M170 or M267/M264 replay proof.

The raw update also shows why this cannot go straight into PPO: optimizing the
fixed loss aggressively creates severe closed-loop behavior regression.

## Decision

Do not promote `m298pref_a020` yet. It has passed only the M298 objective and
first replay checks, not the full public-gate stack.

Decision:

```text
admit_full_public_gate_for_m298pref_a020
```

Next step:

```text
m299-full-public-gate-for-m298-a020
```
