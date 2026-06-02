# m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation Research Review

## Summary

- Generated at UTC: 20260602T200007Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: soft_boundary_env_support_implementation_pass
- Decision reason: M2441 adds opt-in soft-boundary env support with focused tests 4 passed preserving default offtrack behavior and observation shape no rollout repair training ranking verdict claims

## Hypothesis

Opt-in soft-boundary env support can enable metric-selected rollout while preserving default behavior and actor input contract.

## Lineage

- parent_checkpoint: not_applicable_soft_boundary_env_support
- parent_dataset: docs/m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design.md, docs/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.md, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design.json
- parent_objective: add env-level soft-boundary support required before metric-selected measured validation
- derived_from: m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design
- blocked_by: current env offtrack termination is hard-coded at abs(lateral_error) > track_width, fresh actual success under the selected metric needs executed rollout with soft-boundary continuation, track_width scaling would alter actor-visible road geometry and is not an acceptable proxy
- supersedes: direct measured rollout before soft-boundary env support, old-row relabel as actual success, track_width scaling as metric-selected validation
- invalidates: None

## Success Criteria

- soft-boundary env support is implemented behind opt-in config
- default offtrack behavior remains unchanged in focused tests
- enabled behavior continues inside tolerance and terminates beyond tolerance in focused tests
- actor observation shape remains unchanged
- no rollout repair training ranking actual-success or verdict claim is made

## Failure Criteria

- M2441 starts measured validation
- M2441 executes repair or training
- M2441 changes actor input contract
- M2441 changes default offtrack termination behavior
- M2441 treats old soft success as actual success
- M2441 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2441 must preserve default offtrack termination behavior
- M2441 must add opt-in soft-boundary continuation without actor input changes
- M2441 must add focused tests for default and enabled behavior
- M2441 must not run measured rollout, repair, train, rank candidates/controllers, select winners, or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run new measured rollout
- do not rerun reset
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not overwrite active configs
- do not change actor inputs
- do not inject hidden or oracle actor features
- do not rank candidate families
- do not rank controller families
- do not select a winner
- do not claim actual success improvement
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- metric_artifact
- lineage_invalid
- contract_violation
- scenario_sampling_failure

## Scoreboard

- milestone: m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation
- type: infrastructure
- checkpoint: docs/m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: soft_boundary_env_support_implementation_pass
- reason: M2441 adds opt-in soft-boundary env support with focused tests 4 passed preserving default offtrack behavior and observation shape no rollout repair training ranking verdict claims

## Next Blocker

m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation
