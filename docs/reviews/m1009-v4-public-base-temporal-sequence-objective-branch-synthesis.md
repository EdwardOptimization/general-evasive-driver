# m1009-v4-public-base-temporal-sequence-objective-branch-synthesis Research Review

## Summary

- Generated at UTC: 20260526T181209Z
- Type: gate
- Gate tier: process
- Promotion decision: temporal_sequence_objective_branch_synthesis_continue_to_margin_weighted_trust_region_design
- Decision reason: M1009 synthesizes M999-M1008: exact temporal movement is real but replay retention fails; continue branch with margin-weighted rejected-branch trust-region design

## Hypothesis

M999-M1008 should be synthesized before another temporal objective repair because exact temporal improvement and public replay retention currently conflict.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
- parent_dataset: runs/m997_v4_public_base_temporal_sequence_corpus_export/summary.json, runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/summary.json, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/summary.json, runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator/summary.json, docs/m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit.md
- parent_config: experiments/manifests/m998-v4-public-base-capability-step-fault-generation-synthesis.json, experiments/manifests/m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit.json
- parent_objective: synthesize M999-M1008 temporal sequence objective branch before continuing
- derived_from: m999-v4-public-base-temporal-sequence-objective-design, m1000-v4-public-base-temporal-sequence-objective-evaluator, m1001-v4-public-base-temporal-sequence-objective-update-design, m1002-v4-public-base-temporal-sequence-objective-update-probe, m1003-v4-public-base-temporal-sequence-update-public-replay-gate-design, m1004-v4-public-base-temporal-sequence-update-public-replay-gate, m1005-v4-public-base-temporal-sequence-update-replay-failure-audit, m1006-v4-public-base-branch-preserving-temporal-repair-design, m1007-v4-public-base-branch-preserving-temporal-repair-evaluator, m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit
- blocked_by: workflow synthesis cadence reached after M999-M1008 branch work
- supersedes: None
- invalidates: continuing temporal objective local repairs without branch synthesis

## Success Criteria

- synthesis artifact exists
- supported and falsified claims are explicit
- failure taxonomy is explicit
- public gate overfit risk is updated
- next branch decision is explicit
- no training or promotion occurs

## Failure Criteria

- synthesis artifact is missing
- route decision is missing
- M1002 is overclaimed as replay-valid
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1009 must synthesize M999-M1008
- M1009 must not train
- M1009 must not run PPO
- M1009 must not promote
- M1009 must decide whether to continue with margin-weighted repair, pivot, or stop

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not skip synthesis cadence
- do not overclaim M1002 exact candidates as replay-valid
- do not use private holdout
- do not promote a checkpoint
- do not run PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1009-v4-public-base-temporal-sequence-objective-branch-synthesis
- type: gate
- checkpoint: docs/m1009-v4-public-base-temporal-sequence-objective-branch-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_objective_branch_synthesis_continue_to_margin_weighted_trust_region_design
- reason: M1009 synthesizes M999-M1008: exact temporal movement is real but replay retention fails; continue branch with margin-weighted rejected-branch trust-region design

## Next Blocker

m1010-v4-public-base-margin-weighted-branch-trust-region-design
