# M1244 Paper-Route Capability-Separable Short-Sequence Lattice Smoke

## Summary

M1244 implements and runs a bounded short-sequence action lattice for
capability-separable source construction.

Decision:

```text
short_sequence_lattice_smoke_infrastructure_pass_low_regret_route_to_source_window_audit
```

The infrastructure passed. The source-positive test did not pass:

```text
result_class: action_divergent_low_regret
accepted_separable_pairs: 0
```

M1244 is still source construction only. It does not train, run PPO, promote,
use private holdout, change actor inputs, or claim self-identification.

## Implementation

M1244 extends the M1242 constructor with:

```text
--candidate-mode short_sequence
--sequence-length 3
--sequence-template-set steer_brake_pulses
```

Each matched pair uses one shared sequence candidate set under both hidden
conditions. The sequence templates are compact steer/brake pulse templates:

```text
hold
release
ramp
```

The action distance used for best-sequence divergence is normalized by
`sqrt(sequence_length)` so K-step sequences remain comparable to first-action
distances.

## Final Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 124400 \
  --seed-count 24 \
  --max-pairs 120 \
  --max-pairs-per-seed 6 \
  --max-pairs-per-family-pair 18 \
  --candidate-mode short_sequence \
  --sequence-length 3 \
  --sequence-template-set steer_brake_pulses \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1244_capability_separable_short_sequence_lattice_smoke
```

## Final Result

Artifact:

```text
runs/m1244_capability_separable_short_sequence_lattice_smoke/summary.json
```

Key metrics:

```text
candidate_pair_count: 1404
matched_pair_count: 120
sequence_lattice_rows: 5160
sequence_rollouts: 10320
accepted_separable_pairs: 0
best_actions_diverged_pairs: 8
low_regret_pairs: 120
unique_matched_fault_family_pairs: 9
unique_matched_seeds: 20
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
best_actions_too_close: 112
best_candidate_not_viable: 5
insufficient_cross_regret: 3
```

Distribution:

```text
best_action_l2 p50: 0.0
best_action_l2 p90: 0.0
best_action_l2 p99: 0.6000000238
best_action_l2 max: 0.6000000238

cross_regret_A p99: 0.0079031941
cross_regret_A max: 0.0116696467
cross_regret_B p99: 0.0059964217
cross_regret_B max: 0.0080760175

diverged >= 0.12: 8
both regrets >= 0.02: 0
```

## Interpretation

The short-sequence lattice improved divergence count relative to M1242:

```text
M1242 first-action diverged rows: 3 / 160
M1244 short-sequence diverged rows: 8 / 120
```

But it still does not create capability-separable source-positive rows:

```text
accepted_separable_pairs: 0
```

The result is not a threshold-near-miss. Even the strongest short-sequence
cross-regrets are well below `0.02`, and no row has both regrets above the
threshold.

The next bottleneck is likely not the action object alone. The broad matched
snapshot window may be selecting states where both hidden conditions are too
recoverable or where the same maneuver is good enough. M1245 should audit
source windows and boundary conditioning before changing simulator fidelity or
training an actor.

## Next

M1245 should audit source-window/boundary conditioning:

```text
Are matched states too easy or too far from a decision boundary?
Should the source constructor target high action-spread / low-margin states?
Should obstacle distance, timing, baseline margin, or margin-spread filters be
added before larger lattices or simulator extension?
```

No training, PPO, promotion, actor-input expansion, private holdout, or
self-identification claim should occur in that audit.
