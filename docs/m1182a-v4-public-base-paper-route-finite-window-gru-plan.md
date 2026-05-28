# M1182a Paper-Route Finite-Window vs GRU Plan

## Summary

M1182a records a paper-oriented route adjustment before continuing the current
source-rich infrastructure branch. The new governing document is:

```text
docs/paper-route-finite-window-vs-gru-plan.md
```

The key change is that the project should no longer assume the GRU controller
is inherently superior to finite-window command-response feedback. The paper
route should compare current feedback, one-step feedback, finite-window
history, and GRU recurrent belief under matched deployable-input constraints.

## Decision

The route decision is:

```text
paper_route_plan_recorded_continue_with_source_rich_adapter_as_infrastructure_only
```

M1182 no-residual source-rich adapter remains useful, but its role is now
supporting source-rich data generation for the broader paper-route evidence
program. It is not a direct path to training, PPO, promotion, or a GRU
self-identification claim.

## What Is Supported

- Current feedback and finite-window feedback may be strong engineering
  baselines.
- A GRU recurrent-belief claim must be earned by L0/L1/L2/L3 comparisons.
- Future paper claims must be split between engineering performance,
  history-conditioned output feedback, recurrent-belief advantage, and strong
  self-identification.
- Historical proof gates should be audited for utility before remaining active
  training blockers.

## What Is Not Claimed

M1182a does not claim:

- a new driver checkpoint;
- source-rich mining success;
- finite-window superiority;
- GRU superiority;
- private-holdout performance;
- PPO readiness;
- paper-level results.

## Required Follow-Up

The next infrastructure step can still be M1182 no-residual source-rich
adapter. After that, the paper-route sequence should add:

```text
gate utility audit
L0/L1/L2/L3 controller comparison design
same-current same-recent-window different-older-history dataset design
capability prediction probe
controlled behavior comparison
route synthesis
```

## Guardrails

- Do not change actor inputs.
- Do not add hidden or oracle deployable signals.
- Do not continue row-specific repair as the default paper route.
- Do not use all historical proof gates as permanent active blockers without a
  gate utility audit.
- Do not claim recurrent belief unless practical finite-window baselines have
  been tested fairly.
