# m1007-v4-public-base-branch-preserving-temporal-repair-evaluator Research Review

## Summary

- Generated at UTC: 20260526T175533Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: branch_preserving_temporal_repair_evaluator_not_sensitive_route_to_evaluator_sensitivity_audit
- Decision reason: M1007 no-update evaluator is finite base-safe and reproduces M1000 but alpha 0.01 branch loss remains zero despite M1004 proof washout on rows 6 and 15

## Hypothesis

A no-update evaluator can expose branch-ceiling and branch-separation penalties that are near zero for M974 but positive for M1002 proof-washing candidates.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
- parent_dataset: docs/m1006-v4-public-base-branch-preserving-temporal-repair-design.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/m1002_temporal_a0_01/boundary_replay_rows.csv
- parent_config: experiments/manifests/m1006-v4-public-base-branch-preserving-temporal-repair-design.json
- parent_objective: implement a no-update branch-preserving temporal repair evaluator
- derived_from: m1006-v4-public-base-branch-preserving-temporal-repair-design
- blocked_by: M1006 requires evaluator sanity before any repaired actor update
- supersedes: None
- invalidates: actor update before branch-ceiling evaluator sanity

## Success Criteria

- summary.json exists
- M974 base branch metrics are finite
- M1002 alpha 0.01 and alpha 0.2 activate branch-retention penalties
- M997 temporal metrics still reproduce M1000
- actor parameters are unchanged
- ppo_used == false
- promoted == false

## Failure Criteria

- evaluator changes actor parameters
- branch metrics are non-finite
- M1002 proof-washing candidates are not distinguishable from base
- PPO starts
- promotion occurs

## Evidence Gates

- M1007 must not update actor parameters
- M1007 must not run PPO
- M1007 must not promote
- M1007 must preserve P0 actor inputs
- M1007 must show branch-ceiling terms are active on M1002 proof-washing candidates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not imitate wrong-history degraded actions
- do not use private holdout
- do not run replay gates as promotion evidence
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1007-v4-public-base-branch-preserving-temporal-repair-evaluator
- type: infrastructure
- checkpoint: runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: branch_preserving_temporal_repair_evaluator_not_sensitive_route_to_evaluator_sensitivity_audit
- reason: M1007 no-update evaluator is finite base-safe and reproduces M1000 but alpha 0.01 branch loss remains zero despite M1004 proof washout on rows 6 and 15

## Next Blocker

m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit
