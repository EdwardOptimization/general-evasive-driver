# m1830-executable-v2-reset-time-aes-sampler-diagnostic-design Research Review

## Summary

- Generated at UTC: 20260530T112923Z
- Type: gate
- Gate tier: process
- Promotion decision: reset_time_aes_sampler_diagnostic_design_admit_implementation
- Decision reason: M1830 designs reset-time AES sampler diagnostics and admits helper implementation

## Hypothesis

A targeted diagnostic can specify the reset-time observables needed to explain why M1825 AES candidates have offline density but fail M1828 reset sampling.

## Lineage

- parent_checkpoint: not_applicable_reset_time_aes_sampler_diagnostic_design
- parent_dataset: docs/m1829-paper-route-executable-v2-targeted-reset-validation-branch-synthesis.md, runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/summary.json, runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv, runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
- parent_config: experiments/manifests/m1829-paper-route-executable-v2-targeted-reset-validation-branch-synthesis.json
- parent_objective: design reset-time AES sampler diagnostics before further source repair
- derived_from: m1829-paper-route-executable-v2-targeted-reset-validation-branch-synthesis
- blocked_by: M1829 pivots from targeted reset validation to reset-time AES sampler diagnostics
- supersedes: blind source-range widening after M1828, additional reset rerun without sampler diagnostic, measured execution before reset support
- invalidates: None

## Success Criteria

- docs/m1830-executable-v2-reset-time-aes-sampler-diagnostic-design.md exists
- design targets the two AES failure sources
- design lists reset-time sampler observables and offline-density comparators
- design states whether implementation or execution design is next
- no reset rollout measured rollout training replay PPO ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- design omits the two AES failure sources
- design runs reset or rollout
- design routes directly to measured execution or ranking
- design changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1830 must design a diagnostic for the two persistent AES reset-time sampler failures
- M1830 must compare reset-time sampler assumptions against M1825 offline density assumptions
- M1830 must keep reset rollout measured rollout training replay PPO promotion private holdout actor-input changes profile tuning ranking paper-level and level3 claims blocked

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
- metric_artifact

## Scoreboard

- milestone: m1830-executable-v2-reset-time-aes-sampler-diagnostic-design
- type: gate
- checkpoint: docs/m1830-executable-v2-reset-time-aes-sampler-diagnostic-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reset_time_aes_sampler_diagnostic_design_admit_implementation
- reason: M1830 designs reset-time AES sampler diagnostics and admits helper implementation

## Next Blocker

m1831-executable-v2-reset-time-aes-sampler-diagnostic-implementation
