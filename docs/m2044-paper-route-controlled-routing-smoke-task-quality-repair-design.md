# M2044 Paper-Route Controlled Routing Smoke Task-Quality Repair Design

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_design_admit_template_generator_implementation`
- manifest: `experiments/manifests/m2044-paper-route-controlled-routing-smoke-task-quality-repair-design.json`
- evidence source: `runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/summary.json`
- reset/rollout/measured execution in M2044: `false`
- policy actions executed in M2044: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Target

M2042/M2043 show a broad task-quality blocker:

```text
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 0
offtrack_dominance_slice_count: 138
collision_dominance_slice_count: 0
success_obstacle_pass: 20 / 432
off_track_noncollision_noncompletion: 399 / 432
```

This is not a runner or localizer issue. The current routing-smoke panel is too
offtrack-heavy to support ranking. M2044 therefore designs a no-rollout repair
wave whose only purpose is to produce new task/source candidates for a later
preflight/materialization path.

## Repair Principles

The repair must obey:

```text
do not tune controller profiles;
do not change actor inputs;
do not weaken comparison support thresholds;
do not claim generated rows are paper-valid;
do not run reset/rollout/measured execution in the template step;
do not rank controller families from repaired templates.
```

Repair operates at task/source quality only. It should make the panel less
offtrack-dominated by changing scenario geometry and support coverage, not by
changing the controller family definitions.

## Repair Wave

M2045 should implement a deterministic template generator that writes:

```text
configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json
```

Candidate count:

```text
total: 192
public_debug: 112
public_gate: 80
paper_holdout_candidate: 0
```

Repair-axis quotas:

```text
l2_offtrack_relief: 64
family_offtrack_relief: 48
zero_success_source_kind_relief: 40
success_neighborhood_expansion: 24
generated_proxy_support_check: 16
```

### Axis 1: L2 Offtrack Relief

Evidence:

```text
all eight L2 finite-window profiles: 0/36 success, 36/36 offtrack
```

Purpose:

```text
Create task-quality variants where finite-window profiles can stay on road
long enough to be diagnostic.
```

Allowed template deltas:

```text
increase obstacle distance;
slightly reduce obstacle half width;
increase track width or recovery corridor slack;
move warmup reveal earlier for warmup tasks;
increase max_steps only if paired with finish/pass guardrails.
```

### Axis 2: Family Offtrack Relief

Evidence:

```text
T1: 43/48 offtrack
T2: 109/120 offtrack
T3: 113/120 offtrack
T4: 46/48 offtrack
T5: 88/96 offtrack
```

Purpose:

```text
Ensure every panel family has some lower-offtrack diagnostic support before
ranking or finite-window-vs-GRU comparison.
```

Quota:

```text
at least 8-12 candidates per family, source-balanced where possible.
```

### Axis 3: Zero-Success Source-Kind Relief

Evidence examples:

```text
offtrack_boundary_relief: 0/12 success, 12/12 offtrack
same_current_rear_lateral_authority_older_history_proxy: 0/12 success, 12/12 offtrack
same_current_steer_lag_older_history_proxy: 0/12 success, 12/12 offtrack
warmup_mixed_authority_proxy: 0/12 success, 12/12 offtrack
warmup_rear_lateral_authority_proxy: 0/12 success, 12/12 offtrack
warmup_steer_lag_proxy: 0/12 success, 12/12 offtrack
```

Purpose:

```text
Avoid source-kind singletons that are present but non-diagnostic because every
profile leaves the road.
```

### Axis 4: Success-Neighborhood Expansion

Evidence:

```text
20 success rows exist, concentrated in L1/L3 profiles and 17 task sources.
```

Purpose:

```text
Expand around rows that already admit obstacle-pass behavior, creating nearby
support candidates instead of only relaxing fully failed rows.
```

Constraint:

```text
success-neighborhood variants must not become ranking-admissible by default;
they are repair candidates that require the usual preflight, reset, execution,
localization, and audit chain.
```

### Axis 5: Generated-Proxy Support Check

Evidence:

```text
original/smoke_proxy rows: 14/288 success, 265/288 offtrack
generated/smoke_proxy rows: 6/144 success, 134/144 offtrack
```

Purpose:

```text
Check whether generated T2/T3 source proxies can be made smoke-valid without
silently becoming paper-valid benchmark tasks.
```

Constraint:

```text
generated_source_row remains true;
materialization_semantics remains smoke_proxy;
paper_validity_claim remains false.
```

## Artifact Contract

Each repair candidate should include:

```text
repair_candidate_id;
repair_branch_id;
repair_axis;
source_split;
parent_task_source_id;
parent_profile_name or parent_slice_kind;
parent_panel_task_family;
parent_source_kind;
parent_proxy_template_family;
parent_generated_source_row;
parent_outcome_bucket;
parent_offtrack_rate or parent_success_count where applicable;
template_delta fields;
labels_enter_actor_input=false;
profile_specific_tuning=false;
controller_family_ranking_claim_made=false;
finite_window_vs_gru_conclusion_made=false;
paper_level_claim_made=false;
level3_self_id_claim_made=false.
```

The generator should fail closed if:

```text
M2042 summary is not a localization pass;
required localization artifacts are missing;
quota counts do not match 192 total / 112 debug / 80 gate;
any forbidden bool is true;
any generated proxy candidate has paper_validity_claim=true;
any candidate encodes controller-profile tuning.
```

## Next

M2045 should implement the deterministic no-rollout template generator and
focused tests only. Reset, materialization, measured execution, ranking,
finite-window-vs-GRU conclusions, paper-level claims, and level3 self-ID claims
remain blocked.
