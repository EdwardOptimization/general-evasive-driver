# m1541-paper-route-terminal-boundary-history-positive-source-repair-implementation Research Review

## Summary

- Generated at UTC: 20260529T114822Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: terminal_boundary_source_repair_smoke_complete_null_control_dominated_route_to_audit
- Decision reason: M1541 implements terminal-boundary repair smoke with 35 source specs 11 accepted pairs and 880 replay rows but near-boundary target count is 0 history-positive target sides are 0 and control gap dominates

## Hypothesis

A bounded terminal-boundary repair planner can find or falsify T5/terminal-boundary history-positive intervention rows without changing actor inputs or training.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1540-paper-route-terminal-boundary-history-positive-source-repair-design.md, docs/m1539-paper-route-fresh-ambiguity-history-intervention-repeat-result-audit.md
- parent_config: experiments/manifests/m1540-paper-route-terminal-boundary-history-positive-source-repair-design.json
- parent_objective: implement the bounded terminal-boundary source repair planner designed by M1540
- derived_from: m1540-paper-route-terminal-boundary-history-positive-source-repair-design
- blocked_by: M1539 identifies zero T5/terminal-boundary history-positive target sides
- supersedes: direct materialization of M1538 non-terminal positives
- invalidates: None

## Success Criteria

- terminal-boundary source repair module exists
- focused tests cover repair source selection guardrails and summary schema
- runs/m1541_terminal_boundary_source_repair_smoke/summary.json exists
- candidate materialization training PPO promotion private holdout actor-input changes and training-corpus export remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- repair module or smoke artifacts are missing
- implementation changes actor inputs or uses private holdout
- implementation materializes candidates or starts training/replay/PPO
- implementation claims level3 self-identification

## Evidence Gates

- M1541 must implement bounded terminal-boundary repair without training
- M1541 must preserve P0 actor input contract
- M1541 must report terminal target pair history-positive and control metrics
- M1541 must route to audit before materialization

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m1541-paper-route-terminal-boundary-history-positive-source-repair-implementation
- type: infrastructure
- checkpoint: runs/m1541_terminal_boundary_source_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_source_repair_smoke_complete_null_control_dominated_route_to_audit
- reason: M1541 implements terminal-boundary repair smoke with 35 source specs 11 accepted pairs and 880 replay rows but near-boundary target count is 0 history-positive target sides are 0 and control gap dominates

## Next Blocker

m1542-paper-route-terminal-boundary-source-repair-result-audit
