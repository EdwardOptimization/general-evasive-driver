# m1673-paper-route-controller-family-one-seed-public-pilot-design Research Review

## Summary

- Generated at UTC: 20260529T224652Z
- Type: gate
- Gate tier: process
- Promotion decision: one_seed_public_pilot_design_admit_standard_layer_implementation
- Decision reason: M1673 designs standard-layer one-seed public pilot across all 12 profiles while keeping M1615 diagnostic-only

## Hypothesis

A one-seed public controller-family plumbing pilot can be designed with fair controls and clean task-layer semantics before any run.

## Lineage

- parent_checkpoint: not_applicable_pilot_design
- parent_dataset: docs/m1672-paper-route-controller-family-decisive-matrix-protocol-preflight-result-audit.md, runs/m1671_controller_family_decisive_matrix_protocol/summary.json, runs/m1671_controller_family_decisive_matrix_protocol/matrix_protocol.json
- parent_config: experiments/manifests/m1672-paper-route-controller-family-decisive-matrix-protocol-preflight-result-audit.json
- parent_objective: design one-seed public controller-family decisive matrix plumbing pilot
- derived_from: m1672-paper-route-controller-family-decisive-matrix-protocol-preflight-result-audit
- blocked_by: M1672 admits only design, not direct pilot execution, clean-package mapping risk must be handled before implementation
- supersedes: direct one-seed pilot execution after M1672, direct three-seed matrix after M1672, direct private holdout after M1672
- invalidates: None

## Success Criteria

- docs/m1673-paper-route-controller-family-one-seed-public-pilot-design.md exists
- design lists all 12 controller profiles
- design specifies same-budget training and evaluation settings
- design resolves or blocks direct M1615 clean-package use
- design defines plumbing metrics and post-run audit requirements
- training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design document is missing
- design omits current-tiled or reset controls
- design admits profile-specific tuning
- design treats one-seed pilot as architecture ranking
- design routes directly to private holdout or paper evidence

## Evidence Gates

- M1673 must design the one-seed public plumbing pilot without running it
- M1673 must specify all 12 controller profiles and equal-budget rules
- M1673 must decide how M1615 clean package is handled without leakage
- M1673 must specify metrics and audit gates before any three-seed matrix
- M1673 must keep training replay PPO promotion private holdout actor-input changes and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not repair the M1663 artifact
- do not execute the one-seed pilot
- do not claim controller-family ranking
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1673-paper-route-controller-family-one-seed-public-pilot-design
- type: gate
- checkpoint: docs/m1673-paper-route-controller-family-one-seed-public-pilot-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: one_seed_public_pilot_design_admit_standard_layer_implementation
- reason: M1673 designs standard-layer one-seed public pilot across all 12 profiles while keeping M1615 diagnostic-only

## Next Blocker

m1674-paper-route-controller-family-one-seed-public-pilot-implementation
