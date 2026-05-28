# M1399 Paper-Route Warmup Reveal Pressure Redesign

## Summary

M1399 designs the first branch step after M1398 closed the prior causal
history-necessity branch. The goal is to make the warmup-latched task more
outcome-critical without changing the actor input contract.

Decision:

```text
warmup_reveal_pressure_redesign_admit_late_reveal_source_smoke
```

M1399 is design only. It does not train, run PPO, run a new source sweep,
promote, use private holdout, export a corpus, or change actor inputs.

## Blocker From M1398

The previous branch could materialize source-diverse rows, but the outcome
surface was not strong enough:

```text
M1397 selected_candidate_rows: 604
M1397 evaluated unique_source_seeds: 27
M1397 evaluated unique_capability_pairs: 16
M1397 evaluated unique_reveal_buckets: 131
M1397 warmup_history_positive_rows: 31
M1397 accepted_warmup_history_unique_source_seeds: 1
M1397 wrong_warmup outcome-critical rows: 0
M1397 delayed_warmup outcome-critical rows: 0
```

The failure is not source materialization. It is scenario pressure: normal
rollouts are usually too easy or history interventions do not move the outcome
enough.

## Design Target

The next source route must target:

```text
normal_success: true
normal_terminal_reason: obstacle_completed
normal_min_clearance_margin: small but nonnegative
current/recent reveal: strictly matched or bucketed across capability families
warmup evidence: present before reveal
history intervention: capable of changing margin or success in source-diverse rows
```

Near-boundary normal viability is the key difference from M1394:

```text
old source goal: materialize matched/bucketed reveal rows
new source goal: materialize matched/bucketed reveal rows whose normal rollout
                 has small positive clearance margin
```

## Immediate Source Redesign

Start with a no-training late-reveal source smoke using the existing
`warmup_latched_config_smoke` runner. This keeps the first step cheap and avoids
changing the simulator before proving that later reveal timing can be expressed.

Initial reveal grid:

```text
reveal_steps: 64,72,80,88,96
history_length: 48
min_warmup_evidence_steps: 12
seed_count: 48
max_source_rows: 6144
```

Rationale:

```text
M1394 already swept 48,56,64,72.
M1397 positives remained margin-only and source-narrow.
Later reveal steps should increase obstacle pressure if trajectories remain
reconstructable.
```

This source smoke is not allowed to claim self-identification. It should only
answer whether later reveal timing can still materialize matched/bucketed rows
with warmup evidence and source diversity.

## Near-Boundary Outcome Screen

After a late-reveal source smoke passes structurally, the next outcome probe
should screen normal rollout pressure before interpreting history positives.

Candidate-level normal viability window:

```text
normal_success == true
normal_terminal_reason == obstacle_completed
0.00 <= normal_min_clearance_margin <= 0.50
```

Preferred paper-route target:

```text
0.02 <= normal_min_clearance_margin <= 0.25
```

The broader `0.50` window is for source-screen admission; the narrower `0.25`
window is for stronger diagnostic positives. The design must report both.

Rows with high normal margin can remain in diagnostics, but they should not be
used as positive evidence for history necessity.

## Current/Recent Substitution Controls

The next outcome probe must preserve M1395/M1397 controls:

```text
normal
reset_hidden
zero_current_response
delayed_warmup_history_8
delayed_warmup_history_16
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
warmup_removed
warmup_shortened_8
```

Additional reporting requirement:

```text
accepted rows split by strict matched-current versus bucketed-current;
accepted rows split by normal margin band;
accepted rows split by reveal step;
accepted rows split by capability pair and seed.
```

Interpretation rule:

```text
reset_hidden and zero_current_response remain controls;
warmup_removed/shortened rows are warmup-duration evidence only;
wrong_warmup and same_recent_wrong_warmup are the primary self-ID candidates;
delayed_warmup rows are secondary temporal necessity candidates.
```

## Source-Diversity Thresholds

Late-reveal structural smoke:

```text
source_rows >= 512
matched_or_bucketed_reveal_rows >= 160
unique_source_seeds >= 24
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
finite metrics
```

Near-boundary screen admission:

```text
near_boundary_candidates >= 64
near_boundary_unique_seeds >= 12
near_boundary_unique_capability_pairs >= 6
near_boundary_unique_reveal_buckets >= 4
```

Public diagnostic positive:

```text
warmup_history_positive_rows >= 48
accepted_seeds >= 12
accepted_capability_pairs >= 6
accepted_reveal_buckets >= 4
wrong_warmup_or_same_recent_wrong_rows > 0
normal_margin_window_reported: true
```

The last condition prevents warmup-removed-only positives from being counted as
full self-identification evidence.

## Stop Conditions

Stop this branch and synthesize if any of these persist after one source smoke
and one outcome probe:

```text
late reveal cannot reconstruct enough rows;
near-boundary candidates remain source-narrow;
accepted rows remain only seed-singleton warmup_removed/shortened;
wrong_warmup and delayed_warmup variants remain zero;
normal failures dominate before viable near-boundary rows appear;
the required source route needs actor-input or oracle-label changes.
```

## Next

M1400 should run a no-training late-reveal source smoke:

```text
python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --seed-start 140000 \
  --seed-count 48 \
  --reveal-steps 64,72,80,88,96 \
  --history-length 48 \
  --min-warmup-evidence-steps 12 \
  --max-source-rows 6144 \
  --device cpu \
  --run-dir runs/m1400_warmup_reveal_pressure_source_smoke
```

M1400 should not run outcome interventions yet. It should first verify that
late reveal timing remains structurally viable.

## Guardrails

```text
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
