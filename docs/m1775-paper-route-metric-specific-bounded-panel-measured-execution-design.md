# M1775 Paper-Route Metric-Specific Bounded Panel Measured Execution Design

- status: completed
- decision: `bounded_panel_measured_execution_design_admit_adapter_implementation`
- parent audit: `docs/m1774-paper-route-metric-specific-bounded-panel-reset-result-audit.md`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1775 designs the measured execution route for the M1771 metric-specific
bounded panel. The panel is reset-feasible, but the existing scenario-taxonomy
execution module should not be used directly without adaptation because it is
hard-coded around the broader 72-spec / 864-cell taxonomy.

This design admits a bounded-panel execution adapter implementation before any
measured rollout.

## Fixed Inputs

Bounded panel specs:

```text
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json
```

Bounded panel matrix:

```text
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_matrix.csv
```

Reset feasibility summary:

```text
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/summary.json
```

Preflight facts checked before this design:

```text
bounded panel specs: 24
workload rows: 288
profiles: 12
role panels: 4
reset successes: 288
sampling failures: 0
guardrail violations: 0
```

## Executor Compatibility Audit

The existing `task_quality_scenario_taxonomy_execution` module is useful as a
reference, but it is not directly compatible with the bounded panel:

- its scenario-spec loader accepts taxonomy payload keys, not
  `bounded_panel_specs`;
- its pass criteria are hard-coded for `864` episodes, `72` specs, and `6`
  scenario families;
- it expects the taxonomy unsupported-feature file and target unsupported
  feature count;
- its aggregate names are scenario-taxonomy centric and do not expose
  role-panel aggregates as first-class outputs;
- direct reuse would blur bounded-panel evidence with the older full-taxonomy
  execution branch.

Therefore the next milestone should implement a bounded-panel measured
execution adapter instead of forcing the old executor through an incompatible
interface.

## Execution Protocol To Implement

The adapter should run exactly these inputs:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.metric_specific_bounded_panel_measured_execution \
  --bounded-panel-specs runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json \
  --bounded-panel-matrix runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_matrix.csv \
  --output-dir runs/m1777_metric_specific_bounded_panel_measured_execution \
  --eval-seed-base 177700 \
  --device cpu \
  --no-resume \
  --next-blocker m1778-paper-route-metric-specific-bounded-panel-measured-execution-result-audit
```

M1776 should implement and test the adapter. M1777 should run the measured
execution only after M1776 passes.

## Required Pass Criteria For M1777

Measured execution should pass only if:

- `episode_count == 288`;
- `failure_count == 0`;
- `profile_count == 12`;
- `bounded_panel_spec_count == 24`;
- `role_panel_count == 4`;
- `guardrail_violation_count == 0`;
- selected legacy rollout metrics are finite where applicable;
- bounded-panel metadata fields are present in every episode row;
- role-panel aggregate, metric-family aggregate, sampled-label aggregate,
  outcome aggregate, and metric-completeness artifacts are written;
- `metric_completeness_passed == true`;
- `metric_completeness_failure_count == 0`;
- no training, replay, PPO, promotion, private holdout, actor-input change,
  reward change, termination change, profile-specific tuning, ranking claim,
  paper-level claim, or level3 self-ID claim occurs.

## Required Artifacts For M1777

The measured execution should write:

```text
summary.json
episode_rows.csv
failure_rows.csv
run_state.json
profile_aggregate.csv
role_panel_aggregate.csv
scenario_family_aggregate.csv
scenario_role_aggregate.csv
evaluation_role_aggregate.csv
primary_metric_family_aggregate.csv
hidden_dynamics_bucket_aggregate.csv
road_boundary_bucket_aggregate.csv
obstacle_timing_bucket_aggregate.csv
obstacle_lateral_bucket_aggregate.csv
sampled_obstacle_label_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
profile_outcome_aggregate.csv
role_panel_outcome_aggregate.csv
primary_metric_family_outcome_aggregate.csv
role_panel_sampled_label_aggregate.csv
profile_hidden_dynamics_worst_bucket.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

The bounded-panel adapter may reuse existing helper functions for profile
loading, rollout execution, outcome aggregation, and metric completeness, but
its summary targets must be bounded-panel targets, not full-taxonomy targets.

## Interpretation Boundary

M1777 may claim only that the bounded-panel measured execution completed or
failed under the pre-registered gates. It must not interpret controller-family
rank, recurrent advantage, paper-level benchmark quality, private-holdout
evidence, or level3 self-identification.

If M1777 passes, route to a result audit before any ranking or paper claim. If
it fails, route to failure audit or runner repair depending on whether the
failure is sampling, metric completeness, artifact completeness, or guardrail
related.

## Guardrails

- environment reset started in M1775: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- a bounded-panel measured execution protocol is defined;
- existing taxonomy executor incompatibility is identified before rollout;
- adapter implementation is the correct next step.

Unsupported:

- measured rollout success;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1776 bounded-panel execution adapter implementation.
