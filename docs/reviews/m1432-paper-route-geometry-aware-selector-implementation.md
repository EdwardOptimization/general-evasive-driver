# m1432-paper-route-geometry-aware-selector-implementation Research Review

## Summary

- Generated at UTC: 20260529T025416Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: geometry_aware_selector_implemented_route_to_branch_synthesis
- Decision reason: M1432 implements geometry-aware preflight selector and focused tests without replay training PPO promotion corpus export or actor-input changes

## Hypothesis

The bounded relocation replay tool can be extended with a no-training geometry preflight selector that filters behind-vehicle and clipped rows before actual replay.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv, docs/m1431-paper-route-geometry-aware-replay-selector-design.md
- parent_config: experiments/manifests/m1431-paper-route-geometry-aware-replay-selector-design.json
- parent_objective: implement a geometry-aware source preflight selector before bounded relocation replay
- derived_from: m1431-paper-route-geometry-aware-replay-selector-design
- blocked_by: M1431 admits implementation only; no replay run is admitted yet
- supersedes: M1429 selector without source geometry preflight
- invalidates: None

## Success Criteria

- implementation exposes geometry preflight filtering
- focused tests cover source_body_x rejection
- focused tests cover relocation clipping rejection
- focused tests cover source and variant diversity accounting
- docs/m1432-paper-route-geometry-aware-selector-implementation.md exists
- no replay training PPO promotion private holdout corpus export or actor-input change occurs

## Failure Criteria

- implementation is missing
- tests are missing
- implementation cannot identify clipped rows
- implementation runs replay or training
- implementation changes actor inputs
- implementation lowers pre-registered geometry gates

## Evidence Gates

- M1432 must implement geometry preflight without running replay
- M1432 must reject behind-vehicle and clipped relocation candidates
- M1432 must produce focused tests for geometry filters and diversity accounting
- M1432 must not train run PPO run closed-loop replay promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export a training corpus
- do not lower geometry gates after implementation
- do not count preflight rows as actual replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1432-paper-route-geometry-aware-selector-implementation
- type: infrastructure
- checkpoint: docs/m1432-paper-route-geometry-aware-selector-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: geometry_aware_selector_implemented_route_to_branch_synthesis
- reason: M1432 implements geometry-aware preflight selector and focused tests without replay training PPO promotion corpus export or actor-input changes

## Next Blocker

m1433-paper-route-action-divergent-geometry-branch-synthesis
