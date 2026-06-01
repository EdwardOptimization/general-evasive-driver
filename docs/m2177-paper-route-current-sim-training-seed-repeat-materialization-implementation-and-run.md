# M2177 Paper-Route Current-Sim Training-Seed Repeat Materialization Implementation and Run

- status: completed
- decision: `current_sim_training_seed_repeat_materialization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2177-paper-route-current-sim-training-seed-repeat-materialization-implementation-and-run.json`
- implementation: `src/autodrift/paper_route_current_sim_training_seed_repeat_materialization.py`
- tests: `tests/test_paper_route_current_sim_training_seed_repeat_materialization.py`
- focused tests: `2 passed`
- run artifact: `runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/summary.json`
- measured execution in M2177: `false`
- policy actions executed for measured execution: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2177 implemented and ran the training-seed repeat materializer.

The run passed:

```text
result_class = current_sim_training_seed_repeat_materialization_pass
repeat_group_count = 3
existing_repeat_group_count = 1
new_repeat_group_count = 2
new_training_command_count = 14
successful_training_command_count = 14
failed_training_command_count = 0
new_materialized_workload_count = 640
checkpoint_path_missing_count = 0
checkpoint_path_exists_count = 640
reset_control_trained_count = 0
guardrail_violation_count = 0
```

Repeat groups:

```text
repeat_0_existing:
  source = runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv
  materialized rows = 320
  checkpoint paths existing = 320

repeat_1_seed_21761:
  new training commands = 7
  materialized rows = 320
  checkpoint paths existing = 320

repeat_2_seed_21762:
  new training commands = 7
  materialized rows = 320
  checkpoint paths existing = 320
```

`L3_reset_control` remains a same-repeat alias to `L3_online_gru`. It does not
train separately in either new repeat group.

## Artifacts

M2177 wrote:

```text
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/summary.json
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/repeat_group_rows.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/profile_checkpoint_rows.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/repeats/repeat_1_seed_21761/materialized_workload.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/repeats/repeat_2_seed_21762/materialized_workload.csv
```

The combined new-repeat workload has `640` data rows plus one header row.

## Claim Boundary

Supported:

```text
The two additional current-sim training-seed repeat groups are materialized
with existing checkpoint paths.
```

Still unsupported:

```text
repeat measured execution results;
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2178 must audit the repeat materialization output before any repeat measured
execution command is designed.
