# m1012-v4-public-base-margin-weighted-branch-repair-update-design Research Review

## Summary

- Generated at UTC: 20260526T184030Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: margin_weighted_branch_repair_update_design_admit_m1013_probe
- Decision reason: M1012 designs actor_mean-only temporal repair with M1011 wrong-branch trust residual lambda sweep 0.001 0.003 0.01 0.03 and strict trust gates before replay

## Hypothesis

A repaired actor_mean-only temporal update can be specified by combining the M997 temporal objective with the M1011 margin-weighted wrong-branch trust residual before any replay gate.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
- parent_dataset: docs/m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator.md, runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator/summary.json, runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator/margin_weighted_branch_rows.csv, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator.json
- parent_objective: design actor_mean-only temporal repair update with margin-weighted wrong-branch trust residual
- derived_from: m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator, m1010-v4-public-base-margin-weighted-branch-trust-region-design
- blocked_by: M1011 evaluator passes but no repaired actor update has been specified
- supersedes: None
- invalidates: temporal actor update without margin-weighted wrong-branch trust gate

## Success Criteria

- design document exists
- trainable surface is actor_mean only
- objective includes temporal exact terms and margin-weighted wrong-branch trust residual
- candidate gate order requires exact temporal gates before M267/M264 replay preflight
- PPO and promotion remain blocked

## Failure Criteria

- design changes actor inputs
- design trains non-actor_mean parameters
- design skips M1011 trust residual
- design routes directly to PPO or promotion

## Evidence Gates

- M1012 must not train
- M1012 must not run PPO
- M1012 must not promote
- M1012 must preserve P0 actor inputs
- M1012 must keep wrong-history anchors scoped as proof-retention constraints

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not use private holdout
- do not treat wrong-history failure as deployable behavior
- do not change actor input contract
- do not skip M267/M264 preflight in the later implementation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1012-v4-public-base-margin-weighted-branch-repair-update-design
- type: infrastructure
- checkpoint: docs/m1012-v4-public-base-margin-weighted-branch-repair-update-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_weighted_branch_repair_update_design_admit_m1013_probe
- reason: M1012 designs actor_mean-only temporal repair with M1011 wrong-branch trust residual lambda sweep 0.001 0.003 0.01 0.03 and strict trust gates before replay

## Next Blocker

m1013-v4-public-base-margin-weighted-branch-repair-update-probe
