# m1004-v4-public-base-temporal-sequence-update-public-replay-gate Research Review

## Summary

- Generated at UTC: 20260526T171413Z
- Type: gate
- Gate tier: proof
- Promotion decision: temporal_sequence_public_replay_gate_no_preflight_candidate_route_to_replay_failure_audit
- Decision reason: M1004 finds 5/5 exact contract candidates but 0/5 M267/M264 preflight pass; smallest alpha 0.01 regresses success-drop count 17 to 15 on rows 6 and 15

## Hypothesis

At least one M1002 exact temporal objective candidate will retain public replay/proof gates and behavior seeds without PPO or promotion.

## Lineage

- parent_checkpoint: runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_1.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_05.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_02.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt
- parent_dataset: docs/m1003-v4-public-base-temporal-sequence-update-public-replay-gate-design.md, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/summary.json, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/candidate_checkpoints.csv
- parent_config: experiments/manifests/m1003-v4-public-base-temporal-sequence-update-public-replay-gate-design.json
- parent_objective: run no-training public replay/proof gate for M1002 exact candidates
- derived_from: m1003-v4-public-base-temporal-sequence-update-public-replay-gate-design, m1002-v4-public-base-temporal-sequence-objective-update-probe
- blocked_by: M1003 requires replay/proof validation before any candidate can advance
- supersedes: None
- invalidates: promoting M1002 exact candidates without public replay

## Success Criteria

- gate command completes
- summary.json exists
- M267/M264 preflight is reported for candidate alphas
- six public replay surfaces are reported for selected candidate
- behavior seeds 9505 and 9506 are reported
- ppo_used == false
- promoted == false

## Failure Criteria

- M267/M264 preflight is missing
- public replay surfaces are missing
- PPO starts
- promotion occurs
- private holdout is used

## Evidence Gates

- M1004 must not run PPO
- M1004 must not promote
- M1004 must run M267/M264 preflight before full replay
- M1004 must run six public replay surfaces for the selected candidate
- M1004 must run behavior seeds 9505 and 9506

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not promote exact-only candidates
- do not skip M267/M264 preflight
- do not skip old proof surfaces
- do not proceed to PPO

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1004-v4-public-base-temporal-sequence-update-public-replay-gate
- type: gate
- checkpoint: runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_public_replay_gate_no_preflight_candidate_route_to_replay_failure_audit
- reason: M1004 finds 5/5 exact contract candidates but 0/5 M267/M264 preflight pass; smallest alpha 0.01 regresses success-drop count 17 to 15 on rows 6 and 15

## Next Blocker

m1005-v4-public-base-temporal-sequence-update-replay-failure-audit
