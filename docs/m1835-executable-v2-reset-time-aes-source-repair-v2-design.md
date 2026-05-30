# M1835 Executable V2 Reset-Time AES Source Repair V2 Design

- status: completed
- decision: `reset_time_aes_source_repair_v2_design_admit_implementation`
- branch: `paper_route_executable_v2_reset_time_aes_source_repair_v2`
- parent audit: `docs/m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit.md`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1835 designs the second source-level AES sampler repair. M1834 showed that the
previous repair used a weak offline-density proxy: the repaired AES sources had
nonzero offline density, but at reset time they produced 240000 AEB-feasible
rejections and zero accepted AES-only candidates.

The next repair must therefore optimize the same acceptance condition used by
the reset-time obstacle sampler. This milestone is design only. It does not
materialize new project artifacts, run reset, step environments, execute
policies, train, replay, rank controllers, or make paper-level claims.

## Targets

Repair only the two persistent AES sources:

| source | materialized source | hidden bucket | M1833 attempts | accepted | dominant rejection |
| --- | --- | --- | ---: | ---: | --- |
| `m1771-bp1-00` | `m1811-stable-bp-000` | `nominal` | 120000 | 0 | `aeb_feasible_rejected` |
| `m1771-bp1-02` | `m1811-stable-bp-001` | `friction_step` | 120000 | 0 | `aeb_feasible_rejected` |

The previously repaired AEB source passed reset validation in M1828 and should
be carried forward unchanged.

## Core Acceptance Objective

M1836 should implement a no-reset helper that reuses reset-time sampler replay
logic from `autodrift.executable_v2_reset_time_aes_sampler_diagnostic`.

For a candidate source-level obstacle config and the 12 profile/eval-seed rows
belonging to a target source, score the candidate by replaying the obstacle
sampler from reset RNG state:

```text
for each profile row:
  sample vehicle params and speed_ref from reset seed
  advance RNG to obstacle sampler state
  sample obstacle distance and half-width up to max_sample_attempts
  classify each candidate with classify_obstacle_scenario(...)
  apply allowed_labels
  apply require_aeb_infeasible
  apply max_threshold_score
  apply friction-step timing filter when present
```

A profile row is accepted only if replay finds a candidate where:

```text
label == "aes_feasible"
reject_reason == "accepted"
require_aeb_infeasible remains true
```

Primary source-level objective:

```text
accepted_profile_count == 12
```

Tie-breakers:

```text
1. higher minimum accepted-attempt slack across the 12 profile rows;
2. higher accepted candidate count under bounded replay;
3. lower total sampled attempts before first acceptance;
4. smaller range movement from the parent source;
5. stable behavior across nominal and friction-step source requirements.
```

Do not accept a repair candidate because offline density is positive. Offline
density may be written as a diagnostic column only.

## Candidate Search Space

The implementation should generate source-level candidates, not per-profile
patches. Each candidate applies to all 12 profile rows for that source.

Candidate families should include:

```text
original_reset_replay
aes_reset_close_band
aes_reset_close_medium_band
aes_reset_threshold_band
aes_reset_wide_search_band
```

The candidate generator may sweep distance and half-width ranges, but it must
store a named candidate and the final range used. It should prefer closer
obstacle windows than M1825 because M1833 showed the current ranges are too
often AEB-feasible. The final chosen range must still be source-level and must
not depend on profile name.

M1836 should keep:

```text
allowed_labels = ["aes_feasible"]
require_aeb_infeasible = true
stable_aes_beta_limit and friction-step timing semantics unchanged
profile observation/history settings unchanged
```

`max_sample_attempts` should remain 10000 for the main acceptance check. A
larger search budget may be used internally to discover candidates, but a
repair is not reset-ready unless it passes the 10000-attempt replay criterion.

## Required Output Artifacts

M1836 should write:

```text
summary.json
reset_time_aes_source_repair_targets.csv
reset_time_aes_source_repair_candidate_scores.csv
reset_time_aes_source_repair_specs.json
reset_time_aes_source_repair_specs.csv
repaired_targeted_reset_executable_v2_panel_specs.json
reset_time_aes_source_repair_claim_boundary.csv
```

Minimum `reset_time_aes_source_repair_candidate_scores.csv` columns:

```text
source_v1_bounded_panel_spec_id
source_scenario_spec_id
candidate_name
distance_range
half_width_range
max_sample_attempts
profile_count
accepted_profile_count
attempt_count_total
accepted_count_total
attempt_count_by_label
attempt_count_by_reject_reason
dominant_reject_reason
offline_density
selected
selection_reason
```

Minimum `summary.json` fields:

```text
result_class
target_source_count
target_profile_count
repaired_spec_count
selected_source_count
accepted_source_count
accepted_profile_count_total
attempt_count_total
attempt_count_by_label
attempt_count_by_reject_reason
row_count_by_label
row_count_by_reject_reason
summary_aggregation_version
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

The summary aggregation version should be explicit, for example:

```text
summary_aggregation_version = "row_and_attempt_counts_v1"
```

This directly fixes the M1834 metric artifact.

## Pass Criteria

The no-reset repair helper should pass only if:

| field | expected |
| --- | ---: |
| target AES source count | 2 |
| target profiles per source | 12 |
| total AES target profiles | 24 |
| accepted AES target profiles | 24 |
| unchanged AEB profile rows | 12 |
| repaired executable spec count | 36 |
| labels entering actor input | 0 |
| ranking admissible by default | 0 |
| guardrail violations | 0 |

If any source has fewer than 12 accepted profile rows under the 10000-attempt
reset-time replay criterion, the helper should fail and route to broader
scenario-support redesign rather than weakening labels or turning off
`require_aeb_infeasible`.

## Implementation Route

Route to:

```text
m1836-executable-v2-reset-time-aes-source-repair-v2-implementation
```

M1836 should implement the helper and focused tests only. It should not run the
helper on project artifacts. A later execution-design milestone should register
the exact run command.

## Focused Tests Required

M1836 should add tests that cover:

1. A candidate with all AEB-feasible rejections is not selected.
2. A candidate with accepted AES-only replay rows is selected.
3. Selected source patches are source-level and preserve all profile controls.
4. The unchanged AEB source is carried forward without profile-specific edits.
5. `summary.json` contains both row-count and attempt-count aggregations.
6. Forbidden guardrails remain false.

## Guardrails

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

- reset-time AES source repair v2 design;
- reset-time AES-only acceptance should replace offline density as the main
  objective;
- implementation is admitted.

Unsupported:

- repaired reset feasibility;
- reset-time repair success;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
