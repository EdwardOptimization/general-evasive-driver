# M1739 Paper-Route Task-Quality Repaired Scenario Taxonomy Result Audit

- status: completed
- decision: `repaired_scenario_taxonomy_result_audit_route_to_outcome_dominance_localization`
- audited execution: `docs/m1738-paper-route-task-quality-repaired-scenario-taxonomy-execution.md`
- audited summary: `runs/m1738_repaired_scenario_taxonomy_execution/summary.json`

## Summary

M1739 audits M1738 as a clean repaired scenario taxonomy execution pass. The
runner completed the fixed M1734 `864`-cell public diagnostic matrix with zero
execution failures, finite selected metrics, complete repair-provenance
aggregates, and clean guardrails.

The execution pass does not make the workload paper-ready. The raw outcome
distribution is dominated by off-track noncollision noncompletion and collision
outcomes, so the next step must localize outcome dominance before any
controller-family ranking, scenario-quality conclusion, or paper-level claim.

## Pass/Fail Audit

| field | observed | required |
| --- | ---: | ---: |
| result class | `task_quality_scenario_taxonomy_execution_pass` | pass |
| episodes | `864` | `864` |
| execution failures | `0` | `0` |
| selected metrics finite | `true` | `true` |
| profiles | `12` | `12` |
| scenario specs | `72` | `72` |
| scenario families | `6` | `6` |
| guardrail violations | `0` | `0` |
| unsupported features | `5` | `5` |
| silent unsupported approximations | `0` | `0` |
| unsupported faults treated as covered | `false` | `false` |

Required aggregate artifacts are present, including repair-variant,
sampled-label, scenario-family, outcome, termination, profile-outcome, and
scenario-family-outcome tables.

## Outcome Distribution

Raw diagnostic outcomes:

| outcome | episodes | rate |
| --- | ---: | ---: |
| success obstacle pass | `81` | `0.0938` |
| collision failure | `279` | `0.3229` |
| off-track noncollision noncompletion | `504` | `0.5833` |

This is execution-positive but task-quality-incomplete evidence. The workload is
sampleable and measurable, but it is not yet a clean benchmark for profile
ranking because most rows terminate through non-success modes.

## Scenario-Family Pattern

The dominant failure mode differs by family:

- `ordinary_stable_avoidance`: mostly off-track noncollision noncompletion
  (`133/144`) despite being nominally ordinary.
- `aeb_infeasible_stable_aes`: mostly off-track noncollision noncompletion
  (`128/144`).
- `drift_required_avoidance`: mixed off-track (`72/144`) and collision
  (`50/144`).
- `off_track_boundary_stress`: mostly off-track (`105/144`), as expected for a
  stress family but still too dominant for ranking.
- `hidden_dynamics_stress`: mixed collision (`61/144`) and off-track
  (`65/144`).
- `unavoidable_mitigation`: mostly collision (`134/144`), which is expected in
  direction but still needs mitigation-specific scoring before interpretation.

Profile rows also show separation, but M1739 does not rank profiles. Public
diagnostic rows are not a private holdout or a promotion gate, and the workload
quality issue must be localized before comparison.

## Interpretation Boundary

Supported:

- M1738 fixed the M1731/M1734 execution-readiness chain: the repaired taxonomy
  can run all planned cells.
- Repair provenance and sampled-label aggregates are available for analysis.
- Outcome dominance is now measurable rather than blocked by sampling failure.

Unsupported:

- controller-family ranking;
- best-profile selection;
- paper-level benchmark evidence;
- level3 self-identification;
- recurrent advantage from M1738 profile aggregates alone.

## Decision

Route to M1740 no-rollout outcome dominance localization.

M1740 should use existing M1738 episode rows only. It should localize which
scenario families, labels, road-boundary buckets, hidden-dynamics buckets,
profiles, and outcome combinations dominate the non-success mass, then decide
whether the next branch should redesign scenario semantics, add mitigation
metrics, or create a narrower paper-quality evaluation panel.
