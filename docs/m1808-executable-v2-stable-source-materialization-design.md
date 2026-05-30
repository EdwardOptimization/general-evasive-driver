# M1808 Executable V2 Stable Source Materialization Design

- status: completed
- decision: `stable_source_materialization_design_admit_implementation`
- source synthesis: `docs/m1807-paper-route-executable-v2-label-source-compatibility-branch-synthesis.md`
- source artifact: `runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_new_materialization_need_rows.csv`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- source materialization executed: `false`
- training/replay/PPO: `false`

## Problem

M1805/M1806 show that the current M1771 stable source pool has no trusted direct
replacement for the three systematic stable source-label gaps:

| target | label | hidden | road | timing | lateral | missing profiles |
| --- | --- | --- | --- | --- | --- | ---: |
| `m1771-bp1-00` | `aes_feasible` | `nominal` | `nominal` | `medium` | `center` | 12 |
| `m1771-bp1-02` | `aes_feasible` | `friction_step` | `nominal` | `late` | `center` | 12 |
| `m1771-bp1-05` | `aeb_feasible` | `brake_variation` | `moderate` | `late` | `wide_offset` | 12 |

The exact metadata-compatible sources for the first two targets were observed
as `unsupported_systematic`, and the third target has no candidate source in
the current pool. Therefore M1808 designs new source materialization rather
than treating metadata-only candidates as replacements.

## Design Goal

Create a no-reset materialization contract that can generate stable source
specs for missing source-label support while preserving all profile controls and
claim boundaries.

The design must:

- preserve the `12` controller profile controls from the existing panel;
- keep labels, source labels, and feasibility out of actor inputs;
- create new source ids instead of mutating unsupported M1771 sources in place;
- record provenance back to the failed target and any near candidate evidence;
- avoid duplicate materialization for the same stable source-label key;
- mark every materialized source as reset-validation-required;
- keep measured execution and ranking blocked until reset-only support is
  observed.

## Materialization Strategy

Use a target-key materialization strategy:

```text
stable_materialization_key =
  v2_role_surface_id
  target_label
  hidden_dynamics_bucket
  road_boundary_bucket
  obstacle_timing_bucket
  obstacle_lateral_bucket
```

For each unique key, create one new materialized source spec:

| target | new materialized source id | strategy |
| --- | --- | --- |
| `m1771-bp1-00/aes_feasible` | `m1809-stable-src-000` | clone target env config as source basis, apply label-specific stable sampler repair |
| `m1771-bp1-02/aes_feasible` | `m1809-stable-src-001` | clone target env config as source basis, apply label-specific stable sampler repair |
| `m1771-bp1-05/aeb_feasible` | `m1809-stable-src-002` | clone target env config as source basis, apply label-specific stable sampler repair |

Cloning the target env config is not a direct replacement claim. It only creates
a new candidate source with explicit reset-validation requirements. The old
source remains quarantined as unsupported for the failed label.

## Required Materialization Fields

The materialized source spec should include:

```text
stable_materialization_spec_id
target_topup_id
target_bounded_panel_spec_id
target_source_scenario_spec_id
target_v2_task_label
v2_role_surface_id
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
stable_materialization_key
materialized_source_scenario_spec_id
materialized_bounded_panel_spec_id
source_basis_bounded_panel_spec_id
source_basis_type
source_basis_support_status
near_candidate_ids
materialization_strategy
sampler_repair_variant_id
env_config_source
env_config_delta_json
profile_control_count
profile_controls_preserved
labels_enter_actor_input
reset_validation_required
measured_execution_admissible
controller_family_ranking_admissible
diagnostic_only_no_ranking_claim
duplicate_key_detected
materialization_executed
environment_reset_started
environment_rollout_started
```

The initial strategy should set:

```text
source_basis_type: target_env_config_clone
source_basis_support_status: unsupported_systematic
materialization_strategy: label_specific_stable_sampler_repair_v1
sampler_repair_variant_id: stable_source_label_materialization_v1
profile_control_count: 12
profile_controls_preserved: true
labels_enter_actor_input: false
reset_validation_required: true
measured_execution_admissible: false
controller_family_ranking_admissible: false
diagnostic_only_no_ranking_claim: true
materialization_executed: false in implementation tests, true only in a later execution milestone
environment_reset_started: false
environment_rollout_started: false
```

## Output Artifact Contract

The implementation should write:

```text
summary.json
stable_source_materialization_targets.csv
stable_source_materialization_specs.csv
stable_source_materialization_specs.json
stable_source_materialization_matrix.csv
stable_source_materialization_duplicate_keys.csv
stable_source_materialization_claim_boundary.csv
```

The project-artifact execution milestone should target:

```text
stable_materialization_target_count: 3
stable_materialization_spec_count: 3
stable_materialization_matrix_row_count: 36
profile_control_count: 12
duplicate_key_count: 0
labels_enter_actor_input_count: 0
reset_validation_required_count: 3
measured_execution_admissible_count: 0
controller_family_ranking_admissible_count: 0
guardrail_violation_count: 0
```

`stable_source_materialization_matrix.csv` should expand the three materialized
source specs across the existing `12` controller profiles without scheduling
reset or rollout.

## Duplicate and Provenance Rules

Duplicate detection:

- reject duplicate `stable_materialization_key` rows;
- reject duplicate `materialized_source_scenario_spec_id`;
- reject any materialized id already present in the M1771 source pool;
- keep duplicate rows in `stable_source_materialization_duplicate_keys.csv` for
  audit instead of silently dropping them.

Provenance:

- every materialized source must reference the original failed target;
- near candidates from M1805 are recorded as evidence only, not as replacements;
- exact metadata-only unsupported sources are recorded as source basis but remain
  quarantined for the old source-label pair;
- materialized sources are not admitted until a later reset-only support check
  observes success.

## Later Validation Route

M1809 should implement the no-reset materializer and focused tests only. A later
execution milestone should materialize project artifacts. After that, a
reset-only validation milestone should check the newly materialized rows before
they can re-enter executable v2 reset feasibility.

The route is:

```text
M1809 implementation with focused tests
M1810 project-artifact execution design
M1811 no-reset materialization execution
M1812 result audit
M1813 targeted reset-only validation design or execution
```

Exact numbering may shift, but measured execution remains blocked until reset
support is observed.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- source materialization executed: `false`
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

## Route Decision

Route to:

```text
m1809-executable-v2-stable-source-materialization-implementation
```

M1809 should implement the no-reset materializer and focused synthetic tests. It
must not execute project artifact materialization, reset, rollout, measured
execution, ranking, or paper-level claims.

## Claim Boundary

Supported:

- stable source materialization design;
- materialization target keys, artifact contract, duplicate rules, provenance
  rules, and later reset-validation route.

Unsupported:

- source materialization execution result;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- checkpoint promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
