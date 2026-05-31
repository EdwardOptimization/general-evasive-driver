# M2087 Paper-Route Outcome-Supported Decisive Reset-Valid Core Panel Reduction Design

- status: completed
- decision: `reset_valid_core_panel_reduction_design_admit_no_reset_materialization`
- parent synthesis: `docs/m2086-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-result-audit.md`
- source reset artifact: `runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/reset_rows.csv`
- reset/rollout/measured execution in M2087: `false`
- policy actions executed in M2087: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2086 closes the local obstacle-filter repair loop. M2087 therefore does not
try to repair the two remaining reset-failed rows. It defines a reduced core
panel directly from the M2085 reset-success rows.

The inclusion rule is:

```text
include a task iff M2085 reset_success == true
exclude a task iff M2085 reset_success == false
do not change obstacle filters
do not re-sample tasks
do not run environment reset
```

This yields:

```text
input rows: 240
included reset-valid rows: 238
excluded reset-failed rows: 2
```

## Excluded Rows

Excluded rows:

```text
m2063-osd-osd_v0_0002_t1
m2063-osd-osd_v0_0049_t2
```

Both excluded rows are:

```text
source_split: public_debug
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
dynamics_band: low_mu
initial_speed_band: low
```

## Coverage After Reduction

The reduced core preserves all public-gate rows:

```text
public_gate: 96
public_debug: 142
private_holdout: 0
```

Family counts after reduction:

```text
T1_reactive_active_safety: 47
T2_same_current_different_older_history: 59
T3_active_diagnostic_warmup: 60
T4_variable_diagnostic_delay: 36
T5_terminal_boundary_near_constraint: 36
```

Axis coverage after reduction:

```text
early|nominal|high|actuator_delay|nominal: 20
early|nominal|high|low_mu|nominal: 20
early|nominal|high|mixed_mu|nominal: 20
early|nominal|high|nominal_mu|nominal: 20
late|generous|moderate|actuator_delay|low: 20
late|generous|moderate|low_mu|low: 18
late|generous|moderate|mixed_mu|low: 20
late|generous|moderate|nominal_mu|low: 20
medium|tight|straight_or_low|actuator_delay|high: 20
medium|tight|straight_or_low|low_mu|high: 20
medium|tight|straight_or_low|mixed_mu|high: 20
medium|tight|straight_or_low|nominal_mu|high: 20
```

The only coverage loss is two public-debug rows in the
`late|generous|moderate|low_mu|low` axis.

## Implementation Route

M2088 should implement a no-reset selector that:

```text
1. loads M2082 density-aware repaired executable task specs;
2. loads M2085 reset_rows.csv and reset_failure_rows.csv;
3. includes only rows with reset_success == true;
4. preserves env_config and metadata exactly for included rows;
5. writes a reduced executable task spec JSON/CSV;
6. writes excluded rows and coverage distribution artifacts;
7. writes a planned sentinel workload from the included specs and existing profile artifacts;
8. writes a claim boundary and summary.
```

M2088 must not:

```text
change obstacle filters;
run environment reset;
run rollout or policy actions;
run measured execution;
rank controller families;
make paper-level or self-ID claims.
```

Expected artifacts:

```text
reset_valid_core_executable_task_specs.json
reset_valid_core_executable_task_specs.csv
reset_valid_core_excluded_rows.csv
reset_valid_core_planned_sentinel_workload.csv
reset_valid_core_distribution_by_family.csv
reset_valid_core_distribution_by_split.csv
reset_valid_core_distribution_by_axis.csv
claim_boundary.csv
summary.json
```

## Pass Gates

M2088 passes only if:

```text
input_executable_spec_count == 240
input_reset_row_count == 240
reset_success_row_count == 238
reset_failure_row_count == 2
reduced_executable_spec_count == 238
excluded_spec_count == 2
public_gate_preserved_count == 96
public_gate_excluded_count == 0
public_debug_excluded_count == 2
env_config_changed_count == 0
metadata_missing_count == 0
contract_violation_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
family_coverage_loss_count == 2
axis_coverage_loss_count == 2
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

M2087 supports only:

```text
a reset-valid core panel reduction route is specified.
```

M2087 does not support:

```text
reset validity beyond the M2085 seed;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2088-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-implementation
```
