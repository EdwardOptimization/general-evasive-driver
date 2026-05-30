# M1840 Executable V2 Reset-Time AES Feasibility Scan Design

- status: completed
- decision: `reset_time_aes_feasibility_scan_design_admit_implementation`
- branch: `paper_route_executable_v2_reset_time_aes_feasibility_scan`
- parent audit: `docs/m1839-executable-v2-reset-time-aes-source-repair-v2-result-audit.md`
- feasibility scan run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1838 proved that the static M1836 source repair candidates do not find
reset-time AES-only support. M1839 classified that as static candidate-space
failure, not task impossibility.

M1840 designs a conditional feasibility scan. The scan should answer whether
each failed AES reset row has any obstacle distance / half-width grid cell that
is accepted as AES-only under the actual reset-time `speed_ref`, `initial_mu`,
and timing filters. It should not generate a repaired payload. Source repair v3
is only admissible after the scan observes feasible cells.

## Inputs

The later implementation should read:

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

It may use M1838 artifacts only for audit context:

```text
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/summary.json
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_candidate_scores.csv
```

## Target Rows

Target exactly the failed AES reset rows:

```text
source count: 2
profile rows: 24
labels: aes_feasible
```

Expected sources:

```text
m1771-bp1-00
m1771-bp1-02
```

## Scan Method

For each target row:

1. load the repaired spec and env config;
2. use the row's `eval_seed`;
3. reproduce reset-time state without calling `AutoDriftEnv.reset`;
4. capture:
   ```text
   speed_ref
   initial_mu
   friction_step_at or aligned friction-step range
   ```
5. sweep an obstacle grid;
6. classify each grid cell;
7. apply exactly the same accept/reject semantics as reset-time obstacle
   sampling:
   ```text
   allowed_labels
   require_aeb_infeasible
   max_threshold_score
   min_time_after_friction_step / aligned friction-step filter
   ```

Acceptance for a cell:

```text
label == "aes_feasible"
reject_reason == "accepted"
```

Do not infer feasibility from offline density alone.

## Grid Requirements

M1836 did not scan close enough or condition on reset-time speed/mu. M1841
should scan a broad grid:

```text
distance_range: [1.0, 60.0]
distance_count: at least 120
half_width_range: [0.20, 1.40]
half_width_count: at least 61
```

The design deliberately includes distances below the previous 10m lower bound
because low speed / high mu reset rows may stay AEB-feasible until the obstacle
is very close.

The helper should write all accepted cells. It may write full grid rows if the
row count remains manageable; otherwise it must write compact count tables plus
accepted cells and representative boundary cells.

## Required Output Artifacts

M1841 should write:

```text
summary.json
reset_time_aes_feasibility_profile_summary.csv
reset_time_aes_feasibility_source_summary.csv
reset_time_aes_feasibility_accepted_cells.csv
reset_time_aes_feasibility_label_counts.csv
reset_time_aes_feasibility_reject_reason_counts.csv
reset_time_aes_feasibility_boundary_examples.csv
reset_time_aes_feasibility_claim_boundary.csv
```

Minimum `profile_summary` columns:

```text
v2_panel_spec_id
profile_name
source_v1_bounded_panel_spec_id
source_scenario_spec_id
eval_seed
speed_ref
initial_mu
friction_step_at
grid_cell_count
accepted_cell_count
accepted_distance_min
accepted_distance_max
accepted_half_width_min
accepted_half_width_max
dominant_label
dominant_reject_reason
feasible
```

Minimum `source_summary` columns:

```text
source_v1_bounded_panel_spec_id
source_scenario_spec_id
profile_count
feasible_profile_count
accepted_cell_count_total
distance_min_suggestion
distance_max_suggestion
half_width_min_suggestion
half_width_max_suggestion
source_feasible
```

Minimum `summary.json` fields:

```text
result_class
target_source_count
target_profile_count_total
feasible_profile_count_total
feasible_source_count
grid_cell_count_total
accepted_cell_count_total
label_count_total
reject_reason_count_total
environment_reset_started
environment_rollout_started
policy_action_executed
measured_rollout_started
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
guardrail_violation_count
```

## Result Classes

M1841 implementation should define:

```text
reset_time_aes_feasibility_scan_implemented
```

The later execution should define:

```text
reset_time_aes_feasibility_scan_full_support
reset_time_aes_feasibility_scan_partial_support
reset_time_aes_feasibility_scan_no_support
```

For implementation-only M1841, no project artifact scan should run.

## Decision Rules For Later Execution

If all 24 target rows have accepted cells:

```text
route to source repair v3 design using accepted-cell-derived ranges
```

If some but not all target rows have accepted cells:

```text
route to partial-support audit and decide whether source metadata or profile
sampling needs redesign
```

If zero target rows have accepted cells:

```text
route to branch synthesis: current executable AES reset task has no observed
conditional support under the selected sources and reset seeds
```

In all cases, do not run reset until a repaired payload has been produced and
audited.

## Implementation Route

Route to:

```text
m1841-executable-v2-reset-time-aes-feasibility-scan-implementation
```

M1841 should implement the scan helper and focused tests only. It should not run
the scan on project artifacts.

## Focused Tests Required

M1841 should test:

1. A profile with known AES-only cells reports feasible.
2. A profile with only AEB-feasible cells reports infeasible and counts
   `aeb_feasible_rejected`.
3. Accepted-cell range suggestions are derived from accepted cells only.
4. Source summary aggregates profile feasibility correctly.
5. Guardrail flags remain false.
6. No repair payload is generated by the scan helper.

## Guardrails

- feasibility scan run: `false`
- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- conditional feasibility scan design;
- implementation is admitted.

Unsupported:

- scan result;
- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
