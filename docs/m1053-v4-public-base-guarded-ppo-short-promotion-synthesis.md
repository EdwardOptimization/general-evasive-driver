# M1053 V4 Public Base Guarded PPO Short Promotion Synthesis

## Purpose

M1053 synthesizes the project state after M1052 promoted the 4096-step guarded
PPO checkpoint as the current public-gate base.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or make medium/long PPO claims.

## Evidence Summary

New current public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Promotion basis:

```text
M1049:
  one 4096-step guarded PPO proposal passed full public gates.

M1050:
  two fresh 4096-step guarded PPO repeats passed full public gates.

M1051:
  synthesized three 4096-step public-gate passes and routed to promotion audit.

M1052:
  promoted seed61049 as current public-gate base with public-gate scope only.
```

The promoted candidate retained:

```text
M267/M264 row15 wrong-history failure:
  wrong_history_margin: -0.000567

M183/M170 row16 normal-history success:
  normal_margin: +0.000621
```

## Supported Claims

The branch supports these claims:

```text
1. The project now has a public-gate base that includes successful 4096-step
   guarded PPO continuation.
2. The combined active-set retention recipe can preserve the known row15 and
   row16 proof constraints through short PPO escalation.
3. Three independent 4096-step public-gate passes justify a public-gate base
   promotion, provided the scope remains limited.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
1. PPO continuation from this lineage necessarily fails at the short 4096-step
   scale.
2. The 1024-step guarded PPO success was only a one-off smoke artifact.
3. A public-base promotion requires private holdout evidence.
```

The branch does not prove:

```text
private-holdout generalization
medium or long PPO stability
paper-level statistical evidence
real-vehicle transfer
```

## Failure Taxonomy Summary

Current branch failures:

```text
none
```

Historical constraints still relevant:

```text
proof_washout: M267/M264 row15 wrong-history branch can become safe.
proof_washout: M183/M170 row16 normal branch can cross the terminal margin.
metric_artifact: sampled PPO auxiliary loss can disagree with exact gates.
public_gate_overfit_risk: repeated optimization has used known public surfaces.
```

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

The promotion is valid as a public-gate base, but the next research step should
not immediately lengthen PPO. The active-set anchor and promotion gates are
still built around known public proof surfaces. Before medium PPO, the project
should refresh the current-base protected/preference surface and ask whether
new source-diverse rows still support the same self-identification evidence.

## Next Branch Decision

Decision:

```text
continue
```

Branch remains:

```text
combined_active_set_guarded_ppo_readiness
```

Next milestone:

```text
m1054-v4-public-base-post-short-promotion-surface-refresh-design
```

## Next Route

M1054 should design a no-training current-base surface refresh:

```text
base:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

goal:
  refresh source-diverse protected/preference rows for the new base before
  medium PPO or private-holdout planning.

must include:
  source diversity constraints
  row15/row16 carry-over diagnostics
  fresh current-family wrong-history boundary mining
  compact corpus criteria
  no PPO, no promotion, no private holdout
```

If the refresh finds a healthy source-diverse surface, the next route can build
a v2 protected/preference corpus for medium-PPO gating. If the refresh finds
only stale public rows or saturated singletons, the project should audit
public-gate overfit before any more PPO.

## Decision

```text
guarded_ppo_short_promotion_synthesis_route_to_surface_refresh_design
```

Next:

```text
m1054-v4-public-base-post-short-promotion-surface-refresh-design
```
