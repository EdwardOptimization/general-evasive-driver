# m962-v4-public-base-direction-target-export-implementation Research Review

## Summary

- Generated at UTC: 20260526T040620Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: direction_target_export_pass_route_to_branch_synthesis
- Decision reason: M962 exports 1280 accepted direction targets 160 branch-separated proof targets and 1149 retention anchors then routes to branch synthesis before actor fitting due cadence

## Hypothesis

M960 accepted direction targets can be materialized into an auditable branch-separated target corpus without actor changes.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m961-v4-public-base-direction-target-export-actor-fit-objective-design.md, runs/m960_v4_public_base_low_tail_direction_family_target_audit/summary.json, runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_family_summary.csv, runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_rows.csv, runs/m960_v4_public_base_low_tail_direction_family_target_audit/m267_direction_target_preflight.csv
- parent_config: experiments/manifests/m961-v4-public-base-direction-target-export-actor-fit-objective-design.json
- parent_objective: implement no-training export of M960 accepted direction targets and branch-separated proof targets
- derived_from: m961-v4-public-base-direction-target-export-actor-fit-objective-design
- blocked_by: M961 designs the export and actor-fit objective but the target corpus has not been materialized
- supersedes: None
- invalidates: actor fitting before accepted direction targets and branch-separated proof anchors are exported

## Success Criteria

- summary artifact exists
- accepted_direction_targets.csv is written
- direction_target_family_catalog.csv is written
- branch_separated_proof_targets.csv is written
- retention_anchor_targets.csv is written
- rejected_export_candidates.csv is written
- route decision is explicit
- training, PPO, and promotion remain blocked

## Failure Criteria

- implementation trains or updates model weights
- implementation changes actor inputs
- implementation exports diagnostic-only anti-aligned families as targets
- implementation omits branch-separated proof targets
- implementation promotes a checkpoint

## Evidence Gates

- M962 must not train
- M962 must not run PPO
- M962 must not promote
- M962 must preserve the P0 actor-input contract
- M962 must export only M960 accepted primary target families
- M962 must export branch-separated proof targets

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not promote
- do not export diagnostic-only anti-aligned families as training targets
- do not collapse wrong-history proof targets into normal safe targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m962-v4-public-base-direction-target-export-implementation
- type: infrastructure
- checkpoint: runs/m962_v4_public_base_direction_target_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_export_pass_route_to_branch_synthesis
- reason: M962 exports 1280 accepted direction targets 160 branch-separated proof targets and 1149 retention anchors then routes to branch synthesis before actor fitting due cadence

## Next Blocker

direction target export has not been implemented
