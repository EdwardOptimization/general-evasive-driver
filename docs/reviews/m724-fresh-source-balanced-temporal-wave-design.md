# m724-fresh-source-balanced-temporal-wave-design Research Review

## Summary

- Generated at UTC: 20260524T204145Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: manual_review
- Decision reason: no structured gates defined

## Hypothesis

A fresh no-training temporal command-response wave with source-balanced pair selection can remove the M719/M722 seed-concentration bottleneck and produce a better basis for outcome boundary mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m723-temporal-boundary-sparse-audit.md, runs/m722_temporal_action_boundary_outcome_miner/summary.json, runs/m722_temporal_action_boundary_outcome_miner/source_rows.csv, runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv, runs/m719_temporal_action_response_mismatch/intervention_rollouts.csv
- parent_config: experiments/manifests/m723-temporal-boundary-sparse-audit.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: design fresh source-balanced temporal command-response wave after M722 source concentration audit
- derived_from: m723-temporal-boundary-sparse-audit
- blocked_by: m723-temporal-boundary-sparse-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M724 defines source-balanced selection axes and quotas
- M724 defines required M725 implementation artifacts
- M724 keeps temporal action and outcome gates separate
- M724 defines sentinel allocation and diversity thresholds
- no training PPO actor update or promotion occurs

## Failure Criteria

- design only increases max_pairs without source balancing
- design treats action-only rows as outcome proof
- design omits sentinel allocation
- design admits PPO or promotion
- design changes actor input contract

## Evidence Gates

- design fixes M719 max_pairs early-seed saturation with source-balanced selection
- design includes per-seed per-fault-family and source-role quotas
- design preserves temporal action and outcome gates separately
- design carries sentinel allocation into the wave rather than adding sentinels after the fact
- design keeps actor input contract unchanged
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat M722 action-only rows as source-positive
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels or oracle values to actor observations
- do not simply raise max_pairs without source balancing

## Failure Taxonomy

- none

## Scoreboard

- milestone: m724-fresh-source-balanced-temporal-wave-design
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

m725-source-balanced-temporal-wave-implementation
