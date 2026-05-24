# m540-matched-history-training-variance-design Research Review

## Summary

- Generated at UTC: 20260524T033932Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: matched_training_variance_design_admit_m541_variance_config_family
- Decision reason: M540 defines a staged matched 4096-step variance ladder and separate L3-vs-L0/L3-vs-L2 pass rules after broad L2 seed counterexample

## Hypothesis

Because M539 shows a broad seed-3531 L2-over-L3 counterexample, the next research step should pre-register a matched training-variance escalation before running longer baselines or fresh holdout claims.

## Lineage

- parent_checkpoint: runs/m532_matched_l0_short_train_seed3530/checkpoint.pt, runs/m532_matched_l2_short_train_seed3530/checkpoint.pt, runs/m532_matched_l3_short_train_seed3530/checkpoint.pt, runs/m533_matched_l0_short_train_seed3531/checkpoint.pt, runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt, runs/m533_matched_l0_short_train_seed3532/checkpoint.pt, runs/m533_matched_l2_short_train_seed3532/checkpoint.pt, runs/m533_matched_l3_short_train_seed3532/checkpoint.pt
- parent_dataset: runs/m539_matched_history_seed_fragility_audit/summary.json, runs/m538_natural_surface_paired_advantage_audit/summary.json
- parent_config: configs/ppo_m531_matched_l0_short_train.json, configs/ppo_m531_matched_l2_short_train.json, configs/ppo_m531_matched_l3_short_train.json
- parent_objective: design matched L0/L2/L3 training-variance escalation after L2 seed counterexample
- derived_from: m539-matched-history-seed-fragility-audit
- blocked_by: m539-matched-history-seed-fragility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- defines matched seeds budgets configs and eval order for L0 L2 L3
- defines public diagnostic gates and later fresh-holdout boundary
- defines pass/fail thresholds for L3 over L0 and L3 over L2 separately
- defines how to classify finite-window sufficiency versus recurrent instability
- research validation passes

## Failure Criteria

- design allows per-history-level tuning before comparison
- design ignores the seed-3531 L2 counterexample
- design treats M537/M538 public rows as private evidence

## Evidence Gates

- pre-registered identical-budget L0/L2/L3 variance ladder
- included per-seed public paired diagnostics from M537/M538
- defined when L3 beats L2 versus when finite-window history remains competitive
- did not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune one history level independently before comparison
- do not discard L2 because aggregate M537 favored L3
- do not promote any short-train baseline from public diagnostics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m540-matched-history-training-variance-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: matched_training_variance_design_admit_m541_variance_config_family
- reason: M540 defines a staged matched 4096-step variance ladder and separate L3-vs-L0/L3-vs-L2 pass rules after broad L2 seed counterexample

## Next Blocker

m541-matched-history-variance-config-family
