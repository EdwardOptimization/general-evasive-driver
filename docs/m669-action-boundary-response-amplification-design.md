# M669 Action-Boundary Response Amplification Design

## Purpose

M669 designs the next branch after M667/M668 showed that normal-success
near-boundary source windows exist, but compatible wrong-history substitutions
do not create sustained action-sequence or outcome gaps in the current BC5660
actor.

The goal is not to promote a checkpoint. The goal is to create a conservative
ladder that tests whether the actor/action boundary can be made more sensitive
to response history without violating the human-view actor contract.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Evidence Being Addressed

M667 found:

```text
near_boundary_preferred_snapshots: 204
candidate_rows:                   9600
accepted_rows:                       0
wrong_first_action_l2 >= 0.002:   8934 rows
wrong_action_sequence_mean_l2 >= 0.006: 4 rows
preferred/rejected mean_l2 >= 0.010:    0 rows
margin_gap >= 0.010:                    0 rows
success_drop_rate:                      0.000
```

Interpretation:

```text
source windows exist;
first-action sensitivity exists;
but the current actor boundary attenuates wrong-history effects too quickly
and does not affect closed-loop margin or success.
```

So continuing source mining with the same actor is lower leverage unless the
scenario distribution changes. The next high-leverage question is whether a
bounded action-boundary objective can create sustained history-conditioned
action separation while preserving normal behavior.

## Design Principle

Do not jump directly to actor training or PPO.

Use a staged ladder:

```text
M670: shadow objective design
M671: shadow objective implementation / no actor mutation
M672: exact no-update evaluator
M673: tiny gated actor-coupling design only if shadow evidence is positive
```

The first stages should answer:

```text
Can a small head/adapter, reading the same frozen actor features or hidden
state, learn sustained normal-vs-wrong sequence separation on source-heldout
near-boundary windows while preserving normal-action targets?
```

If the shadow objective fails, do not update the actor.

## Allowed Inputs

The deployable actor input contract remains unchanged:

```text
P0 human-view no-wheel 72-dim observation
online GRU hidden from command-response history
```

Training/evaluation metadata may include:

```text
source_index
surface
target label for grouping only
normal_margin
wrong_margin
window_class
candidate action distances
```

Metadata must not enter the deployable actor observation.

## Candidate Data

Use M667 artifacts:

```text
runs/m667_normal_success_boundary_source_miner/normal_window_rows.csv
runs/m667_normal_success_boundary_source_miner/candidate_scores.csv
runs/m667_normal_success_boundary_source_miner/summary.json
```

Initial candidate set:

```text
normal-success near-boundary rows only
normal_margin in [0.0, 1.0]
normal_success == true
wrong_success == true initially allowed for diagnostics
wrong_first_action_l2 >= 0.002 preferred
source-heldout split by physical seed pair
```

This data is not enough for promotion, but it is enough for a shadow diagnostic
because it contains valid preferred branches and first-action wrong-history
sensitivity.

## Shadow Objective

M670 should design a frozen-actor shadow module, not a main actor update.

Candidate module:

```text
response_amplifier_head(feature, hidden) -> action_delta_sequence[K, 3]
```

Feature views to compare:

```text
fused actor feature
next recurrent hidden
fused + next recurrent hidden
```

Loss terms:

```text
L_normal_anchor:
  normal hidden output should stay close to stored normal action sequence

L_wrong_separation:
  wrong hidden output should separate from normal output by a target sequence
  margin, using bounded delta magnitude

L_zero_delta_regularizer:
  keep deltas small unless wrong-history contrast is active

L_source_balance:
  equalize source/seed-pair contribution
```

This is not claiming the wrong action is physically better or worse. It is a
diagnostic that tests whether the feature boundary can support sustained
history-conditioned action separation without corrupting normal behavior.

## Shadow Pass Criteria

A shadow run may pass only if:

```text
normal validation action MSE <= baseline normal sequence MSE + tolerance
wrong-history sequence gap L2 improves by >= 3x over frozen actor baseline
wrong-history sequence gap L2 mean >= 0.010 on source-heldout rows
at least 2/3 seeds pass
actor checksum unchanged
only shadow head checkpoints written
```

If these fail, the next branch should revisit representation or source
construction, not actor coupling.

## Exact No-Update Evaluator

Before any actor coupling, an exact evaluator must compute:

```text
normal action retention
wrong-history sequence separation
source-heldout separation
surface/target split summaries
first-action vs sequence-gap decomposition
```

This prevents the project from repeating the M652/M658 pattern where training
metrics looked active but exact full-corpus gaps remained too small.

## Actor-Coupling Admission

Actor coupling remains blocked unless shadow evidence passes.

If it passes, a later design may consider:

```text
small adapter or residual head
normal-action anchor
wrong-history sequence-separation loss
strict trust region to BC5660
exact full-corpus gates before replay
replay gates before any checkpoint promotion
```

Promotion remains much later and requires closed-loop replay/outcome evidence,
not just supervised sequence separation.

## Negative Result Interpretation

M670/M671 should classify failures explicitly:

```text
normal_anchor_failure:
  shadow cannot preserve normal action sequence.

wrong_sequence_gap_failure:
  shadow preserves normal behavior but cannot create sustained wrong-history gap.

source_holdout_overfit:
  train gap improves but source-heldout gap does not.

feature_view_failure:
  fused, next-hidden, and fused+hidden views all fail.
```

## Forbidden Shortcuts

Do not:

- run PPO;
- mutate the actor in M670/M671 shadow stages;
- promote any checkpoint;
- use hidden parameters, labels, or feasibility as actor input;
- claim self-ID proof from first-action differences alone;
- skip exact full-corpus evaluation before actor coupling.

## Decision

```text
action_boundary_response_amplification_design_admit_shadow_design
```

## Next

```text
m670-action-boundary-response-amplification-shadow-design
```
