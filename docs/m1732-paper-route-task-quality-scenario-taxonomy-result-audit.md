# M1732 Paper-Route Task-Quality Scenario Taxonomy Result Audit

- status: completed
- decision: `scenario_taxonomy_sampling_failure_audit_admit_repair_design`
- audited execution: `docs/m1731-paper-route-task-quality-scenario-taxonomy-execution.md`
- audited summary: `runs/m1731_task_quality_scenario_taxonomy_execution/summary.json`
- audited failures: `runs/m1731_task_quality_scenario_taxonomy_execution/failure_rows.csv`

## Summary

M1732 audits M1731 as a clean execution attempt with a real scenario sampling
failure. The runner preserved metadata joins and guardrails, but the M1728
taxonomy contains label/filter combinations that are not sampling-feasible under
the current obstacle generator.

No new rollout, training, replay, PPO, checkpoint promotion, private holdout,
actor input change, profile tuning, controller-family ranking, paper-level
claim, or level3 self-identification claim occurred in this audit.

## M1731 Pass/Fail Audit

M1731 failed the pre-registered execution pass gate:

| field | observed | required |
| --- | ---: | ---: |
| episode count | `422` | `864` |
| failure count | `442` | `0` |
| completed scenario specs | `36` | `72` |
| completed scenario families | `3` | `6` |
| completed profiles | `12` | `12` |
| selected metrics finite | `true` | `true` |
| guardrail violations | `0` | `0` |
| unsupported features | `5` | `5` |
| silent unsupported approximations | `0` | `0` |

Dominant error:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

Failure family counts:

| scenario family | failed cells | interpretation |
| --- | ---: | --- |
| `aeb_infeasible_stable_aes` | `144` | all S2 specs failed sampling |
| `off_track_boundary_stress` | `144` | all S5 specs failed sampling |
| `hidden_dynamics_stress` | `144` | all S6 specs failed sampling |
| `drift_required_avoidance` | `10` | partial S3 seed/profile failures |

This pattern is not profile-specific: S2/S5/S6 fail across all 12 profiles for
each affected spec. The failure occurs at `env.reset()` before policy rollout,
so it should be classified as `scenario_sampling_failure`, not behavior
regression, proof washout, PPO instability, or controller-family evidence.

## What Worked

M1731 still demonstrated that the execution adapter is mechanically usable for
sampleable specs:

- `episode_rows.csv` retains scenario metadata fields.
- `failure_rows.csv` captures failed cells without hiding them.
- scenario-family, hidden-dynamics, road-boundary, obstacle-timing, outcome,
  termination, profile-outcome, and scenario-family-outcome aggregates are
  written for completed rows.
- unsupported fault-like features remain explicitly not covered.
- guardrail fields remain false.

## What Cannot Be Claimed

The completed subset is not a complete scenario-taxonomy result. It must not be
used for:

- controller-family ranking;
- scenario-family quality conclusions;
- paper-level benchmark evidence;
- recurrent advantage;
- finite-window history necessity;
- level3 self-identification evidence.

The partial completed rows can only be used as debugging evidence that the
runner and metadata plumbing work for sampleable specs.

## Root Cause

The likely root cause is over-tight scenario taxonomy filters:

```text
allowed_labels
require_aeb_infeasible
distance_range
half_width_range
speed / mu randomization
track width / finish distance
max_sample_attempts
```

For S2, S5, and S6, the current combinations often require AEB-infeasible
non-AEB labels while the sampled geometry and dynamics do not produce such
labels within the configured attempts. For S3, the problem is less severe but
still seed-sensitive.

M1728 was a no-rollout metadata preflight, so it could not catch this. The
workflow needs a dedicated sampling-feasibility preflight before any new 864-cell
policy execution.

## Decision

Route to M1733 sampling repair design.

M1733 should not mutate M1728 artifacts in place. It should design a new repaired
taxonomy route with:

- explicit repair of S2/S5/S6 and partial S3 sampling parameters;
- no actor input, profile, checkpoint, reward, PPO, replay, or policy change;
- a reset-only sampling feasibility preflight before any policy rollout;
- exact planned execution-seed coverage for the repaired `72 x 12` matrix;
- label/filter diagnostics per scenario spec;
- unsupported fault-like feature reporting preserved as not covered.

The next executable repair should prove that every planned cell can reset before
any controller-family policy evaluation is attempted.
