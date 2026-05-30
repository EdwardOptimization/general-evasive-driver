# M1858 Executable V2 Support-First Materialization Design

- status: completed
- decision: `support_first_materialization_design_admit_implementation`
- branch: `paper_route_executable_v2_support_first_materialization`
- parent audit: `docs/m1857-executable-v2-support-first-source-mining-result-audit.md`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1856 found 202 supported sources and 149759 accepted cells. M1858 designs a
bounded materialization step that converts a balanced subset of this support
evidence into executable-v2 candidate rows. This is still infrastructure: it
does not reset, run policy, rank controllers, or claim paper-level evidence.

## Materialization V0 Contract

Contract id:

```text
support_first_materialization_v0
```

Inputs:

```text
runs/m1856_executable_v2_support_first_source_mining/support_first_materialization_admissibility_input.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_accepted_cells.csv
configs/executable_v2_support_first_candidate_templates_v0.json
```

The helper must filter to:

```text
source_support_status == supported
materialization_admissible == true
labels_enter_actor_input == false
v2_ranking_admissible_by_default == false
```

Unsupported sources remain blocked. They must not enter materialization.

## Source Selection

Use role-balanced caps:

```text
max_sources_per_role: 24
max_sources_per_role_surface: 12
```

For each role and surface variant, select sources by deterministic round-robin
over speed/mu strata. Within a stratum, prefer sources with more accepted cells;
break ties by candidate source id.

Expected selected source cap:

```text
4 roles * 24 sources = 96 sources
```

If a role/surface has fewer than the cap, select all supported sources in that
stratum and record the shortage. Do not backfill from another role in a way that
destroys role balance without recording it.

## Accepted Cell Selection

Use:

```text
max_cells_per_source: 2
```

For each selected source:

1. Select the boundary cell with minimum `threshold_score`; tie break by
   smaller obstacle distance, then larger obstacle half width, then source id.
2. Select one representative cell near the median accepted obstacle distance;
   tie break by lower threshold score, then smaller half width.
3. Deduplicate. If both selectors choose the same cell, materialize one row for
   that source and record it.

Expected materialized row cap:

```text
96 sources * 2 cells = 192 rows
```

This cap is intentionally small enough for reset validation while preserving all
four roles, both surface variants, and speed/mu diversity.

## Materialized Row Schema

Each materialized row should include:

```text
materialized_v2_panel_spec_id
support_contract_id
materialization_contract_id
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
source_role_semantics
v2_task_label
profile_name
profile_group
source_family_id
surface_variant
speed_ref
mu
friction_step_enabled
friction_step_at
dt
min_time_after_friction_step
obstacle_distance
obstacle_half_width
threshold_score
cell_selection_kind
labels_enter_actor_input
v2_ranking_admissible_by_default
reset_validation_required
measured_execution_required
```

The JSON payload should also include `env_config` for reset validation. It must
pin the materialized speed, mu, obstacle distance, obstacle half width, allowed
label, AEB-infeasible requirement, and friction-step timing from the source
template. Labels remain metadata and must not enter actor inputs.

## Required Outputs For M1859

M1859 should implement a no-reset materialization helper that writes:

```text
summary.json
support_first_materialized_source_selection.csv
support_first_materialized_cell_selection.csv
support_first_materialized_executable_v2_panel_specs.csv
support_first_materialized_executable_v2_panel_specs.json
support_first_materialization_matrix.csv
support_first_materialization_blocked_sources.csv
support_first_materialization_duplicate_keys.csv
support_first_materialization_claim_boundary.csv
```

Minimum summary fields:

```text
contract_id
input_supported_source_count
selected_source_count
selected_cell_count
materialized_spec_count
materialization_matrix_row_count
role_counts
surface_counts
speed_count
mu_count
duplicate_key_count
labels_enter_actor_input_count
ranking_admissible_by_default_count
guardrail_violation_count
```

## Next Validation Order

After materialization is implemented and executed, the next branch should be:

```text
materialization audit
  -> targeted reset validation design
  -> reset-only preflight
  -> reset result audit
  -> measured execution design only after reset support
```

Do not jump from materialization directly to measured execution.

## Guardrails

- materialized executable-v2 rows generated: `false`
- source mining rerun: `false`
- source repair payload generated: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- bounded materialization design;
- source and cell caps;
- materialized row schema;
- M1859 implementation route.

Unsupported:

- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
