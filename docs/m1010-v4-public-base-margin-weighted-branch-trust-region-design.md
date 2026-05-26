# M1010 V4 Public Base Margin-Weighted Branch Trust-Region Design

## Purpose

M1010 designs the replacement branch-retention residual selected by M1009
synthesis.

This milestone is design-only. It does not train, run PPO, run replay gates,
use private holdout, change actor inputs, or promote.

## Motivation

M1004 showed that M1002 exact temporal candidates wash out public proof rows:

```text
alpha 0.01 M267/M264 success-drop count: 17 -> 15
lost rows: 6, 15
```

M1007 then showed that fixed one-step logp/separation terms are too insensitive:

```text
alpha 0.01 branch loss: 0.0
alpha 0.2 branch loss: 4.14467e-7
```

M1008 identified the scale mismatch:

```text
row 6 base wrong margin:  -0.000117
row 15 base wrong margin: -0.000025
```

Tiny wrong-branch action shifts can flip terminal margin. The next residual
therefore must be margin-slack-weighted.

## Contract Boundary

This residual is a public-proof branch trust-region constraint. It is not a
deployable behavior target.

Allowed:

```text
Use M267/M264 wrong-history branch actions and margins as training-time proof
retention constraints.
```

Forbidden:

```text
Do not add hidden dynamics, labels, TTC, feasibility, or controller modes to the
actor input.

Do not claim wrong-history action anchoring is a desired driving behavior.

Do not run PPO or promotion from this design.
```

## Active Rows

Primary active rows:

```text
6, 15
```

Secondary active rows:

```text
11, 16
```

Full preflight rows:

```text
all 17 M267/M264 rows
```

Rows `6` and `15` are mandatory because they fail at alpha `0.01`; rows `11`
and `16` enter because they fail by alpha `0.05`.

## Residual Definition

For each active proof row, reconstruct the base M974 relocated observation and
wrong-history hidden state. Compute:

```text
a_wrong_base_i =
  deterministic action from M974 under wrong-history hidden state

a_wrong_candidate_i =
  deterministic action from candidate under the same observation and
  wrong-history hidden state
```

Define the margin slack:

```text
s_i = max(abs(base_wrong_margin_i), margin_floor)
```

Define the source weight:

```text
source_weight_i =
  4.0 for rows 6 and 15
  2.0 for rows 11 and 16
  1.0 for other M267/M264 rows
```

Define the margin-weighted trust residual:

```text
L_wrong_branch_trust =
  mean_i normalized_weight_i *
    ||a_wrong_candidate_i - a_wrong_base_i||^2 / s_i^2
```

Initial margin floor:

```text
margin_floor: 1e-4
```

The evaluator should also report the unweighted action L2/MSE so the weighting
does not hide large non-critical drift.

## Normal-Branch Guard

The residual should not freeze the whole actor. It should only protect
near-cliff rejected branches.

The future update must still satisfy the M1002 temporal exact gates:

```text
weighted_total_loss <= M1000 base - 0.001
weighted_normal_sequence_nll <= M1000 base + 0.005
weighted_temporal_preference_loss <= M1000 base + 0.005
weighted_logp_gap_mean >= M1000 base - 0.050
temporal_logp_gap_p10 >= M1000 base - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080
```

And add:

```text
margin_weighted_wrong_branch_mse for rows 6 and 15 <= tiny tolerance
margin_weighted_wrong_branch_mse full active set <= tiny tolerance
only actor_mean changes
```

Suggested evaluator tolerances:

```text
base weighted wrong-branch trust loss: 0.0
alpha 0.01 weighted wrong-branch trust loss: positive
alpha 0.2 weighted wrong-branch trust loss: larger than alpha 0.01
finite metrics: true
actor parameters changed: false
```

M1011 should calibrate the actual scale from the no-update evaluator before any
training coefficients are chosen.

## Future Update Objective

If M1011 passes, M1012 can design an actor_mean-only update:

```text
L =
  L_temporal_sequence
+ lambda_pref * L_temporal_preference
+ lambda_anchor * L_base_logp_anchor
+ lambda_wrong_trust * L_wrong_branch_trust
```

Candidate selection order:

```text
1. exact temporal gates
2. margin-weighted branch trust gates
3. M267/M264 full preflight
4. six public replay surfaces
5. behavior seeds
```

No PPO or promotion is allowed until a repaired candidate passes these gates.

## M1011 Requirements

M1011 should implement only the no-update evaluator:

```text
input checkpoints:
  M974 base
  M1002 alpha 0.01
  M1002 alpha 0.02
  M1002 alpha 0.05
  M1002 alpha 0.10
  M1002 alpha 0.20

outputs:
  margin_weighted_branch_summary.csv
  margin_weighted_branch_rows.csv
  summary.json
```

Pass conditions:

```text
M974 base trust loss == 0.0
alpha 0.01 trust loss > 0.0
alpha 0.20 trust loss > alpha 0.01 trust loss
row 6 and row 15 dominate the weighted loss
no actor parameters change
training_started == false
ppo_used == false
promoted == false
```

## Decision

```text
margin_weighted_branch_trust_region_design_admit_m1011_evaluator
```

Next:

```text
m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator
```
