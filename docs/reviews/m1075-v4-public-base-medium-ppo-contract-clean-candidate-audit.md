# m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit Research Review

## Summary

- Generated at UTC: 20260527T095318Z
- Type: gate
- Gate tier: process
- Promotion decision: medium_ppo_contract_clean_candidate_audit_route_to_full_public_gate
- Decision reason: M1075 finds 13 exact-pass contract-clean M1073 projection candidates and selects m1031_base_row16x4_s40_a1 for expanded full public gate

## Hypothesis

M1073 produced at least one exact-pass contract-clean candidate that should be evaluated by the expanded full public gate before redesigning projection.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_line_row16x4_s40_a1.pt
- parent_dataset: docs/m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate.md, runs/m1074_medium_ppo_repair_projection_full_public_gate/summary.json, runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/projection_metrics.csv
- parent_config: experiments/manifests/m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate.json
- parent_objective: audit contract-clean projection alternatives after M1074 fails only allowed-surface contract
- derived_from: m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate
- blocked_by: M1074 closed-loop gates passed but the selected candidate changed disallowed parameter groups
- supersedes: None
- invalidates: treating M1074 as proof washout, promoting the contract-artifact candidate, rerunning PPO before auditing contract-clean alternatives already produced by M1073

## Success Criteria

- audit artifact exists
- audit identifies selected candidate or explains why none exists
- audit checks changed_parameter_names against allowed prefixes
- audit checks exact eligibility
- audit routes to full public gate or selector redesign
- no PPO actor training promotion or private holdout occurs

## Failure Criteria

- audit artifact is missing
- audit omits changed parameter contract
- audit recommends weakening allowed prefixes
- PPO or actor training starts
- private holdout is used

## Evidence Gates

- M1075 must not run PPO
- M1075 must not train actor
- M1075 must not promote
- M1075 must not use private holdout
- M1075 must identify whether M1073 has an exact-pass contract-clean candidate worth full public gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train actor
- do not promote
- do not use private holdout
- do not weaken allowed-surface contract
- do not ignore M1074 proof gate passes

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit
- type: gate
- checkpoint: docs/m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_contract_clean_candidate_audit_route_to_full_public_gate
- reason: M1075 finds 13 exact-pass contract-clean M1073 projection candidates and selects m1031_base_row16x4_s40_a1 for expanded full public gate

## Next Blocker

m1076-v4-public-base-medium-ppo-contract-clean-full-public-gate
