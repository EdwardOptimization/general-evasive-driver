# m728-quota-calibrated-source-balanced-temporal-wave-implementation Research Review

## Summary

- Generated at UTC: 20260524T211601Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_balanced_temporal_action_only
- Decision reason: M728 runs 3951 source-balanced pairs with 2613 temporal action-critical rows across 351 seeds but only 1 outcome row so source export PPO and promotion remain blocked

## Hypothesis

Removing the M725 per-step-bucket cap artifact can produce a full source-balanced 4096-pair temporal wave without changing actor inputs or training.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m727-quota-calibrated-source-balanced-temporal-wave-design.md, docs/m726-source-balanced-temporal-wave-audit.md, runs/m725_source_balanced_temporal_wave/summary.json
- parent_config: experiments/manifests/m727-quota-calibrated-source-balanced-temporal-wave-design.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: run a no-training quota-calibrated source-balanced temporal wave
- derived_from: m727-quota-calibrated-source-balanced-temporal-wave-design
- blocked_by: m727-quota-calibrated-source-balanced-temporal-wave-design
- supersedes: None
- invalidates: None

## Success Criteria

- M728 runs the registered quota-calibrated command
- M728 writes registered run artifacts
- M728 reports source-balance temporal action outcome and sentinel metrics
- M728 keeps action and outcome evidence separate
- actor checksum remains unchanged
- no training PPO actor update or promotion occurs

## Failure Criteria

- runner selects fewer than target pairs without classified quota evidence
- runner omits sentinel rows
- runner combines action-only and outcome-positive claims
- runner changes actor input contract
- runner starts optimizer training PPO or checkpoint promotion

## Evidence Gates

- selected_pair_count reaches the registered target or failure cause is recorded
- source-balance metrics pass or are classified
- temporal action and outcome rows are reported separately
- sentinel false-positive rate is reported
- actor checksum remains unchanged
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower M727 thresholds after seeing M728 output
- do not treat action-only rows as outcome proof
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels or oracle values to actor observations

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m728-quota-calibrated-source-balanced-temporal-wave-implementation
- type: infrastructure
- checkpoint: runs/m728_quota_calibrated_source_balanced_temporal_wave/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_temporal_action_only
- reason: M728 runs 3951 source-balanced pairs with 2613 temporal action-critical rows across 351 seeds but only 1 outcome row so source export PPO and promotion remain blocked

## Next Blocker

m729-quota-calibrated-source-balanced-temporal-wave-audit
