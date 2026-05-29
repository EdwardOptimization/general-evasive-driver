# m1540-paper-route-terminal-boundary-history-positive-source-repair-design Research Review

## Summary

- Generated at UTC: 20260529T113358Z
- Type: gate
- Gate tier: process
- Promotion decision: terminal_boundary_history_positive_source_repair_design_admit_bounded_planner
- Decision reason: M1540 designs bounded terminal-boundary repair planner focused on T5 source families near-boundary margins anchor sweep and history-positive gates

## Hypothesis

A targeted terminal-boundary source repair design can address the M1538 gap where T5 pairs were accepted but history-positive target sides remained zero.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1539-paper-route-fresh-ambiguity-history-intervention-repeat-result-audit.md, runs/m1538_fresh_ambiguity_history_intervention_repeat/summary.json
- parent_config: experiments/manifests/m1539-paper-route-fresh-ambiguity-history-intervention-repeat-result-audit.json
- parent_objective: design terminal-boundary source repair after M1539 audits T5 history-positive absence
- derived_from: m1539-paper-route-fresh-ambiguity-history-intervention-repeat-result-audit
- blocked_by: M1538 is source-expanded positive overall but has zero T5 or terminal-boundary history-positive target sides
- supersedes: direct materialization of M1538 non-terminal positives
- invalidates: None

## Success Criteria

- docs/m1540-paper-route-terminal-boundary-history-positive-source-repair-design.md exists
- design targets terminal-boundary source families and retarget knobs
- design defines history-positive T5 pass thresholds and stop conditions
- candidate materialization training PPO promotion private holdout actor-input changes and training-corpus export remain blocked

## Failure Criteria

- design document is missing
- design treats M1538 non-terminal positives as sufficient
- design weakens the self-ID evidence standard
- design routes directly to training promotion private holdout or materialization

## Evidence Gates

- M1540 must design terminal-boundary source or pair repair before new implementation
- M1540 must preserve the P0 actor input contract
- M1540 must define T5/terminal-boundary pass and fail thresholds
- M1540 must not train run PPO promote use private holdout or materialize candidates

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

- none

## Scoreboard

- milestone: m1540-paper-route-terminal-boundary-history-positive-source-repair-design
- type: gate
- checkpoint: docs/m1540-paper-route-terminal-boundary-history-positive-source-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_history_positive_source_repair_design_admit_bounded_planner
- reason: M1540 designs bounded terminal-boundary repair planner focused on T5 source families near-boundary margins anchor sweep and history-positive gates

## Next Blocker

m1541-paper-route-terminal-boundary-history-positive-source-repair-implementation
