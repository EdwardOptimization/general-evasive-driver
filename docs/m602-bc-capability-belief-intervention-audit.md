# M602 BC Capability Belief-Intervention Audit

## Purpose

M602 audits M601 before any actor, recurrent, or PPO update.

Question:

```text
Does M601 justify an actor/fusion coupling design, or should the project first
strengthen hidden objectives or matched-current surfaces?
```

This milestone is audit-only:

```text
no training
no PPO
no route evaluation
no checkpoint promotion
```

## M601 Result

M601 tested the frozen BC5660 actor plus the M598 `CapabilityHead` on fresh and
moderate-OOD matched-current surfaces.

Real-history capability movement:

| Surface | Variant | Mean z-distance | P90 | Above threshold |
| --- | --- | ---: | ---: | ---: |
| fresh | `shuffled_history` | `0.226604` | `0.848551` | `99 / 329` |
| fresh | `wrong_matched_history` | `0.099081` | `0.189764` | `8 / 329` |
| fresh | `delayed_history` | `0.077070` | `0.145870` | `24 / 329` |
| OOD | `shuffled_history` | `0.213130` | `0.758586` | `78 / 287` |
| OOD | `wrong_matched_history` | `0.140707` | `0.269658` | `49 / 287` |
| OOD | `delayed_history` | `0.075159` | `0.167978` | `20 / 287` |

Positive controls:

| Surface | Variant | Mean z-distance | P90 | Above threshold |
| --- | --- | ---: | ---: | ---: |
| fresh | `zero_current_response` | `1.086501` | `1.429596` | `322 / 329` |
| fresh | `reset_hidden` | `0.777646` | `1.079480` | `271 / 329` |
| fresh | `zero_action_history` | `0.520996` | `0.750341` | `271 / 329` |
| OOD | `zero_current_response` | `1.462632` | `1.938969` | `272 / 287` |
| OOD | `reset_hidden` | `0.802511` | `1.275555` | `215 / 287` |
| OOD | `zero_action_history` | `0.461509` | `0.744327` | `215 / 287` |

M601's pre-registered admission rule was met:

```text
real-history variant mean z-distance >= 0.10
and above-threshold rows >= 16
on at least one surface
```

It was met by:

```text
fresh: shuffled_history
OOD:   shuffled_history, wrong_matched_history
```

## What Is Supported

M601 supports this claim:

```text
BC5660 hidden state contains capability information that a training-only
capability head can decode, and real recurrent-history substitutions can move
that decoded capability belief.
```

This matters because M591 found that the same real wrong/delayed histories
barely move the actor action:

```text
fresh wrong_matched_history mean action distance: 0.000552
fresh delayed_history mean action distance:       0.001658
OOD wrong_matched_history mean action distance:   0.000764
OOD delayed_history mean action distance:         0.001218
```

Combined diagnosis:

```text
belief-level signal exists;
action-level coupling is weak.
```

That is a useful blocker localization. The issue is not simply that the hidden
state is empty. The issue is that the actor/fusion/action head does not
materially use this belief on the current matched-current surfaces.

## What Is Not Supported

M601 does not prove:

- driver improvement;
- route or OOD performance improvement;
- closed-loop outcome causality;
- long-history L3 superiority over L1/L2;
- delayed-history self-ID;
- robust fresh matched-wrong capability movement;
- that arbitrary action separation would be grounded or safe.

The mixed pattern matters:

```text
wrong_matched_history passes on OOD but not fresh;
delayed_history remains weak on both surfaces;
zero_current_response remains much stronger than all real-history variants.
```

So the next step must not be "increase an action contrast loss" or "run PPO".
It must design a guarded, grounded action-coupling path.

## Rejected Next Steps

Do not start actor fine-tuning immediately.

Reason:

```text
M601 admits action-coupling design, not action-coupling training.
```

Do not run PPO.

Reason:

```text
There is still no evidence that PPO would preserve or improve the weak
belief-to-action coupling. PPO remains a later proposal generator only after
the exact/no-oracle coupling objective has a sanity gate.
```

Do not force ungrounded action separation.

Reason:

```text
If two hidden states have different capability predictions, the action should
change only when the scenario, margin, or closed-loop recovery target makes
that change meaningful.
```

## Next Branch

M603 should design a guarded capability-to-action coupling objective.

The design should use M591 and M601 together:

```text
M591: action does not move under real wrong/delayed histories.
M601: capability prediction can move under real histories.
```

Design requirements:

1. Keep P0 actor inputs unchanged.
2. Use capability labels and the M598 head only as training/evaluation targets.
3. Preserve normal-branch base action with an action anchor.
4. Only request action movement on rows where capability movement is real and
   the row is selected as scenario-relevant.
5. Prefer grounded targets: local recovery/action-search targets, route
   margin/risk residuals, or a closed-loop boundary corpus.
6. Include an exact no-update evaluator before any optimizer step.
7. Keep PPO and promotion blocked.

The branch should also keep the L3 framing explicit:

```text
h_t = GRU(h_{t-1}, y_t, u_{t-1})
u_t = pi(y_t, h_t)
```

M603 should not claim L3 superiority. It should only design how to couple an
already-detected capability belief to action in a guarded way. A later
history-length observability audit will still be needed to compare L1/L2/L3.

## Decision

```text
bc_capability_belief_intervention_audit_admit_guarded_action_coupling_design
```

M602 passes because it audits M601 without overclaiming and selects a design
milestone before any actor update.

## Next

```text
M603: design guarded capability-to-action coupling objective.
```
