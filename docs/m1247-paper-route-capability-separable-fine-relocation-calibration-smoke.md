# M1247 Paper-Route Capability-Separable Fine Relocation Calibration Smoke

## Summary

M1247 implements and runs a bounded no-training fine relocation calibration
smoke.

Decision:

```text
fine_relocation_valid_source_negative_route_to_limit_audit
```

The infrastructure passed, but the source-positive gate still did not pass:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

The result is useful because it separates three cases:

1. fine relocation can produce valid rollout artifacts;
2. fine relocation can produce near-boundary viable rows;
3. local half-width/lateral calibration still does not create a row where both
   hidden-dynamics branches are viable and require different best sequences.

## Implementation

M1247 extends `src/autodrift/capability_separable_source_constructor.py` with
an optional second-stage relocation search:

```text
--fine-relocation
--fine-half-width-deltas
--fine-body-y-offsets
--fine-parent-count
```

The implementation first evaluates the existing coarse viability-band
relocation candidates. If no accepted row appears, it picks the best coarse
parent by band distance and local regret signal, then evaluates fine
half-width and lateral-offset variants around that parent.

Relocation labels and oracle outcomes remain source metadata only. They are
not actor inputs.

## Runtime Bound

Two larger commands were interrupted before artifacts because they exceeded
the intended infrastructure-smoke budget:

```text
48 pairs / 24 relocation candidates
24 pairs / 16 relocation candidates
```

The final M1247 run is a focused calibration smoke:

```text
seed_count: 4
max_pairs: 12
max_relocation_candidates: 16
```

This still includes the M1246 near-positive seed `124601`, while keeping the
run bounded.

## Final Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 124600 \
  --seed-count 4 \
  --max-pairs 12 \
  --max-pairs-per-seed 4 \
  --max-pairs-per-family-pair 8 \
  --candidate-mode short_sequence \
  --sequence-length 3 \
  --sequence-template-set steer_brake_pulses \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.02 \
  --target-max-best-margin 0.5 \
  --max-relocation-candidates 16 \
  --fine-relocation \
  --fine-half-width-deltas=-0.08,-0.04,-0.02,-0.01,0.01,0.02,0.04,0.08 \
  --fine-body-y-offsets=-0.40,-0.20,-0.10,-0.05,0.05,0.10,0.20,0.40 \
  --fine-parent-count 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1247_capability_separable_fine_relocation_calibration_smoke
```

## Final Result

Artifact:

```text
runs/m1247_capability_separable_fine_relocation_calibration_smoke/summary.json
```

Key metrics:

```text
candidate_pair_count: 204
matched_pair_count: 12
relocation_candidates: 192
coarse_relocation_candidates: 96
fine_relocation_candidates: 96
relocated_matched_pairs: 12
near_boundary_viability_pairs: 1
sequence_rollouts: 1032
accepted_separable_pairs: 0
best_actions_diverged_pairs: 6
low_regret_pairs: 11
unique_matched_fault_family_pairs: 2
unique_matched_seeds: 3
result_class: action_divergent_low_regret
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

Selected-pair rejection reasons:

```text
best_candidate_not_viable: 6
best_actions_too_close: 6
```

Relocation-candidate rejection reasons:

```text
best_actions_too_close: 174
best_candidate_not_viable: 18
accepted: 0
near_boundary_viability: 8
```

## Key Rows

The strongest two-sided regret row remains the M1246 near-positive case:

```text
pair_id: 5
seed: 124601
family_pair: global_mu_drop->brake_authority_drop
relocation_stage: coarse
best_action_l2: 0.5049752593
cross_regret_A: 0.2107246264
cross_regret_B: 0.0201005052
pair_min_best_margin: -0.0048001855
rejection_reason: best_candidate_not_viable
```

Fine variants around this row increased action divergence in some cases, but
did not restore both-branch viability:

```text
best fine min(cross_regret_A, cross_regret_B): 0.1023287308
best fine pair_min_best_margin: -0.1315487281
```

The only selected near-boundary viable row had no action divergence:

```text
pair_id: 4
seed: 124601
family_pair: global_mu_drop->front_lateral_authority_drop
near_boundary_viability: true
best_action_l2: 0.0
cross_regret_A: 0.0
cross_regret_B: 0.0
pair_min_best_margin: 0.0202010285
```

## Interpretation

M1247 does not support another immediate relocation-grid expansion. The source
shape is now clearer:

```text
near-boundary viable rows exist, but they are action-equivalent;
action-divergent rows exist, but their best branches remain nonviable;
fine half-width/lateral calibration does not bridge that split in the current
focused source window.
```

Do not train yet. Training would optimize on a source corpus that still lacks
accepted capability-separable rows.

## Next

The next milestone should be a negative/source-limit audit:

```text
m1248-paper-route-capability-separable-fine-relocation-negative-audit
```

It should decide whether the current-model local relocation branch is
exhausted, and whether the next source variable should be a richer action
sequence object, a different event timing source, a learned/teacher proposal,
or a higher-fidelity dynamics source. No training, PPO, promotion, private
holdout, actor-input expansion, or self-ID claim should occur before that
audit.
