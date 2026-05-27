# M1052 V4 Public Base Guarded PPO Short Escalation Promotion Audit

## Purpose

M1052 audits the three 4096-step guarded PPO candidates from M1049/M1050 and
decides whether one should become the next public-gate base.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or claim medium/long PPO stability.

## Candidate Set

```text
61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

All three candidates passed:

```text
exact M997/M297/M270/combined-active-set checks
six public proof replay surfaces
three source-diverse protected diagnostics
fresh public seeds 103900/103901
moderate-OOD seed 103920
behavior seeds 9505/9506/103930/103931
```

All three preserved the P0 actor-input contract and kept promotion/private
holdout blocked in their run milestones.

## Selection Table

```text
candidate  exact_improve  row15_wrong_margin  row16_normal_margin  fresh_margin_delta_mean  ood_margin_delta
61049      +0.014599      -0.000567           +0.000621            +0.000198                +0.001624
61050      +0.014407      -0.000847           +0.000467            +0.000472                +0.000349
61051      +0.014658      -0.000847           +0.000467            +0.000460                +0.000358
```

Interpretation:

```text
61051 has the largest exact total-loss improvement, but only by a small margin.
61050/61051 preserve stronger row15 wrong-history negative slack.
61049 has the best balanced hard-row slack, improves row16 normal margin, and
has the largest moderate-OOD margin improvement.
```

The known hard active sets are asymmetric:

```text
row15 protects wrong-history failure.
row16 protects normal-history success.
```

Selecting only by exact loss would over-weight a tiny scalar difference and
ignore the near-cliff row16 slack. The promotion audit therefore selects the
candidate with the better balanced hard-row slack and OOD margin while still
passing every public gate.

## Promotion Decision

Promote as the current public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Decision:

```text
guarded_ppo_short_escalation_promote_public_gate_base
```

Scope:

```text
public-gate base promotion only
no private holdout claim
no medium/long PPO stability claim
no paper-level generalization claim
no real-vehicle claim
```

## Supported Evidence

The promoted checkpoint is supported by:

```text
1. M1049 full public gate pass for the selected checkpoint.
2. M1050 two-seed 4096-step repeat pass for the same recipe.
3. M1051 synthesis showing three 4096-step public-gate passes.
4. Unchanged actor input contract.
5. Retention of row15 wrong-history failure and row16 normal-history success.
```

## Residual Risk

Risk remains:

```text
moderate public-gate overfit risk
no private holdout evidence
no medium/long PPO evidence
no refreshed post-promotion proof surface yet
```

The next step should be post-promotion synthesis before any medium PPO or
source refresh.

## Decision

```text
guarded_ppo_short_escalation_promote_public_gate_base
```

Next:

```text
m1053-v4-public-base-guarded-ppo-short-promotion-synthesis
```
