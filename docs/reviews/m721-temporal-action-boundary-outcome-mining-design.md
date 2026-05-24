# m721-temporal-action-boundary-outcome-mining-design Research Review

## Summary

- Generated at UTC: 20260524T202302Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: manual_review
- Decision reason: no structured gates defined

## Hypothesis

M719's temporal action deltas can become outcome-critical near obstacle/boundary decision surfaces; a no-training local boundary miner can find those rows without changing actor inputs or training.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m720-temporal-action-only-audit.md, runs/m719_temporal_action_response_mismatch/summary.json, runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv, runs/m719_temporal_action_response_mismatch/intervention_rollouts.csv
- parent_config: experiments/manifests/m720-temporal-action-only-audit.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: design no-training miner that converts temporal action sensitivity into outcome-critical rows
- derived_from: m720-temporal-action-only-audit
- blocked_by: m720-temporal-action-only-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M721 defines source selection from M719 temporal action-critical rows
- M721 defines local obstacle/boundary perturbation variables and limits
- M721 defines normal-history retention and temporal mismatch outcome gates
- M721 names M722 implementation artifacts
- no training PPO actor update or promotion occurs

## Failure Criteria

- design treats action-only rows as already outcome-positive
- design omits normal-history retention
- design lacks source diversity gates
- design admits PPO or promotion
- design changes actor input contract

## Evidence Gates

- design starts from M719 temporal action-sensitive rows without treating them as outcome proof
- design defines local obstacle timing lateral offset or boundary-margin search
- acceptance requires temporal action delta and margin/success degradation
- source diversity and normal-history retention gates are explicit
- actor input contract remains unchanged
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim action-only rows are source-positive outcome rows
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not add oracle labels hidden params or fault labels to actor observations
- do not tune obstacle variants after seeing private holdout outcomes

## Failure Taxonomy

- none

## Scoreboard

- milestone: m721-temporal-action-boundary-outcome-mining-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: manual_review
- reason: no structured gates defined

## Next Blocker

m722-temporal-action-boundary-outcome-miner-implementation
