# m948-v4-public-base-controlled-fusion-rejected-branch-retention-design Research Review

## Summary

- Generated at UTC: 20260526T000702Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controlled_fusion_rejected_branch_retention_design_admit_m949
- Decision reason: M948 designs an objective-only controlled-fusion repair with rejected-history action retention proxy and hard M267/M264 row 6 13 15 16 preflight before full replay PPO or promotion

## Hypothesis

A replay-admissible controlled-fusion repair needs an explicit rejected-history branch retention term and an M267/M264 preflight gate, because low-tail exact compatibility and lower backup alphas do not preserve wrong-history failures.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0675.pt, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_07.pt, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
- parent_dataset: docs/m947-v4-public-base-controlled-fusion-candidate-failing-surface-audit.md, runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/full_gates/m267_m264_replay/boundary_replay_rows.csv, runs/m947_v4_public_base_controlled_fusion_candidate_failing_surface_audit/m267_m264_a0675/summary.json, runs/m947_v4_public_base_controlled_fusion_candidate_failing_surface_audit/m267_m264_a0700/summary.json
- parent_config: experiments/manifests/m947-v4-public-base-controlled-fusion-candidate-failing-surface-audit.json
- parent_objective: design a replay-admissible controlled-fusion repair objective that protects rejected-history branch failures
- derived_from: m947-v4-public-base-controlled-fusion-candidate-failing-surface-audit
- blocked_by: all known M944 controlled-fusion candidate alphas fail the same M267/M264 rejected-history rows
- supersedes: None
- invalidates: direct lower-alpha replay gate using M944 alpha 0.0675 or 0.0700 as sufficient repair

## Success Criteria

- design document exists
- active rejected-history row set is specified
- objective terms are specified separately for normal retention, low-tail lift, and rejected-branch retention
- preflight gate and full replay escalation are specified
- PPO and promotion remain blocked

## Failure Criteria

- design relies on hidden or oracle actor inputs
- design skips M267/M264 preflight
- design recommends PPO before rejected-branch repair
- design uses old key 9944 as singleton veto

## Evidence Gates

- M948 must not train
- M948 must not run PPO
- M948 must not promote
- M948 must preserve the P0 actor-input contract
- M948 must design a preflight gate for M267/M264 rows 6/13/15/16 before any full replay gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not widen actor inputs
- do not update response/context encoders or GRU in the design unless routing to synthesis first
- do not use old key 9944 as a singleton veto
- do not claim generalization
- do not run training in the design milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m948-v4-public-base-controlled-fusion-rejected-branch-retention-design
- type: infrastructure
- checkpoint: docs/m948-v4-public-base-controlled-fusion-rejected-branch-retention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_fusion_rejected_branch_retention_design_admit_m949
- reason: M948 designs an objective-only controlled-fusion repair with rejected-history action retention proxy and hard M267/M264 row 6 13 15 16 preflight before full replay PPO or promotion

## Next Blocker

m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe
