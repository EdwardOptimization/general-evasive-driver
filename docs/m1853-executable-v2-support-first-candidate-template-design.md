# M1853 Executable V2 Support-First Candidate Template Design

- status: completed
- decision: `support_first_candidate_template_design_admit_implementation`
- branch: `paper_route_executable_v2_support_first_source_mining`
- parent implementation: `docs/m1852-executable-v2-support-first-source-mining-implementation.md`
- project artifact source mining run: `false`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1852 implemented the no-reset support-first source mining helper, but the
helper deliberately requires explicit candidate source/profile rows. M1853 fixes
the first project candidate template before any mining execution, so source
selection is not hidden inside a run command.

This is a template design only. It does not generate the template file, run the
source miner, scan project artifacts, reset the environment, or materialize
executable-v2 rows.

## Candidate Template V0

Template id:

```text
support_first_candidate_templates_v0
```

Output path for the next implementation:

```text
configs/executable_v2_support_first_candidate_templates_v0.json
```

Candidate source id format:

```text
sfm_v0_{role}_{surface}_v{speed_tag}_mu{mu_tag}
```

Each candidate source has one profile row in V0. Later branches may add
multi-profile sources, but V0 keeps one source equal to one fixed profile so
support failures are easy to localize.

## Coverage Axes

Speeds:

```text
10, 14, 18, 22, 26, 30 m/s
```

Friction values:

```text
0.25, 0.40, 0.60, 0.80, 1.00, 1.15
```

Surface variants:

```text
steady_surface
post_friction_step
```

Roles:

```text
stable_aeb
stable_aes_only
drift_required_recovery
unavoidable_mitigation
```

Total candidate rows:

```text
6 speeds * 6 mu values * 2 surface variants * 4 roles = 288
```

## Role-Specific Grid Parameters

All rows use the existing `classify_obstacle_scenario` model through the M1852
helper. Obstacle coordinates are mining variables only; they are not actor
inputs and they do not become materialized rows.

### stable_aeb

```text
source_role_semantics: stable_aeb
source_required_label: aeb_feasible
require_aeb_infeasible: false
obstacle_distance_min: 10.0
obstacle_distance_max: 95.0
obstacle_distance_count: 86
obstacle_half_width_min: 0.20
obstacle_half_width_max: 1.40
obstacle_half_width_count: 25
min_accepted_cells: 10
```

### stable_aes_only

```text
source_role_semantics: stable_aes_only
source_required_label: aes_feasible
require_aeb_infeasible: true
obstacle_distance_min: 8.0
obstacle_distance_max: 70.0
obstacle_distance_count: 63
obstacle_half_width_min: 0.20
obstacle_half_width_max: 1.40
obstacle_half_width_count: 25
min_accepted_cells: 10
```

### drift_required_recovery

```text
source_role_semantics: drift_required_recovery
source_required_label: drift_required
require_aeb_infeasible: true
recovery_horizon_required: true
obstacle_distance_min: 5.0
obstacle_distance_max: 55.0
obstacle_distance_count: 51
obstacle_half_width_min: 0.20
obstacle_half_width_max: 1.60
obstacle_half_width_count: 29
min_accepted_cells: 10
```

### unavoidable_mitigation

```text
source_role_semantics: unavoidable_mitigation
source_required_label: unavoidable
require_aeb_infeasible: true
mitigation_metric_contract_present: true
obstacle_distance_min: 2.0
obstacle_distance_max: 35.0
obstacle_distance_count: 34
obstacle_half_width_min: 0.20
obstacle_half_width_max: 2.00
obstacle_half_width_count: 37
min_accepted_cells: 10
```

## Surface Variants

`steady_surface`:

```text
friction_step_enabled: false
friction_step_at: ""
min_time_after_friction_step: 0.0
```

`post_friction_step`:

```text
friction_step_enabled: true
friction_step_at: 20
dt: 0.05
min_time_after_friction_step: 0.30
```

The post-step rows do not prove dynamic adaptation. They only ensure the source
mining candidate space includes friction-step timing constraints before later
reset and measured execution.

## Expected Mining Scale

The V0 template is intentionally moderate:

```text
stable_aeb: 72 rows * 86 * 25 = 154800 cells
stable_aes_only: 72 rows * 63 * 25 = 113400 cells
drift_required_recovery: 72 rows * 51 * 29 = 106488 cells
unavoidable_mitigation: 72 rows * 34 * 37 = 90576 cells
total: 465264 cells
```

This remains a no-reset classifier scan. It should be fast enough to run as a
single source-mining project artifact, but M1853 does not run it.

## Diversity Criteria

The execution audit should report:

```text
role_count >= 4
speed_bucket_count >= 6
mu_bucket_count >= 6
source_family_count >= 2
profile_group_count >= 4
max_source_family_share <= 0.50
```

These are reporting/admission criteria, not after-the-fact tuning knobs. If one
role has zero supported sources, record that as a support absence and route to
audit or taxonomy redesign rather than changing V0 and rerunning as if it were
the same template.

## Implementation Requirements For M1854

M1854 should add a deterministic template generator:

```text
src/autodrift/executable_v2_support_first_candidate_templates.py
tests/test_executable_v2_support_first_candidate_templates.py
configs/executable_v2_support_first_candidate_templates_v0.json
```

The generator should:

- produce exactly 288 candidate rows;
- preserve role-specific settings from this document;
- set `labels_enter_actor_input=false`;
- set `v2_ranking_admissible_by_default=false`;
- include `profile_control_hash`;
- include `source_family_id`, `profile_group`, and `template_id`;
- write a summary with role, speed, friction, and surface counts.

M1854 should run focused tests and full pytest, but it should not run source
mining on the generated template. The actual source-mining execution command
must be fixed in a later execution-design milestone.

## Guardrails

- project artifact source mining run: `false`
- project artifact scan: `false`
- generated candidate template file: `false`
- materialized executable-v2 rows generated: `false`
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

- explicit V0 candidate template design;
- role, speed, friction, surface, and grid criteria;
- M1854 implementation route.

Unsupported:

- generated candidate template artifact;
- source mining result;
- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
