# M1241 Paper-Route Capability-Separable Source Construction Design

## Summary

M1241 opens the `paper_route_capability_separable_source_construction` branch
after M1240 closed the same-source extreme/fault path.

Decision:

```text
capability_separable_source_construction_design_admit_lattice_smoke
```

The new branch does not ask first whether the current actor reacts to history.
It asks a prerequisite question:

```text
Does the simulator contain matched-current hidden-dynamics cases where the
right first action or short action sequence is genuinely different?
```

No training, PPO, checkpoint repair, promotion, private holdout, profile tuning,
actor-input expansion, or self-identification claim occurs in M1241.

## Motivation

M1236 repaired normal-history viability:

```text
normal_surviving_fraction: 0.7213541667
```

M1238 then tested a stronger sequence intervention:

```text
intervention_rows: 6912
accepted_sequence_rows: 0
sequence_action_critical_rows: 0
```

This suggests the source itself may not be action-separable. Hidden dynamics
randomization does not automatically create cases where a different action is
needed under matched current observations. Before asking whether a human-view
actor can self-identify, the source must prove that self-identification would
matter.

## Core Separability Criterion

For a matched-current pair:

```text
condition A: current state / scene under hidden dynamics A
condition B: matched current state / scene under hidden dynamics B
```

Evaluate a small action lattice or short action-sequence lattice offline in the
simulator:

```text
U = {candidate actions or K-step action sequences}
J_A(u) = terminal risk / margin when candidate u is applied in condition A
J_B(u) = terminal risk / margin when candidate u is applied in condition B
```

Let:

```text
u_A = argmax margin / minimize risk under A
u_B = argmax margin / minimize risk under B
```

The pair is capability-separable only if:

```text
action_l2(u_A, u_B) >= min_best_action_l2
margin_A(u_A) - margin_A(u_B) >= min_cross_regret_margin
margin_B(u_B) - margin_B(u_A) >= min_cross_regret_margin
best candidates are finite and not collision-only artifacts
```

This is a source-validity test, not a deployable controller.

## Actor-Input Guardrail

The offline constructor may use hidden dynamics labels and simulator outcomes as
metadata to build a source corpus.

The deployable actor must not see:

```text
hidden dynamics labels
mu / mass / tire / brake / actuator parameters
oracle best action labels
oracle separability scores
terminal margin / collision / success labels
```

Any later actor test must still use:

```text
P0 human-view/no-oracle observation
finite-window history or recurrent hidden state
steer / throttle / brake output only
```

## Source Artifacts

The constructor should write:

```text
summary.json
scenario_summary.csv
snapshot_candidates.csv
matched_capability_pairs.csv
action_lattice.csv
action_rollouts.csv
accepted_separable_pairs.csv
rejected_pairs.csv
fault_family_pair_summary.csv
model_fidelity_limits.md
```

Each accepted row should include:

```text
pair_id
seed
preferred_fault / wrong_fault
preferred_fault_family / wrong_fault_family
preferred_snapshot_id / wrong_snapshot_id
feature_distance
best_action_A
best_action_B
best_action_l2
margin_A_best_A
margin_A_best_B
margin_B_best_B
margin_B_best_A
cross_regret_A
cross_regret_B
min_cross_regret
source_weight
```

Those labels are for source construction, diagnostics, and future supervised or
teacher targets only. They are not actor inputs.

## First Bounded Implementation

M1242 should implement a small no-training source constructor:

```text
src/autodrift/capability_separable_source_constructor.py
tests/test_capability_separable_source_constructor.py
```

It should reuse existing pieces where possible:

```text
extreme_dynamics_scenario_corpus:
  fault config loading, fault application, snapshot collection, cross-fault
  matching, model fidelity notes

terminal_margin_recovery_anchor:
  action candidate representation and first-action override rollout pattern
```

M1242 should run only a bounded smoke:

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

The first smoke should use one shared first-action candidate set per matched
pair:

```text
base_action_A = deterministic policy action on snapshot A
base_action_B = deterministic policy action on snapshot B
shared_base_action = 0.5 * (base_action_A + base_action_B)
candidates = clipped(shared_base_action + action_delta_lattice)
```

The same `candidates` are evaluated in both hidden-dynamics conditions, and
each rollout applies the candidate first action before continuing with the
unchanged policy. This avoids declaring action separability from two different
candidate sets and keeps the test bounded while checking whether local action
choices have different value under different hidden dynamics.

## M1242 Smoke Pass Criteria

M1242 should pass as infrastructure if:

```text
summary.json exists
matched_pair_count > 0
action_rollouts > 0
matched fault-family pairs >= 6
matched seeds >= 6
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
labels_enter_actor_input == false
model_fidelity_limits.md exists
```

Accepted separable pairs are diagnostic at M1242 scale. If none appear, the
branch should audit the negative rather than train.

## Source-Positive Gate For Later

A later non-smoke source-positive gate should require:

```text
accepted_separable_pairs >= 30
unique accepted fault-family pairs >= 6
unique accepted seeds >= 12
max accepted seed dominance <= 0.25
max accepted fault-family-pair dominance <= 0.35
median min_cross_regret >= 0.02
median best_action_l2 >= 0.12
```

Only after that should the project ask whether L0/L1/L2/L3 actors can recover
the hidden-dynamics action choice from deployable history.

## Follow-Up Rules

If M1242 finds separable pairs:

```text
audit source diversity and construct a compact public source corpus
```

If M1242 finds no separable pairs:

```text
audit whether the action lattice is too local, the horizon too short, or the
current single-track proxy dynamics cannot create separable cases
```

If best actions differ but cross-regret is near zero:

```text
record action degeneracy and do not train
```

If separability requires true per-wheel or asymmetric faults:

```text
route to simulator extension / high-fidelity vehicle dynamics roadmap
```

## Decision

```text
capability_separable_source_construction_design_admit_lattice_smoke
```

M1242 is admitted as a bounded no-training action-lattice source-construction
smoke.
