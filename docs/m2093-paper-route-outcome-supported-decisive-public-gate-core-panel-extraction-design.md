# M2093 Paper-Route Outcome-Supported Decisive Public-Gate Core Panel Extraction Design

- status: completed
- decision: `public_gate_core_panel_extraction_design_admit_no_reset_materialization`
- parent synthesis: `docs/m2092-paper-route-outcome-supported-decisive-reset-valid-core-reset-validation-result-audit.md`
- source reset artifact: `runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight/reset_rows.csv`
- reset/rollout/measured execution in M2093: `false`
- policy actions executed in M2093: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2092 pivots away from preserving public-debug generated rows. M2093 defines a
public-gate-only core panel from rows that are reset-success rows in M2091.

The inclusion rule is:

```text
include a task iff:
  M2091 reset_success == true
  source_split == public_gate

exclude all public_debug rows
do not change obstacle filters
do not re-sample tasks
do not run environment reset
```

This yields:

```text
input rows: 238
included public-gate rows: 96
excluded rows: 142
```

## Coverage

Family counts in the public-gate core:

```text
T3_active_diagnostic_warmup: 24
T4_variable_diagnostic_delay: 36
T5_terminal_boundary_near_constraint: 36
```

The public-gate core excludes all T1 and T2 rows. This is an intentional smoke
panel, not a full task-distribution panel.

Difficulty-axis counts remain balanced:

```text
early|nominal|high|actuator_delay|nominal: 8
early|nominal|high|low_mu|nominal: 8
early|nominal|high|mixed_mu|nominal: 8
early|nominal|high|nominal_mu|nominal: 8
late|generous|moderate|actuator_delay|low: 8
late|generous|moderate|low_mu|low: 8
late|generous|moderate|mixed_mu|low: 8
late|generous|moderate|nominal_mu|low: 8
medium|tight|straight_or_low|actuator_delay|high: 8
medium|tight|straight_or_low|low_mu|high: 8
medium|tight|straight_or_low|mixed_mu|high: 8
medium|tight|straight_or_low|nominal_mu|high: 8
```

Dynamics counts:

```text
actuator_delay: 24
low_mu: 24
mixed_mu: 24
nominal_mu: 24
```

Source-kind counts:

```text
actuator_delay_terminal_boundary: 6
delayed_obstacle_reveal_response: 6
late_terminal_boundary_margin: 6
long_delay_steer_lag_evidence: 6
low_grip_terminal_boundary: 6
medium_delay_yaw_evidence: 6
mixed_dynamics_terminal_boundary: 6
near_zero_clearance_margin: 6
short_delay_brake_evidence: 6
stale_evidence_boundary_check: 6
tight_road_terminal_boundary: 6
variable_delay_mixed_authority: 6
warmup_brake_authority_probe: 4
warmup_combined_brake_steer_probe: 4
warmup_steering_lag_probe: 4
warmup_terminal_recovery_probe: 4
warmup_throttle_release_response: 4
warmup_yaw_authority_probe: 4
```

## Implementation Route

M2094 should implement a no-reset selector that:

```text
1. loads M2088 reset-valid core executable task specs;
2. loads M2091 reset_rows.csv and reset_failure_rows.csv;
3. includes only rows with source_split == public_gate and reset_success == true;
4. preserves env_config and metadata exactly for included rows;
5. writes a public-gate core executable spec JSON/CSV;
6. writes excluded rows and coverage distribution artifacts;
7. writes a planned sentinel workload from the included specs and existing profile artifacts;
8. writes a claim boundary and summary.
```

Expected artifacts:

```text
public_gate_core_executable_task_specs.json
public_gate_core_executable_task_specs.csv
public_gate_core_excluded_rows.csv
public_gate_core_planned_sentinel_workload.csv
public_gate_core_distribution_by_family.csv
public_gate_core_distribution_by_split.csv
public_gate_core_distribution_by_axis.csv
public_gate_core_distribution_by_dynamics_band.csv
public_gate_core_distribution_by_source_kind.csv
claim_boundary.csv
summary.json
```

M2094 must not:

```text
change obstacle filters;
run environment reset;
run rollout or policy actions;
run measured execution;
rank controller families;
make paper-level or self-ID claims.
```

## Pass Gates

M2094 passes only if:

```text
input_executable_spec_count == 238
input_reset_row_count == 238
public_gate_core_executable_spec_count == 96
excluded_spec_count == 142
public_gate_included_count == 96
public_gate_excluded_count == 0
public_debug_included_count == 0
env_config_changed_count == 0
metadata_missing_count == 0
contract_violation_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
planned_sentinel_workload_count == 480
dynamics_counts == {actuator_delay: 24, low_mu: 24, mixed_mu: 24, nominal_mu: 24}
axis_count_min == 8
axis_count_max == 8
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Claim Boundary

M2093 supports only:

```text
a public-gate-only reset-stable core panel extraction route is specified.
```

M2093 does not support:

```text
full task-distribution coverage;
fresh reset validity beyond existing M2085/M2091 evidence;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2094-paper-route-outcome-supported-decisive-public-gate-core-panel-extraction-implementation
```
