# M1159 V4 Public Base Row15 Promoted Projection Post-Promotion Synthesis

## Purpose

M1159 synthesizes the state after M1158 promoted `alpha_0_05` as the current
public-gate base and selects the next branch.

This milestone is process-only. It does not train actor weights, run PPO, run
replay, run objective optimization, mine rows, promote another checkpoint, use
private holdout, or change actor inputs.

## Evidence Summary

New public-gate base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Promotion path:

```text
M1154:
  selected alpha_0_05
  exact M1144 delta: -0.000378
  failed-row unsafe-margin pass: 76 / 76
  M1149 first replay pass: 10 / 10 surfaces

M1156:
  M1144 exact recheck delta: -0.000378400
  expanded diagnostic exact/proof/family/source/generalization/behavior: pass

M1157:
  M1156 result audit: internally consistent
  promotion audit admitted: true

M1158:
  alpha_0_05 promoted as current public-gate base
  scope: public proof-base hardening only
```

## Supported Claims

Supported:

```text
alpha_0_05 is the current public-gate base.
The promotion is limited to public proof-base hardening.
The actor input contract is unchanged.
M1154/M1156/M1157/M1158 preserve level2 history-encoded reactive proof scope.
```

Still unsupported:

```text
medium or long PPO readiness
driver-performance improvement
private-holdout generalization
paper-level statistical evidence
real-vehicle transfer
level3 anticipatory self-identification
```

## Falsified Claims

The recent branch falsified two tempting shortcuts:

```text
direct M1144 exact-objective actor update is replay-safe
M1156 diagnostic pass should directly trigger promotion without audit
```

M1158 resolved the second shortcut through an explicit promotion audit, but the
first shortcut remains important: future updates should treat exact objective
improvement as a proposal signal, not as a replay-safety proof.

## Failure Taxonomy Summary

Recent failure and repair path:

```text
M1149/M1150 failure type: proof_washout
mechanism: wrong-history branches became safe while normal-history success was preserved
repair: no-training unsafe-margin projection
promotion status: repaired candidate promoted only after expanded diagnostics and audits
```

No contract violation, private holdout contamination, or actor-input change
occurred in the M1154-M1158 path.

## Public-Gate Overfit Risk

The largest remaining process risk is public-gate overfit around the
row15-promoted materialized surface:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

This is not a blocker to the M1158 proof-base promotion because the selected
candidate still passed all public diagnostics. It is a blocker to immediate PPO
or broad capability claims. The next branch should refresh current-base
source-diverse protected/preference surfaces and explicitly track margin slack,
source diversity, and near-boundary rows before any PPO proposal.

## Next Branch Decision

Close:

```text
row15_promoted_unsafe_margin_projection
```

Open:

```text
row15_promoted_margin_slack_surface_refresh
```

The branch objective is to refresh current-base source-diverse
protected/preference surfaces for `alpha_0_05`, with explicit margin-slack
coverage so the next objective/replay corpus is not only a thin near-zero
repair surface.

The next milestone should design that refresh. It should not mine rows yet and
should not run PPO.

```text
decision: row15_promoted_projection_post_promotion_open_margin_slack_surface_refresh
next: m1160-v4-public-base-row15-promoted-margin-slack-surface-refresh-design
```
