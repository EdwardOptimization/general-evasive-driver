# m1078-v4-public-base-contract-clean-projection-promotion-audit Research Review

## Summary

- Generated at UTC: 20260527T110430Z
- Type: gate
- Gate tier: promotion
- Promotion decision: contract_clean_projection_promote_public_gate_base
- Decision reason: M1078 promotes the M1076 contract-clean projection checkpoint as current public-gate base scoped to proof hardening only

## Hypothesis

The M1076 contract-clean projection checkpoint should replace M1049 as the current public-gate base for proof hardening, while explicitly not claiming medium-PPO performance improvement.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1077-v4-public-base-medium-ppo-readiness-synthesis.md, docs/m1076-v4-public-base-medium-ppo-contract-clean-full-public-gate.md, runs/m1076_medium_ppo_contract_clean_full_public_gate/summary.json
- parent_config: experiments/manifests/m1077-v4-public-base-medium-ppo-readiness-synthesis.json
- parent_objective: audit whether the M1076 contract-clean full-gate candidate should become the next public-gate base
- derived_from: m1077-v4-public-base-medium-ppo-readiness-synthesis
- blocked_by: M1077 closed expanded_gate_medium_ppo_readiness and opened contract_clean_projection_promotion
- supersedes: None
- invalidates: promoting the M1076 candidate without a separate promotion audit, claiming medium-PPO performance improvement from the projection-only candidate, using private-holdout language for public-gate-only evidence

## Success Criteria

- promotion audit artifact exists
- M1076 evidence is summarized
- promotion decision is explicit
- current-status and scoreboard lineage are updated if promoted
- scope limits are explicit
- no training or PPO occurs
- private holdout is not used

## Failure Criteria

- promotion decision is missing
- promotion occurs without current-status update
- private holdout is used
- PPO starts
- paper-level generalization or medium-PPO performance lift is claimed

## Evidence Gates

- M1078 must not train
- M1078 must not run PPO
- M1078 must not use private holdout
- M1078 must decide promote or reject for public-gate base status only
- M1078 must keep the promotion scope limited to proof-base hardening
- M1078 must not claim medium-PPO performance improvement or paper-level generalization

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not change actor inputs
- do not claim medium or long PPO stability
- do not claim paper-level generalization
- do not promote without updating current status and scoreboard lineage

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1078-v4-public-base-contract-clean-projection-promotion-audit
- type: gate
- checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contract_clean_projection_promote_public_gate_base
- reason: M1078 promotes the M1076 contract-clean projection checkpoint as current public-gate base scoped to proof hardening only

## Next Blocker

m1079-v4-public-base-contract-clean-post-promotion-synthesis
