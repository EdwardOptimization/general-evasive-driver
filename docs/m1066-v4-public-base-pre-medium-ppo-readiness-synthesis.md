# M1066 V4 Public Base Pre-Medium PPO Readiness Synthesis

## Purpose

M1066 synthesizes readiness for medium PPO after the 4096-step short-PPO
promotion, the post-promotion proof-surface refresh, and the expanded public
proof gate integration.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Evidence Summary

The current public-gate base is:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Short-PPO evidence from M1049-M1052:

```text
4096-step guarded PPO candidates: 3
public-gate passes: 3 / 3
selected public-gate base: seed61049
row15 wrong-history failure retained
row16 normal-history success retained
private_holdout_used: false
medium_or_long_ppo_claim: false
```

Post-promotion surface refresh from M1054-M1061:

```text
matched-current accepted pairs: 926
accepted wrong-history rows after relocation: 315
family-intersection candidates: 305
selected strict family-intersection rows: 79
selected physical pairs: 15
selected targets: 3
objective sanity: 3 / 3 source corpora passed
cross-family replay sanity: 6 / 6 gates passed
```

Expanded proof gate integration from M1063-M1065:

```text
M1064 reusable family-intersection public gate implemented.
M1065 integrated it into run_combined_active_set_full_public_gate.
Current base passed the M1065 no-PPO proof-tier preflight.
```

M1065 preflight:

```text
result_class: family_intersection_public_gate_pass
replay_gate_count: 3
replay_gates_passed: 3
failed_replay_gates: []
actor_inputs_changed: false
ppo_used: false
promoted: false
private_holdout_used: false
```

## Supported Claims

The evidence supports these claims:

```text
1. The current public-gate base is backed by three 4096-step guarded PPO public
   gate passes.
2. The project refreshed the proof surface after that promotion instead of
   immediately lengthening PPO.
3. The refreshed M1061 family-intersection corpus is source-diverse enough for
   public proof gating and has passed objective/replay sanity.
4. Future full public gates now include the M1061 family-intersection gate, so
   medium PPO proposals cannot pass by preserving old rows while breaking the
   refreshed short-PPO family surface.
5. A conservative medium PPO design is now admissible as a design milestone.
```

## Falsified Claims

The evidence falsifies or weakens these claims:

```text
1. Medium PPO should be attempted without refreshing current-family proof rows.
2. The M1055 margin-bucket failure meant no useful post-promotion surface
   existed.
3. Current-base-only compact rows are enough for family-wide proof gating.
4. The M1061 corpus can stay as ad hoc replay commands outside the public gate
   stack.
```

The evidence still does not prove:

```text
medium PPO stability
long PPO stability
private-holdout generalization
paper-level statistical evidence
real-vehicle transfer
```

## Failure Taxonomy Summary

Relevant recent failures:

```text
scenario_sampling_failure:
  M1055 failed the coarse 0.01m margin-bucket diagnostic.
  M1056 resolved it as a coarse bucket artifact.

proof_washout:
  M1058 lost three cross-family success-drop rows.
  M1061 resolved it through family-intersection filtering.
```

Historical failure modes that medium PPO must still guard:

```text
proof_washout:
  M267/M264 row15 wrong-history branch can become safe.

proof_washout:
  M183/M170 row16 normal branch can cross the terminal margin.

metric_artifact:
  sampled PPO auxiliary metrics can diverge from exact full-corpus gates.
```

Current M1066 branch failures:

```text
none
```

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

Risk is lower than before M1054 because the project refreshed the proof surface
after the short-PPO promotion and integrated that refresh into the public gate
stack. Risk remains because all of this is still public-gate evidence. The
M1061 rows are not private holdout evidence and should not be used for
paper-level claims.

Medium PPO can be designed, but it must be conservative:

```text
single seed first
moderate step increase, not long-run jump
expanded exact/proof/family-intersection/source-diverse/fresh/OOD/behavior
gates before any promotion discussion
hard rollback on row15, row16, and M1061 family-intersection regression
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close branch:

```text
post_short_promotion_family_gate_integration
```

Open branch:

```text
expanded_gate_medium_ppo_readiness
```

Next milestone:

```text
m1067-v4-public-base-expanded-gate-medium-ppo-design
```

M1067 should design a conservative medium PPO escalation using the expanded
gate stack. It should not run PPO. The design should specify:

```text
1. step count and seed;
2. exact proof gates;
3. old public replay gates;
4. M1061 family-intersection gate;
5. source-diverse diagnostics;
6. fresh/OOD and behavior gates;
7. rollback conditions;
8. no promotion and no private holdout.
```

## Decision

```text
pre_medium_ppo_readiness_synthesis_admit_expanded_gate_medium_ppo_design
```

Next:

```text
m1067-v4-public-base-expanded-gate-medium-ppo-design
```
