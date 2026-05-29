# M1679 Paper-Route Controller-Family Bounded Task-Source Generation Design

## Summary

M1679 designs a bounded fresh task-source generation route from the audited
M1677 metadata mapping.

Decision:

```text
bounded_task_source_generation_design_admit_no_training_preflight
```

This milestone is design-only. It does not materialize task-source specs, run
environment rollout, train, replay, run PPO, use private holdout, promote,
change actor inputs, or claim controller-family ranking, paper-level evidence,
or level3 self-identification.

## Why Fresh Generation Is Required

M1677/M1678 show the metadata is broad enough:

```text
62 candidate rows
12 source families
2 task families
15 source edges
5 window tags
44 seed namespaces
0 leakage violations
0 guardrail violations
```

But M1615 contributes `39 / 62` rows. Therefore:

```text
M1615 may identify useful source-family, edge, and window contours.
M1615 must not become a direct controller-family benchmark.
M1615 hidden/action tensors must not become labels or targets.
```

The next step must generate fresh bounded task-source specs from public metadata
contours rather than replaying M1615 rows as tasks.

## Generation Contract

The no-training preflight should write:

```text
runs/m1680_controller_family_bounded_task_source_generation_preflight/summary.json
runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json
runs/m1680_controller_family_bounded_task_source_generation_preflight/source_budget_summary.csv
```

Each generated spec should include only deployable task/source metadata:

```text
task_source_id
task_family: T4 or T5
source_edge
source_family_left
source_family_right
window_tag
seed_namespace_source
generation_seed
source_metadata_roles
controller_profiles_required
controls_required
mapping_lineage
```

Forbidden spec fields:

```text
hidden_tensor
action_tensor
preferred_action
rejected_action
action_target
mu / mass / tire / brake / actuator hidden parameter labels as actor inputs
oracle feasibility labels
private holdout identifiers
```

## Source Budgets

The first preflight should target a compact but source-diverse spec set:

```text
target_total_specs: 72
max_total_specs: 96
target_T4_share: 0.50
target_T5_share: 0.50
min_task_family_share: 0.40
min_source_family_count: 8
min_source_edge_count: 10
min_window_tag_count: 3
max_single_source_family_share: 0.30
max_single_source_edge_share: 0.20
max_single_metadata_role_share: 0.55
```

The generator should equalize source edges before duplicating rows. If caps
cannot be met, it should report a source-budget shortfall and stop before
rollout.

## Controller-Family Controls

Every generated spec must require the full controller-family comparison matrix:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Required comparisons:

```text
L1 versus L2/L3
L2 normal versus matched current-tiled
L3 online versus corrected reset
T4 versus T5 task family behavior
```

No profile-specific tuning is allowed. A later benchmark must use one frozen
training/eval recipe across all profiles.

## Preflight Stop Rules

M1680 must stop before rollout if:

```text
any hidden/action target key appears in specs;
source caps fail and are not explicitly classified;
T4 or T5 is missing;
L1/current-tiled/reset controls are missing;
M1615 rows are copied as direct benchmark tasks;
private holdout identifiers appear;
profile-specific tuning is introduced.
```

## Next Step

Admit exactly one no-training preflight:

```text
m1680-paper-route-controller-family-bounded-task-source-generation-preflight
```

M1680 should implement or run a deterministic spec generator only. It should
write artifacts and route to an audit before any environment rollout.

## Guardrails

```text
task_sources_materialized: false
environment_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1680-paper-route-controller-family-bounded-task-source-generation-preflight
```
