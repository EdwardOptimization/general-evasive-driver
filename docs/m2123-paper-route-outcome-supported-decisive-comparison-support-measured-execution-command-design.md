# M2123 Paper-Route Outcome-Supported Decisive Comparison-Support Measured Execution Command Design

- status: completed
- decision: `comparison_support_measured_execution_command_design_admit_branch_synthesis_before_implementation`
- parent specs: `runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json`
- parent workload: `runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/planned_workload.csv`
- reset/rollout/measured execution in M2123: `false`
- policy actions executed in M2123: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Constraint

M2122 admits measured-execution design because the M2118 panel is reset-valid.
However, M2123 must not run the old controlled routing-smoke runner directly:
that runner reports old panel metadata fields, while this branch must preserve:

```text
comparison_support_intent
target_support_tier
dynamics_band
obstacle_timing_band
road_width_band
initial_speed_band
materialization_semantics=comparison_support_smoke_proxy
```

The measured runner should therefore be comparison-support-specific and reuse
the same low-level rollout path while keeping the new metadata and claim
boundary intact. However, the comparison-support scenario-redesign branch has
now reached its workflow-synthesis cadence, so the next milestone must be a
branch synthesis before implementation.

## Frozen Command

After the required synthesis, the measured-execution implementation milestone
must implement and run exactly:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_measured_runner \
  --executable-task-specs runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json \
  --workload runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution \
  --eval-seed-base 212300 \
  --device cpu \
  --target-episode-count 1200 \
  --target-spec-count 240 \
  --target-profile-count 5 \
  --next-blocker m2126-paper-route-outcome-supported-decisive-comparison-support-measured-execution-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_outcome_supported_decisive_comparison_support_measured_runner.py
```

## Planned Artifacts

The measured-execution implementation milestone must write:

```text
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/summary.json
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/episode_rows.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/failure_rows.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/validation_failure_rows.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/metadata_missing_rows.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/metric_completeness_failures.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/profile_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/intent_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/target_support_tier_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/source_kind_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/proxy_template_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/outcome_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/termination_reason_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/claim_boundary.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/run_state.json
```

## Pass Gates

The measured-execution implementation milestone passes only if:

```text
result_class == comparison_support_measured_execution_pass
episode_count == 1200
failure_count == 0
spec_count == 240
profile_count == 5
metadata_missing_count == 0
validation_failure_count == 0
metric_completeness_failure_count == 0
intent_quota_pass == true
target_support_tier_quota_pass == true
source_kind_quota_pass == true
proxy_template_quota_pass == true
generated_proxy_quota_pass == true
guardrail_violation_count == 0
```

A clean measured execution is still not a comparison. The follow-up audit must
inspect the artifact and route to outcome localization before any profile
interpretation.

## Claim Boundary

Supported after a clean measured-execution run:

```text
the reset-valid comparison-support panel has complete measured rollout artifacts
for the fixed 5-profile workload.
```

Unsupported:

```text
profile ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2124-paper-route-outcome-supported-decisive-comparison-support-scenario-redesign-branch-synthesis
```
