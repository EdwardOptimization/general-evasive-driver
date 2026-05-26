# m1014-v4-public-base-margin-weighted-repair-failure-audit Research Review

## Summary

- Generated at UTC: 20260526T190554Z
- Type: gate
- Gate tier: process
- Promotion decision: margin_weighted_repair_failure_audit_route_to_replay_calibrated_trust_audit_design
- Decision reason: M1014 classifies M1013 as exact_branch_active_set_conflict and routes to minimal M267/M264 preflight calibration before threshold relaxation

## Hypothesis

The M1013 negative result can be diagnosed without new training by comparing exact-safe small-alpha points, exact-but-unsafe points, branch contributions, and train-history branch-loss oscillation.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m1013-v4-public-base-margin-weighted-branch-repair-update-probe.md, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/summary.json, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/interpolation_metrics.csv, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/train_history.csv
- parent_config: experiments/manifests/m1013-v4-public-base-margin-weighted-branch-repair-update-probe.json
- parent_objective: audit why exact temporal candidates fail the M1011 branch trust region
- derived_from: m1013-v4-public-base-margin-weighted-branch-repair-update-probe
- blocked_by: M1013 found exact candidates but zero exact+branch candidates
- supersedes: None
- invalidates: direct threshold relaxation without failure audit

## Success Criteria

- audit document exists
- failure is classified with process-v2 taxonomy
- audit names the next route without relaxing thresholds in-place
- PPO and promotion remain blocked

## Failure Criteria

- audit runs new training
- audit changes branch thresholds and declares success
- audit routes directly to PPO or promotion
- audit ignores actor contract

## Evidence Gates

- M1014 must not train
- M1014 must not run PPO
- M1014 must not promote
- M1014 must preserve P0 actor inputs
- M1014 must classify whether M1013 is threshold conflict, actor_mean capacity conflict, optimizer instability, or projection-needed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not relax M1011 trust gates inside this audit
- do not use private holdout
- do not run replay gates as promotion evidence
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1014-v4-public-base-margin-weighted-repair-failure-audit
- type: gate
- checkpoint: docs/m1014-v4-public-base-margin-weighted-repair-failure-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_weighted_repair_failure_audit_route_to_replay_calibrated_trust_audit_design
- reason: M1014 classifies M1013 as exact_branch_active_set_conflict and routes to minimal M267/M264 preflight calibration before threshold relaxation

## Next Blocker

m1015-v4-public-base-m1013-exact-candidate-preflight-design
