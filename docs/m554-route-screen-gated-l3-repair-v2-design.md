# M554 Route-Screen-Gated L3 Repair V2 Design

## Purpose

M554 designs the next L3 recurrent repair branch after M550-M553.

This is design-only. It does not train, evaluate public frozen-source rows, or
promote a checkpoint.

## Starting Evidence

M544-M550 established:

- L3 has a valid P0 human-view/no-wheel/no-oracle input contract.
- L3 can briefly learn useful route behavior, but the seed-3540 4096-step run
  peaks early and collapses late.
- M548 update-aligned checkpoints fixed the missing-checkpoint problem, but not
  the underlying L3 weakness.
- M549 selected one 5-episode route-health pass, `fast_select_ckpt256` step
  `2816`.
- M550 rejected that checkpoint on public frozen-source diagnostics: it improved
  over original L3 but remained below L0 and far below L2.
- M552 showed route-screen v2 would have rejected M549 before public eval.
- M553 made route-screen v2 reusable and reproduced the rejection.

Therefore the next branch should not repeat M548 with a different seed. It must
both target recurrent PPO instability and use route-screen v2 as the pre-public
admission rule.

## Frozen Boundaries

Keep fixed for the next diagnostic branch:

```text
actor input contract = P0_human_view_no_wheel_no_oracle
actor encoder = human_view_online_gru
env history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
track/task/randomization = M541/M548 L3 distribution
total_steps = 4096
num_envs = 4
seed = 3540 for the first diagnostic branch
checkpoint_interval_steps = 256
```

Do not change:

- actor inputs;
- reward terms;
- obstacle labels or feasibility filters;
- road/obstacle perception profile;
- L0/L2 reference checkpoints;
- public frozen-source rows as selection data.

## Allowed Repair Controls

The next branch may change PPO stability controls only:

- `learning_rate`;
- `update_epochs`;
- `clip_coef`;
- `max_grad_norm`;
- `rollout_steps`;
- `minibatch_size` as required by rollout length;
- `ent_coef`;
- `freeze_log_std` and `log_std_init`.

These controls address the observed L3 failure mode:

```text
early useful recurrent behavior -> later PPO update drift -> route/public failure
```

They do not change what the driver can see.

## Candidate Config Family

M555 should add a small L3-only config family.

| Candidate | Intent | PPO Changes From M548 `fast_select_ckpt256` |
| --- | --- | --- |
| `epoch1_clip01` | Reduce recurrent policy drift per rollout update | `learning_rate = 0.0001`, `update_epochs = 1`, `clip_coef = 0.10`, `max_grad_norm = 0.25` |
| `longseq_epoch1` | Give online-GRU updates a longer contiguous recurrent sequence | `rollout_steps = 128`, `minibatch_size = 128`, `learning_rate = 0.0001`, `update_epochs = 1`, `clip_coef = 0.10`, `max_grad_norm = 0.25` |
| `lowentropy_epoch1` | Test whether stochastic policy-scale drift is hurting deterministic route eval | `learning_rate = 0.0001`, `update_epochs = 1`, `clip_coef = 0.10`, `max_grad_norm = 0.25`, `ent_coef = 0.0005`, `freeze_log_std = true`, `log_std_init = -1.25` |

Do not add more variants in M555. The goal is a controlled diagnostic, not a
wide hyperparameter search.

## Route-Screen V2 Selection

M556 should train the M555 configs and evaluate all interval/final checkpoints
with `autodrift.route_screen_v2`.

The screen must include:

```text
l0_s3540 = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
l2_s3540 = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
all M555 L3 interval checkpoints as candidate labels
episodes >= 64
seed pre-registered before launch
uses_public_frozen_source_rows = false
```

Each policy must use its level-matched env config:

```text
L0: configs/ppo_m541_matched_l0_variance_4096.json
L2: configs/ppo_m541_matched_l2_variance_4096.json
L3 candidates: their own M555 L3 env configs
```

Admission rule:

```text
if no candidate passes L0 route-screen v2:
    stop; classify as training_instability / promotion_gate_failure

if candidate passes L0 but is far below L2:
    public diagnostic may be admitted, but no matched-repeat or promotion claim

if candidate passes L0 and is L2-competitive:
    admit public diagnostic and consider matched-repeat design after public result
```

L2-competitive means the existing M551 boundary:

```text
candidate_success_delta_vs_l2 >= -0.02
candidate_margin_delta_vs_l2 >= -0.05
```

## Public Diagnostic Boundary

Only after route-screen v2 pass:

1. Evaluate the selected L3 checkpoint on the same public M543 frozen-source
   natural surfaces used by M550.
2. Compare against L0, L2, original M542 L3, and M549 selected L3.
3. Use public rows only as diagnostics.

Minimum continuation condition:

```text
L3 selected - L0 paired success delta >= 0
L3 selected - L0 paired margin delta >= 0
```

If the selected L3 still fails L0, stop and audit PPO instability before more
training. If it beats L0 but remains below L2, continue only as a recurrent
repair diagnostic, not as an architecture win.

## Failure Taxonomy

Use:

| Condition | Failure Types |
| --- | --- |
| all route-screen v2 candidates fail L0 | `training_instability`, `promotion_gate_failure` |
| route-screen v2 admits candidate but public diagnostic fails L0 | `behavior_regression`, `promotion_gate_failure` |
| public result improves only on one surface or one seed | `seed_fragility` |
| any actor input or env shortcut is introduced | `contract_violation` |
| selection uses public frozen-source rows | `private_holdout_contamination` |

## Next Milestones

```text
M555: implement M554 L3 repair-v2 config family and tests; no training
M556: train M555 configs and run route-screen v2 multi-candidate selection
M557: only if M556 admits a candidate, run public frozen-source diagnostic
```

## Decision

```text
route_screen_gated_l3_repair_v2_design_admit_m555_config_family
```
