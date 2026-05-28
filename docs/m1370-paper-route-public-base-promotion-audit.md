# M1370 Paper-Route Public-Base Promotion Audit

## Summary

M1370 audits the M1369 promotion/generalization gate result and promotes M1362
alpha `0.1` as the official public-gate base.

Decision:

```text
promote_public_base_m1362_alpha_0_1
```

New public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Previous public-gate base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

This is a public-gate base promotion only. It is not a private-holdout result,
not a source-rich extreme result, not a PPO continuation result, not a paper-level
generalization result, and not level3 anticipatory self-identification evidence.

## Evidence Accepted

M1370 accepts the M1369 gate because every pre-registered tier passed:

```text
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
private_holdout_used: false
promoted_in_M1369: false
```

M1369 result class:

```text
materialized_source_history_public_base_promotion_gate_candidate
```

## Exact Source-History Evidence

M1369 recomputed the active M1336 materialized source-history corpus and M1342
pair-group metric interpretation.

```text
combined_loss_delta_vs_base: -0.5148637358
group_min_joint_margin_delta_vs_base: +0.5245143158
eval_fold_4_group_min_joint_margin_delta_vs_base: +0.4884667325
allowed_parameter_l2: 0.1266231245
allowed_parameter_max_abs: 0.0009239744
```

The candidate improves exact source-history metrics relative to M1154 without
changing actor inputs, `log_std`, or forbidden parameters.

## Public Proof Evidence

M1369 passed all public proof replay surfaces:

```text
M183/M168: pass
M183/M170: pass
M193/M189: pass
M212/M204: pass
M223/M219: pass
M267/M264: pass
```

Source-diverse protected diagnostics passed:

```text
replay_gates_passed: 3
replay_gates_failed: 0
overall_pass: true
```

The old `9944|perturbed|28|28` key remains diagnostic-only. It does not veto the
promotion because both M1154 and M1362 fail the old singleton policy pass while
the source-diverse protected diagnostic passes.

## Fresh/OOD Generalization Evidence

M1369 ran fresh public and moderate-OOD comparisons against M1154 with fixed
public seeds.

```text
fresh_public comparisons: 3 / 3 pass
moderate_ood comparisons: 2 / 2 pass
success regressions: 0
collision regressions: 0
failed rows: none
```

Mean clearance margin improved slightly on every compared row:

```text
fresh_public margin deltas: +0.000839, +0.000839, +0.000851
moderate_ood margin deltas: +0.001779, +0.001760
```

## Behavior/Ablation Evidence

M1369 passed all behavior seeds:

```text
9505: pass
9506: pass
136930: pass
136931: pass
```

For all four seeds:

```text
candidate success delta vs M1154: 0.0
normal >= reset_recurrent_state >= zero_all_response: true
```

This supports behavior retention. It does not prove level3 self-identification.

## Promotion Decision

Promote:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

as the official public-gate base for subsequent public-base work.

Keep:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

as the previous public-gate base and comparison baseline for lineage audits.

Future public-base experiments should start from M1362 alpha `0.1` unless the
manifest explicitly states that it is comparing against an older base or replaying
older lineage evidence.

## Claim Boundary

Allowed claim:

```text
M1362 alpha 0.1 is the current public-gate base after passing exact,
public-proof, source-diverse, fresh/OOD, and behavior-retention gates against
M1154.
```

Not allowed:

```text
private-holdout claim
source-rich extreme validation claim
paper-level simulation evidence claim
guarded PPO continuation stability claim
high-fidelity or real-vehicle claim
level3 anticipatory recurrent-belief/self-identification claim
finite-window vs GRU claim
```

Those claims require later branches with pre-registered evidence.

## Next Route

The promotion branch has achieved its immediate objective. The next milestone
should synthesize the post-promotion state before any PPO, private holdout,
source-rich run, or L0/L1/L2/L3 comparison.

Recommended next branch after synthesis:

```text
paper_route_promoted_base_source_rich_and_comparison_readiness
```

Candidate next evidence priorities:

```text
1. source-rich extreme public generalization design from the promoted base;
2. L0/L1/L2/L3 fair comparison refresh using the promoted base as the recurrent baseline;
3. guarded PPO readiness only after promotion-specific rollback and proof gates are fixed.
```

## Guardrails

M1370 performs no training, PPO, new replay, new evaluation, actor update,
checkpoint mutation, private holdout, threshold relaxation, actor-input
expansion, high-fidelity claim, paper-level claim, source-rich extreme claim, or
level3 self-identification claim.

## Next

```text
m1371-paper-route-post-public-base-promotion-synthesis
```
