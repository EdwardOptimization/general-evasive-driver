# M1980 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Repair Template Implementation

- status: completed
- decision: `task_quality_calibrated_outcome_support_repair_templates_pass_route_to_audit`
- result class: `task_quality_calibrated_outcome_support_repair_templates_pass`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_outcome_support_repair_templates.py`
- focused tests: `2 passed`
- compile check: `python -m compileall -q src tests`
- artifact: `configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json`
- reset/rollout/measured execution in M1980: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_calibrated_outcome_support_repair_templates.py
```

Result:

```text
2 passed
```

Template generation:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_outcome_support_repair_templates \
  --localization-summary runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json \
  --output configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json \
  --next-blocker m1981-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-result-audit
```

Return code:

```text
0
```

## Pass Gate Result

The generated artifact passes the M1979 quota and guardrail gates:

```text
result_class: task_quality_calibrated_outcome_support_repair_templates_pass
candidate_source_count: 192
guardrail_violation_count: 0
labels_enter_actor_input_count: 0
v2_ranking_admissible_by_default_count: 0
profile_specific_tuning_count: 0
paper_holdout_candidate_count: 0
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
```

Repair-axis quotas:

```text
offtrack_anchor_relief: 64
offtrack_boundary_relief_extension: 32
success_support_expansion: 48
collision_mitigation_relief: 32
mitigation_metric_isolation: 16
```

Split quotas:

```text
public_debug: 112
public_gate: 80
paper_holdout_candidate: 0
```

Additional schema sanity:

```text
unknown parent_feasibility_tier_id count: 0
unknown parent_source_role_semantics count: 0
unknown parent_normalized_surface_variant count: 0
unknown parent_sampled_obstacle_label count: 0
```

## What Changed

M1980 adds a deterministic template generator that reads M1977 localization
artifacts through the localization summary and materializes a bounded repair
wave. It does not run reset, rollout, measured execution, replay, PPO, or any
controller-family comparison.

The template axes follow M1979:

```text
offtrack_anchor_relief:
  repair anchor-neighborhood offtrack-only support.

offtrack_boundary_relief_extension:
  extend the explicit offtrack-boundary relief sentinel family.

success_support_expansion:
  expand around existing successful public diagnostic rows.

collision_mitigation_relief:
  add bounded severity relief around collision-dominated mitigation rows.

mitigation_metric_isolation:
  keep mitigation diagnostics separate from obstacle-pass ranking.
```

## Supported Claims

M1980 supports:

- a no-rollout calibrated outcome-support repair template artifact exists;
- the artifact has the intended `192` candidate count and repair-axis quotas;
- the artifact preserves public-debug/public-gate split and uses no holdout;
- no labels enter actor inputs and no ranking/paper/self-ID claims are made;
- the artifact is ready for audit before source mining or materialization.

## Unsupported Claims

Still unsupported:

- reset validity of the repair templates;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- high-fidelity validation readiness.

## Next

Next milestone:

```text
m1981-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-result-audit
```

M1981 should audit the template artifact before source mining, materialization,
reset validation, or measured execution.
