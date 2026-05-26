# M1018 V4 Public Base M1013 Candidate B Full Replay Design

## Purpose

M1018 designs the full public replay gate for Candidate B after M1016 showed it
passes M267/M264 preflight and M1017 diagnosed the unsigned branch-L2 ordering
artifact.

This is design-only. It does not run replay, train, run PPO, use private
holdout, change actor inputs, or promote.

## Candidate

Candidate B:

```text
label: m1013_lam0030_a050
checkpoint:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
source:
  M1013 lambda_wrong_trust=0.03, alpha=0.5
```

Known M1016 preflight:

```text
M267/M264 success-drop count: 17/17
normal_success_delta: 0.0
normal_margin_mean_delta: -0.000074
margin_gap_mean_delta: 0.000031
actor_inputs_changed: false
non_actor_checksum_changed: false
```

This preflight pass is not promotion evidence by itself.

## M1019 Gate Order

M1019 should run these tiers in order.

### Tier 0: Contract And Exact Retention

Check:

```text
actor input config equals M974 base
non-actor parameters equal M974 base
changed parameters are only actor_mean.bias and actor_mean.weight
```

Recompute M997 temporal exact retention:

```text
weighted_total_loss <= M1000 base - 0.001
weighted_normal_sequence_nll <= M1000 base + 0.005
weighted_temporal_preference_loss <= M1000 base + 0.005
weighted_logp_gap_mean >= M1000 base - 0.050
temporal_logp_gap_p10 >= M1000 base - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080
```

Do not use M1013 cached metrics alone.

### Tier 1: Six Public Replay Surfaces

Run Candidate B against M974 base on:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Use the same replay tolerances:

```text
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
max_continuation_steps: 60
env_config: configs/m121_human_view_zero_obstacle_relvel.json
```

Candidate B passes Tier 1 only if all six replay surfaces pass.

### Tier 2: Source-Diverse Protected Diagnostics

Run the same source-diverse diagnostics used in recent public-base gates:

```text
current_m333_surface
m317_continuity_surface
m314_continuity_surface
```

These diagnostics are public proof/generalization checks, not private holdout.

### Tier 3: Behavior Seeds

Run behavior/ablation seeds:

```text
9505
9506
```

At minimum, retain:

```text
normal success no worse than M974 on both seeds;
reset/zero-all ordering not inverted;
no actor-input contract change.
```

## Decision Rule

If Tier 0 or any public replay surface fails:

```text
Reject Candidate B as a full public replay candidate.
Route to signed/outcome-aware branch objective design or branch synthesis.
```

If six surfaces pass but protected diagnostics or behavior seeds fail:

```text
Do not promote.
Route to candidate-specific failure audit.
```

If all tiers pass:

```text
Candidate B becomes a public-gate candidate.
Route to promotion/generalization audit, not immediate promotion.
```

## Blocked Routes

Do not:

```text
promote directly from M1019;
run PPO;
use private holdout;
change actor inputs;
skip exact retention;
skip behavior seeds;
claim paper-level generalization.
```

## Decision

```text
candidate_b_full_replay_design_admit_m1019_gate
```

Next:

```text
m1019-v4-public-base-m1013-candidate-b-full-replay-gate
```
