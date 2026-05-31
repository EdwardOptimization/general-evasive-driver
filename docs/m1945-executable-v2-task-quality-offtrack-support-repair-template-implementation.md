# M1945 Executable V2 Task-Quality Offtrack Support Repair Template Implementation

- status: completed
- decision: `task_quality_offtrack_support_repair_templates_pass_admit_source_mining_design`
- result class: `task_quality_offtrack_support_repair_templates_pass`
- branch: `paper_route_task_quality_offtrack_support_repair`
- implementation: `src/autodrift/executable_v2_task_quality_offtrack_support_repair_templates.py`
- focused tests: `2 passed`
- config artifact: `configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json`
- reset/rollout/measured execution in M1945: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_offtrack_support_repair_templates \
  --success-source-rows runs/m1942_executable_v2_task_quality_measured_outcome_localization/success_source_rows.csv \
  --comparison-support-candidates runs/m1942_executable_v2_task_quality_measured_outcome_localization/comparison_support_candidates.csv \
  --offtrack-dominance-rows runs/m1942_executable_v2_task_quality_measured_outcome_localization/offtrack_dominance_rows.csv \
  --output configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json
```

Return code:

```text
0
```

## Template Result

The generated artifact passes the M1944 no-rollout count gates:

```text
result_class: task_quality_offtrack_support_repair_templates_pass
candidate_source_count: 160 / 160

source_kind_counts:
  anchor_neighborhood: 64 / 64
  success_stabilizer: 48 / 48
  offtrack_boundary_relief: 32 / 32
  mitigation_isolation_check: 16 / 16

source_split_counts:
  public_debug: 96 / 96
  public_gate: 64 / 64
  paper_holdout_candidate: 0
```

Guardrails:

```text
labels_enter_actor_input_count: 0
v2_ranking_admissible_by_default_count: 0
profile_specific_tuning_count: 0
guardrail_violation_count: 0
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## What Changed

Before M1945, the off-track repair route was a design document. After M1945,
the route is executable as a deterministic no-rollout config artifact.

The config contains:

- anchor-neighborhood rows around the two M1942 candidate-support slices;
- success-stabilizer rows from existing successful source families;
- offtrack-boundary-relief rows from high-offtrack/low-collision slices;
- mitigation-isolation rows to keep tier E out of success ranking.

This is still task-quality infrastructure. It does not run the simulator and
does not make a controller-performance claim.

## Supported Claims

M1945 supports:

- the off-track support repair template generator exists and is tested;
- the repair candidate panel has exact pre-registered counts;
- no labels enter actor input;
- no profile tuning, ranking, paper claim, or level3 self-ID claim is made.

## Unsupported Claims

Still unsupported:

- whether the repaired templates produce better task support;
- whether off-track rate falls below the comparison threshold;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1946-executable-v2-task-quality-offtrack-support-repair-source-mining-design
```

M1946 should design the source-mining/preflight step that turns the 160
template rows into source-quality evidence. It should still not run measured
execution, controller ranking, training, replay, PPO, or self-ID tests.
