# M1242 Paper-Route Capability-Separable Source Constructor Smoke

## Summary

M1242 implements and runs a bounded no-training offline source constructor for
matched-current hidden-dynamics action separability.

Decision:

```text
capability_separable_constructor_smoke_infrastructure_pass_low_regret_route_to_audit
```

The infrastructure passed. The source-positive test did not pass:

```text
result_class: action_divergent_low_regret
accepted_separable_pairs: 0
```

This is not an actor failure and not a self-identification result. M1242 only
asks whether the current source plus local first-action lattice contains cases
where different hidden dynamics require different first actions.

## Implementation

Added:

```text
src/autodrift/capability_separable_source_constructor.py
tests/test_capability_separable_source_constructor.py
```

The constructor:

1. loads the existing M1236 extreme/fault source config;
2. collects no-training hidden-dynamics snapshots with the frozen L3 checkpoint;
3. matches current ego/scene states across hidden fault families;
4. builds one shared clipped first-action lattice per matched pair;
5. evaluates the same candidate actions under both hidden-dynamics conditions;
6. accepts a pair only if best actions diverge and cross-regret is meaningful.

The shared candidate set is:

```text
base_action_A = deterministic policy action on condition A
base_action_B = deterministic policy action on condition B
shared_base_action = 0.5 * (base_action_A + base_action_B)
candidates = clipped(shared_base_action + delta_lattice)
```

This keeps labels and oracle outcomes out of actor inputs. Hidden dynamics and
best-action labels are source metadata only.

## Sampler Repair During M1242

The first smoke produced matched pairs and rollouts, but source selection was
dominated by early seeds:

```text
unique_matched_seeds: 3
```

M1242 added a per-seed cap.

The second smoke repaired seed diversity but remained family-pair dominated:

```text
unique_matched_seeds: 20
unique_matched_fault_family_pairs: 3
```

M1242 added a per-fault-family-pair cap.

The final smoke satisfies the infrastructure diversity gates.

## Final Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 124200 \
  --seed-count 24 \
  --max-pairs 160 \
  --max-pairs-per-seed 8 \
  --max-pairs-per-family-pair 24 \
  --max-continuation-steps 18 \
  --steer-deltas=-0.30,-0.15,0,0.15,0.30 \
  --throttle-deltas=-0.20,0,0.20 \
  --brake-deltas=-0.30,-0.15,0,0.15,0.30 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1242_capability_separable_source_constructor_smoke
```

## Final Result

Artifact:

```text
runs/m1242_capability_separable_source_constructor_smoke/summary.json
```

Key metrics:

```text
candidate_pair_count: 1356
matched_pair_count: 160
action_lattice_rows: 12000
action_rollouts: 24000
accepted_separable_pairs: 0
best_actions_diverged_pairs: 3
low_regret_pairs: 160
unique_matched_fault_family_pairs: 10
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

The best-action divergence rows exist but are not strong enough:

```text
max observed best_action_l2: 0.7211102843
largest observed cross_regret_A: 0.0148353594
largest observed paired cross_regret_B in that row: 0.0000558759
```

The median row in each family pair has zero action divergence and zero
cross-regret.

## Interpretation

M1242 proves that the new constructor and artifact path are usable:

```text
matched pairs exist
action rollouts exist
source diversity is no longer seed-collapsed or family-pair-collapsed
the frozen actor/checkpoint is not mutated
no labels enter the deployable actor
```

It does not prove capability-separable source availability:

```text
accepted_separable_pairs: 0
```

The current local first-action lattice mostly finds either the same best action
under both hidden conditions or action differences with negligible cross-regret.
That means the current branch should audit the source/lattice/horizon before
any actor history training or self-ID claim.

## Next

M1243 should audit why M1242 is `action_divergent_low_regret`:

```text
local first-action lattice may be too local
18-step horizon may be too short
policy continuation after the first action may wash out action differences
matched current windows may be too easy / too late / too similar
current single-track proxy faults may not create separable current-state cases
short sequence lattices or source task redesign may be needed
```

No training, PPO, promotion, actor-input expansion, or private holdout should
start before that audit.
