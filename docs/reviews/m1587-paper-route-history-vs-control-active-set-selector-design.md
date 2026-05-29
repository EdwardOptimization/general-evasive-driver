# m1587-paper-route-history-vs-control-active-set-selector-design Research Review

## Summary

- Generated at UTC: 20260529T160902Z
- Type: gate
- Gate tier: process
- Promotion decision: history_vs_control_active_set_selector_design_admit_selector_only_implementation
- Decision reason: M1587 designs selector-only clean dominated null labels over M1585 rows before source repair

## Hypothesis

A history-vs-control active-set selector can turn M1585's control-dominated result into a cleaner next source-generation objective.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1585_source_diverse_pairability_history_intervention_smoke/summary.json, runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv, docs/m1586-paper-route-source-diverse-pairability-intervention-result-audit.md
- parent_config: experiments/manifests/m1586-paper-route-source-diverse-pairability-intervention-result-audit.json
- parent_objective: design a history-vs-control active-set selector after M1585 control-dominated result
- derived_from: m1586-paper-route-source-diverse-pairability-intervention-result-audit
- blocked_by: M1585 broad pairability intervention is control-dominated and has only 7 clean history-vs-control directed pairs
- supersedes: another broad pairability intervention without history-vs-control selection, candidate materialization after M1585, training corpus export after M1585
- invalidates: None

## Success Criteria

- docs/m1587-paper-route-history-vs-control-active-set-selector-design.md exists
- design pre-registers clean, dominated, and null labels
- design pre-registers source-diversity and control dominance metrics
- design chooses selector-only implementation, source-generation repair, synthesis, or stop
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1585 as history-necessity or level3 self-ID evidence
- design ignores control dominance or high-speed caveat
- design routes directly to training PPO promotion private holdout corpus export actor-input changes or candidate materialization

## Evidence Gates

- M1587 must design a selector whose primary criterion is history-vs-control separation
- M1587 must keep M1585 as public diagnostic evidence rather than history-necessity evidence
- M1587 must pre-register clean, dominated, and null labels
- M1587 must decide whether the next implementation is selector-only or source-generation repair
- M1587 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
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

- milestone: m1587-paper-route-history-vs-control-active-set-selector-design
- type: gate
- checkpoint: docs/m1587-paper-route-history-vs-control-active-set-selector-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: history_vs_control_active_set_selector_design_admit_selector_only_implementation
- reason: M1587 designs selector-only clean dominated null labels over M1585 rows before source repair

## Next Blocker

m1588-paper-route-history-vs-control-active-set-selector-implementation
