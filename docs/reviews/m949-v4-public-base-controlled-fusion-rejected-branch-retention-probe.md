# m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe Research Review

## Summary

- Generated at UTC: 20260526T001711Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controlled_fusion_rejected_branch_retention_objective_conflict_route_to_audit
- Decision reason: M949 restores M267 preflight at alphas 0.005 0.010 0.200 but exact_candidate_alpha_count is 0 so no full replay PPO or promotion is allowed

## Hypothesis

Adding rejected-history branch retention to the controlled-fusion objective may preserve M267/M264 wrong-history failures while retaining low-tail exact objective lift.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m948-v4-public-base-controlled-fusion-rejected-branch-retention-design.md, runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/full_gates/m267_m264_replay/boundary_replay_rows.csv, runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m948-v4-public-base-controlled-fusion-rejected-branch-retention-design.json
- parent_objective: implement controlled-fusion objective-only probe with explicit rejected-history branch retention proxy and M267/M264 preflight
- derived_from: m948-v4-public-base-controlled-fusion-rejected-branch-retention-design
- blocked_by: controlled-fusion low-tail objective has no rejected-history branch retention implementation
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- active rejected rows are reconstructed
- forbidden_parameter_changed is false
- M267/M264 preflight is evaluated
- candidate_alpha_count is reported
- ppo_used and promoted are false

## Failure Criteria

- actor inputs change
- forbidden parameters change
- M267/M264 preflight is skipped
- PPO or promotion is run
- active rejected rows cannot be reconstructed

## Evidence Gates

- M949 must preserve P0 actor-input contract
- M949 may train only actor_mean and response_context_fusion.0
- M949 must evaluate exact objective metrics
- M949 must evaluate M267/M264 preflight rows 6/13/15/16
- M949 must not run PPO
- M949 must not promote

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not widen actor inputs
- do not update response/context encoders or online GRU
- do not use old key 9944 as a singleton veto
- do not skip M267/M264 preflight
- do not run PPO or promotion

## Failure Taxonomy

- objective_overfit

## Scoreboard

- milestone: m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe
- type: infrastructure
- checkpoint: runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_fusion_rejected_branch_retention_objective_conflict_route_to_audit
- reason: M949 restores M267 preflight at alphas 0.005 0.010 0.200 but exact_candidate_alpha_count is 0 so no full replay PPO or promotion is allowed

## Next Blocker

m950-v4-public-base-rejected-branch-retention-objective-conflict-audit
