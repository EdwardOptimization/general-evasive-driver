# m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design Research Review

## Summary

- Generated at UTC: 20260526T231905Z
- Type: gate
- Gate tier: proof
- Promotion decision: candidate_b_m183_row16_active_set_retention_design_admit_anchor_export
- Decision reason: M1033 designs M183/M170 row16 normal-trajectory retention as a hard active-set constraint before the next repair/projection attempt

## Hypothesis

Adding M183/M170 row16 normal-branch retention as a hard active-set constraint should be designed before any further post-PPO repair/projection attempt.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/m1031_candidate_b_temporal_safe_projection_probe/checkpoints/m1031_raw_conflict_s40_a0_05.pt
- parent_dataset: docs/m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit.md, runs/m1031_candidate_b_temporal_safe_projection_probe/first_replay/m1031_raw_conflict_s40_a0_05/m183_m170/boundary_replay_rows.csv, runs/m1031_candidate_b_temporal_safe_projection_probe/projection_metrics.csv
- parent_config: experiments/manifests/m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit.json
- parent_objective: design active-set retention for M183/M170 row16 normal terminal-margin cliff
- derived_from: m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit
- blocked_by: M1032 classifies M1031 failure as M183/M170 row16 normal-branch terminal-margin cliff rather than wrong-history sensitivity loss
- supersedes: None
- invalidates: running another projection without adding M183/M170 row16 to the hard active set, running longer PPO before first-replay active-set retention is specified, promoting M1031 low-alpha projections

## Success Criteria

- design artifact exists
- M183/M170 row16 retention data source is specified
- M997 temporal, M297/M270, M267/M264 row15, and M183/M170 row16 gate order is explicit
- next implementation scope is bounded and no PPO promotion private holdout or actor-input change occurs

## Failure Criteria

- design omits M183/M170 row16
- design relaxes M997 thresholds
- design runs repair or PPO
- design changes actor inputs
- design promotes a candidate

## Evidence Gates

- M1033 must run no PPO
- M1033 must not promote
- M1033 must not use private holdout
- M1033 must preserve P0 actor inputs
- M1033 must keep M997 temporal retention, M297/M270 exact checks, M267/M264 row15, and M183/M170 row16 in the gate order

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not relax M997 thresholds
- do not treat low-alpha near-base movement as a promotion candidate
- do not drop M267/M264 row15
- do not ignore M183/M170 row16 normal branch
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design
- type: gate
- checkpoint: docs/m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_m183_row16_active_set_retention_design_admit_anchor_export
- reason: M1033 designs M183/M170 row16 normal-trajectory retention as a hard active-set constraint before the next repair/projection attempt

## Next Blocker

m1034-v4-public-base-candidate-b-m183-row16-active-set-anchor-export
