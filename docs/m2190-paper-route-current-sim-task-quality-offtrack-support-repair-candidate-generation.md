# M2190 Paper-Route Current-Sim Task-Quality Offtrack Support Repair Candidate Generation

- status: completed
- decision: `current_sim_task_quality_offtrack_support_repair_candidate_generation_pass_route_to_required_synthesis`
- manifest: `experiments/manifests/m2190-paper-route-current-sim-task-quality-offtrack-support-repair-candidate-generation.json`
- summary: `runs/m2190_paper_route_current_sim_task_quality_offtrack_support_repair_candidates/summary.json`
- candidate config: `configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json`
- focused tests: `2 passed`
- training in M2190: `false`
- reset in M2190: `false`
- measured execution in M2190: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Ran

M2190 implements:

```text
src/autodrift/paper_route_current_sim_task_quality_offtrack_support_repair_candidates.py
tests/test_paper_route_current_sim_task_quality_offtrack_support_repair_candidates.py
```

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_task_quality_offtrack_support_repair_candidates \
  --original-episodes runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/episode_rows.csv \
  --repeat-episodes runs/m2184_paper_route_current_sim_repeat_measured_execution/episode_rows.csv \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --output-dir runs/m2190_paper_route_current_sim_task_quality_offtrack_support_repair_candidates \
  --candidate-config configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json
```

## Result

```text
result_class: current_sim_task_quality_offtrack_support_repair_candidate_generation_pass
candidate_count: 288
expected_candidate_count: 288
duplicate_candidate_id_count: 0
boolean_guardrail_violation_count: 0
profile_specific_candidate_count: 0
actor_input_contract_change_count: 0
exact_axis_quota_pass: true
exact_split_quota_pass: true
```

Axis counts:

```text
offtrack_saturation_relief: 96
terminal_boundary_support_ladder: 64
older_history_ambiguity_support_ladder: 64
diagnostic_warmup_support_ladder: 32
positive_support_preservation: 32
```

Split counts:

```text
public_debug: 176
public_gate: 112
```

Artifacts:

```text
runs/m2190_paper_route_current_sim_task_quality_offtrack_support_repair_candidates/summary.json
runs/m2190_paper_route_current_sim_task_quality_offtrack_support_repair_candidates/repair_candidate_rows.csv
runs/m2190_paper_route_current_sim_task_quality_offtrack_support_repair_candidates/parent_task_support_rows.csv
configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json
```

## Claim Boundary

Allowed claim:

```text
The project now has a deterministic no-rollout 288-candidate task-quality /
offtrack-support repair wave.
```

Still blocked:

```text
candidate reset validation;
candidate materialization;
measured execution;
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2191 must synthesize the current-sim repeat/offtrack-support branch before any
candidate audit, materialization, reset, or rollout. If that synthesis continues
the branch, the next implementation can audit or materialize the candidate
artifact under the synthesis decision.
