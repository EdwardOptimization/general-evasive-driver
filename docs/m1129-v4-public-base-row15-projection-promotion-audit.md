# M1129 V4 Public Base Row15 Projection Promotion Audit

## Purpose

M1129 audits whether the M1123 alpha `0.15` row15 projection candidate should
become the next public-gate base.

This milestone does not train actor weights, run PPO, run replay, run objective
optimization, mine rows, use private holdout, or change actor inputs.

## Candidate

Previous public-gate base:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Candidate:

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

## Evidence

M1127 classified the candidate as:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
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

M1107 exact recheck:

```text
proof_current exact loss: 0.679117322
alpha_0_15 exact loss:   0.678699851
delta vs proof_current:  -0.000417471
```

Proof replay coverage:

```text
old public replay gates: 6 / 6
M1061 family-intersection replay gates: 3 / 3
source-diverse replay gates: 3 / 3
```

Fresh/OOD and behavior success rates were retained:

```text
fresh seed 103900: 0.8671875 -> 0.8671875
fresh seed 103901: 0.87109375 -> 0.87109375
moderate OOD seed 103920: 0.640625 -> 0.640625
behavior seed 9505:   0.8625 -> 0.8625
behavior seed 9506:   0.8625 -> 0.8625
behavior seed 103930: 0.8375 -> 0.8375
behavior seed 103931: 0.8250 -> 0.8250
```

The candidate repaired the row15 wrong-history-safe failure that rejected the
full M1118 actor update while preserving the old public, family-intersection,
source-diverse, fresh/OOD, and behavior gate stack.

## Scope

Promotion scope is limited:

```text
public-gate base: yes
proof-base hardening: yes
row15 unsafe-margin repair: yes
medium-PPO performance improvement: no
long-run PPO stability: no
private-holdout evidence: no
paper-level generalization: no
real-vehicle claim: no
level3 anticipatory self-identification claim: no
```

The reason to promote is not broad success-rate lift. The reason is that
alpha `0.15` is a no-training public proof-hardening projection from the
previous base that passes the expanded public gate stack after M1120 exposed a
row15 wrong-history terminal-margin failure.

## Decision

Promote alpha `0.15` as the current public-gate base:

```text
row15_projection_promote_public_gate_base
```

New public-gate base:

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Previous public-gate base:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Next:

```text
m1130-v4-public-base-row15-projection-post-promotion-synthesis
```
