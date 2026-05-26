# m960-v4-public-base-low-tail-direction-family-target-audit-implementation Research Review

## Summary

- Generated at UTC: 20260526T031455Z
- Type: gate
- Gate tier: process
- Promotion decision: low_tail_direction_family_target_audit_joint_candidate_route_to_export_objective_design
- Decision reason: M960 finds 20 joint direction-target candidates from primary families with best candidate throttle_minus_amp_0_0080 and routes to direction target export plus actor-fit objective design

## Hypothesis

Behavior-improving direction families from M958 can yield at least one normal-retained, proof-retained target candidate before actor training.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m959-v4-public-base-low-tail-direction-family-target-audit-design.md, runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/summary.json, runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/direction_family_summary.csv, runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/row_metric_grounding.csv
- parent_config: experiments/manifests/m959-v4-public-base-low-tail-direction-family-target-audit-design.json
- parent_objective: implement a no-training audit converting behavior-improving M958 direction families into normal-retained proof-retained target candidates
- derived_from: m959-v4-public-base-low-tail-direction-family-target-audit-design
- blocked_by: M958 finds direction-sign suspicion and M959 designs direction-family target audit but the audit has not been implemented
- supersedes: None
- invalidates: training on away-from-intervention low-tail targets, actor fitting on direction-family targets before normal-retention and M267 proof-retention checks

## Success Criteria

- summary artifact exists
- direction target family summary is written
- row-level direction target metrics are written
- normal-retention metrics are written
- M267/M264 direction target preflight is written
- route decision is explicit
- training, PPO, and promotion remain blocked

## Failure Criteria

- implementation trains or updates model weights
- implementation changes actor inputs
- implementation omits normal-retention checks
- implementation omits terminal-margin behavior grounding
- implementation omits M267/M264 proof retention
- implementation promotes a checkpoint

## Evidence Gates

- M960 must not train
- M960 must not run PPO
- M960 must not promote
- M960 must preserve the P0 actor-input contract
- M960 must evaluate normal-retention metrics
- M960 must evaluate terminal-margin behavior grounding
- M960 must evaluate M267/M264 branch-separated proof retention

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not promote
- do not treat old low-tail proxy improvement as sufficient without terminal-margin grounding
- do not export diagnostic-only anti-aligned families as training targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m960-v4-public-base-low-tail-direction-family-target-audit-implementation
- type: gate
- checkpoint: runs/m960_v4_public_base_low_tail_direction_family_target_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: low_tail_direction_family_target_audit_joint_candidate_route_to_export_objective_design
- reason: M960 finds 20 joint direction-target candidates from primary families with best candidate throttle_minus_amp_0_0080 and routes to direction target export plus actor-fit objective design

## Next Blocker

low-tail direction-family target audit has not been implemented
