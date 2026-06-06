# M2863 Engineering Controller Route A Response-Predictive Recurrent-Belief Response-Prediction Localization Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2864_localized_response_prediction_training_recipe_design`
- manifest: `experiments/manifests/m2863-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-localization-branch-synthesis.json`
- synthesis artifact: `docs/m2863-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-localization-branch-synthesis.md`
- parent audit: `docs/m2862-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-trace-localization-materialization-result-audit.md`
- follow-up manifest: `experiments/manifests/m2864-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design.json`
- next: `m2864-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design`

## Evidence Summary

The response-predictive recurrent-belief branch from M2843 through M2862
produced a complete but still diagnostic evidence chain:

```text
M2846: implementation smoke produced response-predictive recurrent-belief checkpoint
M2848: bounded continuation produced continuation candidate
M2850: paired closed-loop delta panel showed zero success but positive clearance deltas
M2854: existing-artifact localization showed clearance/progress tradeoff and low-speed issue
M2857: per-step telemetry localized unresolved response-prediction timing
M2859: response-prediction trace instrumentation materialized 12288 trace rows
M2861: trace localization materialized 1152 localization rows and 3 recipe-signal rows
M2862: audit accepted M2861 as complete claim-safe diagnostic evidence
```

Key accepted M2861 facts:

```text
localization rows: 1152
channel summary rows: 36
recipe signal rows: 3
relative high error rows: 289
terminal gap accounted rows: 863
actuator_response_prediction_loss_weight_review: 155
ego_response_prediction_loss_weight_review: 134
horizon_boundary_masking_preserved: 863
```

## Supported Claims

This branch supports the following bounded claims:

```text
response-predictive recurrent-belief implementation exists and can be run in
closed-loop diagnostic panels

the current continuation candidate is not ready for ranking or promotion

M2850/M2857/M2859/M2861 produced diagnostic evidence that localizes
response-prediction, clearance/progress, low-speed, and horizon-mask issues

the actor contract remains actor 72/action 3 with no hidden/oracle actor inputs
or future-label actor visibility
```

## Falsified Claims

This branch does not support:

```text
checkpoint superiority
repair success
driver performance
validation readiness or validation result
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```

It also rejects direct PPO continuation from M2861 recipe-signal rows because
those rows are public diagnostic artifacts and require a bounded recipe design
with rollback and audit gates.

## Failure Taxonomy Summary

The dominant failure/risk classes are:

```text
metric_artifact:
  response-prediction error and horizon gaps are diagnostic and can be
  misread as performance if not guarded.

objective_overfit:
  M2850 explanatory rows are public diagnostic rows and cannot be optimized as
  validation denominators.

proof_washout:
  localized response-prediction changes could improve auxiliary losses while
  losing closed-loop clearance/progress behavior unless rollback gates are
  explicit.

contract_violation:
  future response labels must remain actor-invisible and cannot become actor
  inputs.
```

## Public-Gate Overfit Risk

Public-gate overfit risk remains medium. M2861 localized useful recipe signals,
but the source is still the M2850 explanatory diagnostic surface. Continuing is
allowed only because the next task is design-only and must require fresh-surface
or rollback evidence before any implementation is interpreted.

## Next Branch Decision

Decision:

```text
continue_to_m2864_localized_response_prediction_training_recipe_design
```

Rationale:

```text
M2861 changed the evidence state enough to justify a bounded recipe design, but
not enough to train directly. The next milestone must specify exact loss
weighting/masking, public-row overfit guards, fresh-surface requirements,
rollback criteria, and result-audit gates before implementation.
```

M2863 therefore resets the branch cadence with a `continue` synthesis decision
and registers M2864 as the next bounded design milestone.

## Rejected Shortcuts

M2863 rejects:

```text
direct training from M2861 recipe signals
promotion or ranking from response-prediction localization
using M2850 explanatory rows as ordinary validation denominators
changing actor inputs or exposing future labels to actor input
performance, paper, current-sim, high-fidelity, full-driver, or self-ID claims
```
