# m1513-paper-route-decisive-history-source-retarget-design Research Review

## Summary

- Generated at UTC: 20260529T091212Z
- Type: gate
- Gate tier: process
- Promotion decision: decisive_history_source_retarget_design_admit_implementation
- Decision reason: M1513 designs bounded public retarget modes and caps to reduce margins and improve label diversity while blocking candidate materialization and training

## Hypothesis

A bounded retarget plan can turn the M1511 source families from safe trace plumbing into near-boundary public source traces suitable for later measured interventions.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1512-paper-route-decisive-history-bounded-runner-result-audit.md, runs/m1511_decisive_history_bounded_runner_smoke/source_trace_rows.csv, runs/m1511_decisive_history_bounded_runner_smoke/source_snapshot_rows.csv
- parent_config: experiments/manifests/m1512-paper-route-decisive-history-bounded-runner-result-audit.json
- parent_objective: design bounded public source retargeting after M1512 found traces too safe for candidate materialization
- derived_from: m1512-paper-route-decisive-history-bounded-runner-result-audit
- blocked_by: current M1511 traces are too high-margin and mostly aeb_feasible for decisive-history materialization
- supersedes: candidate materialization directly from M1511 traces
- invalidates: None

## Success Criteria

- docs/m1513-paper-route-decisive-history-source-retarget-design.md exists
- retarget axes for obstacle distance width lateral offset reveal timing speed friction and capability ranges are explicit
- design names public caps and acceptance metrics for a small retarget smoke
- design keeps candidate materialization training PPO promotion private holdout actor-input changes and corpus export blocked
- design routes to retarget implementation or records a blocker

## Failure Criteria

- design document is missing
- retarget axes or caps are ambiguous
- design uses private holdout or unbounded random search
- design materializes candidates or starts training PPO promotion corpus export or actor-input changes

## Evidence Gates

- M1513 must design a bounded public retarget route for near-boundary source traces
- M1513 must identify retarget axes and safety caps
- M1513 must keep trace collection separate from candidate materialization
- M1513 must not train run PPO promote use private holdout alter actor inputs or export corpus
- M1513 must not claim self-identification from retarget design

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not materialize candidates
- do not broaden into unbounded random search
- do not claim self-identification from source retargeting

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1513-paper-route-decisive-history-source-retarget-design
- type: gate
- checkpoint: docs/m1513-paper-route-decisive-history-source-retarget-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_source_retarget_design_admit_implementation
- reason: M1513 designs bounded public retarget modes and caps to reduce margins and improve label diversity while blocking candidate materialization and training

## Next Blocker

m1514-paper-route-decisive-history-source-retarget-implementation
