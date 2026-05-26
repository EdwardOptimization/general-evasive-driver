# m1005-v4-public-base-temporal-sequence-update-replay-failure-audit Research Review

## Summary

- Generated at UTC: 20260526T171758Z
- Type: gate
- Gate tier: process
- Promotion decision: temporal_sequence_replay_failure_audit_route_to_branch_preserving_temporal_repair_design
- Decision reason: M1005 classifies the M1004 failure as localized wrong-history branch lift proof washout rather than contract violation or broad normal regression

## Hypothesis

M1004 failed because the actor_mean-only temporal objective lifts wrong-history near-threshold public proof rows, not because of actor contract changes or broad normal-branch regression.

## Lineage

- parent_checkpoint: runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_1.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_05.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_02.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt
- parent_dataset: runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/summary.json, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight_summary.csv, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/m1002_temporal_a0_01/boundary_replay_rows.csv
- parent_config: experiments/manifests/m1004-v4-public-base-temporal-sequence-update-public-replay-gate.json
- parent_objective: audit why exact temporal sequence candidates failed M267/M264 preflight
- derived_from: m1004-v4-public-base-temporal-sequence-update-public-replay-gate
- blocked_by: M1004 exact temporal candidates all fail M267/M264 success-drop retention
- supersedes: None
- invalidates: lower-alpha replay without auditing rows 6 and 15, PPO from M1002 temporal candidates

## Success Criteria

- audit document exists
- failure cause is classified with process-v2 taxonomy
- rows lost by the smallest alpha are identified
- next blocker is registered

## Failure Criteria

- audit ignores M267/M264 row-level evidence
- audit routes to PPO
- audit routes to promotion
- audit uses private holdout

## Evidence Gates

- M1005 must not run PPO
- M1005 must not promote
- M1005 must classify the M1004 preflight failure
- M1005 must decide whether the next step is objective repair or branch synthesis

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune alpha after seeing M1004 without a new objective
- do not run full public replay for candidates that failed M267/M264 preflight
- do not use private holdout
- do not claim temporal objective update improves deployable driver behavior

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1005-v4-public-base-temporal-sequence-update-replay-failure-audit
- type: gate
- checkpoint: docs/m1005-v4-public-base-temporal-sequence-update-replay-failure-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_replay_failure_audit_route_to_branch_preserving_temporal_repair_design
- reason: M1005 classifies the M1004 failure as localized wrong-history branch lift proof washout rather than contract violation or broad normal regression

## Next Blocker

m1006-v4-public-base-branch-preserving-temporal-repair-design
