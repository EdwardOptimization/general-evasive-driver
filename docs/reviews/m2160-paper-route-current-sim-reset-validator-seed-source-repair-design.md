# m2160-paper-route-current-sim-reset-validator-seed-source-repair-design Research Review

## Summary

- Generated at UTC: 20260601T063206Z
- Type: gate
- Gate tier: process
- Promotion decision: reset_validator_seed_source_repair_design_admit_implementation_and_run
- Decision reason: M2160 freezes reset-validator repair to prefer per-spec eval_seed_override and log seed_source actual_eval_seed before full reset rerun no reset executed no ranking paper FW-vs-GRU or self-ID claims

## Hypothesis

A reset-validator seed-source repair can preserve M2151 materialization semantics by using per-spec eval_seed_override when present and falling back to eval_seed_base+index only when missing.

## Lineage

- parent_checkpoint: not_applicable_current_sim_reset_validator_seed_source_repair_design
- parent_dataset: docs/m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit.md, runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/summary.json, runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/diagnostic_rows.csv, runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json
- parent_config: experiments/manifests/m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit.json
- parent_objective: design reset-validation seed-source repair using per-spec eval_seed_override
- derived_from: m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit
- blocked_by: M2159 audits M2154 failure as seed-source mismatch
- supersedes: raising terminal-boundary max_sample_attempts as the primary repair, rerunning full reset validation with eval_seed_base_plus_index seeds
- invalidates: None

## Success Criteria

- docs/m2160-paper-route-current-sim-reset-validator-seed-source-repair-design.md exists
- seed-source repair rule is explicit
- planned artifacts include seed_source and actual_eval_seed fields
- full-panel rerun command is explicit
- next implementation/run route is explicit
- no reset rerun rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design document is missing
- seed-source rule is ambiguous
- next route is ambiguous
- reset rerun rollout measured execution ranking or paper-level claims are made

## Evidence Gates

- M2160 must freeze the reset-validator seed-source repair rule
- M2160 must not edit implementation code or rerun reset
- M2160 must preserve current-sim metadata and actor-input claim boundaries
- M2160 must define the exact full-panel rerun command for the implementation milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit implementation code
- do not rerun reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact
- scenario_sampling_failure

## Scoreboard

- milestone: m2160-paper-route-current-sim-reset-validator-seed-source-repair-design
- type: gate
- checkpoint: docs/m2160-paper-route-current-sim-reset-validator-seed-source-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reset_validator_seed_source_repair_design_admit_implementation_and_run
- reason: M2160 freezes reset-validator repair to prefer per-spec eval_seed_override and log seed_source actual_eval_seed before full reset rerun no reset executed no ranking paper FW-vs-GRU or self-ID claims

## Next Blocker

m2161-paper-route-current-sim-reset-validator-seed-source-repair-implementation-and-run
