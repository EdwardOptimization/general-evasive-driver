# M1062 V4 Public Base Post Short-Promotion Surface Refresh Synthesis

## Purpose

M1062 synthesizes the post-short-promotion surface-refresh branch from M1054
through M1061. This is a process milestone: it does not train, run PPO, use
private holdout, change actor inputs, or promote a checkpoint.

## Evidence Summary

The branch started because M1053 judged immediate medium PPO too risky after
M1052 promoted the 4096-step guarded PPO checkpoint as the current public-gate
base. The goal was to refresh the proof surface for the short-PPO family before
lengthening PPO again.

M1054 designed a no-training surface refresh for the short-PPO family:

```text
short61049: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
short61050: runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
short61051: runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

M1055 found that the current public-gate base still has a rich wrong-history
surface:

```text
matched-current accepted pairs: 926
boundary relocation rows: 18375
accepted wrong-history rows: 315
accepted wrong-history physical pairs: 15
accepted targets: 3
wrong-history success-drop fraction: 1.0
control accepted wrong rows: 0
```

M1055 failed only the coarse `0.01m` normal-margin bucket diversity gate:

```text
normal-margin buckets: 1 / 2
```

M1056 audited this as a coarse bucket artifact rather than true sparsity:

```text
bucket_width 0.0050: passed, margin_buckets 2
bucket_width 0.0025: passed, margin_buckets 4
```

M1058 converted the surface into compact objective corpora and all three
objective sanity checks passed, but cross-family replay exposed a proof issue:

```text
short61049 corpus -> short61050 candidate:
  success drops: 27 -> 24
```

M1059 localized this to current-base-only row selection. The failed rows were
near-zero wrong-history positives under the repeat checkpoint, not large-margin
safe wrong-history behavior:

```text
wrong_history_margin: +0.000086
wrong_history_margin: +0.000259
wrong_history_margin: +0.000114
```

M1060 designed a deterministic family-intersection selector. M1061 implemented
and ran it:

```text
family replay rows: 945
family-intersection candidates: 305
candidate physical pairs: 15
candidate targets: 3
selected rows: 79
selected physical pairs: 15
selected targets: 3
```

M1061 objective sanity passed for all three source checkpoints:

```text
short61049: 25 rows, 14 physical groups, 3 targets, 3 / 3 seeds passed
short61050: 27 rows, 15 physical groups, 3 targets, 3 / 3 seeds passed
short61051: 27 rows, 15 physical groups, 3 targets, 3 / 3 seeds passed
```

M1061 cross-family replay sanity passed in all six directions:

```text
short61049 -> short61050: 25 / 25 success drops retained
short61049 -> short61051: 25 / 25 success drops retained
short61050 -> short61049: 27 / 27 success drops retained
short61050 -> short61051: 27 / 27 success drops retained
short61051 -> short61049: 27 / 27 success drops retained
short61051 -> short61050: 27 / 27 success drops retained
```

## Supported Claims

The branch supports these claims:

```text
1. The promoted short-PPO public-gate family still contains a fresh,
   source-diverse wrong-history boundary surface.
2. The M1055 margin-bucket failure was a coarse diagnostic artifact, not proof
   that refreshed rows were absent.
3. Current-base-only compact selection is not enough; replay-calibrated
   family-intersection filtering is required.
4. M1061 produces a compact, strict, all-family-valid proof corpus suitable for
   integration into the public proof gate stack.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
1. Medium PPO can start safely immediately after M1052 without a refreshed
   proof-surface check.
2. M1055 should be rejected as sparse solely because the 0.01m bucket gate
   failed.
3. A row accepted under the current public-gate base is automatically valid
   across the short-PPO repeat family.
4. The M1058 replay failure requires actor repair or PPO changes.
```

The branch still does not prove:

```text
private-holdout generalization
medium or long PPO stability
paper-level statistical evidence
real-vehicle transfer
```

## Failure Taxonomy Summary

Branch failures and resolutions:

```text
scenario_sampling_failure:
  M1055 failed the 0.01m margin-bucket diversity check.
  M1056 resolved this as a coarse bucket artifact.

proof_washout:
  M1058 cross-family replay lost three success-drop rows.
  M1059 localized this to missing family-intersection filtering.
  M1061 resolved it with all-family replay-calibrated row selection.

none:
  M1061 objective and replay sanity both passed.
```

No actor contract violation, private holdout contamination, training
instability, or promotion-gate failure occurred in this branch.

## Public-Gate Overfit Risk

Risk level:

```text
reduced but not eliminated
```

The risk is lower than after M1053 because the branch mined and filtered a
fresh current-family proof surface instead of only reusing older M183/M193/M267
rows. It is not eliminated because the selected M1061 rows are now public
debugging rows. They should be integrated as public proof-retention gates, not
used as private or paper-level evidence.

Before any medium PPO escalation, the public gate stack should include the
M1061 family-intersection corpus so future PPO proposals cannot pass by keeping
old rows while breaking the refreshed short-PPO family surface.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close branch:

```text
post_short_promotion_surface_refresh
```

Open branch:

```text
post_short_promotion_family_gate_integration
```

Next milestone:

```text
m1063-v4-public-base-family-intersection-gate-integration-design
```

M1063 should design how M1061 becomes a first-class public proof gate before
medium PPO. It should not train, run PPO, promote, or use private holdout.

The design should decide:

```text
1. which M1061 artifacts become gate inputs;
2. whether the gate is a reusable wrapper around boundary_outcome_replay_gate
   or an extension of the combined active-set guarded PPO preflight;
3. how exact/objective sanity, six-direction replay, and source summaries are
   ordered before PPO;
4. how this refreshed public proof gate interacts with existing M183/M193/M267,
   source-diverse diagnostics, fresh/OOD, behavior, and row15/row16 gates;
5. what rollback rule blocks medium PPO if M1061 family success drops regress.
```

## Decision

```text
post_short_promotion_surface_refresh_synthesis_promote_to_family_gate_integration
```

Next:

```text
m1063-v4-public-base-family-intersection-gate-integration-design
```
