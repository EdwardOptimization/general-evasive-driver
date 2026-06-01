# m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design Research Review

## Summary

- Generated at UTC: 20260601T111325Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_measured_runner_repeat_metadata_activation_repair_design_admit_implementation
- Decision reason: M2206 designs repeat activation by identity fields while checkpoint_materialization_mode remains checkpoint provenance and partial repeat identity metadata remains fail-closed no implementation rerun ranking paper FW-vs-GRU or self-ID claims

## Hypothesis

The M2204 failure can be repaired by changing repeat-mode activation in the measured runner so checkpoint_materialization_mode alone is accepted for non-repeat workloads while partial repeat identity metadata still fails closed.

## Lineage

- parent_checkpoint: not_applicable_repair_design_only
- parent_dataset: docs/m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit.md, runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/summary.json, runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/validation_failure_rows.csv, src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py, docs/m2181-paper-route-current-sim-repeat-measured-runner-metadata-extension-implementation.md
- parent_config: experiments/manifests/m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit.json
- parent_objective: design repeat metadata activation compatibility repair before code changes or rerun
- derived_from: m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit
- blocked_by: M2205 classifies M2204 as repeat metadata activation overreach
- supersedes: adding fake repeat IDs to non-repeat workload rows, removing checkpoint_materialization_mode provenance
- invalidates: None

## Success Criteria

- docs/m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design.md exists
- repeat activation fields are specified
- checkpoint_materialization_mode preservation is specified
- partial repeat identity metadata fail-closed behavior is specified
- focused tests are specified
- no implementation rerun ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design document is missing
- design weakens repeat metadata preservation
- design requires fake repeat IDs
- design removes checkpoint provenance
- implementation or rerun occurs

## Evidence Gates

- M2206 must define repeat-mode activation fields
- M2206 must preserve checkpoint_materialization_mode as non-repeat provenance
- M2206 must keep partial repeat identity metadata fail-closed
- M2206 must define focused tests
- M2206 must not implement, rerun, or rank

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not add fake repeat IDs to non-repeat workload rows
- do not remove checkpoint_materialization_mode provenance
- do not rank controller families
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design
- type: gate
- checkpoint: docs/m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_measured_runner_repeat_metadata_activation_repair_design_admit_implementation
- reason: M2206 designs repeat activation by identity fields while checkpoint_materialization_mode remains checkpoint provenance and partial repeat identity metadata remains fail-closed no implementation rerun ranking paper FW-vs-GRU or self-ID claims

## Next Blocker

m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design
