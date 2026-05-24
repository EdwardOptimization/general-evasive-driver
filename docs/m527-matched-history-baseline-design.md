# M527 Matched History Baseline Design

## Purpose

M527 designs the next step after M526 confirms source-diverse natural
history-value event rows. The project now needs matched history baselines to
separate true recurrent belief value from reset-hidden diagnostic artifacts.

No training is run in M527. No actor-input contract change, checkpoint update,
or checkpoint promotion is performed.

## Motivation

M526 provides the strongest recent evidence for recurrent-history value:

```text
source_diverse_history_value_events
18 obstacle-completion event rows
2 natural surfaces
5 probe seeds
2 targets
0 projected event rows
```

But the comparison is still:

```text
L3 online GRU recurrent actor
vs
L0 reset-hidden diagnostic over the same recurrent actor
```

That is a good diagnostic, not a matched baseline. The next evidence layer
should compare deployable policies with comparable training budgets and no
privileged inputs.

## Baseline Levels

Design the baseline family:

```text
L0 feedforward/current observation:
  no recurrent state; same P0 frame at the current step.

L1 one-step command-response:
  current P0 frame including previous command and actuator/IMU-like response,
  but no multi-step recurrent state.

L2 finite command-response window:
  fixed window of recent P0 response/action frames, for example 4 or 8 frames,
  without online recurrent hidden state.

L3 online GRU recurrent belief:
  current mainline actor.
```

The first implementation may start with L0 and L3 if L1/L2 need architecture
plumbing, but it must not call that complete L0/L1/L2/L3 evidence.

## Training And Evaluation Discipline

Matched baselines should use:

```text
same P0/no-wheel/no-oracle actor input contract;
same train/eval seeds where practical;
same curriculum/task distribution;
same PPO budget for each trainable baseline;
same public proof gates;
same natural history-value eval surfaces;
same private-holdout discipline when promotion-level claims start.
```

Forbidden actor inputs remain:

```text
mu, tire, mass, brake scale, actuator tau;
slip or tire forces;
oracle feasibility labels;
TTC or required clearance;
reference path errors;
success/collision/progress labels.
```

## M528 Implementation Target

M528 should not launch long training immediately. It should first implement or
preflight the baseline plumbing:

```text
configurable actor history level;
checkpoint/load compatibility for L0 or L2 when applicable;
smoke train/eval config for the smallest baseline;
history-value evaluation command against M524/M526 surfaces;
manifest fields recording baseline level and input contract.
```

Acceptance for M528:

```text
one baseline level can run a smoke train/eval or diagnostic eval;
actor contract is unchanged;
history-level metadata is written to artifacts;
no checkpoint is promoted;
no comparison is overclaimed as final.
```

## Decision

```text
admit_m528_matched_history_baseline_plumbing
```

Next blocker:

```text
m528-matched-history-baseline-plumbing
```
