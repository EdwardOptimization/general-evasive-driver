# M1030 V4 Public Base Candidate B Temporal Retention Repair Design

## Purpose

M1030 designs the next repair step after M1029 showed that the no-PPO exact
repair candidates can satisfy M297/M270 but fail M997 temporal exact retention.

M1030 is design only. It does not run repair, PPO, training, private holdout,
promotion, first replay, or actor-input changes.

## Parent Result

M1029 candidates:

| Candidate | M297 delta | M270 delta | M997 exact pass | Action L2 mean |
| --- | ---: | ---: | --- | ---: |
| raw_conflict_s40 | -0.000571609 | -0.000009418 | false | 0.043320605 |
| base_conflict_s40 | -0.000331402 | -0.000004232 | false | 0.032059840 |
| line_conflict_s40 | -0.000331402 | -0.000004232 | false | 0.032059840 |

M997 temporal action-drift threshold:

```text
candidate_action_l2_mean <= 0.015
```

M1029 failure class:

```text
candidate_b_post_ppo_exact_repair_temporal_regression
```

The failed candidates were not first-replay gated, by design.

## Diagnosis

The M1029 repair objective was:

```text
M297 rejected-history preference
M270 outcome intervention
M293 rejected-history trajectory anchor
M393 current-family conflict residual
base/raw parameter trust terms
```

That objective does not directly include:

```text
M997 normal-sequence action replay retention
M997 normal-sequence NLL retention
M997 temporal preference retention
M997 temporal logp-gap retention
```

So the optimizer can improve M297/M270 and read the row15 conflict corpus while
moving the policy too far on the M997 temporal sequence surface. This is not a
PPO instability and not a row15 conflict infeasibility result. It is an
objective-coverage gap.

## Design Decision

M1031 should first implement the lowest-risk projection route:

```text
temporal-safe interpolation/projection from Candidate B to each M1029 repair
candidate
```

This is preferred before modifying `exact_post_ppo_repair` because it answers a
smaller question:

```text
Does any fraction of the M1029 exact-repair direction retain M997 temporal
exact feasibility while keeping M297/M270 improvement and M267/M264 row15
readiness?
```

If this projection finds no admissible alpha, then the next step should add
M997 terms into the repair objective itself.

## M1031 Projection Problem

Define:

```text
theta_base = Candidate B public-gate base
theta_repair_i = one M1029 repair candidate
theta_alpha_i = theta_base + alpha * (theta_repair_i - theta_base)
```

Candidate sources:

```text
raw_conflict_s40
base_conflict_s40
line_conflict_s40
```

Alpha grid:

```text
0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60,0.75,1.00
```

M1031 should save candidate checkpoints for every evaluated alpha so replay
gates can be run without recomputing interpolation.

## Gate Order

M1031 must evaluate in this order:

1. P0 actor-input contract unchanged.
2. M997 temporal exact retention passes.
3. M297/M270 exact no-regression remains true.
4. Candidate retains nontrivial repair movement:

```text
alpha >= 0.10
or M297 delta <= -0.00005
or M270 delta <= -0.000002
```

5. M267/M264 first replay passes `17/17`, including row15 wrong-history
   failure.
6. M183/M170 first replay passes `17/17`.
7. Only then route to a full public gate design.

If no alpha passes M997, M1031 must stop before replay and route to temporal
objective integration.

## Required Metrics

For each candidate source and alpha:

```text
source_candidate
alpha
checkpoint
actor_inputs_changed
changed_parameter_names
M997 exact_gate_pass
M997 weighted_total_loss
M997 candidate_action_l2_mean
M997 candidate_action_l2_max
M297 delta vs Candidate B
M270 delta vs Candidate B
M297/M270 exact pass
raw_movement_retained proxy
selected_for_replay
```

For replay-gated candidates:

```text
M267/M264 success_drop_count
M267/M264 row15 wrong_history_success
M267/M264 row15 wrong_history_margin
M183/M170 success_drop_count
normal_success_delta
normal_margin_mean_delta
```

## Result Classes

Use these classifications:

```text
candidate_b_temporal_safe_projection_first_replay_candidate:
  M997 temporal exact, M297/M270 exact, M267/M264, and M183/M170 first replay
  pass. Route to full public gate design.

candidate_b_temporal_safe_projection_no_temporal_candidate:
  no alpha passes M997 temporal exact. Route to temporal objective integration.

candidate_b_temporal_safe_projection_no_exact_candidate:
  temporal-safe alphas lose M297/M270 exact non-regression. Route to
  multi-objective temporal repair design.

candidate_b_temporal_safe_projection_proof_washout:
  exact and temporal gates pass but M267/M264 or M183/M170 replay fails. Route
  to row-specific objective coverage audit.

candidate_b_temporal_safe_projection_base_equivalent:
  only alpha values too close to zero pass. Route to PPO/repair recipe audit.
```

## Explicit Non-Goals

M1031 must not:

- run PPO;
- alter the actor input/output contract;
- relax M997 temporal thresholds;
- run replay for temporal-failing candidates;
- use private holdout;
- promote a checkpoint;
- claim paper-level evidence.

## Fallback If Projection Fails

If M1031 finds no useful temporal-safe projection, M1032 should design direct
M997 integration into `exact_post_ppo_repair`:

```text
lambda_temporal_action_anchor
lambda_temporal_normal_nll
lambda_temporal_preference
lambda_temporal_gap_retention
```

That should be a code change only after projection proves that interpolation
alone cannot recover an admissible candidate.

## Decision

```text
candidate_b_temporal_retention_design_admit_projection_probe
```

Next milestone:

```text
m1031-v4-public-base-candidate-b-temporal-safe-projection-probe
```
