# M1046 V4 Public Base Guarded PPO Post-Promotion Synthesis

## Purpose

M1046 synthesizes the M1043-M1045 guarded PPO smoke branch before any repeat
PPO, longer PPO, proof-surface refresh, or additional objective update.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or claim multi-seed/long-run PPO stability.

## Evidence Summary

M1043 designed the post-promotion guarded PPO protocol from the combined
active-set public base:

```text
base:
  runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt

required gates:
  M997 temporal retention
  M297/M270 exact no-regression
  combined active-set loss
  six public replay surfaces
  source-diverse diagnostics
  fresh public / moderate-OOD checks
  behavior/ablation seeds
```

M1044 ran one 1024-step PPO proposal:

```text
raw checkpoint:
  runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt

ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
```

The two historical hard active sets were retained:

```text
M267/M264 row15:
  wrong_history_success: false
  wrong_history_margin: -0.000847

M183/M170 row16:
  normal_success: true
  normal_margin: 0.000467
```

M1045 promoted the raw PPO checkpoint as the current public-gate base:

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

## Supported Claims

The branch supports these claims:

```text
1. A 1024-step guarded PPO proposal can improve/move the public-gate base while
   preserving exact, proof replay, source-diverse, fresh/OOD, and behavior
   public gates.
2. The combined active-set anchor is useful as a PPO-time retention signal:
   M1044 avoids the M1026 row15 proof washout and the M1031 row16 normal cliff.
3. PPO can be used as a proposal generator under exact full-corpus gate control.
4. The M1044 raw checkpoint is a valid public-gate base successor.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
1. Any guarded PPO from this lineage necessarily washes out M267/M264 row15.
2. PPO must be avoided entirely after active-set repair.
3. Aggregate fresh/OOD behavior is sufficient for promotion without proof gates.
4. A single successful PPO smoke proves multi-seed or long-run PPO stability.
```

## Failure Taxonomy Summary

M1043-M1045 ended with:

```text
failure_types: none
```

The relevant historical failures are still active design constraints:

```text
M1026: proof_washout on M267/M264 row15
M1031: proof_washout via M183/M170 row16 normal terminal-margin cliff
```

M1044 shows these failures are avoidable under the combined active-set guarded
recipe, but not yet that the recipe is seed-stable.

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons it remains:

```text
1. All promotion evidence is still public-gate evidence.
2. M1044 is one PPO seed, not a repeat.
3. The combined active-set anchor directly includes known public hard rows.
```

Reasons it is acceptable to continue:

```text
1. Fresh public and moderate-OOD checks did not regress.
2. Source-diverse protected diagnostics passed.
3. Behavior/ablation ordering was retained.
4. The hard rows were retained with the exact failure/success polarity needed
   for self-identification evidence.
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
m1047-v4-public-base-guarded-ppo-fresh-seed-repeat
```

## Next Route

The next step should not be 4k/16k PPO yet. M1047 should run a fresh-seed
smoke repeat from the current public-gate base.

Proposed repeat:

```text
base:
  runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt

seeds:
  61045
  61046

total_steps per seed:
  1024
```

M1047 should use the same M1044 gate stack:

```text
M997
M297/M270
combined active-set loss
six public replay surfaces
source-diverse diagnostics
fresh public / moderate-OOD
behavior/ablation seeds
```

Pass rule:

```text
at least 2 / 2 fresh PPO seeds run with finite metrics;
at least 2 / 2 preserve actor inputs;
at least 2 / 2 pass exact and public proof gates;
at least 2 / 2 preserve row15 wrong-history failure and row16 normal success;
at least 2 / 2 avoid fresh/OOD/behavior regression.
```

If either seed fails proof while training and generalization are otherwise
healthy, route to exact repair/projection audit. If both pass, route to short
PPO escalation design.

## Decision

```text
guarded_ppo_post_promotion_synthesis_continue_to_fresh_seed_repeat
```

Next:

```text
m1047-v4-public-base-guarded-ppo-fresh-seed-repeat
```
