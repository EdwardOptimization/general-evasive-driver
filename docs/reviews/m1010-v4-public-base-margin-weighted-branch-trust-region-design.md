# m1010-v4-public-base-margin-weighted-branch-trust-region-design Research Review

## Summary

- Generated at UTC: 20260526T181620Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: margin_weighted_branch_trust_region_design_admit_m1011_evaluator
- Decision reason: M1010 designs margin-slack-weighted rejected-branch trust-region residual on M267/M264 rows 6 and 15 primary before any actor update

## Hypothesis

A margin-slack-weighted rejected-branch trust-region can detect the tiny action shifts that flip M267/M264 near-cliff wrong-history rows.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m1009-v4-public-base-temporal-sequence-objective-branch-synthesis.md, docs/m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit.md, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/*/boundary_replay_rows.csv, runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator/branch_metric_rows.csv
- parent_config: experiments/manifests/m1009-v4-public-base-temporal-sequence-objective-branch-synthesis.json
- parent_objective: design a margin-slack-weighted rejected-branch trust-region residual
- derived_from: m1009-v4-public-base-temporal-sequence-objective-branch-synthesis, m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit
- blocked_by: M1009 synthesis continues the branch but stops unweighted fixed one-step branch proxies
- supersedes: None
- invalidates: actor update using unweighted fixed one-step branch ceiling or separation proxy

## Success Criteria

- design document exists
- wrong-history branch trust-region is defined as a proof constraint, not a deployable behavior target
- margin weighting and active rows are specified
- no-update evaluator gates are specified before any actor update
- PPO and promotion remain blocked

## Failure Criteria

- design trains directly toward wrong-history behavior without proof-constraint framing
- design changes actor inputs
- design skips rows 6 and 15
- design routes directly to PPO or promotion

## Evidence Gates

- M1010 must not train
- M1010 must not run PPO
- M1010 must not promote
- M1010 must preserve P0 actor inputs
- M1010 must define a margin-weighted branch trust-region evaluator before any actor update

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat wrong-history action anchors as deployable behavior targets
- do not use private holdout
- do not skip M267/M264 preflight
- do not run PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1010-v4-public-base-margin-weighted-branch-trust-region-design
- type: infrastructure
- checkpoint: docs/m1010-v4-public-base-margin-weighted-branch-trust-region-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_weighted_branch_trust_region_design_admit_m1011_evaluator
- reason: M1010 designs margin-slack-weighted rejected-branch trust-region residual on M267/M264 rows 6 and 15 primary before any actor update

## Next Blocker

m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator
