# m1601-paper-route-contour-aware-source-rule-design Research Review

## Summary

- Generated at UTC: 20260529T171456Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_source_rule_design_admit_offline_selector_implementation
- Decision reason: M1601 designs strict clean_edge_window primary contour and diagnostic exclusions before offline selector implementation

## Hypothesis

M1599's contour map can define a safer contour-aware source rule before any replay.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1599_clean_active_set_contour_mapper/summary.json, runs/m1599_clean_active_set_contour_mapper/selection_source_summary.csv, runs/m1599_clean_active_set_contour_mapper/source_edge_contour_summary.csv, docs/m1600-paper-route-clean-contour-mapper-result-audit.md
- parent_config: experiments/manifests/m1600-paper-route-clean-contour-mapper-result-audit.json
- parent_objective: design contour-aware source rule before any replay
- derived_from: m1600-paper-route-clean-contour-mapper-result-audit
- blocked_by: M1599 shows clean contour is source/window specific and endpoint-neighbor expansion is null-heavy
- supersedes: direct replay from M1599 contour summaries, broad source-edge round-robin repair, candidate materialization from M1599 clean rows
- invalidates: None

## Success Criteria

- docs/m1601-paper-route-contour-aware-source-rule-design.md exists
- design pre-registers primary clean contours and diagnostic exclusions
- design preserves clean selector thresholds and source-share gate
- design decides implementation, synthesis, pivot, or stop
- training PPO promotion private holdout corpus export materialization replay and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1599 as materialization or level3 self-ID evidence
- design ignores M1595 negative result or M1599 endpoint-neighbor null contour
- design routes directly to training PPO promotion private holdout corpus export actor-input changes replay or candidate materialization

## Evidence Gates

- M1601 must design contour-aware source rule without replay
- M1601 must preserve clean selector thresholds and source-share gate
- M1601 must keep dominated/control-only rows as diagnostics
- M1601 must decide implementation, synthesis, pivot, or stop
- M1601 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m1601-paper-route-contour-aware-source-rule-design
- type: gate
- checkpoint: docs/m1601-paper-route-contour-aware-source-rule-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_source_rule_design_admit_offline_selector_implementation
- reason: M1601 designs strict clean_edge_window primary contour and diagnostic exclusions before offline selector implementation

## Next Blocker

m1602-paper-route-contour-aware-source-rule-implementation
