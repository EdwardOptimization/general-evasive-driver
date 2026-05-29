# m1437-paper-route-forward-geometry-source-mining-design Research Review

## Summary

- Generated at UTC: 20260529T031244Z
- Type: gate
- Gate tier: process
- Promotion decision: forward_geometry_source_mining_design_admit_implementation
- Decision reason: M1437 designs geometry-first earlier-source mining with forward unclipped gates and admits implementation with focused tests only

## Hypothesis

A new source-mining design can sample earlier or different snapshots so action-divergent rows satisfy forward unclipped geometry before replay.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1435_geometry_aware_preflight_smoke/summary.json, docs/m1436-paper-route-geometry-preflight-result-audit.md
- parent_config: experiments/manifests/m1436-paper-route-geometry-preflight-result-audit.json
- parent_objective: design source mining that produces forward unclipped geometry before replay
- derived_from: m1436-paper-route-geometry-preflight-result-audit
- blocked_by: M1435 found zero geometry-pass rows across all M1425 pressure rows
- supersedes: lowering geometry gates, replaying M1425 pressure rows, training from geometry-failed rows
- invalidates: None

## Success Criteria

- docs/m1437-paper-route-forward-geometry-source-mining-design.md exists
- design specifies source_body_x and raw_relocated_body_x gates before action divergence
- design specifies earlier reveal or source timing changes
- design specifies seed capability reveal-bucket and variant diversity gates
- design chooses a non-training next route without source mining preflight replay PPO promotion private holdout corpus export or actor-input changes

## Failure Criteria

- design document is missing
- design lowers M1435 geometry gates
- design routes directly to replay training PPO promotion private holdout corpus export or claim expansion
- design does not address source_body_x timing

## Evidence Gates

- M1437 must design forward geometry source mining before implementation or run
- M1437 must pre-register source geometry before action divergence or replay
- M1437 must not lower M1435 geometry gates
- M1437 must not run source mining replay train PPO promote use private holdout export corpus or change actor inputs

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
- do not lower source_body_x or clipping gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1437-paper-route-forward-geometry-source-mining-design
- type: gate
- checkpoint: docs/m1437-paper-route-forward-geometry-source-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: forward_geometry_source_mining_design_admit_implementation
- reason: M1437 designs geometry-first earlier-source mining with forward unclipped gates and admits implementation with focused tests only

## Next Blocker

m1438-paper-route-forward-geometry-source-miner-implementation
