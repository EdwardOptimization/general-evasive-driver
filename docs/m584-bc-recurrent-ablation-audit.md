# M584 BC Recurrent Ablation Audit

## Purpose

M584 audits the first two BC5660 recurrent-ablation diagnostics:

```text
M582: fresh route seeds       23560..23815
M583: moderate-OOD seeds      24560..24815
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

This milestone is audit-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Evidence Summary

Normal policy metrics:

| milestone | surface | success | collision | mean margin |
| --- | --- | ---: | ---: | ---: |
| M582 | fresh route | 0.691406 | 0.308594 | 1.068165 |
| M583 | moderate-OOD | 0.621094 | 0.378906 | 0.985368 |

Ablation deltas against normal:

| milestone | ablation | success drop | margin drop | collision increase | label |
| --- | --- | ---: | ---: | ---: | --- |
| M582 | reset_recurrent_state | 0.007812 | 0.017594 | 0.007812 | weak |
| M582 | zero_action_history | 0.011719 | 0.052959 | 0.011719 | meaningful |
| M582 | zero_current_response | 0.027344 | 0.144810 | 0.027344 | strong |
| M582 | zero_all_response | 0.027344 | 0.144810 | 0.027344 | strong |
| M583 | reset_recurrent_state | 0.003906 | 0.012892 | 0.003906 | weak |
| M583 | zero_action_history | 0.015625 | 0.036946 | 0.015625 | weak |
| M583 | zero_current_response | 0.035156 | 0.100321 | 0.035156 | strong |
| M583 | zero_all_response | 0.035156 | 0.100321 | 0.035156 | strong |

## What This Supports

The repeated `zero_current_response` result supports:

```text
BC5660 uses the deployable current ego/IMU-like response stream for behavior.
```

This is not a trivial route-only artifact because the signal appears on both:

- fresh same-distribution route seeds;
- fresh moderate-OOD route seeds.

The M582 `zero_action_history` result gives weaker support for previous-command
features on the fresh route block. This signal does not repeat at the same
threshold on moderate-OOD, so it should be treated as suggestive rather than
settled.

## What This Does Not Support

The current evidence does not prove:

```text
BC5660 needs accumulated online-GRU hidden state.
```

`reset_recurrent_state` stays below the meaningful threshold in both M582 and
M583. Therefore, claiming complete recurrent self-identification from these
ablations would be an overclaim.

The current evidence also does not prove:

```text
BC5660 has a causal belief over hidden vehicle capability.
```

`zero_current_response` removes deployable response inputs, but it does not test
whether the same current observation produces different behavior when paired
with a different command-response history. The next proof gate needs to hold the
current scene as fixed as possible and intervene on hidden/history directly.

## Interpretation

The BC branch has now established two useful facts:

1. Scaled L2-to-L3 BC transfers L2-level route behavior into L3 online-GRU
   checkpoints across fresh route and OOD evaluations.
2. BC5660 behavior depends on current deployable response features.

The missing fact is:

```text
The online hidden state changes decisions in a way that is causally tied to
past command-response history.
```

Because reset-hidden is weak, broadening the same reset/zero-current ablation to
BC5661/BC5662 is not the highest-leverage next step. It would likely confirm
current-response dependence again while still leaving hidden-belief causality
unclear.

## Next Diagnostic Direction

M585 should design a sharper history-intervention gate for BC5660. The design
should use existing wrong-history/delayed-history tooling where possible and
should target interventions like:

```text
normal current observation + normal hidden
normal current observation + reset hidden
normal current observation + delayed hidden
normal current observation + wrong matched history hidden
normal current observation + zero-current-response positive control
```

The key evidence should be outcome-related, not just action-difference related:

```text
normal-history margin > wrong-history margin
normal-history success > wrong-history success
delayed-history or wrong-history causes measurable degradation on accepted rows
```

M585 should pre-register:

- source snapshot construction;
- matching criteria for current observation / scene similarity;
- accepted-row count thresholds;
- action-divergence and terminal-margin thresholds;
- positive and negative controls;
- failure taxonomy for no-signal, source-narrow signal, or tooling mismatch.

## Decision

```text
bc_recurrent_ablation_audit_admit_history_intervention_design
```

M584 passes because it records the evidence boundary and blocks promotion/PPO
until a sharper causal history-intervention diagnostic is designed.

## Next

```text
M585: design BC5660 history-intervention gate.
```
