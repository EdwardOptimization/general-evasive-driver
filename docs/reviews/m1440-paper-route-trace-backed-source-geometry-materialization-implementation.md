# m1440-paper-route-trace-backed-source-geometry-materialization-implementation Research Review

## Summary

- Generated at UTC: 20260529T033435Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: trace_backed_source_geometry_materializer_implemented_route_to_action_divergence_enrichment_design
- Decision reason: M1440 implements trace-backed emergency-obstacle source geometry materializer and focused tests while blocking public run replay training promotion and actor-input changes

## Hypothesis

Trace-backed source geometry materialization can be implemented to compute emergency-obstacle source_body_x/source_body_y/source_half_width rows at earlier source steps without running public source mining.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1439-paper-route-trace-backed-source-geometry-materialization-design.md, src/autodrift/forward_geometry_source_miner.py
- parent_config: experiments/manifests/m1439-paper-route-trace-backed-source-geometry-materialization-design.json
- parent_objective: implement trace-backed source geometry materialization without running it
- derived_from: m1439-paper-route-trace-backed-source-geometry-materialization-design
- blocked_by: M1439 admits implementation only; no source materialization run, source smoke, preflight, replay, or training is admitted yet
- supersedes: fabricating source_body_x/source_body_y/source_half_width from stale reveal-step CSV metrics
- invalidates: None

## Success Criteria

- implementation exists
- focused tests cover trace-backed emergency-obstacle geometry extraction
- focused tests cover active-obstacle diagnostic-only handling
- focused tests cover source row schema validation
- docs/m1440-paper-route-trace-backed-source-geometry-materialization-implementation.md exists
- no source materialization run source mining source preflight replay training PPO promotion private holdout corpus export or actor-input change occurs

## Failure Criteria

- implementation is missing
- tests are missing
- implementation fabricates source geometry fields
- implementation treats active-obstacle geometry as canonical selector geometry
- implementation runs source materialization or replay
- implementation changes actor inputs

## Evidence Gates

- M1440 must implement trace-backed source geometry materialization without running it on public data
- M1440 must include focused tests for emergency-obstacle geometry extraction and schema validation
- M1440 must not run source materialization source mining source preflight replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source materialization on public data
- do not run source mining
- do not run source preflight
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not use active-obstacle geometry as the canonical selector geometry
- do not reuse M1425 pressure rows as the new source pool

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1440-paper-route-trace-backed-source-geometry-materialization-implementation
- type: infrastructure
- checkpoint: docs/m1440-paper-route-trace-backed-source-geometry-materialization-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trace_backed_source_geometry_materializer_implemented_route_to_action_divergence_enrichment_design
- reason: M1440 implements trace-backed emergency-obstacle source geometry materializer and focused tests while blocking public run replay training promotion and actor-input changes

## Next Blocker

m1441-paper-route-geometry-first-action-divergence-enrichment-design
