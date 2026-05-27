# M1130 V4 Public Base Row15 Projection Post Promotion Synthesis

## Purpose

M1130 synthesizes the `row15_projection_promotion_audit` branch after M1129
promoted alpha `0.15` as the current public-gate base.

This milestone is process-only. It does not train actor weights, run PPO, run
replay, run objective optimization, mine rows, promote another checkpoint, use
private holdout, or change actor inputs.

## Evidence Summary

M1129 promoted:

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Previous public-gate base:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

The promotion evidence came from M1127:

```text
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
private_holdout_used: false
```

M1129 scoped the promotion to public proof-base hardening only.

## Supported Claims

The current public-gate base is now the alpha `0.15` row15 projection
checkpoint. It is a no-training public proof-hardening projection that repairs
the row15 unsafe-margin failure exposed by M1120 while retaining exact,
proof-replay, family-intersection, source-diverse, fresh/OOD, and behavior
gates.

Future public-gate work should use the promoted alpha `0.15` checkpoint as the
current base.

## Falsified Or Unsupported Claims

M1129 does not prove medium-PPO performance improvement. Broad success rates
were retained, not materially improved.

M1129 does not prove medium/long PPO stability. It also does not show that PPO
from alpha `0.15` can improve driving performance without proof washout.

M1129 does not prove private-holdout or paper-level generalization. The
candidate was selected and validated using public artifacts.

M1129 does not prove level3 anticipatory self-identification. The evidence
remains level2 history-encoded reactive proof retention.

## Failure Taxonomy Summary

```text
M1120: proof_washout plus objective_overfit
M1121: none; diagnostic audit found row15 anchor coverage was present
M1123: none; no-training unsafe-margin projection found alpha_0_15
M1125: none; family-intersection replay passed
M1127: none; expanded full public gate passed
M1129: none; public proof-base hardening promotion
```

The post-promotion state is coherent: current-status was updated, the previous
base is preserved in lineage, and the claim scope remains public-gate only.

## Public-Gate Overfit Risk

Alpha `0.15` was selected after several rounds of public proof-gate repair.
That is acceptable for a public-gate base, but it increases public-gate overfit
risk.

The next PPO branch should not start from the promoted base until the promoted
base has a fresh current-base source-diverse protected/preference surface. The
refresh should mine new boundary rows under alpha `0.15` instead of only
reusing M1120/M1123/M1127 active rows.

## Next Branch Decision

```text
synthesis_decision: promote_to_next_branch
closed_branch: row15_projection_promotion_audit
opened_branch: row15_promoted_base_surface_refresh
```

Next milestone:

```text
m1131-v4-public-base-row15-promoted-surface-refresh-design
```

M1131 should design a current-base source-diverse protected/preference surface
refresh before any new PPO proposal. It should not mine rows, train actor
weights, run PPO, promote another checkpoint, or use private holdout.

## Decision

```text
row15_projection_post_promotion_synthesis_open_surface_refresh
```
