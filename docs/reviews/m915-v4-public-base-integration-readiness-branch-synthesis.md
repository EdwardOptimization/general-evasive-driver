# m915-v4-public-base-integration-readiness-branch-synthesis Research Review

## Summary

- Generated at UTC: 20260525T212852Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_next_branch
- Decision reason: M915 closes public-base integration-readiness after feature compatibility and stale-target residual failures and opens v4_public_base_target_regeneration

## Hypothesis

The public-base integration-readiness branch has enough evidence to close and route to M399-rooted target regeneration.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m905-v4-pair-delta-public-base-integration-readiness-design.md, docs/m914-v4-public-base-tail-weighted-residual-probe-implementation.md, runs/m914_v4_public_base_tail_weighted_residual_probe/summary.json, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
- parent_config: experiments/manifests/m914-v4-public-base-tail-weighted-residual-probe-implementation.json
- parent_objective: synthesize public-base integration-readiness branch before opening target-regeneration branch
- derived_from: m905-v4-pair-delta-public-base-integration-readiness-design, m914-v4-public-base-tail-weighted-residual-probe-implementation
- blocked_by: workflow synthesis cadence reached for v4_pair_delta_public_base_integration_readiness
- supersedes: None
- invalidates: None

## Success Criteria

- M915 summarizes M905-M914 evidence
- M915 records supported and falsified claims
- M915 records failure taxonomy
- M915 opens v4_public_base_target_regeneration
- M915 blocks training, exact compatibility, replay, PPO, and promotion

## Failure Criteria

- M915 omits synthesis questions
- M915 continues the branch without a synthesis decision
- M915 admits replay, PPO, or promotion
- M915 does not choose a next branch

## Evidence Gates

- M915 must synthesize M905-M914
- M915 must list supported and falsified claims
- M915 must classify failures
- M915 must decide the next branch
- M915 must block training, target generation, exact compatibility, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M915
- do not run target generation
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not open another narrow milestone without synthesis

## Failure Taxonomy

- objective_overfit
- lineage_invalid
- metric_artifact

## Scoreboard

- milestone: m915-v4-public-base-integration-readiness-branch-synthesis
- type: gate
- checkpoint: docs/m915-v4-public-base-integration-readiness-branch-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_next_branch
- reason: M915 closes public-base integration-readiness after feature compatibility and stale-target residual failures and opens v4_public_base_target_regeneration

## Next Blocker

Target-regeneration branch has not yet been opened
