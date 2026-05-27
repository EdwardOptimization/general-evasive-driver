# m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate Research Review

## Summary

- Generated at UTC: 20260527T093841Z
- Type: gate
- Gate tier: proof
- Promotion decision: medium_ppo_projection_full_gate_contract_artifact_route_to_contract_clean_candidate_audit
- Decision reason: M1074 selected candidate passes closed-loop proof family-intersection source-diverse fresh/OOD and behavior gates but fails allowed-surface contract so it is rejected

## Hypothesis

The M1073 repaired projection candidate can pass the expanded full public gate after restoring first-replay proof constraints.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_line_row16x4_s40_a1.pt
- parent_dataset: docs/m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe.md, runs/m1073_medium_ppo_failed_row_repair_projection_probe/summary.json, runs/m1072_medium_ppo_failed_row_projection_corpus/current_family_conflict_corpus.npz
- parent_config: experiments/manifests/m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe.json
- parent_objective: run the expanded full public gate for the M1073 no-PPO projection candidate
- derived_from: m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe
- blocked_by: M1073 found only a first-replay candidate; expanded full public gates have not yet been run
- supersedes: None
- invalidates: promoting the M1073 first-replay candidate before expanded full public gate, claiming the M1069 proof washout is repaired without M1061 family-intersection and source-diverse gates

## Success Criteria

- full public gate completes
- summary artifact exists
- actor inputs are unchanged
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
- any exact/proof/family/source/generalization/behavior gate fails
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1074 must not run PPO
- M1074 must not promote
- M1074 must not use private holdout
- M1074 must preserve the P0 actor-input contract
- M1074 must run exact, old public replay, M1061 family-intersection, source-diverse, fresh/OOD, and behavior gates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not change actor inputs
- do not promote from M1074
- do not use private holdout
- do not skip M1061 family-intersection gate
- do not skip source-diverse or behavior gates

## Failure Taxonomy

- contract_violation

## Scoreboard

- milestone: m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate
- type: gate
- checkpoint: runs/m1074_medium_ppo_repair_projection_full_public_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_projection_full_gate_contract_artifact_route_to_contract_clean_candidate_audit
- reason: M1074 selected candidate passes closed-loop proof family-intersection source-diverse fresh/OOD and behavior gates but fails allowed-surface contract so it is rejected

## Next Blocker

m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit
