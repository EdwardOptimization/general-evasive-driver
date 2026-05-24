# M580 BC Family Generalization Audit

## Purpose

M580 audits the scaled BC family after the route and moderate-OOD family repeats.

This milestone is audit-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Evidence Summary

| Milestone | Surface | BC5660 | BC5661 | BC5662 | L2 |
| --- | --- | ---: | ---: | ---: | ---: |
| M578 success | Fresh route `21560..21815` | 0.675781 | 0.671875 | 0.675781 | 0.671875 |
| M578 collision | Fresh route `21560..21815` | 0.324219 | 0.328125 | 0.324219 | 0.328125 |
| M578 margin | Fresh route `21560..21815` | 0.992939 | 0.982097 | 0.991177 | 0.978128 |
| M579 success | Moderate-OOD `22560..22815` | 0.582031 | 0.574219 | 0.582031 | 0.574219 |
| M579 collision | Moderate-OOD `22560..22815` | 0.417969 | 0.425781 | 0.417969 | 0.425781 |
| M579 margin | Moderate-OOD `22560..22815` | 0.921253 | 0.914780 | 0.920871 | 0.913270 |

All three BC seeds are L0-safe and L2-competitive on both repeat blocks. BC5660
and BC5662 slightly exceed L2 on both blocks; BC5661 essentially matches L2.

## Current Claim

The evidence now supports:

```text
Scaled L2-to-L3 behavior cloning reliably transfers the L2 finite-window route
behavior into L3 online-GRU students across three optimizer seeds, a fresh route
block, and a moderate-OOD route block, without L2 stack leakage into the deployed
actor.
```

This is a strong engineering result and a useful platform result.

## Remaining Gap

The evidence still does not prove:

```text
The deployed L3 actor needs and uses recurrent command-response history.
```

It may be that:

1. the online-GRU hidden state carries useful command-response state;
2. the current 72-value frame plus previous command is already enough for these
   route distributions;
3. the BC objective distilled L2 behavior into a mostly memoryless policy.

The next evidence layer must distinguish these cases before promotion or PPO.

## Available Tooling

The repository already has checkpoint ablation support through
`autodrift.benchmark`:

```text
runs/checkpoint.pt@reset_recurrent_state
runs/checkpoint.pt@zero_current_response
runs/checkpoint.pt@zero_action_history
runs/checkpoint.pt@zero_all_response
```

This is sufficient for a first recurrent-dependence diagnostic because the
comparison is L3-only and can use one shared L3 env config at a time.

## Next Direction

M581 should design recurrent-dependence ablation benchmarks for the scaled BC
branch.

First diagnostic:

```text
checkpoint: BC5660
normal vs reset_recurrent_state vs zero_current_response vs zero_action_history
same-distribution fresh seed block: 23560..23815
moderate-OOD fresh seed block:     24560..24815
```

Interpretation:

- If reset/zero-current/zero-action significantly degrade success or margin,
  admit a broader BC-family ablation gate.
- If ablations do not degrade behavior, do not claim recurrent self-ID; classify
  the result as L2 behavior transfer without demonstrated recurrent dependence.
- If zero-current degrades but reset does not, the current response frame matters
  more than accumulated hidden state.
- If zero-action degrades, command-response pairing matters.

Suggested diagnostic thresholds:

```text
success_drop >= 0.02 or margin_drop >= 0.05: meaningful degradation
success_drop >= 0.05 or margin_drop >= 0.10: strong degradation
```

These thresholds are diagnostic only, not promotion criteria.

## Decision

```text
bc_family_generalization_audit_admit_recurrent_ablation_design
```

M580 passes because it records the BC family generalization evidence, blocks
promotion/PPO, and identifies recurrent-dependence ablation diagnostics as the
next evidence layer.

## Next

```text
M581: design recurrent-dependence ablation benchmarks for the scaled BC branch.
```
