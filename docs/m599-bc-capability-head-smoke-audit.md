# M599 BC Capability Head Smoke Audit

## Purpose

M599 audits the M598 frozen-actor capability-head smoke before any actor or
hidden fine-tuning.

This milestone is audit-only:

```text
no training
no PPO
no route evaluation
no checkpoint promotion
```

## What M598 Proves

M598 proves the M596 corpus and objective path are live:

| metric | result |
| --- | ---: |
| train regression drop | 0.791643 |
| validation regression drop | 0.668041 |
| train rank drop | 0.321892 |
| validation rank change | -0.166812 |
| train action-anchor MSE | 0.0 |
| validation action-anchor MSE | 0.0 |
| actor parameters changed | false |
| labels enter actor input | false |
| promoted | false |
| PPO used | false |

The supported positive result is:

```text
future-response capability targets are learnable from BC5660 base hidden states.
```

So the hidden state is not empty noise. A training-only head can decode braking,
yaw, and lateral response labels from `base_next_hidden_seq`.

## What M598 Does Not Prove

M598 does not prove:

- the driver is improved;
- actor actions use the decoded capability;
- wrong-history or delayed-history action sensitivity is fixed;
- route/OOD performance improves;
- recurrent self-ID is demonstrated under counterfactual intervention.

The actor was frozen, so M598 cannot change driving behavior by design.

## Updated Diagnosis

Combining M591 and M598:

```text
M591: real wrong/delayed hidden barely changes action.
M598: base hidden contains learnable future-response capability signal.
```

This leaves two plausible blockers:

1. Capability information exists in hidden, but the actor head/fusion does not
   use it for action.
2. The head learned capability from ordinary rollout hidden states, but
   counterfactual wrong/delayed hidden states may still not change capability
   predictions in matched-current interventions.

These are different. Actor fine-tuning before distinguishing them would be
premature.

## Rejected Next Step

Do not immediately fine-tune actor or recurrent modules.

Reason:

```text
we have not yet shown that the learned capability head is sensitive to the same
wrong/delayed hidden interventions that failed action sensitivity in M591.
```

If capability predictions are also insensitive to wrong/delayed hidden, then
actor fine-tuning is targeting the wrong bottleneck. The hidden/corpus objective
or matched-current surface must be strengthened first.

## Next Probe

M600 should design a capability-belief intervention probe.

Use the frozen M598 `capability_head.pt` and the M591/M586 snapshot machinery to
compare capability predictions under:

```text
normal hidden
reset hidden
delayed hidden
wrong matched hidden
shuffled hidden
scaled hidden
random hidden
```

The key question:

```text
Do wrong/delayed histories change predicted capability even when actions do not?
```

Interpretation:

| result | meaning | next branch |
| --- | --- | --- |
| capability changes, action does not | belief signal exists; action coupling is missing | design fusion/action coupling fine-tune |
| capability also does not change | hidden manifold is action- and belief-equivalent under these interventions | strengthen hidden objective or mine stronger pairs |
| random hidden changes capability only | off-manifold sensitivity, not self-ID evidence | avoid overclaiming; improve real-history contrast |
| reset changes capability but wrong does not | reset is too blunt; matched wrong-history surface remains weak | refresh matched-current pairs |

## Decision

```text
bc_capability_head_smoke_audit_admit_belief_intervention_design
```

M599 passes because it separates M598's data/objective signal from driver
improvement and redirects the next step to a capability-belief intervention
probe before any actor fine-tuning.

## Next

```text
M600: design capability-belief intervention probe.
```
