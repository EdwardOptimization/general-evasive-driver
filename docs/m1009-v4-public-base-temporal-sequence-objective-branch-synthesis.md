# M1009 V4 Public Base Temporal Sequence Objective Branch Synthesis

## Purpose

M1009 synthesizes M999-M1008 before any further temporal-objective repair.

This is a process milestone only. It does not train, run PPO, use private
holdout, change actor inputs, or promote.

## Evidence Summary

M999-M1000 established a clean exact objective surface over the M997 temporal
sequence corpus:

```text
M997 corpus rows: 277
M997 positive rows: 277
M1000 weighted normal sequence NLL: -1.373014
M1000 weighted temporal preference loss: 0.491601
M1000 weighted logp gap mean: 0.640106
```

M1001-M1002 showed that the objective is trainable at exact level:

```text
trainable surface: actor_mean only
exact candidates: 5
best alpha: 0.2
best weighted total loss: -0.907863
best weighted temporal preference loss: 0.463279
best weighted logp gap mean: 0.758060
best action L2 mean/max: 0.008939 / 0.036729
non-actor parameters changed: false
```

M1003-M1005 showed the exact candidates are not replay-valid:

```text
M1004 exact/contract pass count: 5 / 5
M1004 M267/M264 preflight pass count: 0 / 5
alpha 0.2 success-drop count: 17 -> 6
alpha 0.01 success-drop count: 17 -> 15
alpha 0.01 lost rows: 6, 15
failure type: proof_washout
failure subtype: wrong_history_branch_lift
```

M1006-M1008 tried to design a branch-preserving exact evaluator and found a
negative result:

```text
M1007 branch evaluator:
  finite metrics: true
  temporal base reproduced: true
  base branch near zero: true
  alpha 0.01 branch loss: 0.0
  alpha 0.2 branch loss: 4.14467e-7
  result: not sensitive

M1008 audit:
  failure subtype: margin_slack_mismatch
  row 6 base wrong margin:  -0.000117
  row 15 base wrong margin: -0.000025
```

## Supported Claims

The branch supports these claims:

```text
1. The M997 temporal sequence corpus is usable for exact log-prob objective
   work.

2. A small actor_mean-only update can improve temporal exact metrics without
   changing the actor input contract or non-actor parameters.

3. Exact temporal improvement alone is not sufficient for public replay
   validity.

4. The first public proof blocker is M267/M264 wrong-history branch lift, not
   normal-history success regression.

5. Rows 6 and 15 are active near-cliff constraints because alpha 0.01 already
   flips their wrong-history terminal margin.

6. Fixed one-step logp/separation branch proxies are too insensitive to protect
   those near-cliff rows.
```

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. M1002 exact candidates can be promoted to public replay evaluation directly.

2. Lower alpha is enough to repair M1002. Even alpha 0.01 loses rows 6 and 15.

3. M1007 fixed one-step branch ceiling/separation is a sufficient repair
   objective. It does not activate on alpha 0.01.

4. Temporal sequence objective progress proves cross-fault wrong-history
   self-identification. Cross-fault evidence remains blocked from M995/M998.

5. PPO continuation is admissible from the M1002 candidates. Replay proof
   retention is not yet restored.
```

## Failure Taxonomy Summary

Observed failure categories:

```text
proof_washout:
  M1004 rejects all M1002 exact candidates at M267/M264 preflight.

metric_artifact:
  M1007 fixed one-step branch proxy is finite and base-safe but does not detect
  alpha 0.01 proof washout.

none:
  M997 export, M1000 no-update evaluator, and M1002 exact actor_mean update
  infrastructure all function as intended within their narrower claim scopes.
```

No PPO, private holdout, or promotion occurs in this branch segment.

## Public Gate Overfit Risk

Risk level:

```text
moderate-high
```

Reasons:

```text
The next likely repair will use M267/M264 public rows 6 and 15 as active
constraints.

The M997 temporal corpus is public and derived from previous diagnostics.

The branch currently relies on public proof rows to prevent washout, so any
future candidate must still pass fresh/generalization gates before promotion.
```

Mitigations required before any promotion:

```text
1. M267/M264 can be used as a proof preflight, but not as promotion evidence by
   itself.

2. Any repaired candidate must pass all six public replay surfaces.

3. Generalization and behavior gates must remain separate from proof gates.

4. A later fresh temporal-history corpus refresh is needed before paper-level
   claims.
```

## Next Branch Decision

Synthesis decision:

```text
continue
```

Keep current branch:

```text
v4_public_base_temporal_sequence_objective
```

Rationale:

```text
The temporal objective produced real exact movement and exposed a concrete
closed-loop proof conflict. The branch should continue, but the unweighted
fixed one-step branch proxy must be stopped.
```

Next ordinary milestone:

```text
m1010-v4-public-base-margin-weighted-branch-trust-region-design
```

The next design should define a margin-slack-weighted rejected-branch
trust-region residual:

```text
L_wrong_branch_trust =
  mean_i w_i * ||a_wrong_candidate_i - a_wrong_base_i||^2

w_i =
  source_weight_i / max(abs(base_wrong_margin_i), margin_floor)^2
```

It must frame wrong-history branch anchors as proof-retention constraints, not
as deployable behavior targets. It must require a no-update evaluator and
M267/M264 preflight before any actor update, full replay, PPO, or promotion.

## Decision

```text
temporal_sequence_objective_branch_synthesis_continue_to_margin_weighted_trust_region_design
```
