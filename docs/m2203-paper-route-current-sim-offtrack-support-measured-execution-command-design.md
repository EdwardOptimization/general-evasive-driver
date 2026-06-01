# M2203 Paper-Route Current-Sim Offtrack-Support Measured-Execution Command Design

- status: completed
- decision: `current_sim_offtrack_support_measured_execution_command_design_admit_implementation_and_run`
- manifest: `experiments/manifests/m2203-paper-route-current-sim-offtrack-support-measured-execution-command-design.json`
- synthesis parent: `docs/m2202-paper-route-current-sim-offtrack-support-readiness-branch-synthesis.md`
- measured execution in M2203: `false`
- policy actions executed in M2203: `false`
- training/replay/PPO in M2203: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2202 synthesized the M2192-M2201 readiness branch and chose to continue to
measured-execution command design. M2203 freezes the exact measured-execution
command for the repaired offtrack-support panel. This milestone does not run
the command.

## Inputs

Executable specs:

```text
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json
```

Materialized workload:

```text
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv
```

Audited counts:

```text
executable specs: 288
workload rows / target episodes: 2304
profiles: 8
rows per profile: 288
checkpoint paths existing: 2304
missing checkpoint paths: 0
```

## Frozen Command

M2204 may run only this command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner \
  --executable-task-specs runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json \
  --workload runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv \
  --output-dir runs/m2204_paper_route_current_sim_offtrack_support_measured_execution \
  --eval-seed-base 220400 \
  --device cpu \
  --no-resume \
  --target-episode-count 2304 \
  --target-spec-count 288 \
  --target-profile-count 8 \
  --next-blocker m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit
```

Expected output:

```text
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/summary.json
```

## Pass Gates for M2204

M2204 should be considered an execution pass only if:

```text
episode_count == 2304
failure_count == 0
spec_count == 288
profile_count == 8
metadata_missing_count == 0
metric_completeness_failure_count == 0
task_family_quota_pass == true
profile_quota_pass == true
history_representation_quota_pass == true
all_selected_metrics_finite == true
guardrail_violation_count == 0
environment_rollout_started == true
policy_action_executed == true
measured_rollout_started == true
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If the run fails, M2204 must preserve failure rows and route to result audit
instead of retrying with changed configs.

## Claim Boundary

Allowed after a clean M2204 run:

```text
current-sim measured execution completed for the repaired 2304-cell
offtrack-support panel.
```

Still not allowed after M2204 alone:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

Those require result audit and denominator-backed comparison protocol.

## Next Step

M2204 may execute the frozen command above. It must not alter checkpoint paths,
profile configs, actor inputs, task specs, workload rows, or target counts.
