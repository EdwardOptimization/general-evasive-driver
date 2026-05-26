# M977 V4 Public Base Post-Promotion Exact Repair Promotion Audit

## Purpose

M977 audits whether the M974 exact-repaired candidate should replace alpha
`1.0` as the current public-gate base.

M977 does not train, run PPO, use private holdout, change actor inputs, or make
paper-level or real-vehicle claims.

## Candidate

Previous public-gate base:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Promotion candidate:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

## Evidence Checked

M974 exact repair and first replay:

```text
exact M297 delta: -0.000044584
exact M270 delta: -0.000060797
M267/M264 first replay: pass, 17 / 17 success drops
M183/M170 first replay: pass, 17 / 17 success drops
```

M976 full public gate:

```text
proof_pass: true
proof_replay_gates_passed: 6 / 6
source_diverse_protected_status: pass
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
ppo_used: false
private_holdout_used: false
promoted: false
```

The old-key neighborhood remains diagnostic-only. It does not veto this
promotion because both the previous base and candidate have `policy_pass=false`
there, and the branch promotion criteria were public replay, source-diverse
diagnostic, fresh/OOD, and behavior retention.

## Decision

Promote the M974 exact-repaired candidate as the new current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Decision:

```text
exact_repair_promote_public_gate_base
```

## Caveats

This is only a public-gate base promotion.

Still blocked:

- PPO continuation from the promoted candidate;
- private holdout;
- paper-level statistical evidence;
- broader scenario-distribution benchmark;
- real-vehicle or high-fidelity simulator claims.

The next milestone should synthesize M971-M977 before starting another
post-promotion PPO or repair branch.

## Next Blocker

```text
m978-v4-public-base-post-exact-repair-promotion-synthesis
```
