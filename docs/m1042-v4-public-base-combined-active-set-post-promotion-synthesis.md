# M1042 V4 Public Base Combined Active-Set Post-Promotion Synthesis

## Purpose

M1042 synthesizes the M1036-M1041 combined active-set repair and promotion
branch before any PPO continuation or additional objective update.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or claim paper-level/real-vehicle generalization.

## Evidence Summary

The branch started after M1035 concluded that Candidate B guarded PPO readiness
was blocked by two active sets:

```text
M267/M264 row15: wrong-history branch lift under PPO/repair
M183/M170 row16: normal-history terminal-margin cliff under projection
```

M1036 rejected naive anchor concatenation because the M293 rejected-history
anchor and M1034 row16 anchor shared source indices and the 57-row row16 anchor
would be diluted by the 3900-row M293 anchor.

M1037 exported source-namespaced, family-normalized combined anchors:

```text
balanced
row16x4
row16x8
rows per variant: 3957
M293 rows: 3900
M1034 row16 rows: 57
M1034 source offset: 1000000
```

M1038 used the `row16x4` anchor and found a temporal/exact-safe first-replay
candidate:

```text
checkpoint:
  runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt

source: base_row16x4_s40
alpha: 0.15
M997 action_l2_mean: 0.002198
M297 delta: -0.000020
M270 delta: -0.000001
M267/M264 first replay: pass, row15 retained
M183/M170 first replay: pass, row16 retained
```

M1040 upgraded that checkpoint to a full public-gate candidate:

```text
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
proof replay surfaces: 6 / 6
source-diverse diagnostics: 3 / 3
fresh public seeds: 103900, 103901
moderate-OOD seed: 103920
behavior seeds: 9505, 9506, 103930, 103931
```

M1041 promoted the checkpoint as the current public-gate base:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

## Supported Claims

The branch supports these claims:

```text
1. Candidate B's post-PPO blocker was a combined active-set problem, not a
   single-row issue.
2. M267/M264 row15 wrong-history retention and M183/M170 row16 normal-margin
   retention can be jointly preserved with a source-namespaced combined anchor.
3. Updating only actor_mean and response_context_fusion.0 can produce a
   checkpoint that passes exact, proof replay, source-diverse, fresh/OOD, and
   behavior public gates.
4. The promoted checkpoint is a valid public-gate base successor to Candidate B.
5. The promotion discipline worked: first replay, full public gate, and
   promotion audit stayed separate.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
1. M293 rejected-history retention alone is enough after PPO washout.
2. M183/M170 row16 can be ignored as a stale singleton during Candidate B repair.
3. Exact M297/M270 no-regression alone is enough to protect public replay gates.
4. M1038 first-replay evidence is sufficient for direct promotion.
5. Public-gate promotion proves long-run PPO stability or paper-level
   generalization.
```

## Failure Taxonomy Summary

The failure chain before this branch was:

```text
M1026: proof_washout
M1029: temporal_retention_regression
M1031: proof_washout via M183/M170 row16 normal terminal margin
```

The M1036-M1041 branch itself ends with:

```text
failure_types: none
```

The important residual risk is not a failing gate; it is active-set overfit risk
from repeated use of public proof surfaces.

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons it remains:

```text
1. The new base was engineered against known public active sets.
2. M267/M264 row15 and M183/M170 row16 are now explicitly in the repair logic.
3. Promotion is still based on public gates, not private holdout.
```

Reasons it is lower than before:

```text
1. The gate includes six historical public replay surfaces, not only row15/row16.
2. Source-diverse public diagnostics pass on three additional surfaces.
3. Fresh public and moderate-OOD success/termination rates do not regress.
4. Behavior/ablation ordering is retained on four seeds.
5. Actor inputs remain P0 human-view and no oracle fields were added.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Closed branch:

```text
candidate_b_combined_active_set_repair
```

Opened branch:

```text
combined_active_set_guarded_ppo_readiness
```

Next milestone:

```text
m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design
```

## Next Route

The next branch should design a guarded PPO readiness protocol from the new
public-gate base, but it must not immediately run PPO.

M1043 should require:

```text
1. base checkpoint fixed to the M1041 public-gate base;
2. P0 actor inputs unchanged;
3. exact M997, M297/M270, and combined active-set checks before replay;
4. six public replay surfaces and source-diverse diagnostics after any PPO
   proposal;
5. fresh public, moderate-OOD, and behavior seeds as non-regression gates;
6. explicit rollback if M267/M264 row15 or M183/M170 row16 regresses;
7. no private holdout and no long PPO until a smoke proposal passes.
```

M1043 should also decide whether post-PPO exact repair/projection is mandatory
for every PPO proposal, rather than treating scalar auxiliary loss as enough.

## Decision

```text
combined_active_set_post_promotion_synthesis_promote_to_guarded_ppo_readiness
```

Next:

```text
m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design
```
