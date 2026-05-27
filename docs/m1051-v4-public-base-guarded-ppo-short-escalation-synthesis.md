# M1051 V4 Public Base Guarded PPO Short Escalation Synthesis

## Purpose

M1051 synthesizes the guarded PPO short-escalation branch after M1049 and
M1050 produced three 4096-step public-gate PPO passes.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Evidence Summary

The current public-gate base is:

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

M1047 first tested smoke repeatability:

```text
total_steps per seed: 1024
seeds: 61045, 61046
raw_candidate_pass_count: 2 / 2
exact/proof/source-diverse/fresh/OOD/behavior: 2 / 2
```

M1049 escalated to one short PPO proposal:

```text
total_steps: 4096
seed: 61049
result_class: combined_active_set_guarded_ppo_raw_candidate
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
row15 wrong_history_margin: -0.000567
row16 normal_margin: 0.000621
```

M1050 repeated the 4096-step recipe:

```text
total_steps per seed: 4096
seeds: 61050, 61051
raw_candidate_pass_count: 2 / 2
exact/proof/source-diverse/fresh/OOD/behavior: 2 / 2
actor_inputs_changed_count: 0 / 2
```

Across M1049-M1050:

```text
4096-step public-gate passes: 3 / 3
private_holdout_used: false
promoted: false
```

## Supported Claims

The branch now supports these claims:

```text
1. The combined active-set guarded PPO recipe is not limited to a 1024-step
   smoke budget; it can survive 4096-step short PPO proposals.
2. The 4096-step guarded PPO result is repeatable across three PPO seeds under
   the current public-gate stack.
3. M267/M264 row15 wrong-history failure and M183/M170 row16 normal-history
   success can be retained through short PPO escalation.
4. PPO can remain useful as a proposal generator when exact/proof/source-
   diverse/fresh/OOD/behavior gates control acceptance.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
1. Any PPO beyond 1024 steps necessarily washes out the known row15 or row16
   proof rows.
2. The M1044 1024-step PPO pass was only a single-seed accident.
3. Guarded PPO must be abandoned before short-horizon escalation.
4. Exact/proof gates can be skipped because aggregate fresh/OOD behavior is
   enough.
```

The branch does not falsify the risk that public proof gates can be overfit,
because all evidence remains public-gate evidence.

## Failure Taxonomy Summary

Current branch failures:

```text
none
```

Historical failure modes that remain design constraints:

```text
M1026: proof_washout on M267/M264 row15
M1031: proof_washout via M183/M170 row16 normal terminal-margin cliff
M302/M303: sampled PPO auxiliary metrics can diverge from exact full-corpus gates
```

M1049/M1050 show these failures are avoidable at 4096 steps under the current
guarded recipe, but not that they are eliminated for medium/long PPO.

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

Risk remains because:

```text
1. All M1049/M1050 acceptance evidence is public-gate evidence.
2. The active-set anchor directly protects known historical public failure
   rows.
3. Private holdout has intentionally not been used.
```

Risk is reduced by:

```text
1. Three independent 4096-step PPO seeds passed.
2. Six proof replay surfaces passed per seed.
3. Three source-diverse diagnostics passed per seed.
4. Fresh public and moderate-OOD checks passed per seed.
5. Behavior ablation ordering was retained per seed.
```

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
m1052-v4-public-base-guarded-ppo-short-escalation-promotion-audit
```

## Why Promotion Audit Comes Next

The project now has enough public-gate evidence to ask whether one of the
4096-step raw checkpoints should become the next public-gate base. Promotion
should still be a separate audit because:

```text
1. M1049/M1050 explicitly blocked promotion.
2. There are three candidate checkpoints, and selection should be
   lexicographic rather than ad hoc.
3. Promotion scope must remain public-gate only.
4. Medium PPO should not start until the base candidate is explicit.
```

M1052 should evaluate these candidate checkpoints:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

Suggested lexicographic selection criteria:

```text
1. exact/proof/source-diverse/fresh/OOD/behavior gates all pass;
2. row15 wrong-history margin remains negative;
3. row16 normal margin remains positive;
4. exact total loss improvement is non-negative;
5. fresh/OOD margins do not regress;
6. prefer the checkpoint with better balanced row15/row16 slack and exact
   improvement, not only the largest aggregate return.
```

If M1052 promotes a candidate, the next route should be post-promotion
synthesis and likely source-diverse/public-surface refresh before medium PPO.

## Decision

```text
guarded_ppo_short_escalation_synthesis_route_to_promotion_audit
```

Next:

```text
m1052-v4-public-base-guarded-ppo-short-escalation-promotion-audit
```
