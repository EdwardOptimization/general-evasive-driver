# M1234 Paper-Route Extreme Fault Source Smoke Audit

## Summary

M1234 audits M1233 before any larger source wave, objective, training, or PPO.

Decision:

```text
extreme_fault_source_smoke_audit_route_to_timing_repair_design
```

M1233 is a valid infrastructure smoke, but it is not a useful cross-fault
wrong-history proof source in its current form.

Key facts:

```text
scenario_count: 832
snapshot_count: 3211
matched_pair_count: 768
accepted_rows: 0
wrong_history_action_critical_rows: 0
reset_only_rows: 58
reset_history_action_critical_rows: 58
normal_failed_rejected: 636
history_insensitive_rejected: 74
```

No training, PPO, checkpoint repair, promotion, private holdout, profile tuning,
actor-input expansion, or self-identification claim occurs in M1234.

## What M1233 Supports

M1233 supports these infrastructure and diagnostic claims:

```text
1. The current paper-route L3 checkpoint can run through the existing
   capability-step/fault corpus harness.

2. The harness produces the expected artifact set:
   summary, scenario, snapshot, matched-pair, rollout, reset-only/rejected,
   source-summary, and fidelity-limit files.

3. The actor checksum remains stable:
   actor_parameters_changed: false.

4. Hidden fault labels remain scenario/logging metadata and are not actor inputs.

5. Reset-hidden sensitivity exists under some fault scenarios:
   reset_only_rows: 58.
```

This is enough to keep the branch alive. It is not enough to train or claim
self-identification.

## What M1233 Falsifies Or Blocks

M1233 blocks these claims:

```text
source-positive cross-fault wrong-history evidence
source-diverse wrong-history causal-history proof
training readiness
PPO readiness
recurrent-belief or online self-identification
paper-level evidence
true per-wheel/asymmetric fault physics
```

The strongest negative is direct:

```text
accepted_rows: 0
wrong_history_action_critical_rows: 0
wrong_history_source_positive: false
```

Cross-fault wrong histories did not damage behavior under the current smoke.

## Source-Shape Diagnosis

The dominant failure is normal-branch viability:

```text
rejected_rows: 710
normal_failed_rejected: 636
history_insensitive_rejected: 74
```

Most candidate pairs are therefore not usable proof rows. If the normal-history
branch already fails, wrong-history degradation cannot be interpreted as a
causal history effect.

Reset-only rows are broader by fault-family pair but too narrow by seed:

```text
reset_only_rows: 58
unique reset-only fault-family pairs: 13
unique reset-only preferred families: 9
unique reset-only wrong families: 8
unique reset-only severity pairs: 5
unique reset-only seeds: 2
```

This shape says the run has recurrent-state disruption sensitivity, but the
evidence is not source-diverse enough to become a corpus.

Largest reset-only groups:

```text
combined_fault -> front_lateral_authority_drop: 9
global_mu_drop -> front_lateral_authority_drop: 8
brake_authority_drop -> global_mu_drop: 8
rear_lateral_authority_drop -> drive_authority_drop: 5
front_lateral_authority_drop -> global_mu_drop: 5
drive_authority_drop -> rear_lateral_authority_drop: 5
delay_noise_fault -> steering_fault: 5
```

## Relation To Earlier Capability-Step Evidence

The result is consistent with the older capability-step branch:

```text
M990: small smoke produced sparse wrong-history positives and many reset-only rows.
M991: larger wave produced zero accepted wrong-history rows and many reset-only rows.
M994-M997: sequence-level temporal disruptions, not simple cross-fault hidden
           swaps, produced the useful temporal-history corpus.
```

M1233 repeats the important lesson under the current paper-route L3 checkpoint:

```text
single cross-fault hidden-state swap is not currently a reliable source-positive
construction.
```

But M1233 also adds a practical blocker for this checkpoint/config pair:

```text
normal branches fail too often under the current timing/horizon.
```

## Rejected Next Steps

Do not:

- train from reset-only rows;
- count reset-only rows as self-identification proof;
- scale the exact same M990 config before repairing normal-branch viability;
- lower thresholds until accepted rows appear;
- add fault labels or hidden parameters to actor inputs;
- claim per-wheel, split-mu, stuck-caliper, or half-shaft physics from the
  current single-track model.

## Selected Next Route

M1235 should design a timing/horizon/normal-success repair before any larger
source wave.

The repair design should target:

```text
1. reduce normal_failed_rejected before trying to increase accepted rows;
2. preserve hidden-fault metadata as non-actor logging only;
3. test shorter continuations and safer source windows;
4. record normal-survival diversity by fault family, seed, step, and target;
5. only then rerun cross-fault or sequence interventions.
```

Candidate levers:

```text
max_continuation_steps
min_step and snapshot_stride
activation_step phase
obstacle longitudinal window
min_normal_margin
fault severity subset
normal-survival prefilter
```

The first repaired run should remain no-training and bounded. It should pass or
fail on normal-survival/source-shape gates before any self-ID or PPO claim.

## Decision

```text
extreme_fault_source_smoke_audit_route_to_timing_repair_design
```

The branch remains worth pursuing, but the next milestone should repair source
timing and normal-history survivability rather than scaling the current smoke or
training from reset-only rows.
