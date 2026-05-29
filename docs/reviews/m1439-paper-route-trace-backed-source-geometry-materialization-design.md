# m1439-paper-route-trace-backed-source-geometry-materialization-design Research Review

## Summary

- Generated at UTC: 20260529T032735Z
- Type: gate
- Gate tier: process
- Promotion decision: trace_backed_source_geometry_materialization_design_admit_implementation
- Decision reason: M1439 designs trace-backed emergency-obstacle source geometry materialization and blocks direct source smoke until source-step action-divergence enrichment is explicit

## Hypothesis

Trace-backed materialization can generate source_body_x/source_body_y/source_half_width rows at earlier source steps for the M1438 row-level miner.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1438-paper-route-forward-geometry-source-miner-implementation.md, src/autodrift/forward_geometry_source_miner.py
- parent_config: experiments/manifests/m1438-paper-route-forward-geometry-source-miner-implementation.json
- parent_objective: design trace-backed source geometry materialization before public source smoke
- derived_from: m1438-paper-route-forward-geometry-source-miner-implementation
- blocked_by: M1438 implements row-level source-geometry mining but not trace-backed materialization
- supersedes: running source miner without source_body_x/source_body_y/source_half_width materialization
- invalidates: None

## Success Criteria

- docs/m1439-paper-route-trace-backed-source-geometry-materialization-design.md exists
- design specifies trace reconstruction inputs and source step offsets
- design specifies source geometry output schema
- design chooses a non-training next route without source mining preflight replay PPO promotion private holdout corpus export or actor-input changes

## Failure Criteria

- design document is missing
- design fabricates source geometry fields
- design routes directly to source smoke replay training PPO promotion private holdout corpus export or claim expansion
- design ignores M1438 row-level input schema

## Evidence Gates

- M1439 must design trace-backed source geometry materialization before implementation or run
- M1439 must specify source step offsets and trace reconstruction inputs
- M1439 must not run source mining source preflight replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source mining
- do not run source preflight
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not fabricate source geometry fields

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1439-paper-route-trace-backed-source-geometry-materialization-design
- type: gate
- checkpoint: docs/m1439-paper-route-trace-backed-source-geometry-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trace_backed_source_geometry_materialization_design_admit_implementation
- reason: M1439 designs trace-backed emergency-obstacle source geometry materialization and blocks direct source smoke until source-step action-divergence enrichment is explicit

## Next Blocker

m1440-paper-route-trace-backed-source-geometry-materialization-implementation
