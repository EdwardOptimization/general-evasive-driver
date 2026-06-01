# M2199 Paper-Route Current-Sim Offtrack-Support Measured-Readiness Design

- status: completed
- decision: `current_sim_offtrack_support_measured_readiness_design_admit_implementation`
- manifest: `experiments/manifests/m2199-paper-route-current-sim-offtrack-support-measured-readiness-design.json`
- parent reset audit: `docs/m2198-paper-route-current-sim-offtrack-support-reset-validation-result-audit.md`
- parent workload: `runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/planned_workload.csv`
- profile checkpoints: `runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv`
- next manifest: `experiments/manifests/m2200-paper-route-current-sim-offtrack-support-measured-readiness-implementation.json`
- measured execution in M2199: `false`
- policy action executed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2199 freezes a no-rollout readiness step:

```text
M2194 repaired planned workload
  + M2171 profile checkpoint rows
  -> checkpoint-complete repaired measured workload
```

The readiness artifact must make measured execution possible later, but it must
not execute policies.

## Inputs

```text
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/planned_workload.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv
```

Expected input counts:

```text
planned_workload_row_count: 2304
profile_checkpoint_row_count: 8
profile_count: 8
workload rows per profile: 288
```

## Join Rule

Join by `profile_name`.

Each output workload row must copy all M2194 planned workload fields and add or
overwrite:

```text
checkpoint_path
checkpoint_exists
checkpoint_source_profile_name
checkpoint_materialization_mode
training_enabled_for_source_profile
actor_encoder
actor_history_length
env_history_length
observation_dim
input_contract
uses_hidden_oracle_actor_inputs
uses_wheel_or_slip_inputs
uses_reference_or_ttc_inputs
```

M2171 reset-control alias rule must be preserved:

```text
L3_reset_control checkpoint_source_profile_name = L3_online_gru
L3_reset_control checkpoint_path = L3_online_gru checkpoint_path
L3_reset_control reset_or_truncated_control = true
```

## Output Artifacts

M2200 should write:

```text
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/summary.json
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/profile_checkpoint_join_rows.csv
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/missing_checkpoint_rows.csv
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/claim_boundary.csv
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/run_state.json
```

Expected output counts:

```text
materialized_workload_count: 2304
target_workload_count: 2304
checkpoint_path_present_count: 2304
checkpoint_path_exists_count: 2304
checkpoint_path_missing_count: 0
profile_count: 8
profile_counts:
  each profile = 288
```

## Guardrails

Readiness must fail closed if:

```text
any workload row has no matching profile checkpoint row
any checkpoint_path is empty or missing on disk
any profile checkpoint row uses hidden/oracle actor inputs
any profile checkpoint row uses wheel/slip inputs
any profile checkpoint row uses reference/TTC inputs
profile_specific_tuning is true
controller-family ranking, winner selection, paper, FW-vs-GRU, or self-ID claim flag is true
```

Allowed claim:

```text
The repaired reset-valid workload is checkpoint-complete and ready for a
separate measured-execution command design.
```

Still blocked:

```text
measured execution
controller-family ranking
winner selection
finite-window vs GRU verdict
paper-level benchmark evidence
level3 self-identification
```

## Next Step

M2200 may implement and run this no-rollout measured-readiness materialization.
If M2200 passes, M2201 must audit readiness before measured-execution command
design.
