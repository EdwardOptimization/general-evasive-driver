# m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit Research Review

## Summary

- Generated at UTC: 20260526T231522Z
- Type: gate
- Gate tier: proof
- Promotion decision: candidate_b_temporal_projection_first_replay_failure_audit_route_to_m183_row16_active_set_retention_design
- Decision reason: M1032 classifies M1031 failure as M183/M170 normal-branch terminal-margin active-set failure with closest miss raw alpha0.05 row16 normal margin -0.000165

## Hypothesis

M1031's remaining proof washout is caused by an M183/M170 normal-branch terminal-margin cliff, especially row16, rather than loss of wrong-history sensitivity.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/m1031_candidate_b_temporal_safe_projection_probe/checkpoints/m1031_raw_conflict_s40_a0_05.pt, runs/m1031_candidate_b_temporal_safe_projection_probe/checkpoints/m1031_base_conflict_s40_a0_25.pt, runs/m1031_candidate_b_temporal_safe_projection_probe/checkpoints/m1031_line_conflict_s40_a0_25.pt
- parent_dataset: runs/m1031_candidate_b_temporal_safe_projection_probe/summary.json, runs/m1031_candidate_b_temporal_safe_projection_probe/projection_metrics.csv, runs/m1031_candidate_b_temporal_safe_projection_probe/first_replay_summary.csv, runs/m1031_candidate_b_temporal_safe_projection_probe/first_replay/m1031_raw_conflict_s40_a0_05/m183_m170/boundary_replay_rows.csv, docs/m1031-v4-public-base-candidate-b-temporal-safe-projection-probe.md
- parent_config: experiments/manifests/m1031-v4-public-base-candidate-b-temporal-safe-projection-probe.json
- parent_objective: audit why temporal/exact-safe projections still fail first replay
- derived_from: m1031-v4-public-base-candidate-b-temporal-safe-projection-probe
- blocked_by: M1031 finds 14 temporal/exact-safe projection candidates but 0 pass both M267/M264 and M183/M170 first replay
- supersedes: None
- invalidates: routing M1031 directly to full public gate, running longer PPO from M1026 before first-replay failure is audited, promoting any M1031 projected checkpoint

## Success Criteria

- audit artifact exists
- M1031 first replay failures are summarized by surface, row, branch, and margin
- the next repair route is selected with no PPO, no promotion, and no actor-input change
- M183/M170 row16 is either admitted as a hard active-set constraint or ruled out with evidence

## Failure Criteria

- audit cannot localize the M1031 failure
- audit recommends longer PPO before repair/gate correction
- audit ignores the M183/M170 first replay failure
- audit changes actor inputs
- audit promotes a checkpoint

## Evidence Gates

- M1032 must run no PPO
- M1032 must not promote
- M1032 must not use private holdout
- M1032 must preserve P0 actor inputs
- M1032 must classify whether the M1031 replay failure is M183 row16 normal-margin cliff, broader normal-branch regression, or wrong-history sensitivity loss

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not relax M997 thresholds
- do not treat M267/M264 pass as full first-replay pass
- do not ignore M183/M170 row16 normal failure
- do not change actor inputs
- do not promote any projection candidate

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit
- type: gate
- checkpoint: docs/m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_temporal_projection_first_replay_failure_audit_route_to_m183_row16_active_set_retention_design
- reason: M1032 classifies M1031 failure as M183/M170 normal-branch terminal-margin active-set failure with closest miss raw alpha0.05 row16 normal margin -0.000165

## Next Blocker

m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design
