# M948 V4 Public Base Controlled Fusion Rejected-Branch Retention Design

## Purpose

M947 showed that all known M944 controlled-fusion candidate alphas fail the same
M267/M264 wrong-history proof rows. M948 designs the next repair route.

This is design-only. It does not train, run PPO, change actor inputs, or
promote.

## Diagnosis From M947

M946/M947 isolated the failure:

```text
failure_type: proof_washout
failure_mode: rejected_history_branch_washout
failed public surface: M267/M264
failed rows: 6, 13, 15, 16
behavior_regression: false
contract_violation: false
known backup alpha repair: false
```

All three M944 materialized candidate alphas fail the same public proof rows:

| candidate | M267/M264 success drops | failed rows |
| --- | ---: | --- |
| alpha 0.0675 | 13 / 17 | 6, 13, 15, 16 |
| alpha 0.0700 | 13 / 17 | 6, 13, 15, 16 |
| alpha 0.0725 | 13 / 17 | 6, 13, 15, 16 |

The issue is not normal-history success. It is that the wrong-history branch is
also made safe on fragile rows.

## Design Constraint

Keep the M936 controlled-fusion trainable surface:

```text
allowed:
  actor_mean.weight
  actor_mean.bias
  response_context_fusion.0.weight
  response_context_fusion.0.bias

forbidden:
  response_encoder.*
  context_encoder.*
  online_gru_cell.*
  critic.*
  log_std
  actor inputs
```

M948 does not justify opening encoders or GRU. If this surface cannot satisfy
normal lift and rejected-branch retention together, the branch must synthesize
before widening the trainable surface.

## Active Rejected-Branch Rows

The first active set should be small and explicit:

```text
M267/M264 rows: 6, 13, 15, 16
source-diverse continuity rows: 15, 16
old key 9944: diagnostic-only, not an active singleton veto
```

For each active row, reconstruct:

```text
relocated observation
normal/preferred hidden
wrong/rejected hidden
M399 normal first action
M399 wrong-history first action
M399 normal rollout result
M399 wrong-history rollout result
```

Use existing boundary replay reconstruction utilities rather than adding new
state sources. The actor must still see only the P0 human-view observation and
its recurrent hidden state.

## Objective

The next objective should extend the M940 boundary-alpha controlled-fusion
objective. It should not replace normal retention or low-tail lift; it should
add a rejected-branch retention term.

Recommended loss:

```text
loss =
  existing_boundary_low_tail_terms
+ existing_normal_retention_terms
+ existing_target_auxiliary_terms
+ lambda_wrong_anchor * rejected_wrong_action_anchor
+ lambda_wrong_separation * rejected_wrong_vs_normal_separation_floor
+ lambda_wrong_direction * rejected_wrong_direction_anchor
+ lambda_parameter * allowed_parameter_anchor
```

Definitions:

```text
rejected_wrong_action_anchor:
  active rejected rows only;
  mean(||a_wrong_candidate - a_wrong_M399||^2)

rejected_wrong_vs_normal_separation_floor:
  active rejected rows only;
  relu(d_min - ||a_wrong_candidate - a_normal_candidate||)^2

rejected_wrong_direction_anchor:
  active rejected rows only;
  preserves the signed first-action direction from M399 wrong-history behavior
  against the candidate normal action. This is a proxy for "do not repair the
  wrong-history branch into the same safe maneuver."
```

Initial coefficients should be conservative:

```text
lambda_wrong_anchor: 25.0
lambda_wrong_separation: 5.0
lambda_wrong_direction: 5.0
```

The exact numbers are not a claim. M949 should expose them as CLI/config values
and report sensitivity if the first probe is inconclusive.

## Why This Is Only A Proxy

The actual proof condition is closed-loop terminal behavior:

```text
normal-history rollout succeeds
wrong-history rollout fails
```

That condition is not directly differentiable through the current simulator
and replay harness. Therefore, the training-time rejected-branch terms are only
proxies. Promotion must depend on closed-loop replay preflight, not on the
proxy loss.

## Preflight Gate

Before running all six public replay gates, every candidate alpha must pass a
cheap M267/M264 preflight:

```text
surface: M267/M264
required rows: 6, 13, 15, 16
normal_success: true for all 4 rows
wrong_history_success: false for all 4 rows
success_drop_count on full M267/M264: 17 / 17
normal_margin_mean_delta >= -0.005
margin_gap_mean_delta >= -0.001
```

If M267/M264 preflight fails, do not run the full M946 gate stack.

If M267/M264 preflight passes, run:

```text
1. source-diverse continuity preflight on rows 15/16 family
2. six public replay surfaces
3. behavior seeds 9505 and 9506
4. old key 9944 diagnostic-only
```

## Candidate Selection

M949 should evaluate a wider but still bounded alpha grid for the new raw
update:

```text
0.005, 0.010, 0.020, 0.035, 0.050,
0.0675, 0.0700, 0.0725, 0.0750, 0.1000,
0.1250, 0.1500, 0.2000, 0.2500
```

Candidate acceptance requires all of:

```text
P0 actor-input contract unchanged
forbidden parameters unchanged
exact low-tail objective compatibility retained or improved versus M942/M944
M267/M264 preflight pass
source-diverse row-family preflight pass
training_started true only for the objective probe
ppo_used false
promoted false
```

## Route Logic

If a candidate passes exact objective and M267/M264 preflight:

```text
route: full replay gate implementation, not promotion
```

If exact objective improves but M267/M264 preflight still fails:

```text
route: rejected-branch trajectory target export or branch synthesis
```

If M267/M264 preflight passes but low-tail objective no longer improves:

```text
route: objective conflict audit
```

If all useful alphas require too much rejected-branch anchoring and no low-tail
lift remains:

```text
route: controlled-fusion branch synthesis before opening a wider trainable surface
```

## Decision

M948 admits a small no-PPO objective-only implementation:

```text
m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe
```

M949 must implement the active rejected-branch row export, the proxy retention
loss, and the M267/M264 preflight gate. It must not run PPO or promote.
