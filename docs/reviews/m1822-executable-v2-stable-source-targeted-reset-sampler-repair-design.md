# m1822-executable-v2-stable-source-targeted-reset-sampler-repair-design Research Review

## Summary

- Generated at UTC: 20260530T105626Z
- Type: gate
- Gate tier: process
- Promotion decision: stable_source_targeted_reset_sampler_repair_design_admit_no_reset_planner
- Decision reason: M1822 designs source-level no-reset sampler repair planner for systematic AES and sparse AEB failures

## Hypothesis

A source-level sampler repair can be designed for the M1820 failures without profile-specific tuning or actor-input changes.

## Lineage

- parent_checkpoint: not_applicable_targeted_reset_sampler_repair_design
- parent_dataset: docs/m1821-executable-v2-stable-source-targeted-reset-feasibility-result-audit.md, runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/summary.json, runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/sampling_failure_rows.csv
- parent_config: experiments/manifests/m1821-executable-v2-stable-source-targeted-reset-feasibility-result-audit.json
- parent_objective: design source-level sampler repair for M1820 targeted reset failures
- derived_from: m1821-executable-v2-stable-source-targeted-reset-feasibility-result-audit
- blocked_by: M1821 classifies M1820 failure as systematic AES sampler infeasibility plus sparse AEB seed sampling failure
- supersedes: profile-specific reset repair, direct measured execution before reset support, controller-family ranking before reset support
- invalidates: None

## Success Criteria

- docs/m1822-executable-v2-stable-source-targeted-reset-sampler-repair-design.md exists
- design separates systematic AES repair from sparse AEB seed repair
- design preserves all 12 profile controls
- design keeps labels out of actor input and ranking blocked
- next implementation or rematerialization route is explicit
- no reset rollout measured rollout training replay PPO ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- design runs reset or rollout
- design proposes profile-specific tuning
- design admits measured execution or ranking before reset support
- design changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1822 must design a source-level sampler repair without running reset
- M1822 must address systematic AES failures and sparse AEB seed failures separately
- M1822 must preserve profile controls labels-out-of-actor and ranking blocks
- M1822 must keep rollout measured rollout training replay PPO promotion private holdout actor-input changes profile tuning ranking paper-level and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not run measured rollout
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

## Scoreboard

- milestone: m1822-executable-v2-stable-source-targeted-reset-sampler-repair-design
- type: gate
- checkpoint: docs/m1822-executable-v2-stable-source-targeted-reset-sampler-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: stable_source_targeted_reset_sampler_repair_design_admit_no_reset_planner
- reason: M1822 designs source-level no-reset sampler repair planner for systematic AES and sparse AEB failures

## Next Blocker

m1823-executable-v2-stable-source-targeted-reset-sampler-repair-implementation
