# m2167-paper-route-current-sim-measured-runner-adapter-design Research Review

## Summary

- Generated at UTC: 20260601T074242Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_measured_runner_adapter_design_admit_fake_rollout_implementation
- Decision reason: M2167 freezes current-sim runner adapter metadata contract aggregates fake-rollout tests and fail-closed checkpoint validation while blocking real rollout ranking paper FW-vs-GRU and self-ID claims

## Hypothesis

A focused current-sim measured runner adapter can preserve M2151 metadata and provide fake-rollout-tested infrastructure before expensive checkpoint materialization.

## Lineage

- parent_checkpoint: not_applicable_current_sim_measured_runner_adapter_design
- parent_dataset: docs/m2166-paper-route-current-sim-measured-readiness-inventory-result-audit.md, runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/summary.json, runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json, runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv
- parent_config: experiments/manifests/m2166-paper-route-current-sim-measured-readiness-inventory-result-audit.json
- parent_objective: design a current-sim-specific measured runner adapter before checkpoint repair
- derived_from: m2166-paper-route-current-sim-measured-readiness-inventory-result-audit
- blocked_by: M2166 chooses runner adapter design before checkpoint materialization
- supersedes: reusing old measured runner schemas, training checkpoints before runner output contract is fixed
- invalidates: None

## Success Criteria

- docs/m2167-paper-route-current-sim-measured-runner-adapter-design.md exists
- metadata fields are enumerated
- planned artifacts and pass gates are explicit
- focused fake-rollout tests are specified
- next implementation route is explicit
- no rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design document is missing
- metadata fields are ambiguous
- next route is ambiguous
- measured execution or policy action is run
- ranking or paper-level claims are made

## Evidence Gates

- M2167 must not implement or run measured execution
- M2167 must define current-sim runner metadata fields and aggregates
- M2167 must define fake-rollout focused tests before real rollout
- M2167 must keep ranking paper finite-window-vs-GRU and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit implementation code
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

- lineage_invalid

## Scoreboard

- milestone: m2167-paper-route-current-sim-measured-runner-adapter-design
- type: gate
- checkpoint: docs/m2167-paper-route-current-sim-measured-runner-adapter-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_measured_runner_adapter_design_admit_fake_rollout_implementation
- reason: M2167 freezes current-sim runner adapter metadata contract aggregates fake-rollout tests and fail-closed checkpoint validation while blocking real rollout ranking paper FW-vs-GRU and self-ID claims

## Next Blocker

m2167-paper-route-current-sim-measured-runner-adapter-design
