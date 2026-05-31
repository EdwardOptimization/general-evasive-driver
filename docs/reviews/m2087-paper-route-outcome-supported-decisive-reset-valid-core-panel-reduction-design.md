# m2087-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-design Research Review

## Summary

- Generated at UTC: 20260531T230357Z
- Type: gate
- Gate tier: process
- Promotion decision: reset_valid_core_panel_reduction_design_admit_no_reset_materialization
- Decision reason: M2087 designs 238-row reset-valid core panel from M2085 reset-success rows preserving all 96 public-gate rows and excluding two public-debug failures without filter repair

## Hypothesis

A reset-valid core panel can be defined from M2085 reset-success rows without further obstacle-filter repair, preserving all public-gate rows and enough coverage to justify materialization.

## Lineage

- parent_checkpoint: not_applicable_reset_valid_core_panel_reduction_design
- parent_dataset: runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/summary.json, runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/reset_rows.csv, runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/reset_failure_rows.csv, docs/m2086-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-result-audit.md
- parent_config: experiments/manifests/m2086-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-result-audit.json
- parent_objective: design a reset-valid core panel after closing the local obstacle-filter repair branch
- derived_from: m2086-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-result-audit
- blocked_by: M2085 reset validation failed 2/240 attempts and M2086 pivots away from local repair
- supersedes: another obstacle-filter repair, direct measured execution on the full 240-row panel
- invalidates: None

## Success Criteria

- docs/m2087-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-design.md exists
- reduced-panel inclusion rule is explicit
- public-gate preservation is audited
- coverage loss is documented
- next route is explicit
- no reset rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design doc is missing
- inclusion rule is ambiguous
- coverage loss is not documented
- next route is ambiguous
- new reset or rollout is performed

## Evidence Gates

- M2087 must design a reduced reset-valid panel route using M2085 reset-success rows
- M2087 must preserve all public-gate rows unless it explicitly justifies a stricter subset
- M2087 must not change obstacle filters or rerun reset
- M2087 must block measured execution until reduction materialization is implemented and audited

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit code
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not treat generated rows as paper-valid tasks

## Failure Taxonomy

- none

## Scoreboard

- milestone: m2087-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-design
- type: gate
- checkpoint: docs/m2087-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reset_valid_core_panel_reduction_design_admit_no_reset_materialization
- reason: M2087 designs 238-row reset-valid core panel from M2085 reset-success rows preserving all 96 public-gate rows and excluding two public-debug failures without filter repair

## Next Blocker

m2088-selected-by-m2087-design
