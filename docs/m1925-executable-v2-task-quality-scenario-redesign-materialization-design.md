# M1925 Executable V2 Task-Quality Scenario Redesign Materialization Design

- status: completed
- decision: `task_quality_scenario_materialization_design_admit_implementation`
- branch: `paper_route_task_quality_scenario_redesign`
- parent audit: `docs/m1924-executable-v2-task-quality-scenario-redesign-source-mining-result-audit.md`
- source support table: `runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/joined_source_support.csv`
- reset/rollout/measured execution in M1925: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M1925 turns the M1924 audited support surface into a bounded executable-panel
design. It does not materialize or execute the panel. The next milestone should
implement a deterministic selector that creates a non-holdout source subset
from already supported candidates.

The design target is deliberately small:

```text
feasibility tiers: 5
source roles: 4
selected sources per tier-role cell: 4
selected source count: 80
expected controller-profile count: 12
expected planned workload cells: 960
```

The 960 workload cells are only a planning target for the later materializer:
80 selected sources crossed with the current 12 support-first controller
profiles. M1925 itself produces no workload rows, reset rows, rollout rows, or
ranking table.

## Eligibility Filter

M1926 should load:

```text
runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/joined_source_support.csv
```

and select only rows satisfying:

```text
materialization_admissible == true
source_split in {public_gate, public_debug}
paper_holdout_candidate == false
labels_enter_actor_input == false
v2_ranking_admissible_by_default == false
```

The paper holdout split must remain unused. If any selected row comes from
`paper_holdout_candidate`, the materialization implementation must fail closed.

## Support Check

M1924 confirms that the non-holdout supported pool is large enough:

```text
non_holdout_supported_source_count: 357
tier_role_group_count: 20
minimum_non_holdout_supported_sources_per_tier_role: 6
```

This means the target `4` sources per tier-role cell is feasible without
touching holdout candidates.

Tier-role support before holdout exclusion:

```text
tier_a_positive_support_sanity:
  drift_required_recovery: 19
  stable_aeb: 26
  stable_aes_only: 25
  unavoidable_mitigation: 10
tier_b_feasible_emergency:
  drift_required_recovery: 25
  stable_aeb: 20
  stable_aes_only: 27
  unavoidable_mitigation: 18
tier_c_boundary_near_miss:
  drift_required_recovery: 27
  stable_aeb: 8
  stable_aes_only: 28
  unavoidable_mitigation: 20
tier_d_handling_limit_drift_required:
  drift_required_recovery: 27
  stable_aeb: 8
  stable_aes_only: 21
  unavoidable_mitigation: 21
tier_e_mitigation_only:
  drift_required_recovery: 24
  stable_aeb: 12
  stable_aes_only: 12
  unavoidable_mitigation: 21
```

Non-holdout support per tier-role cell has minimum `6`, so all 20 cells can
select exactly four rows.

## Selection Protocol

M1926 should implement a deterministic source-only selector:

1. Group eligible rows by:

```text
feasibility_tier_id
source_role_semantics
```

2. For each group, select exactly four sources.

3. Prefer `public_gate` before `public_debug`, but use `public_debug` to fill
   any group with fewer than four `public_gate` supported sources.

4. Balance surface variants inside each tier-role group:

```text
target per group:
  steady_surface: 2
  post_friction_step: 2
```

If exact 2/2 surface balance is impossible in a group, fail and route to
source-template repair instead of silently selecting an imbalanced panel.
M1924 support makes exact 2/2 balance feasible.

5. Within each split/surface bucket, use a stable diversity sort:

```text
source_split priority: public_gate before public_debug
surface_variant target bucket
speed_ref ascending
mu ascending
candidate_source_id ascending
```

6. Emit source-level selection metadata, not controller rankings.

## Output Artifact Contract

M1926 should write a config artifact:

```text
configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json
```

Required top-level fields:

```text
scenario_quality_branch_id
source_support_parent_artifact
selected_source_count
expected_controller_profile_count
expected_planned_workload_cell_count
selection_protocol_version
selected_sources
selection_summary
guardrail_flags
```

Each selected source row should preserve at least:

```text
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
feasibility_tier_id
source_role_semantics
source_split
surface_variant
speed_ref
mu
target_support_mode
target_boundary_mode
source_support_accepted_cell_count_total
source_support_feasible_profile_count
diagnostic_only_no_ranking_claim
```

The config must not contain controller-family rankings, success claims, or
paper-level conclusions.

## Pass Gates

M1926 selector/materialization implementation should pass only if:

```text
selected_source_count == 80
tier_role_group_count == 20
selected_source_count_per_tier_role == 4 for every group
steady_surface_selected_count_per_tier_role == 2 for every group
post_friction_step_selected_count_per_tier_role == 2 for every group
paper_holdout_selected_count == 0
labels_enter_actor_input_count == 0
ranking_admissible_by_default_count == 0
expected_controller_profile_count == 12
expected_planned_workload_cell_count == 960
environment_reset_started == false
environment_rollout_started == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Interpretation Boundary

Supported by M1925:

- a bounded non-holdout materialization subset is feasible;
- target source count and workload count are explicit;
- M1926 can implement a deterministic source selector;
- holdout candidates remain reserved for later paper-evidence protocol.

Unsupported by M1925:

- executable reset success;
- measured rollout success;
- controller-family ranking;
- any policy improvement claim;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation
```

M1926 should implement the deterministic selector, focused tests, and the
source-only subset artifact. It should still not run environment reset, rollout,
measured execution, training, replay, PPO, controller ranking, paper-level
claims, or level3 self-ID claims.
