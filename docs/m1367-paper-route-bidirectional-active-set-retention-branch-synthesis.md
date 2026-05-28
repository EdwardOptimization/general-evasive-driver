# M1367 Paper-Route Bidirectional Active-Set Retention Branch Synthesis

## Summary

M1367 synthesizes the `paper_route_bidirectional_replay_active_set_retention`
branch from M1357 through M1366.

Synthesis decision:

```text
promote_to_next_branch
```

Closed branch:

```text
paper_route_bidirectional_replay_active_set_retention
```

Opened branch:

```text
paper_route_public_base_promotion_generalization
```

The branch achieved its purpose: it turned the M1355 normal-retention failure
into a bidirectional active-set candidate that passes broad public replay and
behavior diagnostics. The next work should no longer be local active-set tuning.

## Evidence Summary

M1357 designed the branch-asymmetric objective:

```text
correct-history branch:
  preserve safe normal behavior.

wrong-history branch:
  preserve rejected/wrong-history behavior.
```

M1358 exported the combined bidirectional anchor:

```text
combined anchor rows: 12113
required wrong-history rows 6,10,13,15,16 present: true
```

M1360 ran the raw no-PPO bidirectional update:

```text
combined_loss_delta: -4.7206263688
group_min_delta: +5.3494348235
success_drop_count_delta: 0
wrong_safe_required_row_ids: []
M267/M264 margin_gap_delta: -0.0012517729
```

Raw M1360 fixed M1355's wrong-history success-drop washout but overshot the
M267/M264 margin-gap threshold.

M1362 tested update amplitude and selected alpha `0.1`:

```text
selected_checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

combined_loss_delta_vs_base: -0.5148637349
group_min_delta_vs_base: +0.5245143565
eval_fold_delta_vs_base: +0.4884667957
M267/M264: pass
M183/M170: pass
```

M1365 ran broader public replay and behavior diagnostics:

```text
six public replay surfaces: 6 / 6 pass
source-diverse protected diagnostic: pass
behavior seeds 9505/9506: pass
actor input contract: unchanged
PPO/private holdout/promotion: not used
```

## Supported Claims

The branch supports these claims:

```text
1. A bidirectional active-set anchor can fix the M1355 wrong-branch washout.
2. Raw update amplitude is too aggressive; interpolation is the right control.
3. Alpha 0.1 gives meaningful exact source-history lift while preserving the
   public replay surfaces tested so far.
4. The M1362 alpha 0.1 checkpoint is a broad-public-replay-passing candidate
   relative to M1154.
```

## Falsified Claims

The branch falsified or rejected these claims:

```text
1. Raw M1360 can be accepted directly.
2. Two-surface preflight is enough for promotion.
3. Broad public replay pass is the same as private/generalization evidence.
4. Broad public replay pass proves level3 anticipatory self-identification.
```

The older M1355 branch already falsified:

```text
normal-branch retention alone is enough.
```

## Failure Taxonomy Summary

Important failures:

```text
M1360:
  proof_washout, specifically M267/M264 margin-gap retention failure.

M1362:
  larger alphas 0.2-0.8 passed M267/M264 but failed M183/M170.

Raw alpha 1.0:
  failed M267/M264 margin-gap retention.
```

Resolved failure:

```text
M1355 wrong-history rows becoming safe was resolved by the bidirectional anchor.
```

## Public-Gate Overfit Risk

Risk level:

```text
medium
```

Reason:

```text
The candidate now passes a broad public replay stack, protected diagnostics, and
behavior seeds. That is strong public evidence, but the candidate was still
selected and audited through public surfaces. It has not run private holdout or
fresh scenario/generalization distributions.
```

So public evidence is strong enough to justify a promotion/generalization branch,
but not enough to make a final paper or private-holdout claim.

## Next Branch Decision

Open:

```text
paper_route_public_base_promotion_generalization
```

First task:

```text
m1368-paper-route-public-base-promotion-generalization-design
```

That design should decide the exact promotion/generalization gate for the M1362
alpha `0.1` candidate. It should include:

```text
exact source-history non-regression
broad public replay retention
protected diagnostic policy
behavior seed retention
fresh scenario/generalization evaluation
private holdout policy
clear promotion decision rule
```

No PPO should start until this promotion/generalization decision is resolved.

## Guardrails

M1367 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1368-paper-route-public-base-promotion-generalization-design
```
