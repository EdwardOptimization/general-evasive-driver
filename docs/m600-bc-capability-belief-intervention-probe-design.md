# M600 BC Capability Belief-Intervention Probe Design

## Purpose

M600 designs a probe that sits between M598 head-only learning and any actor
fine-tuning.

Question:

```text
Do wrong/delayed recurrent histories change the learned capability belief even
though M591 showed they do not change action?
```

This milestone is design-only:

```text
no actor update
no head retraining
no PPO
no route evaluation
no checkpoint promotion
```

## Probe Object

Use:

```text
actor checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
capability head:  runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt
target stats:      runs/m598_bc_capability_repair_head_only_smoke/summary.json
```

The capability head was trained on `base_next_hidden_seq`, so the probe must
compare predictions after applying the recurrent update for the current
observation:

```text
features, next_hidden = actor.recurrent_features_tensor(obs_variant, hidden_variant)
capability = capability_head(next_hidden)
```

Do not feed capability labels to the actor. They are used only for z-score
normalization and interpretation.

## Surfaces

Use the same BC5660 matched-current pair surfaces as M591:

```text
runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv
runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
```

The probe should reconstruct snapshots using the same environment configs:

```text
configs/ppo_m541_matched_l3_variance_4096.json
configs/eval_m574_moderate_ood_l3.json
```

## Variants

Required hidden variants:

| variant | observation | hidden |
| --- | --- | --- |
| normal | left/current | left/current |
| reset_hidden | left/current | initial zero hidden |
| delayed_history | left/current | left hidden from `step - delay_steps` |
| wrong_matched_history | left/current | right hidden from matched-current pair |
| shuffled_history | left/current | hidden from another row in same surface |
| scaled_hidden_0_5 | left/current | `0.5 * left_hidden` |
| scaled_hidden_1_5 | left/current | `1.5 * left_hidden` |
| scaled_hidden_2_0 | left/current | `2.0 * left_hidden` |
| random_hidden_fit | left/current | empirical hidden mean/std sample |
| random_hidden_unit | left/current | random direction scaled to empirical hidden norm |

Observation controls:

| variant | observation | hidden |
| --- | --- | --- |
| zero_current_response | response slots zeroed | left/current |
| zero_action_history | previous command slots zeroed | left/current |

`random_*` variants are diagnostic only. They must not be treated as self-ID
proof.

## Metrics

Let:

```text
normal_cap = capability_head(next_hidden_normal)
variant_cap = capability_head(next_hidden_variant)
target_std = M598 train target_std
```

Compute:

```text
capability_delta = variant_cap - normal_cap
capability_z_delta = capability_delta / target_std
capability_z_distance = ||capability_z_delta||_2
```

Also record per-target absolute z deltas:

```text
abs_z_future_braking_deceleration
abs_z_future_yaw_response
abs_z_future_lateral_accel_response
```

Primary threshold:

```text
min_capability_z_distance = 0.25
```

Aggregate summaries:

```text
pair_count
capability_z_distance_mean
capability_z_distance_p50
capability_z_distance_p90
capability_z_distance_max
above_threshold_count
above_threshold_fraction
```

## Artifacts

M601 should write:

```text
runs/m601_bc_capability_belief_intervention_fresh/summary.json
runs/m601_bc_capability_belief_intervention_fresh/capability_intervention_rows.csv
runs/m601_bc_capability_belief_intervention_fresh/variant_summary.csv

runs/m601_bc_capability_belief_intervention_ood/summary.json
runs/m601_bc_capability_belief_intervention_ood/capability_intervention_rows.csv
runs/m601_bc_capability_belief_intervention_ood/variant_summary.csv
```

## Interpretation Rules

| result | meaning | next branch |
| --- | --- | --- |
| wrong/delayed capability movement is strong but M591 action movement is weak | belief signal exists; action coupling is missing | design actor/fusion coupling fine-tune |
| wrong/delayed capability movement is weak | real hidden histories are belief-equivalent on this surface | strengthen hidden objective or mine stronger pairs |
| reset movement is strong but wrong/delayed weak | reset is too blunt; matched intervention surface remains weak | refresh matched-current pairs |
| random movement only | off-manifold sensitivity | no self-ID claim |
| zero-current dominates belief movement | head may rely on current response update, not accumulated history | isolate history-only objective before actor update |

## Admission Rule For Actor Fine-Tune Design

Actor/fusion fine-tune design is admitted only if at least one real-history
variant passes on at least one surface:

```text
variant in {wrong_matched_history, delayed_history, shuffled_history}
capability_z_distance_mean >= 0.10
above_threshold_count >= 16
```

If this fails on both fresh and OOD surfaces, actor fine-tuning remains blocked.

## Decision

```text
bc_capability_belief_intervention_probe_design_admit_m601
```

M600 passes because it defines the capability-belief intervention metrics,
variants, artifacts, thresholds, and interpretation rules before any actor
fine-tuning.

## Next

```text
M601: implement and run the capability-belief intervention probe.
```
