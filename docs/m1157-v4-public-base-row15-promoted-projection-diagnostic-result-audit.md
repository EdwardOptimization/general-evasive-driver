# M1157 V4 Public Base Row15 Promoted Projection Diagnostic Result Audit

## Purpose

M1157 audits whether the M1156 all-pass diagnostic result is coherent enough
to admit a formal promotion audit for the M1154 `alpha_0_05` projection.

This milestone reads existing artifacts only. It does not train actor weights,
run PPO, run replay, mine rows, promote, use private holdout, or change actor
inputs.

## Evidence Reviewed

```text
candidate checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

base checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

primary docs/artifacts:
  docs/m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run.md
  docs/m1156-v4-public-base-row15-promoted-projection-family-behavior-run.md
  runs/m1156_row15_promoted_projection_m1144_exact_eval/summary.json
  runs/m1156_row15_promoted_projection_expanded_public_diagnostic/summary.json
```

## Diagnostic Consistency

M1156 supports the all-pass diagnostic summary:

```text
M1144 exact delta: -0.000378400
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
```

The proof replay evidence is complete for the current public stack:

```text
old-public surfaces: 6 / 6 pass
M1061 family-intersection surfaces: 3 / 3 pass
source-diverse protected surfaces: 3 / 3 pass
```

The generalization and behavior checks do not show regression:

```text
fresh_public success delta max abs: 0.0
moderate_ood success delta max abs: 0.0
behavior success delta max abs: 0.0
reset/zero-all ordering retained: true
```

The old `9944|perturbed|28|28` neighborhood remains a diagnostic singleton.
It did not regress relative to the base and is not a blocker for this
candidate.

## Near-Boundary Risk

M1154 selected the largest pre-registered alpha that preserved all failed-row
unsafe outcomes while improving exact M1144:

```text
selected_alpha: 0.05
failed_row_unsafe_margin_pass_count: 76 / 76
first_replay_surface_count: 10 / 10
```

The critical caveat is still real:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

This means the candidate is close to the wrong-history terminal-margin
boundary. However, M1156 shows that this near-boundary candidate still passes
the expanded public diagnostic stack. The risk should therefore constrain the
promotion claim scope, not force another repair before the promotion audit.

## Scope Classification

Allowed claim:

```text
alpha_0_05 is eligible for a formal public proof-base hardening promotion
audit.
```

Blocked claims:

```text
direct promotion without audit
medium/long PPO readiness
driver performance improvement
private-holdout generalization
paper-level statistical evidence
real-vehicle transfer
level3 anticipatory self-identification
```

## Decision

M1157 admits a separate promotion audit. It does not promote.

The promotion audit must explicitly decide whether the near-zero
wrong-history margin is acceptable for a public proof-base hardening checkpoint
and must keep the scope narrower than driver performance or PPO readiness.

```text
decision: row15_promoted_projection_result_audit_admit_promotion_audit
next: m1158-v4-public-base-row15-promoted-projection-promotion-audit
```
