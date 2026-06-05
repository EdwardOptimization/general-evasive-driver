# M2798 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Corrective Training Design

## Metadata

- status: completed
- decision: `admit_source_only_belief_stress_clearance_localized_corrective_training_preflight`
- manifest: `experiments/manifests/m2798-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-design.json`
- design doc: `docs/m2798-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-design.md`
- parent audit: `docs/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.md`
- parent atlas summary: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/summary.json`
- parent atlas aggregate rows: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/clearance_regression_aggregate_rows.csv`
- follow-up manifest: `experiments/manifests/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight.json`
- next: `m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight`

## Design Decision

M2798 admits one bounded corrective training/update preflight. The design uses
M2796/M2797 only as evaluator-side attribution evidence. It does not train,
execute rollout, validate, rank, promote, select a winner, compute a
success-rate verdict, or claim driver performance.

The design target is narrow:

```text
primary correction:
  protect obstacle clearance on drift_required_recovery and stable_aes rows

mandatory retention:
  preserve stable_avoidable behavior, where M2796 had only 1/48 negative
  clearance rows

forbidden optimization:
  do not improve road-margin, speed, yaw-rate, or action-delta metrics by
  making obstacle clearance worse
```

## Parent Evidence Used

M2797 accepts M2796 as complete and claim-safe. The usable design facts are:

```text
M2796_clearance_regression_rows: 144
M2796_aggregate_rows: 237
candidate_minus_source_clearance: 30 positive, 42 negative
candidate_minus_base_clearance: 29 positive, 43 negative
drift_required_recovery: 48/48 negative
stable_aes: 36/48 negative
stable_avoidable: 1/48 negative
```

The atlas also shows road-margin and final-speed positives in the same families
where clearance is negative. M2798 therefore treats road-margin and speed as
subordinate side-effect diagnostics. They are not promoted to objectives unless
clearance retention passes first.

## Actor Contract

M2799 must preserve the deployed actor interface:

```text
observation shape: 72
action shape: 3
hidden/oracle actor input: false
actor-visible role labels: false
actor-visible dynamics labels: false
actor-visible stress labels: false
actor-visible seed labels: false
actor-visible atlas/clearance labels: false
actor-visible outcome/progress/route/verdict labels: false
```

Role family, dynamics axis, stress family, seed index, delta family, clearance
sign, and aggregate attribution are allowed only as evaluator-side curriculum,
objective-weight, and gate metadata. They must not be appended to observations,
encoded as mode bits, or exposed through any hidden controller switch.

## Training Recipe

M2799 should start from the M2791 guardrailed candidate checkpoint and keep the
M2655 source and M2782 base candidate as references:

```text
source reference:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt

base candidate reference:
  runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt

training start checkpoint:
  runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt
```

M2799 may write one new candidate checkpoint, but it must not promote it. The
update is bounded:

```text
max_updates: 1
target_training_seeds_per_bucket: 4
proof_seeds_per_bucket: 2
stable_avoidable_retention_seed_count: 4
behavior_retention_seed_count: 4
rollback_on_guard_failure: true
checkpoint_overwrite_allowed: false
promotion_allowed: false
```

The objective rows should be built from M2796 atlas aggregates:

```text
target families:
  drift_required_recovery
  stable_aes

retention family:
  stable_avoidable

target bucket admission:
  admit every drift_required_recovery bucket because all are 8/8 negative
  admit stable_aes buckets with negative_clearance_rate >= 0.625
  include both dynamics axes
  include all three stress families

ordinary denominator:
  ordinary target and retention rows only
  mitigation reference rows excluded
```

Objective priority:

```text
1. obstacle-clearance non-regression against both source and base reference
2. stable_avoidable retention against M2793/M2796 baseline behavior
3. throttle/brake conflict remains zero
4. action delta remains bounded
5. road-margin, speed, and yaw-rate are diagnostic side effects only
```

## Required Gates For M2799

M2799 must write separate gate rows:

```text
proof gates:
  source/base/start checkpoint lineage
  target objective row completeness
  no actor input or action contract change
  no hidden/oracle actor input
  finite observation/action rows
  mitigation reference rows excluded from ordinary denominators

generalization gates:
  fresh proof seed indices outside the M2793 seed surface when execution rows
  are produced
  coverage of drift_required_recovery and stable_aes target buckets
  coverage of stable_avoidable retention rows

behavior-retention gates:
  stable_avoidable clearance non-regression
  throttle/brake conflict no worse
  bounded mean action delta
  obstacle clearance remains hard before road-margin or speed

promotion guards:
  no checkpoint promotion
  no ranking
  no winner selection
  no success-rate verdict
```

If any behavior-retention or actor-contract gate fails, M2799 must preserve the
failure, write rollback status, and route to result audit. It must not weaken
the gate and rerun inside the same milestone.

## Required Artifacts For M2799

M2799 should write:

```text
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/summary.json
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/training_objective_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/training_run_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/proof_probe_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/proof_gate_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/generalization_gate_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/behavior_retention_gate_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/promotion_guard_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/actor_contract_guard_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/mitigation_reference_guard_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/claim_boundary_rows.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/gate_matrix.csv
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/run_state.json
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/checkpoints/m2799_clearance_localized_corrective_candidate.pt
runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/checkpoint_manifest.json
docs/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight.md
experiments/manifests/m2800-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-result-audit.json
```

## Claim Boundary

M2798 supports only the claim that a bounded corrective training design is
admitted. It rejects:

```text
training result
repair success
driver performance
validation readiness
validation result
checkpoint ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```

## Next

Route to M2799 bounded corrective training preflight. M2799 must execute exactly
the bounded preflight described above or fail closed and route to audit.
