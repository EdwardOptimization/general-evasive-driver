# M1245 Paper-Route Capability-Separable Source-Window Audit

## Summary

M1245 audits why both M1242 first-action and M1244 short-sequence source
constructors produced source-diverse but low-regret negative results.

Decision:

```text
source_window_audit_select_viability_band_relocation_smoke
```

The next step should not train or tune actor history. It should change the
source-window construction so matched hidden-dynamics rows are moved into a
near-boundary viability band before testing action separability.

## Inputs Audited

Primary artifact:

```text
runs/m1244_capability_separable_short_sequence_lattice_smoke/summary.json
```

Supporting artifacts:

```text
runs/m1244_capability_separable_short_sequence_lattice_smoke/matched_capability_pairs.csv
runs/m1244_capability_separable_short_sequence_lattice_smoke/sequence_rollouts.csv
runs/m1244_capability_separable_short_sequence_lattice_smoke/snapshot_candidates.csv
```

## M1244 Recap

```text
candidate_pair_count: 1404
matched_pair_count: 120
sequence_rollouts: 10320
accepted_separable_pairs: 0
best_actions_diverged_pairs: 8
low_regret_pairs: 120
unique_matched_fault_family_pairs: 9
unique_matched_seeds: 20
result_class: action_divergent_low_regret
```

Rejection distribution:

```text
best_actions_too_close: 112
best_candidate_not_viable: 5
insufficient_cross_regret: 3
```

## Obstacle Window Audit

The obstacle is not far away in the selected source rows:

```text
obstacle_distance_A min: 2.3889469961
obstacle_distance_A p10: 4.1528741638
obstacle_distance_A p50: 10.5810085669
obstacle_distance_A p90: 15.1396288196
obstacle_distance_A max: 17.6561988535
near obstacle A <= 30m: 120 / 120
```

Step window:

```text
step_A min: 20
step_A p50: 28
step_A p90: 36
step_A max: 36
```

So the source-negative result is not explained by selecting pre-emergency
states that are too far from the obstacle.

## Viability-Band Audit

Pair-level minimum best margin is bifurcated:

```text
pair_min_best_margin p0: -0.2665277600
pair_min_best_margin p10: -0.1791754961
pair_min_best_margin p25: -0.0716362285
pair_min_best_margin p50: 1.8906735438
pair_min_best_margin p75: 4.6691690890
pair_min_best_margin p90: 7.0663964368
pair_min_best_margin p100: 9.5912178860
```

Band counts:

```text
[-1.0, 0.0): 46 pairs, 5 diverged
[0.0, 0.05): 0 pairs, 0 diverged
[0.05, 0.2): 0 pairs, 0 diverged
[0.2, 1.0): 8 pairs, 0 diverged
[1.0, 10.0): 66 pairs, 3 diverged
```

This is the key finding. The selected matched rows are mostly either:

```text
too hard: even the best sequence is nonviable
too easy: both hidden conditions have large positive margin
```

The source has almost no rows where both hidden conditions are viable but close
to a decision boundary.

## Action-Spread Audit

Within-condition action sensitivity exists:

```text
margin_spread p50: 0.0254935179
margin_spread p90: 0.0702511867
margin_spread p99: 0.1946895563
margin_spread max: 0.2565641777
```

But it does not become branch-specific separability:

```text
both cross regrets >= 0.02: 0
```

So simply adding more action templates is not the highest-leverage next move.
The source window must first produce viable near-boundary states where action
choice matters enough for hidden dynamics to change the correct maneuver.

## Decision

M1245 selects a bounded viability-band relocation smoke.

Keep fixed:

```text
checkpoint
M1236 fault/source config
cross-fault matching
short-sequence candidate object
seed/family-pair diversity caps
no training
no PPO
no promotion
actor input contract
```

Change one source-construction variable:

```text
relocate obstacle/source geometry to target a pair-level viability band
```

Initial target:

```text
both hidden conditions have best_margin >= 0
pair_min_best_margin in [0.02, 0.5]
```

The source-positive criterion remains unchanged:

```text
best sequence divergence and cross-regret under matched hidden dynamics
```

## Why Not Other Next Steps

Do not train:

```text
source-positive rows do not exist yet
```

Do not keep broadening sequence templates:

```text
action sensitivity exists, but branch-specific cross-regret is still too low
```

Do not jump directly to high-fidelity simulation:

```text
the current model has not yet been tested under boundary-conditioned source
relocation
```

Do not lower thresholds:

```text
no M1244 row has both cross regrets near 0.02
```

## Next

M1246 should implement and run a no-training viability-band relocation smoke:

```text
m1246-paper-route-capability-separable-viability-band-relocation-smoke
```

It should write:

```text
relocated_source_pairs.csv
relocation_candidates.csv
sequence_rollouts.csv
accepted_separable_pairs.csv
summary.json
model_fidelity_limits.md
```

Accepted rows remain diagnostic only.
