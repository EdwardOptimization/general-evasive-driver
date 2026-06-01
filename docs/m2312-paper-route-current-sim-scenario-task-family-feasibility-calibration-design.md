# M2312 Paper-Route Current-Sim Scenario Task-Family Feasibility Calibration Design

- status: completed
- decision: `feasibility_calibration_design_admit_support_policy_panel_implementation`
- manifest: `experiments/manifests/m2312-paper-route-current-sim-scenario-task-family-feasibility-calibration-design.json`
- parent synthesis: `docs/m2311-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.md`
- reset/rollout/policy action in M2312: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Question

M2311 closed the same-support guarded-v2 repair branch. M2312 changes the
question from repair tuning to support calibration:

```text
Is the 72-spec role-family task pack feasible, calibrated, and supportable
enough to be a fair training/evaluation target?
```

The next evidence must separate:

```text
task infeasibility or over-aggressive geometry;
scenario support imbalance;
current actor weakness under feasible tasks;
metric artifacts around offtrack/collision/recovery semantics;
collision/offtrack tradeoffs that require role-specific constraints.
```

## Diagnostic Boundary

Support policies are allowed only as diagnostic support bounds. They are not
candidate controllers and must not be ranked.

Use three support policies:

```text
aeb:
  full braking support bound for R0/AEB-feasible rows.

aes:
  simple emergency steering with braking support bound for stable AES geometry.

envelope_aes:
  privileged friction-envelope support bound. It may read simulator info such
  as mu through the policy info path, so it is not deployable and not a
  controller-family candidate.
```

All support-policy rows must carry:

```text
diagnostic_only: true
ranking_admissible: false
controller_family_ranking_claim_made: false
winner_selected: false
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
```

## Execution Panel

M2313 should implement and run one diagnostic support panel:

```text
scenario specs: 72
support policies: 3
seed repeats per support policy/spec: 5
episodes: 72 * 3 * 5 = 1080
eval_seed_base: 231300
config: configs/paper_route_current_sim_scenario_task_family_v0.json
output_dir: runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_feasibility_calibration \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration \
  --eval-seed-base 231300 \
  --support-policies aeb aes envelope_aes \
  --seed-repeats 5 \
  --target-scenario-spec-count 72 \
  --target-support-policy-count 3 \
  --target-episode-count 1080 \
  --next-blocker m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit
```

M2313 may run environment reset, rollout, measured policy action, and support
policy execution. It must not train, replay, use PPO, promote, use private
holdout, rank profiles, select a winner, or make paper/self-ID claims.

## Required Artifacts

M2313 should write:

```text
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/summary.json
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/support_aggregate_rows.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/role_support_summary.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/claim_boundary.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/run_state.json
```

The runner should preserve scenario metadata from the config:

```text
scenario_spec_id
scenario_family_id
role_family
sampled_obstacle_label
allowed_labels_metadata_only
same_scene_group_id
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
initial_speed_mps
track_radius_m
track_width_m
actor_contract_id
```

It should add support metadata:

```text
support_policy_name
support_policy_kind
support_policy_uses_privileged_info
support_policy_deployable_candidate
seed_repeat_index
eval_seed
diagnostic_only
ranking_admissible
```

## Support Labels

For each `scenario_spec_id`, M2313 should assign one diagnostic label:

```text
support_clear:
  at least one support policy succeeds in >= 3 / 5 repeats without increasing
  collision beyond the policy's own repeats.

support_mixed:
  at least one support policy succeeds in 1-2 repeats, or policies disagree
  strongly between collision and offtrack.

support_blocked:
  no support policy succeeds in any repeat, or all successful-like rows are
  dominated by collision/offtrack termination.

metric_conflict:
  support policies produce high clearance or obstacle completion but still
  terminate offtrack/collision in a way that suggests metric semantics need an
  audit.
```

For each role family, M2313 should aggregate:

```text
support_clear_count
support_mixed_count
support_blocked_count
metric_conflict_count
support_success_rate_by_policy
support_collision_rate_by_policy
support_offtrack_rate_by_policy
```

## Pass/Fail Gates

M2313 passes as an execution artifact if:

```text
episode_count == 1080
scenario_spec_count == 72
support_policy_count == 3
seed_repeat_count == 5
failure_count == 0
metadata_missing_count == 0
metric_completeness_failure_count == 0
guardrail_violation_count == 0
ranking_admissible_count == 0
winner_selected == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

M2313 does not pass or fail based on support success rate. Low support success
is a result to audit, not a harness failure.

## Interpretation Rules

M2314 should interpret M2313 with these rules:

```text
support_clear + checkpoint failure:
  likely actor/training weakness on a feasible task.

support_blocked + checkpoint failure:
  likely task infeasibility, over-aggressive geometry, or missing support
  policy coverage.

metric_conflict:
  route to metric/termination semantics audit before training.

support_mixed:
  route to role-specific scenario calibration or additional support-policy
  bounds before controller-family comparison.
```

The audit must not rank `aeb`, `aes`, and `envelope_aes`. It may only use them
to label scenario support.

## Follow-Up

Pre-register:

```text
experiments/manifests/m2313-paper-route-current-sim-scenario-task-family-feasibility-calibration-implementation.json
```
