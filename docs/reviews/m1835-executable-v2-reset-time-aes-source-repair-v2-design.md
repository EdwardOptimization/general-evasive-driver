# m1835-executable-v2-reset-time-aes-source-repair-v2-design Research Review

## Summary

- Generated at UTC: 20260530T115252Z
- Type: gate
- Gate tier: process
- Promotion decision: reset_time_aes_source_repair_v2_design_admit_implementation
- Decision reason: M1835 designs reset-time AES-only source-level acceptance objective with 10000-attempt pass criterion and row/attempt aggregation requirements

## Hypothesis

A reset-time source repair v2 can be specified that searches for accepted AES-only candidates under require_aeb_infeasible for m1771-bp1-00 and m1771-bp1-02, while preserving profile controls and fixing attempt-count aggregation.

## Lineage

- parent_checkpoint: not_applicable_reset_time_aes_source_repair_v2_design
- parent_dataset: docs/m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit.md, runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_attempt_summary.csv, runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_reject_reason_counts.csv, runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_label_counts.csv
- parent_config: experiments/manifests/m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit.json
- parent_objective: design reset-time AES source repair v2 for the two persistent AES failure sources
- derived_from: m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit
- blocked_by: M1834 classifies M1833 as reset-time AES source support failure dominated by AEB-feasible rejection
- supersedes: offline-density-only AES repair, blind attempt-budget increase, reset rerun before source repair v2 design
- invalidates: None

## Success Criteria

- docs/m1835-executable-v2-reset-time-aes-source-repair-v2-design.md exists
- design targets m1771-bp1-00 and m1771-bp1-02
- design defines reset-time AES-only acceptance criteria and expected artifacts
- design treats offline density as diagnostic only
- design includes summary attempt-count aggregation requirements
- design routes to implementation or broader support redesign without running reset rollout measured rollout training replay PPO ranking or paper-level claims

## Failure Criteria

- design document is missing
- design omits one of the two persistent AES sources
- design uses offline density as the main acceptance objective
- design tunes profile-specific controls
- design runs reset or rollout
- design routes directly to measured execution or ranking
- design changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1835 must design source repair v2 against reset-time accepted AES-only candidates, not offline density alone
- M1835 must include explicit handling for M1834 summary aggregation weakness
- M1835 must keep reset rollout measured rollout training replay PPO promotion private holdout actor-input changes profile tuning ranking paper-level and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not run measured rollout
- do not execute policy actions
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change reward
- do not change dynamics
- do not change termination behavior
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m1835-executable-v2-reset-time-aes-source-repair-v2-design
- type: gate
- checkpoint: docs/m1835-executable-v2-reset-time-aes-source-repair-v2-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reset_time_aes_source_repair_v2_design_admit_implementation
- reason: M1835 designs reset-time AES-only source-level acceptance objective with 10000-attempt pass criterion and row/attempt aggregation requirements

## Next Blocker

m1836-executable-v2-reset-time-aes-source-repair-v2-implementation
