# M1921 Executable V2 Task-Quality Scenario Redesign Template Implementation

- status: completed
- decision: `task_quality_scenario_template_implementation_pass_admit_source_mining_execution_design`
- branch: `paper_route_task_quality_scenario_redesign`
- source: `src/autodrift/executable_v2_task_quality_scenario_redesign_templates.py`
- tests: `tests/test_executable_v2_task_quality_scenario_redesign_templates.py`
- generated template: `configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json`
- focused tests: `4 passed`
- source mining/reset/rollout/measured execution in M1921: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M1921 implements a deterministic first-wave candidate-template generator for
the task-quality scenario redesign branch.

The template generator writes:

```text
configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json
```

and records:

```text
template_id: task_quality_scenario_redesign_candidates_v0
scenario_quality_branch_id: paper_route_task_quality_scenario_redesign
candidate_row_count: 640
feasibility_tier_count: 5
role_count: 4
surface_count: 2
speed_bucket_count: 4
mu_bucket_count: 4
source_mining_execution_started: false
materialized_row_count: 0
```

## Template Counts

The generated config satisfies the M1920 first-wave design:

```text
feasibility tiers:
  tier_a_positive_support_sanity: 128
  tier_b_feasible_emergency: 128
  tier_c_boundary_near_miss: 128
  tier_d_handling_limit_drift_required: 128
  tier_e_mitigation_only: 128

roles:
  stable_aeb: 160
  stable_aes_only: 160
  drift_required_recovery: 160
  unavoidable_mitigation: 160

surfaces:
  steady_surface: 320
  post_friction_step: 320

speed buckets:
  12.0: 160
  18.0: 160
  24.0: 160
  30.0: 160

mu buckets:
  0.25: 160
  0.40: 160
  0.60: 160
  0.80: 160
```

Split counts:

```text
public_debug: 384
public_gate: 192
paper_holdout_candidate: 64
```

Claim-boundary counts:

```text
positive_support_gate_required_count: 512
expected_joint_support_count: 512
expected_near_miss_support_count: 512
mitigation_only_count: 128
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
guardrail_violation_count: 0
```

## Validation

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_scenario_redesign_templates.py
```

Result:

```text
4 passed
```

Template generation command:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_scenario_redesign_templates \
  --output configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json
```

## Supported Claims

Supported:

- deterministic 640-row candidate template generation is implemented;
- scenario-quality tiers, fresh splits, actor-input guards, and ranking blocks
  are represented in the template artifact;
- source-mining execution can now be designed against a concrete template.

Unsupported:

- source-mining result;
- positive-support existence;
- task-quality scenario success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1922-executable-v2-task-quality-scenario-redesign-source-mining-execution-design
```

M1922 should register the exact source-mining execution command and pass gates
for the generated template. It should still not run reset, rollout, measured
execution, training, replay, PPO, controller ranking, paper-level claims, or
level3 self-ID claims.
