# m1745-paper-route-task-quality-outcome-metric-instrumentation-design Research Review

## Summary

- Generated at UTC: 20260530T044542Z
- Type: gate
- Gate tier: process
- Promotion decision: metric_instrumentation_design_admit_logging_only_implementation
- Decision reason: M1745 defines all seven M1743 metric gaps as bounded logging-only metric routes and admits implementation before any rollout

## Hypothesis

The explicit M1743 metric gaps can be converted into bounded metric definitions and instrumentation routes before implementation or rerun.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m1744-paper-route-task-quality-outcome-semantics-materialization-preflight-result-audit.md, runs/m1743_task_quality_outcome_semantics_materialization_preflight/unsupported_metric_gaps.csv, runs/m1743_task_quality_outcome_semantics_materialization_preflight/metric_support.csv, runs/m1743_task_quality_outcome_semantics_materialization_preflight/outcome_semantics_registry.csv
- parent_config: experiments/manifests/m1744-paper-route-task-quality-outcome-semantics-materialization-preflight-result-audit.json
- parent_objective: design metric definitions and instrumentation route for explicit M1743 metric gaps
- derived_from: m1744-paper-route-task-quality-outcome-semantics-materialization-preflight-result-audit
- blocked_by: direct execution is blocked until benchmark-critical recovery and drift metrics are defined or instrumented
- supersedes: direct revised-semantics execution with unsupported metric approximations
- invalidates: None

## Success Criteria

- docs/m1745-paper-route-task-quality-outcome-metric-instrumentation-design.md exists
- all seven M1743 metric gaps have proposed definitions and data requirements
- each metric is classified as existing-row computable evaluator time-series logging or environment instrumentation
- next route is implementation preflight bounded-panel design branch synthesis or stop
- environment rollout training replay PPO promotion private holdout actor-input changes ranking and level3 claims remain blocked

## Failure Criteria

- design document is missing
- one or more M1743 metric gaps are omitted
- data requirements are ambiguous
- design admits execution while benchmark-critical gaps remain unresolved
- environment rollout training replay PPO private holdout promotion or actor-input changes occur
- paper-level or level3 claims are made

## Evidence Gates

- M1745 must define metric semantics for all seven M1743 gaps
- M1745 must separate metric definition from implementation and rollout
- M1745 must decide whether each metric is computable from existing rows, requires evaluator time-series logging, or requires env instrumentation
- M1745 must not run environment rollout train replay PPO promote use private holdout change actor inputs tune profiles rank controller families or claim paper-level evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune profiles
- do not rank controller families
- do not treat unsupported metric gaps as covered
- do not implement instrumentation in the design milestone
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1745-paper-route-task-quality-outcome-metric-instrumentation-design
- type: gate
- checkpoint: docs/m1745-paper-route-task-quality-outcome-metric-instrumentation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: metric_instrumentation_design_admit_logging_only_implementation
- reason: M1745 defines all seven M1743 metric gaps as bounded logging-only metric routes and admits implementation before any rollout

## Next Blocker

m1746-paper-route-task-quality-outcome-metric-instrumentation-implementation
