# M1246 Paper-Route Capability-Separable Viability-Band Relocation Smoke

## Summary

M1246 implements and runs a bounded no-training viability-band relocation smoke.

Decision:

```text
viability_band_relocation_infrastructure_pass_near_positive_route_to_fine_relocation
```

The infrastructure passed. Relocation fixed the missing viability-band problem,
but the source-positive action-separability gate still did not pass:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

The important new evidence is that relocation produced near-boundary viable
rows and exposed one near-positive nonviable row with strong two-sided
cross-regret.

## Implementation

M1246 extends `src/autodrift/capability_separable_source_constructor.py` with:

```text
--source-window-mode viability_band_relocation
--target-min-best-margin
--target-max-best-margin
--max-relocation-candidates
```

The relocation logic:

1. evaluates the source pair with the shared short-sequence lattice;
2. builds obstacle geometry candidates from the source obstacle body-frame
   geometry and pair-level best margin;
3. applies the same relocated obstacle geometry to both hidden-dynamics
   conditions;
4. evaluates the same sequence candidates under both conditions;
5. selects the relocation closest to the target viability band.

Relocation labels and oracle outcomes remain source metadata only. They are not
actor inputs.

## Runtime Bound

The first full M1246 command used 96 pairs with an unbounded relocation scan and
was interrupted after about 16 minutes without artifacts. The final smoke is
bounded:

```text
max_pairs: 48
max_pairs_per_seed: 4
max_pairs_per_family_pair: 8
max_relocation_candidates: 8
```

This keeps M1246 as an infrastructure smoke rather than a long experiment.

## Final Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 124600 \
  --seed-count 24 \
  --max-pairs 48 \
  --max-pairs-per-seed 4 \
  --max-pairs-per-family-pair 8 \
  --candidate-mode short_sequence \
  --sequence-length 3 \
  --sequence-template-set steer_brake_pulses \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.02 \
  --target-max-best-margin 0.5 \
  --max-relocation-candidates 8 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1246_capability_separable_viability_band_relocation_smoke
```

## Final Result

Artifact:

```text
runs/m1246_capability_separable_viability_band_relocation_smoke/summary.json
```

Key metrics:

```text
candidate_pair_count: 1404
matched_pair_count: 48
relocation_candidates: 384
relocated_matched_pairs: 48
near_boundary_viability_pairs: 24
sequence_rollouts: 4128
accepted_separable_pairs: 0
best_actions_diverged_pairs: 10
low_regret_pairs: 47
unique_matched_fault_family_pairs: 8
unique_matched_seeds: 12
result_class: action_divergent_low_regret
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

Rejection reasons:

```text
best_actions_too_close: 38
best_candidate_not_viable: 6
insufficient_cross_regret: 4
```

Distribution:

```text
pair_min_best_margin p50: 0.0200058103
pair_min_best_margin p90: 0.2599905099
best_action_l2 p90: 0.3872983456
best_action_l2 max: 0.6000000238
cross_regret_A max: 0.2107246264
cross_regret_B max: 0.3418288535
one regret >= 0.02: 6
both regrets >= 0.02: 1
```

## Key Row

One selected relocation has strong two-sided cross-regret but remains slightly
nonviable:

```text
pair_id: 5
seed: 124601
family_pair: global_mu_drop->brake_authority_drop
best_action_l2: 0.5049752593
cross_regret_A: 0.2107246264
cross_regret_B: 0.0201005052
margin_A_best_A: -0.0040640062
margin_B_best_B: -0.0048001855
rejection_reason: best_candidate_not_viable
```

This is qualitatively different from M1242/M1244. The source now contains a
matched hidden-dynamics pair where different sequences matter, but the current
relocation grid undershoots viability by about `0.005` margin.

## Interpretation

M1246 confirms the M1245 diagnosis:

```text
relocation can create near-boundary viable rows
source-window repair increases action divergence and cross-regret
the current coarse relocation grid is not yet calibrated enough for accepted
source-positive rows
```

Do not train yet. The correct next step is a bounded fine-relocation
calibration around the near-positive rows, keeping the actor and source contract
unchanged.

## Next

M1247 should implement a fine viability-band relocation calibration smoke:

```text
m1247-paper-route-capability-separable-fine-relocation-calibration-smoke
```

It should focus on rows/candidates with:

```text
best_action_l2 >= 0.12
one or both cross_regrets near or above threshold
pair_min_best_margin near zero
```

The only changed source variable should be finer obstacle half-width / lateral
relocation around the near-positive candidates. No training, PPO, promotion,
private holdout, actor-input expansion, or self-ID claim should occur.
