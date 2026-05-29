# m1588-paper-route-history-vs-control-active-set-selector-implementation Research Review

## Summary

- Generated at UTC: 20260529T161354Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: history_vs_control_active_set_selector_public_pass_clean_shortfall_route_to_audit
- Decision reason: M1588 selector public gates pass with 7 clean directed pairs across 4 edges but evidence-quality fails clean count target

## Hypothesis

A selector-only classifier can make M1585's clean history-vs-control sub-surface explicit and decide whether source-generation repair is needed.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv, docs/m1587-paper-route-history-vs-control-active-set-selector-design.md
- parent_config: experiments/manifests/m1587-paper-route-history-vs-control-active-set-selector-design.json
- parent_objective: implement selector-only history-vs-control active-set classification over M1585 rows
- derived_from: m1587-paper-route-history-vs-control-active-set-selector-design
- blocked_by: M1587 design has not yet been implemented
- supersedes: another source-diverse intervention implementation before selector audit, candidate materialization after M1585
- invalidates: None

## Success Criteria

- selector implementation module exists
- focused tests cover clean/dominated/null labels and summary gates
- runs/m1588_history_vs_control_active_set_selector/summary.json exists
- classified and clean row artifacts exist
- no simulator rerun or history intervention is executed
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- implementation reruns simulator or history interventions
- implementation changes actor inputs or uses private holdout
- implementation exports a training corpus or starts training/PPO
- implementation claims level3 self-identification

## Evidence Gates

- M1588 must classify M1585 directed pairs into clean dominated null and invalid labels
- M1588 must not rerun simulator or interventions
- M1588 must report source-edge and source-family diversity of clean rows
- M1588 must report whether clean count is sufficient or a source-generation repair is needed
- M1588 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke that reruns simulator
- do not rerun simulator
- do not run history interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1588-paper-route-history-vs-control-active-set-selector-implementation
- type: infrastructure
- checkpoint: runs/m1588_history_vs_control_active_set_selector/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: history_vs_control_active_set_selector_public_pass_clean_shortfall_route_to_audit
- reason: M1588 selector public gates pass with 7 clean directed pairs across 4 edges but evidence-quality fails clean count target

## Next Blocker

m1589-paper-route-history-vs-control-selector-result-audit
