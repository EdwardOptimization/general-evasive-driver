# m950-v4-public-base-rejected-branch-retention-objective-conflict-audit Research Review

## Summary

- Generated at UTC: 20260526T002130Z
- Type: gate
- Gate tier: process
- Promotion decision: rejected_branch_retention_conflict_audit_admit_one_boundary_retune
- Decision reason: M950 classifies M949 as a real alpha-boundary conflict and admits exactly one bounded lower-boundary retune before synthesis or trajectory target export

## Hypothesis

M949 exposed a real tradeoff: low alphas preserve M267 proof but lack tail lift, while higher alphas lift low-tail metrics but break normal retention or M267 proof.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/checkpoints/raw_rejected_branch_retention_update.pt
- parent_dataset: docs/m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe.md, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/summary.json, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/alpha_metrics.csv, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/m267_preflight_summary.csv
- parent_config: experiments/manifests/m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe.json
- parent_objective: audit why rejected-branch retention restored M267 preflight at some alphas but lost exact low-tail candidate overlap
- derived_from: m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe
- blocked_by: M949 has M267 preflight pass alphas but zero exact candidate alphas
- supersedes: None
- invalidates: full replay, PPO, or promotion from M949 raw update

## Success Criteria

- audit document exists
- M949 alpha/preflight conflict is summarized
- next route is selected without training, full replay, PPO, or promotion

## Failure Criteria

- audit recommends full replay from a non-candidate
- audit recommends PPO or promotion
- audit ignores the M267 preflight and exact candidate mismatch

## Evidence Gates

- M950 must not train
- M950 must not run PPO
- M950 must not promote
- M950 must classify the 0.075-0.100 objective conflict boundary
- M950 must choose between coefficient retuning, trajectory-target export, or branch synthesis

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune after looking at private holdout
- do not run full replay from a non-candidate
- do not promote M949
- do not widen actor inputs
- do not open encoders or GRU without synthesis

## Failure Taxonomy

- objective_overfit

## Scoreboard

- milestone: m950-v4-public-base-rejected-branch-retention-objective-conflict-audit
- type: gate
- checkpoint: docs/m950-v4-public-base-rejected-branch-retention-objective-conflict-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: rejected_branch_retention_conflict_audit_admit_one_boundary_retune
- reason: M950 classifies M949 as a real alpha-boundary conflict and admits exactly one bounded lower-boundary retune before synthesis or trajectory target export

## Next Blocker

m951-v4-public-base-rejected-branch-boundary-retune-probe
