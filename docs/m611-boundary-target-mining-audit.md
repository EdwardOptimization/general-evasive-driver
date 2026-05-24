# M611 Boundary Target Mining Audit

## Purpose

M611 audits the M610 zero-accepted result before changing the target-mining
formulation.

Question:

```text
Why did near-boundary source rows still fail to produce accepted first-action
targets?
```

Scope:

```text
no training
no PPO
no checkpoint promotion
no threshold retrofitting
```

## Evidence

M610 used:

```text
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
runs/m610_boundary_conditioned_grounded_target_miner/target_candidates.csv
runs/m610_boundary_conditioned_grounded_target_miner/unaccepted_rows.csv
runs/m610_boundary_conditioned_grounded_target_miner/summary.json
```

It evaluated `3332` candidates from `17` near-boundary rows with an `80`-step
continuation horizon.

## Result Summary

| Metric | Value |
| --- | ---: |
| source rows | `17` |
| candidate rollouts | `3332` |
| accepted targets | `0` |
| unaccepted rows | `17` |
| max candidate improvement | `0.017662` |
| max trust-region improvement | `0.015549` |
| target corpus written | `false` |
| optimizer admission | `false` |

Rejection counts:

| Reason | Count |
| --- | ---: |
| candidate collision | `1443` |
| insufficient margin or risk improvement | `1283` |
| outside action trust region | `606` |

## What This Rules Out

M606 could have failed because its source rows were far from boundary. M609
addressed that by selecting rows with collision or margin-window evidence.
M610 still accepted zero targets.

M610 also used the `80`-step horizon that M609 used for boundary screening, so
the result is not just a `40`-step horizon artifact.

The best trust-region candidate improved margin by `0.015549`, but no
accepted-eligible trust-region candidate reached the pre-registered `0.02`
threshold. Diagnostic lower-threshold checks show only one source row would
produce candidates at `0.010`, and none at `0.015` under the non-collision hard
filters.

Therefore the main blocker is not:

```text
source rows too far from boundary
continuation horizon too short
accepted rows hidden by logging
threshold artifact alone
```

## Classification

The supported blocker is:

```text
first-action locality / myopia
```

A single first-action override, followed immediately by the unchanged BC5660
policy, is too weak to produce a robust margin improvement on these rows. Many
large-improvement directions are either outside the action trust region or
collide.

This suggests that the useful control object is probably a short maneuver
sequence rather than a one-step action.

## Decision

Decision:

```text
boundary_target_mining_audit_admit_sequence_target_design
```

Next:

```text
m612-sequence-target-mining-design
```

M612 should design a no-training sequence/trajectory target miner before any
actor update. M612 should not loosen M610 thresholds and reinterpret prior
results as accepted.

## Requirements For M612

M612 should design:

```text
source rows:
  M609 boundary_source_rows.csv

candidate object:
  short action sequence, not only first action

sequence length:
  start with 3 to 5 control steps

candidate families:
  constant small delta
  decaying steering / braking pulse
  steer then brake-release sequence
  brake-release then steer sequence

trust region:
  per-step action_l2 <= 0.10
  sequence_l2 <= 0.20
  smoothness / delta-delta bound

rollout:
  execute sequence prefix
  then continue under unchanged BC5660
  horizon aligned with M609/M610, initially 80 steps

acceptance:
  no candidate collision
  no off-road / spin-out
  margin improvement >= 0.02
  or risk improvement >= 0.05

artifacts:
  sequence_candidates.csv
  accepted_sequences.csv
  unaccepted_rows.csv
  optional sequence_target_corpus.npz
```

Any accepted sequence targets remain diagnostic until source diversity and
repeatability are improved.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
```
