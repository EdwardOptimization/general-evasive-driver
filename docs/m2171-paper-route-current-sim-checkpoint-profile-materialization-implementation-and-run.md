# M2171 Paper-Route Current-Sim Checkpoint/Profile Materialization Implementation and Run

- status: completed
- decision: `current_sim_checkpoint_profile_materialization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2171-paper-route-current-sim-checkpoint-profile-materialization-implementation-and-run.json`
- implementation: `src/autodrift/paper_route_current_sim_checkpoint_profile_materialization.py`
- tests: `tests/test_paper_route_current_sim_checkpoint_profile_materialization.py`
- focused tests: `2 passed`
- run artifact: `runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json`
- real M2151 measured execution: `false`
- measured rollout started: `false`
- policy actions executed for measured execution: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2171 implemented the current-sim checkpoint/profile materializer and ran the
frozen M2170 materialization route.

The run passed:

```text
result_class = current_sim_checkpoint_profile_materialization_pass
profile_count = 8
trainable_profile_count = 7
alias_profile_count = 1
training_command_count = 7
successful_training_command_count = 7
failed_training_command_count = 0
materialized_workload_count = 320
checkpoint_path_present_count = 320
checkpoint_path_missing_count = 0
checkpoint_path_exists_count = 320
guardrail_violation_count = 0
```

`L3_reset_control` did not train a separate checkpoint. It aliases the
`L3_online_gru` checkpoint:

```text
checkpoint_materialization_mode = alias_same_weights_reset_hidden_control
checkpoint_source_profile_name = L3_online_gru
training_started_for_profile = false
```

This preserves the intended reset-control comparison: same weights, different
evaluation-time hidden-state policy.

## Artifacts

M2171 wrote:

```text
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/claim_boundary.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/run_state.json
```

The materialized workload preserves the M2151 workload fields and fills the
previously empty `checkpoint_path` column.

## Claim Boundary

Supported:

```text
The current-sim comparison panel now has materialized checkpoint paths for all
320 M2151 workload rows.
```

Supported:

```text
The 8-profile checkpoint panel is internally consistent under the M2170
fairness rule: 7 trainable profiles use their frozen configs, and
L3_reset_control reuses L3_online_gru weights.
```

Still unsupported:

```text
driver performance;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2172 must audit the materialization result before any real measured execution
command is designed. Direct measured execution remains blocked until that audit
checks the output workload, checkpoint alias policy, and claim boundary.
