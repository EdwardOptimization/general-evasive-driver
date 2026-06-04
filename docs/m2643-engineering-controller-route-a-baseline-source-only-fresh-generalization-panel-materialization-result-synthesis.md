# M2643 Engineering Controller Route A Source-Only Fresh Generalization Panel Materialization Result Synthesis

- status: completed
- synthesis decision: `continue_to_source_only_behavior_gap_taxonomy_materialization_preflight`
- manifest: `experiments/manifests/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-synthesis.json`
- parent audit: `docs/m2642-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-audit.md`
- parent summary: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/summary.json`
- parent measured rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_behavior_rows.csv`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-preflight.json`
- next: `m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-preflight`

## Evidence Summary

M2641/M2642 moved Route A beyond static readiness bookkeeping. The accepted
panel contains 160 source-only measured behavior rows and 12800 telemetry rows:

```text
role families: stable_avoidable, stable_aes, drift_required_recovery, unavoidable_mitigation
fresh seeds per role: 4
dynamics axes: fresh_nominal_or_role_default, fresh_fault_delay_noise
subjects: 5
actor contract: P0 human-view 72 observations, action 3
gate matrix: 19/19 pass
actor visibility guards: 19/19 pass
```

Aggregate event pattern from the accepted rows:

```text
stable_avoidable:
  rows: 40
  collisions: 0
  road_departures: 14
  minimum_obstacle_clearance_m: 7.941
  minimum_road_margin_m: -3.790

stable_aes:
  rows: 40
  collisions: 0
  road_departures: 24
  minimum_obstacle_clearance_m: 0.254
  minimum_road_margin_m: -4.353

drift_required_recovery:
  rows: 40
  collisions: 9
  road_departures: 24
  minimum_obstacle_clearance_m: -1.325
  minimum_road_margin_m: -5.382

unavoidable_mitigation:
  rows: 40
  collisions: 40
  road_departures: 8
  minimum_obstacle_clearance_m: -1.561
  minimum_road_margin_m: -2.646
```

The dynamics-axis split does not justify a separate fault-axis conclusion yet:

```text
fresh_nominal_or_role_default:
  rows: 80
  collisions: 24
  road_departures: 34

fresh_fault_delay_noise:
  rows: 80
  collisions: 25
  road_departures: 36
```

The axis is useful as diagnostic coverage, but M2643 does not claim validated
delay/noise physics or high-fidelity robustness.

## Supported Claims

M2643 supports these bounded claims:

```text
M2641 source-only fresh generalization panel was materialized and audited.
The P0 actor/action contract and actor-visibility boundary were preserved.
The panel exposed behavior gaps across role families and subjects.
stable_avoidable and stable_aes rows show no collision in this source-only panel.
drift_required_recovery exposes mixed collision and road-boundary stress.
unavoidable_mitigation remains collision-saturated as expected for mitigation reference rows.
```

## Falsified Or Rejected Claims

M2643 rejects these claims:

```text
M2641/M2642 proves driver performance.
M2641/M2642 ranks controller families or selects a winner.
M2641/M2642 is a promotion gate.
M2641/M2642 is a validation result.
M2641/M2642 is paper-level finite-window-vs-GRU or self-ID evidence.
M2641/M2642 is a current-sim verdict.
M2641/M2642 is a high-fidelity validation result.
M2641 delay/noise metadata proves applied high-fidelity delay/noise physics.
```

## Failure Taxonomy Summary

The accepted rows should be reanalyzed into gap taxonomy rows before repair or
training work:

```text
road_departure_dominant_gap:
  visible in stable_avoidable, stable_aes, and drift_required_recovery rows
  needs role/subject/axis localization before repair design

drift_recovery_mixed_gap:
  drift_required_recovery has 9 collision rows and 24 road-departure rows
  needs separation of collision avoidance versus recovery margin failure

mitigation_collision_saturated_reference:
  unavoidable_mitigation has 40/40 collision rows
  should remain a mitigation diagnostic reference, not a pass/fail denominator

axis_sensitivity_not_yet_decisive:
  nominal and fault/delay/noise axes are close at aggregate level
  source-only fault-axis rows are useful, but not enough for a robust-fault verdict
```

## Public-Gate Overfit Risk

Risk is medium.

The panel uses fresh seeds and adds a stable_avoidable role plus two dynamics
axes, which lowers fixed-public-row overfit risk relative to M2544. However, it
is still source-only, small, and diagnostic. More rows alone would not justify
ranking or promotion; the next useful step is to convert the measured gaps into
a bounded taxonomy that can guide repair decisions without changing claims.

## Next Branch Decision

Continue to:

```text
m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-preflight
```

M2644 should materialize a gap taxonomy from the accepted M2641 rows:

```text
input artifacts:
  M2641 measured_behavior_rows.csv
  M2641 measured_event_rows.csv
  M2641 telemetry_rows.csv
  M2641 gate_matrix.csv
  M2642 audit doc

required outputs:
  role_gap_rows.csv
  subject_gap_rows.csv
  dynamics_axis_gap_rows.csv
  repair_target_admission_rows.csv
  claim_boundary_rows.csv
  gate_matrix.csv
  summary.json
```

M2644 must not rank subjects, select a winner, promote a checkpoint, train,
validate, compute success rates, or claim driver performance. Its only purpose
is to turn accepted source-only diagnostics into a repair-target map or a stop
decision.
