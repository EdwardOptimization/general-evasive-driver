# m1076-v4-public-base-medium-ppo-contract-clean-full-public-gate Research Review

## Summary

- Generated at UTC: 20260527T104421Z
- Type: gate
- Gate tier: proof
- Promotion decision: medium_ppo_contract_clean_full_public_gate_pass_route_to_readiness_synthesis
- Decision reason: M1076 contract-clean projection candidate passes exact public replay family-intersection source-diverse fresh/OOD and behavior gates without PPO or promotion; route to branch synthesis before promotion audit

## Hypothesis

The M1075-selected contract-clean projection candidate can pass the expanded full public gate without broad parameter movement.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit.md, runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/projection_metrics.csv, runs/m1074_medium_ppo_repair_projection_full_public_gate/summary.json
- parent_config: experiments/manifests/m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit.json
- parent_objective: run expanded full public gate for the M1075-selected exact-pass contract-clean projection candidate
- derived_from: m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit
- blocked_by: M1075 selected a contract-clean candidate that has not yet run expanded full public gates
- supersedes: None
- invalidates: claiming M1075-selected candidate is full-gate safe before M1076, promoting the contract-clean candidate without full public gate, rerunning PPO before testing the existing contract-clean candidate

## Success Criteria

- full public gate completes
- summary artifact exists
- actor inputs are unchanged
- allowed changed-parameter surface passes
- exact gate passes
- all old public replay gates pass
- M1061 family-intersection gate passes
- source-diverse gate passes
- fresh/OOD gates pass
- behavior gates pass
- no promotion or private holdout occurs

## Failure Criteria

- full public gate crashes
- summary artifact is missing
- actor inputs change
- allowed changed-parameter surface fails
- any exact/proof/family/source/generalization/behavior gate fails
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1076 must not run PPO
- M1076 must not train actor
- M1076 must not promote
- M1076 must not use private holdout
- M1076 must preserve P0 actor-input contract
- M1076 must preserve allowed changed-parameter surface
- M1076 must run exact, old public replay, M1061 family-intersection, source-diverse, fresh/OOD, and behavior gates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train actor
- do not change actor inputs
- do not weaken allowed changed-parameter prefixes
- do not promote
- do not use private holdout
- do not skip M1061 family-intersection gate
- do not skip source-diverse or behavior gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1076-v4-public-base-medium-ppo-contract-clean-full-public-gate
- type: gate
- checkpoint: runs/m1076_medium_ppo_contract_clean_full_public_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_contract_clean_full_public_gate_pass_route_to_readiness_synthesis
- reason: M1076 contract-clean projection candidate passes exact public replay family-intersection source-diverse fresh/OOD and behavior gates without PPO or promotion; route to branch synthesis before promotion audit

## Next Blocker

m1077-v4-public-base-medium-ppo-readiness-synthesis
