# M1158 V4 Public Base Row15 Promoted Projection Promotion Audit

## Purpose

M1158 decides whether the M1154 `alpha_0_05` projection should replace
`alpha_0_15` as the current public-gate base.

This is a promotion audit only. It does not train actor weights, run PPO, run
replay, run objective optimization, mine rows, use private holdout, or change
actor inputs.

## Candidate

```text
new public-gate base candidate:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

previous public-gate base:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

## Evidence

M1154 established the local proof repair:

```text
selected_alpha: 0.05
exact M1144 delta: -0.000378
failed-row unsafe-margin pass: 76 / 76
M1149 first replay pass: 10 / 10 surfaces
row15-promoted materialized replay: 148 / 148 success drops retained
```

M1156 established expanded public diagnostics:

```text
M1144 exact recheck delta: -0.000378400
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

M1157 audited the result:

```text
M1156 evidence internally consistent: true
promotion audit admitted: true
direct promotion from M1156: blocked
near-boundary caveat preserved: true
```

## Caveat

The candidate remains near the wrong-history unsafe-margin boundary:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

This caveat is acceptable for a public proof-base hardening promotion because:

1. The margin is still negative on the selected failed-row screen.
2. The candidate passes all M1149 first-replay surfaces.
3. The candidate passes the expanded public proof, family-intersection,
   source-diverse, fresh/OOD, and behavior diagnostics.
4. The promotion scope is explicitly limited to public proof-base hardening.

The caveat is not acceptable as evidence for PPO readiness, driver performance
improvement, private-holdout generalization, paper-level statistical evidence,
real-vehicle transfer, or level3 anticipatory self-identification.

## Promotion Decision

Promote `alpha_0_05` as the current public-gate base for proof-base hardening
only:

```text
decision: row15_promoted_projection_promote_public_gate_base
new_public_gate_base:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
previous_public_gate_base:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
scope: public proof-base hardening only
```

## Explicitly Blocked Claims

```text
medium_ppo_performance_claim: false
long_run_ppo_stability_claim: false
private_holdout_claim: false
paper_level_generalization_claim: false
driver_performance_claim: false
real_vehicle_claim: false
level3_self_identification_claim: false
```

## Next Step

After promotion, the next step should be a post-promotion synthesis. It should
close `row15_promoted_unsafe_margin_projection` and select the next branch
before any PPO, private holdout, or medium-scale training.

```text
next: m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis
```
