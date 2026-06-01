# M2173 Paper-Route Current-Sim Measured Execution Command Design

- status: completed
- decision: `current_sim_measured_execution_command_design_admit_implementation_and_run`
- manifest: `experiments/manifests/m2173-paper-route-current-sim-measured-execution-command-design.json`
- real M2151 measured execution in M2173: `false`
- policy actions executed in M2173: `false`
- training/replay/PPO in M2173: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2172 audits the checkpoint/profile materialization as clean. M2173 freezes the
exact measured-execution command for the next milestone. This milestone does
not run the command.

## Frozen Command

M2174 may run only this command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --workload runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv \
  --output-dir runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution \
  --eval-seed-base 217400 \
  --device cpu \
  --no-resume \
  --target-episode-count 320 \
  --target-spec-count 40 \
  --target-profile-count 8 \
  --next-blocker m2175-paper-route-current-sim-measured-execution-result-audit
```

Important details:

```text
workload source:
  runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv

not allowed:
  runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv
  because that workload has empty checkpoint_path cells.

output dir:
  runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution

eval seed base:
  217400

target episodes:
  320 = 40 specs x 8 profiles
```

## Pass Gates for M2174

M2174 should pass only if:

```text
episode_count == 320
failure_count == 0
spec_count == 40
profile_count == 8
metadata_missing_count == 0
metric_completeness_failure_count == 0
task_family_quota_pass == true
profile_quota_pass == true
history_representation_quota_pass == true
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

If the run fails, M2174 must still preserve failure rows and route to result
audit instead of retrying with changed configs.

## Claim Boundary

Allowed after a clean M2174 run:

```text
current-sim measured execution completed for the 320-cell profile/workload
panel.
```

Still not allowed after M2174 alone:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

Those require result audit and denominator-backed comparison protocol.

## Next Step

M2174 may execute the frozen command above. It must not alter checkpoint paths,
profile configs, actor inputs, task specs, workload rows, or target counts.
