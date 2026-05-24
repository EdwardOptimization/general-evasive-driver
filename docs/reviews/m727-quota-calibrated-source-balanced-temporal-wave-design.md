# m727-quota-calibrated-source-balanced-temporal-wave-design Research Review

## Summary

- Generated at UTC: 20260524T210306Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: quota_calibrated_wave_design_admit_m728
- Decision reason: M727 preserves the 4096 selected-pair target and fixes the M725 step-bucket cap artifact while keeping action outcome gates and no-training constraints separate

## Hypothesis

M725 source_balance_blocked can be addressed by calibrating selection quotas rather than changing the actor or training objective.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m726-source-balanced-temporal-wave-audit.md, docs/m725-source-balanced-temporal-wave-implementation.md, runs/m725_source_balanced_temporal_wave/summary.json, runs/m725_source_balanced_temporal_wave/pair_proposals.csv, runs/m725_source_balanced_temporal_wave/selected_pair_proposals.csv, runs/m725_source_balanced_temporal_wave/variant_summary.csv
- parent_config: experiments/manifests/m726-source-balanced-temporal-wave-audit.json, experiments/manifests/m725-source-balanced-temporal-wave-implementation.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: design quota-calibrated source-balanced temporal wave after M725 selected-pair cap blockage
- derived_from: m726-source-balanced-temporal-wave-audit
- blocked_by: m726-source-balanced-temporal-wave-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M727 documents the exact M725 quota overconstraint
- M727 defines calibrated source-balance thresholds and run command
- M727 keeps source-balance pass separate from outcome proof
- M727 blocks source export actor update PPO and promotion
- M727 admits only a no-training M728 implementation

## Failure Criteria

- design treats M725 action rows as closed-loop outcome proof
- design removes source-balance checks to force a pass
- design changes actor input contract
- design admits PPO or checkpoint promotion

## Evidence Gates

- M727 identifies the quota caps that blocked M725
- M727 defines calibrated caps that can reach the registered selected-pair target
- M727 keeps action and outcome gates separate
- M727 preserves sentinel and source-balance checks
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower thresholds after seeing M727 implementation output
- do not treat action-only temporal rows as outcome proof
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m727-quota-calibrated-source-balanced-temporal-wave-design
- type: infrastructure
- checkpoint: docs/m727-quota-calibrated-source-balanced-temporal-wave-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: quota_calibrated_wave_design_admit_m728
- reason: M727 preserves the 4096 selected-pair target and fixes the M725 step-bucket cap artifact while keeping action outcome gates and no-training constraints separate

## Next Blocker

m728-quota-calibrated-source-balanced-temporal-wave-implementation
