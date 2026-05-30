# m1827-executable-v2-stable-source-repaired-targeted-reset-execution-design Research Review

## Summary

- Generated at UTC: 20260530T111617Z
- Type: gate
- Gate tier: process
- Promotion decision: stable_source_repaired_targeted_reset_execution_design_admit_preflight_run
- Decision reason: M1827 fixes exact repaired reset-only command over the M1825 repaired payload and admits M1828 preflight

## Hypothesis

The M1825 repaired payload can be targeted by an exact M1792-compatible reset-only preflight command with fixed target counts and guardrails.

## Lineage

- parent_checkpoint: not_applicable_repaired_targeted_reset_execution_design
- parent_dataset: docs/m1826-executable-v2-stable-source-targeted-reset-sampler-repair-result-audit.md, runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
- parent_config: experiments/manifests/m1826-executable-v2-stable-source-targeted-reset-sampler-repair-result-audit.json
- parent_objective: pre-register exact reset-only command over repaired targeted reset payload
- derived_from: m1826-executable-v2-stable-source-targeted-reset-sampler-repair-result-audit
- blocked_by: M1826 admits repaired reset-only design but exact command has not been registered
- supersedes: direct repaired reset rerun without command registration, measured execution before reset support, controller-family ranking before executable reset validation
- invalidates: None

## Success Criteria

- docs/m1827-executable-v2-stable-source-repaired-targeted-reset-execution-design.md exists
- design lists exact command input payload output directory target counts and next blocker
- design targets 36 specs, 12 profiles, 1 role surface, 36 reset-ready specs, and zero expected guardrail violations
- design keeps reset measured execution and ranking blocked
- next route is explicit
- no reset rollout measured rollout training replay PPO ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- design runs reset or rollout
- design omits target counts or output directory
- design routes directly to measured execution or ranking
- design changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1827 must fix exact M1792-compatible reset-only command over the M1825 repaired payload
- M1827 must pre-register target counts and next output directory
- M1827 must keep reset rollout measured rollout training replay PPO promotion private holdout actor-input changes profile tuning ranking paper-level and level3 claims blocked

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

- milestone: m1827-executable-v2-stable-source-repaired-targeted-reset-execution-design
- type: gate
- checkpoint: docs/m1827-executable-v2-stable-source-repaired-targeted-reset-execution-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: stable_source_repaired_targeted_reset_execution_design_admit_preflight_run
- reason: M1827 fixes exact repaired reset-only command over the M1825 repaired payload and admits M1828 preflight

## Next Blocker

m1828-executable-v2-stable-source-repaired-targeted-reset-feasibility-preflight
