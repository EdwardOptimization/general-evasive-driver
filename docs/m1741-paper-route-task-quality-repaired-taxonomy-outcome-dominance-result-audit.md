# M1741 Paper-Route Task-Quality Repaired Taxonomy Outcome Dominance Result Audit

- status: completed
- decision: `diffuse_outcome_dominance_audit_admit_task_quality_outcome_semantics_redesign`
- audited localization: `docs/m1740-paper-route-task-quality-repaired-taxonomy-outcome-dominance-localization.md`
- audited summary: `runs/m1740_repaired_taxonomy_outcome_dominance_localization/summary.json`

## Summary

M1741 audits M1740 as a clean no-rollout localization pass. The artifacts are
complete, guardrails are clean, and no new rollout, training, replay, PPO,
promotion, private holdout, actor-input change, profile tuning, or
controller-family ranking occurred.

The important result is not a local repair target. M1740 found:

```text
dominant_slice_count: 143
dominant_family_count: 6
dominant_profile_count: 12
outcome_dominance_class: diffuse_outcome_dominance
```

This makes a narrow profile or slice repair the wrong next move. The branch
needs outcome-semantics redesign: family-specific success, mitigation,
off-track, and recovery metrics must be defined before another public rollout or
comparison.

## Audit

| field | observed |
| --- | ---: |
| result class | `task_quality_outcome_dominance_localization_pass` |
| episodes analyzed | `864` |
| dominant slices | `143` |
| dominant families | `6` |
| dominant profiles | `12` |
| outcome dominance class | `diffuse_outcome_dominance` |
| selected metrics finite | `true` |
| guardrail violations | `0` |

The top dominant slice is diagnostic:

```text
aeb_infeasible_stable_aes::L2_window_100_current_tiled
dominant_outcome: off_track_noncollision_noncompletion
dominant_outcome_rate: 1.0
episode_count: 12
```

This does not justify ranking that profile. The same dominance pattern spans all
families and all profiles, so the main issue is workload/outcome semantics.

## Why Redesign

M1738/M1740 indicate that the current repaired taxonomy is executable but not
yet a paper-quality evaluation set:

- ordinary stable avoidance mostly becomes off-track noncompletion;
- AEB-infeasible stable AES mostly becomes off-track noncompletion;
- drift-required and hidden-dynamics stress mix off-track and collision;
- unavoidable mitigation mostly collides, which needs mitigation metrics rather
  than ordinary pass/fail interpretation;
- off-track boundary stress is doing what it says, but its dominance prevents
  fair profile comparison.

This means M1742 should redesign outcome semantics before any new rollout. The
redesign should define what each family is supposed to measure:

- avoidance success versus completion;
- off-track violation severity;
- collision/impact mitigation;
- recovery after maneuver;
- drift-required outcome quality;
- hidden-dynamics stress robustness;
- which rows are benchmark rows versus diagnostic stress rows.

## Claim Boundary

Supported:

- M1740 localization is complete and guardrail-clean.
- Outcome dominance is diffuse, not a single repair target.
- The next route should redesign task-quality outcome semantics.

Unsupported:

- controller-family ranking;
- profile promotion;
- paper-level evidence;
- recurrent advantage;
- level3 self-identification.

## Decision

Admit M1742 task-quality outcome semantics redesign.

M1742 should be design-only: no rollout, no training, no profile tuning, and no
ranking. It should produce a durable semantics document and next manifest for
no-rollout materialization/preflight.
