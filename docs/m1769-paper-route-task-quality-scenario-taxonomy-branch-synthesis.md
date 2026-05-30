# M1769 Paper-Route Task-Quality Scenario Taxonomy Branch Synthesis

- status: completed
- workflow synthesis decision: `pivot`
- decision: `pivot_to_metric_specific_bounded_panel_design`
- synthesized range: `M1760-M1768`
- no rollout: true
- training/replay/PPO: false

## Evidence Summary

M1760-M1768 completed the revised scenario-taxonomy execution branch and turned
it into a usable diagnostic artifact:

- M1760 designed a deterministic single-cell seed-repair completion protocol
  after M1758 showed the exact failed seed was fragile but neighboring seeds
  were feasible.
- M1761 implemented provenance-aware seed-repair completion helpers.
- M1762 fixed the one-cell execution command, output directory, replacement
  seed, and guardrails.
- M1763 implemented the completion execution CLI with focused tests.
- M1764 executed the single replacement row and wrote a completed `864`-row
  artifact with zero failures and explicit seed-repair provenance.
- M1765 audited the completed artifact as valid.
- M1766 audited completed outcomes and blocked ranking because overall success
  was only `0.0845`, with broad off-track and collision dominance.
- M1767 localized outcome dominance into `305` dominant slices and `291` target
  slices across all `6` scenario families and all `12` profiles.
- M1768 audited M1767 as coherent but diffuse and routed to branch synthesis
  before repair, bounded-panel design, ranking, or paper claims.

The branch achieved its execution goal: the taxonomy matrix is now complete and
diagnostic. It did not achieve benchmark readiness: the completed matrix is too
outcome-dominated and too role-mixed to support controller-family ranking.

## Supported Claims

Supported:

- deterministic one-cell seed repair can complete the revised taxonomy while
  preserving original failure provenance;
- the completed M1764 artifact is internally valid: `864` rows, zero failures,
  finite selected metrics, metric completeness passed, and guardrail count `0`;
- the scenario taxonomy and profile controls can expose meaningful differences;
- the completed outcome issue is not a stale singleton: dominance spans all
  scenario families and all profiles;
- profile ranking remains blocked because task-quality failures dominate the
  matrix.

These are process and task-quality diagnostic claims only.

## Falsified Claims

Falsified or blocked:

- the completed `864`-row taxonomy is not a paper-quality controller-family
  benchmark;
- broad success rate alone is not an interpretable score for mixed benchmark,
  diagnostic-stress, and mitigation rows;
- mitigation rows should not be interpreted with the same success semantics as
  ordinary avoidable obstacles;
- direct best-profile selection is not justified because every profile appears
  in dominant slices;
- another narrow repair milestone on the same full matrix would risk optimizing
  public diagnostic rows instead of producing general task-quality evidence.

## Failure Taxonomy Summary

Observed or active failure classes:

```text
seed_fragility:
  M1758/M1760-M1764 resolved a single reset-time failure with explicit
  replacement-seed provenance, while preserving the original failed row as
  diagnostic evidence.

scenario_sampling_failure:
  The branch exposed and repaired sampling/execution fragility, so this is no
  longer the active blocker.

metric_artifact:
  Mixed roles still make raw success hard to interpret, especially for
  mitigation rows where collision may be expected but severity matters.

behavior_regression / outcome dominance:
  The public completed matrix is dominated by off-track noncompletion in
  benchmark rows and by collision in mitigation rows.
```

The active blocker is now task-quality evaluation design, not execution
plumbing.

## Public-Gate Overfit Risk

Risk level: `high`.

Reasons:

- M1760-M1768 repeatedly inspected and repaired the same public scenario
  taxonomy branch.
- M1767 exposes many fixed public dominant slices, making direct repair tempting
  but overfit-prone.
- The matrix mixes roles with different intended metrics, so optimizing one
  scalar success or one dominant slice family would likely distort the task.
- The seed repair is explicit and auditable, but it still means the completed
  artifact is public diagnostic evidence, not private-holdout evidence.

The next branch should reduce public overfit by designing a bounded,
metric-specific panel before any controller-family comparison.

## Next Branch Decision

Decision:

```text
pivot_to_metric_specific_bounded_panel_design
```

Next branch:

```text
paper_route_metric_specific_bounded_panel
```

Next milestone:

```text
m1770-paper-route-metric-specific-bounded-panel-design
```

M1770 should be design-only. It should define a smaller, metric-specific public
diagnostic panel that separates at least these roles:

- avoidable and stable-AES rows scored by obstacle pass plus road-boundary
  retention;
- drift-required rows scored by avoidance plus controlled recovery;
- hidden-dynamics stress rows scored by robustness without collapsing collision
  and off-track into one scalar;
- unavoidable mitigation rows scored primarily by impact severity and
  mitigation score, not obstacle-pass success.

It should retain the controller-family controls (`L1`, finite-window `L2`,
current-tiled `L2`, `L3_online_gru`, and `L3_reset_control_corrected`) but must
not rank them until the panel has passed materialization, execution, and
outcome-quality audits.

## Claim Boundary

Allowed:

```text
completed taxonomy branch synthesis;
seed-repair completion provenance;
diffuse outcome-dominance diagnosis;
route decision toward a metric-specific bounded panel.
```

Forbidden:

```text
controller-family ranking;
profile promotion;
private-holdout evidence;
paper-level benchmark evidence;
level3 self-identification.
```

## Decision

M1769 passes as a synthesis milestone. Pivot from the full completed taxonomy
branch to a metric-specific bounded-panel design branch before any new repair,
rollout, ranking, or paper-route claim.
