# M1802 Executable V2 Stable Source-Label Top-Up Design

- status: completed
- decision: `stable_source_label_topup_design_admit_preflight_implementation`
- source audit: `docs/m1801-executable-v2-label-source-compatibility-result-audit.md`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Problem

M1801 chose stable source-label top-up because M1800 leaves
`stable_avoidance_aes` with only `36` compatible rows. The missing rows are
systematic source-label incompatibilities, not sparse seed failures:

| target | missing label | hidden | road | timing | lateral | missing profiles |
| --- | --- | --- | --- | --- | --- | ---: |
| `m1771-bp1-00` | `aes_feasible` | `nominal` | `nominal` | `medium` | `center` | 12 |
| `m1771-bp1-02` | `aes_feasible` | `friction_step` | `nominal` | `late` | `center` | 12 |
| `m1771-bp1-05` | `aeb_feasible` | `brake_variation` | `moderate` | `late` | `wide_offset` | 12 |

The existing M1771 stable source pool is:

| bounded spec | source | metadata labels | hidden | road | timing | lateral |
| --- | --- | --- | --- | --- | --- | --- |
| `m1771-bp1-00` | `m1728-s1-00` | `aeb_feasible;aes_feasible` | `nominal` | `nominal` | `medium` | `center` |
| `m1771-bp1-01` | `m1728-s1-02` | `aeb_feasible;aes_feasible` | `nominal` | `moderate` | `late` | `wide_offset` |
| `m1771-bp1-02` | `m1728-s1-08` | `aeb_feasible;aes_feasible` | `friction_step` | `nominal` | `late` | `center` |
| `m1771-bp1-03` | `m1728-s2-01` | `aes_feasible` | `nominal` | `moderate` | `close` | `wide_offset` |
| `m1771-bp1-04` | `m1728-s2-04` | `aes_feasible` | `friction_step` | `moderate` | `close` | `mild_offset` |
| `m1771-bp1-05` | `m1728-s2-09` | `aes_feasible` | `brake_variation` | `moderate` | `late` | `wide_offset` |

This pool is not enough to claim exact replacements by metadata alone. Some
candidate sources are label-compatible but geometry-shifted; the
`aeb_feasible/brake_variation` target has no obvious metadata-supported
existing source. The top-up plan must therefore distinguish:

- exact existing candidate;
- near existing candidate requiring reset probe;
- new source materialization required.

## Design Goal

Build a no-reset top-up preflight that converts replacement needs and stable
source metadata into a candidate plan before any reset, rollout, or measured
execution.

The plan must:

- preserve all `12` profile controls;
- keep actor inputs label-free;
- keep measured execution and ranking blocked;
- avoid profile-specific tuning;
- separate metadata label support from observed reset support;
- explicitly mark candidates that require new materialization or reset probing.

## Candidate Classification

For each stable top-up target, compare candidate sources by:

```text
candidate_label_support
hidden_dynamics_bucket_match
road_boundary_bucket_match
obstacle_timing_bucket_match
obstacle_lateral_bucket_match
source_family_match
sampling_repair_variant
observed_reset_support_status
```

Candidate class:

| class | meaning |
| --- | --- |
| `exact_existing_candidate` | label and all target buckets match in existing metadata |
| `near_existing_candidate` | label and hidden bucket match, but one or more geometry buckets differ |
| `metadata_only_untrusted` | metadata says label is allowed but M1800 observed the same source-label as unsupported |
| `new_materialization_required` | no existing candidate can support the target label/bucket combination |

`metadata_only_untrusted` must not be used as a replacement without a later
reset probe. This prevents the project from repeating the M1790 mistake of
treating metadata labels as executable support.

## Artifacts for M1803/M1804

The top-up preflight should write:

```text
summary.json
stable_topup_targets.csv
stable_candidate_source_pool.csv
stable_topup_candidate_rows.csv
stable_new_materialization_need_rows.csv
stable_topup_claim_boundary.csv
```

Required target fields:

```text
topup_target_id
source_scenario_spec_id
v2_role_surface_id
v2_task_label
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
missing_profile_count
required_profile_controls
```

Required candidate fields:

```text
topup_target_id
candidate_bounded_panel_spec_id
candidate_source_scenario_spec_id
candidate_class
candidate_label_support
hidden_match
road_match
timing_match
lateral_match
bucket_match_score
observed_reset_support_status
requires_reset_probe
requires_new_materialization
admissible_as_direct_replacement
```

## Expected Current Top-Up State

Expected target count:

```text
stable_topup_target_count: 3
target_missing_profile_count_total: 36
```

Expected candidate interpretation:

- `m1771-bp1-00/aes_feasible`: metadata matches the target source exactly, but
  M1800 observed this exact source-label as `unsupported_systematic`; it is
  `metadata_only_untrusted`, not a direct replacement.
- `m1771-bp1-02/aes_feasible`: same situation; metadata matches, observed reset
  support rejects it.
- `m1771-bp1-05/aeb_feasible`: no existing stable source has trusted
  `aeb_feasible` support with `brake_variation/moderate/late/wide_offset`;
  this likely requires new materialization.

Near candidates such as `m1771-bp1-03` or `m1771-bp1-04` may help discover
replacement directions, but they are not direct replacements because their road
or obstacle buckets differ.

## Acceptance Rules

M1803 implementation should pass if focused tests cover:

- exact existing candidate;
- metadata-only untrusted candidate;
- near existing candidate;
- new materialization required;
- profile-control preservation;
- label-leakage and ranking-block guardrails.

M1804 execution should pass only if:

- all three stable top-up targets are represented;
- no direct replacement is admitted from unsupported M1800 source-label evidence;
- all replacement needs remain blocked from measured execution until reset
  support is observed;
- no reset, rollout, training, replay, PPO, private holdout, profile tuning,
  actor-input change, ranking, paper-level, or level3 claim occurs.

## Route Decision

Route to:

```text
m1803-executable-v2-stable-source-label-topup-preflight-implementation
```

M1803 should implement the no-reset planner and focused tests. A later execution
milestone can run it on M1800/M1771/M1790 artifacts and decide whether to
materialize new source specs or run a targeted reset probe.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
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

- stable source-label top-up design;
- candidate classification and artifact contract;
- no-reset implementation route.

Unsupported:

- top-up execution result;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
