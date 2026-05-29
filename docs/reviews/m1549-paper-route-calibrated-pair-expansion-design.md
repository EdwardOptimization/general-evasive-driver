# m1549-paper-route-calibrated-pair-expansion-design Research Review

## Summary

- Generated at UTC: 20260529T122714Z
- Type: gate
- Gate tier: process
- Promotion decision: calibrated_pair_expansion_design_admit_bounded_planner
- Decision reason: M1549 designs pairability-first calibrated terminal-boundary source expansion with accepted_pair_count >= 8 accepted_source_family_edge_count >= 5 and no interventions

## Hypothesis

A pair-expansion design can address the M1547 bottleneck by making calibrated matched-pair diversity the source objective before any further terminal-boundary interventions.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1548-paper-route-fresh-ambiguity-source-mining-branch-synthesis.md, runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv, runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/summary.json
- parent_config: experiments/manifests/m1548-paper-route-fresh-ambiguity-source-mining-branch-synthesis.json
- parent_objective: design calibrated pair expansion after M1547 pair bottleneck
- derived_from: m1548-paper-route-fresh-ambiguity-source-mining-branch-synthesis
- blocked_by: M1547 accepted pair count below threshold, M1547 accepted source-family edge count is one, terminal-boundary history effects are null on the narrow pair subset
- supersedes: direct calibrated intervention repair inside the closed fresh-ambiguity branch
- invalidates: None

## Success Criteria

- docs/m1549-paper-route-calibrated-pair-expansion-design.md exists
- design specifies calibrated pairability metrics and caps
- design specifies source-family edge, pair count, and max-share gates
- candidate materialization training PPO promotion private holdout actor-input changes and training-corpus export remain blocked
- the next route is explicit

## Failure Criteria

- design document is missing
- design routes directly to training promotion private holdout or materialization
- design changes actor inputs or weakens history-positive standards
- design ignores M1547 pair bottleneck

## Evidence Gates

- M1549 must design pair expansion before another intervention implementation
- M1549 must keep calibrated pairability as a first-class source-generation objective
- M1549 must preserve P0 actor input contract
- M1549 must block materialization, training, PPO, promotion, and private holdout

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1549-paper-route-calibrated-pair-expansion-design
- type: gate
- checkpoint: docs/m1549-paper-route-calibrated-pair-expansion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: calibrated_pair_expansion_design_admit_bounded_planner
- reason: M1549 designs pairability-first calibrated terminal-boundary source expansion with accepted_pair_count >= 8 accepted_source_family_edge_count >= 5 and no interventions

## Next Blocker

m1550-paper-route-calibrated-pair-expansion-planner-implementation
