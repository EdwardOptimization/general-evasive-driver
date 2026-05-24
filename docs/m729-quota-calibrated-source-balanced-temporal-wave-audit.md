# M729 Quota-Calibrated Source-Balanced Temporal Wave Audit

## Purpose

M729 audits the M728 quota-calibrated temporal wave before another experiment.

The question is:

```text
After source balancing is fixed, should the next step be another quota/scenario
wave, source-balanced boundary mining, sequence-level interventions, or
dynamics fidelity?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M728 removes the M725 source-balance blocker.

```text
proposal_count: 69591
selected_pair_count: 3951
unique_selected_seeds: 494
unique_preferred_fault_families: 9
unique_fault_family_pairs: 33
max_seed_dominance: 0.002025
max_preferred_family_dominance: 0.161984
sentinel_false_positive_rate: 0.0
```

Compared with M725:

```text
M725 selected_pair_count: 2048
M728 selected_pair_count: 3951

M725 unique_selected_seeds: 256
M728 unique_selected_seeds: 494

M725 unique_preferred_fault_families: 7
M728 unique_preferred_fault_families: 9

M725 max_preferred_family_dominance: 0.3125
M728 max_preferred_family_dominance: 0.161984
```

M728 still misses exact `4096` selected pairs by `145`, but this is no longer a
source-balance blocker:

```text
selected_pair_count: 3951
source-balance thresholds: pass
result_class: source_balanced_temporal_action_only
```

## Action vs Outcome Evidence

M728 has strong action evidence:

```text
temporal_action_critical_rows: 2613
unique_temporal_action_seeds: 351
dominant variant: mismatch_zero_command_history
```

Dominant action variant:

```text
mismatch_zero_command_history:
  rows: 3951
  action-critical rows: 2609
  first action distance mean: 0.021337
  first action distance max: 0.035347
  margin gap max: 0.006935
```

But M728 has weak outcome evidence:

```text
temporal_outcome_critical_rows: 1
unique_temporal_outcome_seeds: 1
registered outcome gate: >= 20
```

The singleton outcome row:

```text
seed: 72339
variant: mismatch_zero_command_history
fault_family_pair: front_lateral_authority_drop->steering_fault
normal_success: true
variant_success: false
normal_margin: 0.001388798
variant_margin: -0.000232400
first_action_distance_from_normal: 0.023885543
```

This row should be preserved as a diagnostic seed, but it is not enough for a
source-positive corpus.

## Supported Claims

M729 supports:

```text
1. The source coverage concern was real and has now been substantially fixed.

2. The actor uses command-history information at the action level across a
   broad source-balanced scenario set.

3. The useful signal is still mainly in command-history mismatch, not
   cross-fault hidden replacement.

4. M728 provides a much stronger source pool for boundary mining than M722:
   M722 source rows came from 4 seeds; M728 action rows come from 351 seeds.

5. No actor/input contract violation occurred.
```

## Falsified Claims

M729 falsifies:

```text
1. The absence of outcome evidence in M725 was only the M725 quota artifact.

2. Another quota-only rerun is the highest-leverage next step.

3. M728 justifies source export, actor update, PPO, or promotion.

4. The singleton outcome row is enough to claim closed-loop self-ID proof.
```

M729 does not falsify:

```text
1. Source-balanced boundary mining may convert action rows into outcome rows.

2. Sequence-level interventions may be needed if boundary mining remains
   action-only.

3. More physical asymmetric/yaw-disturbance dynamics may be needed if current
   proxy faults still fail to produce outcome-sensitive surfaces.
```

## Failure Taxonomy Summary

Primary:

```text
metric_artifact
```

Reason:

```text
M728 has strong action-critical evidence but only one outcome-critical row.
Action criticality remains diagnostic and must not be treated as closed-loop
self-identification proof.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
The current source-balanced wave did not sample enough near-boundary terminal
conditions to generate an outcome-positive corpus.
```

Not classified as:

```text
contract_violation:
  actor input contract was unchanged.

training_instability:
  no training occurred.

proof_washout:
  actor parameters were unchanged.
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate to high if we continue quota-only
reruns:

```text
the project could keep optimizing selected-source distributions while the
scientific blocker has moved to action-to-outcome conversion.
```

The guardrail is:

```text
do not run another quota-only wave unless M730/M731 identifies a specific
remaining source-balance failure.
```

The next branch must be allowed to fail if action rows still do not become
outcome rows under boundary perturbations.

## Next Branch Decision

Decision:

```text
promote_to_next_branch: source_balanced_boundary_outcome_mining
```

Rationale:

```text
M728 gives a broad action-critical source pool.
The current blocker is not source coverage; it is action-to-outcome conversion.
Boundary mining is the most direct next falsification step before changing the
intervention type or simulator fidelity.
```

M730 should design a source-balanced boundary miner that starts from M728
action-critical rows and searches local obstacle timing, lateral offset,
footprint, road slack, and fault timing around rows where:

```text
normal history remains viable;
mismatch_zero_command_history keeps action distance >= 0.015;
terminal clearance is near the success/failure boundary;
sentinel false positives stay near zero.
```

M730 should not:

```text
train an actor;
run PPO;
promote a checkpoint;
export action-only rows as outcome-positive proof.
```

If M731 boundary mining remains source-balanced but outcome-negative, then the
next audit should consider:

```text
1. sequence-level command-response interventions;
2. explicit asymmetric/yaw-disturbance fault dynamics;
3. four-wheel or higher-fidelity vehicle dynamics.
```
