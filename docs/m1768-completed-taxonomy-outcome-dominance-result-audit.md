# M1768 Completed Taxonomy Outcome-Dominance Result Audit

- status: completed
- decision: `diffuse_dominance_route_to_branch_synthesis_before_repair_or_ranking`
- audited summary: `runs/m1767_completed_taxonomy_outcome_dominance_localization/summary.json`
- parent localization: `docs/m1767-completed-taxonomy-outcome-dominance-localization.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1768 audits the M1767 completed-taxonomy localization result. The localization
artifact is internally coherent and useful, but it does not justify immediate
controller-family ranking or a narrow profile repair.

M1767 outcome state:

```text
result_class: task_quality_outcome_dominance_localization_pass
episode_count: 864
dominant_slice_count: 305
target_dominant_slice_count: 291
dominant_family_count: 6
dominant_profile_count: 12
outcome_dominance_class: diffuse_outcome_dominance
guardrail_violation_count: 0
```

The dominance spans all scenario families and all profiles. It also separates
into at least three behavior modes:

- benchmark and avoidance-success rows are mainly off-track dominated;
- hidden-dynamics and boundary rows mix collision and off-track failures;
- mitigation rows are collision dominated and may need role-specific
  interpretation before comparing profiles.

## Audit Findings

M1767 satisfies its process gates:

- it uses existing M1764/M1766 artifacts only;
- it writes target slices for evaluation role, metric family, scenario family,
  profile, hidden dynamics, road boundary, obstacle timing, and lateral buckets;
- all guardrail flags remain false;
- no profile ranking or paper-level claim is made.

The result blocks these routes:

- direct controller-family ranking, because broad task-quality failure
  dominates profile differences;
- direct best-profile selection, because every profile appears in dominant
  slices;
- direct paper benchmark claim, because the matrix is a public diagnostic
  artifact and overall success remains too low;
- narrow one-profile repair, because the top slices include multiple profiles,
  roles, metrics, and context buckets.

## Route Decision

Route to M1769 branch synthesis before any new repair design.

Reasoning:

- M1760-M1768 have completed the one-cell seed repair path and proved the
  completed artifact is valid, but the completed artifact is still
  outcome-dominated.
- M1767 shows diffuse dominance, not one stale singleton or one bad profile.
- The branch is close to the workflow synthesis cadence, and the synthesis
  trigger has fired: another local repair/design milestone would risk
  over-fragmenting the branch.
- A synthesis milestone can decide cleanly whether the next branch should be
  task-quality repair, metric-semantics refinement, bounded diagnostic-panel
  design, or a paper-route benchmark redesign.

M1769 should synthesize M1760-M1768 and produce a next-branch decision. The
current audit does not choose the repair implementation itself.

## Guardrails

- environment rollout started: `false`
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

- M1767 localization is a valid no-rollout diagnostic artifact;
- completed taxonomy dominance is diffuse across all families and profiles;
- ranking remains blocked;
- branch synthesis is the next justified process step.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Admit M1769 paper-route task-quality scenario taxonomy branch synthesis.

M1769 must answer the synthesis questions over M1760-M1768 and decide the next
branch without rollout, training, profile tuning, ranking, paper-level claims,
or self-identification claims.
