# M2056 Paper-Route Controlled Routing Smoke Task-Quality Repaired Measured Execution Implementation And Run

- status: completed
- decision: `controlled_routing_smoke_task_quality_repaired_measured_execution_pass_route_to_result_audit`
- result class: `controlled_routing_smoke_measured_execution_pass`
- runner: `autodrift.paper_route_controlled_routing_smoke_measured_runner`
- focused tests: `3 passed`
- summary: `runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/summary.json`
- measured execution in M2056: `true`
- rollout/policy actions in M2056: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_measured_runner.py
```

Result:

```text
3 passed
```

Frozen measured-execution command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_measured_runner \
  --executable-task-specs runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json \
  --workload runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution \
  --eval-seed-base 205600 \
  --device cpu \
  --target-episode-count 2304 \
  --target-spec-count 192 \
  --target-profile-count 12 \
  --next-blocker m2057-paper-route-controlled-routing-smoke-task-quality-repaired-measured-execution-result-audit
```

Result:

```text
result_class=controlled_routing_smoke_measured_execution_pass
episode_count=2304
failure_count=0
metric_completeness_failure_count=0
guardrail_violation_count=0
```

## Execution Gates

M2056 passes the registered execution and metadata gates:

```text
episode_count: 2304 / 2304
failure_count: 0
spec_count: 192 / 192
profile_count: 12 / 12
metadata_missing_count: 0
metric_completeness_failure_count: 0
all_selected_metrics_finite: true
family_quota_pass: true
source_kind_quota_pass: true
proxy_template_quota_pass: true
generated_proxy_quota_pass: true
guardrail_violation_count: 0
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
```

Guarded false flags remain false:

```text
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
```

## Raw Outcomes

Raw outcome counts are recorded for the next audit:

```text
success_obstacle_pass: 45
collision_failure: 14
off_track_noncollision_noncompletion: 2245
```

Profile-level success rates:

```text
L0_current_masked: 1 / 192
L1_one_step: 1 / 192
L2_window_13: 0 / 192
L2_window_25: 0 / 192
L2_window_50: 0 / 192
L2_window_100: 0 / 192
L2 current-tiled controls: 0 / 768 total
L3_online_gru: 26 / 192
L3_reset_control_corrected: 17 / 192
```

These are execution artifacts only. M2056 does not rank controller families,
does not make a finite-window-vs-GRU conclusion, and does not claim paper-level
evidence or self-identification.

## Supported Claims

Supported:

```text
The repaired 2304-row routing-smoke workload executed completely.
The runner preserved metadata and metric completeness.
The repaired measured-execution artifact is ready for result audit.
```

Unsupported:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
paper-valid generated task semantics;
level3 self-identification.
```

## Next

M2057 must audit the measured-execution outcome distribution before candidate
qualification, ranking, localization, task-quality repair, or any paper-level
claim.
