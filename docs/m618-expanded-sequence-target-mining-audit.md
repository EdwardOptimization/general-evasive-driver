# M618 Expanded Sequence Target Mining Audit

## Purpose

M618 audits the M617 diagnostic-positive expanded sequence target result before
any optimizer, training, or PPO step.

Question:

```text
Does M617 provide an optimizer-ready sequence target corpus?
```

Answer:

```text
No. It provides stronger repeatability evidence than M613, but accepted
sequence diversity remains too narrow for training.
```

## Evidence

M617 artifacts:

```text
runs/m617_expanded_sequence_target_miner/summary.json
runs/m617_expanded_sequence_target_miner/accepted_sequences.csv
runs/m617_expanded_sequence_target_miner/unaccepted_rows.csv
runs/m617_expanded_sequence_target_miner/sequence_candidates.csv
runs/m617_expanded_sequence_target_miner/sequence_target_corpus.npz
```

M617 used:

```text
runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv
```

It kept M613 thresholds unchanged:

```text
margin_improvement >= 0.02
or risk_improvement >= 0.05
```

## What Improved

M617 clearly improves repeatability over M613:

| Metric | M613 | M617 |
| --- | ---: | ---: |
| source rows | `17` | `30` |
| candidate rollouts | `5916` | `10440` |
| selected accepted sequences | `1` | `6` |
| accepted mean margin improvement | `0.020817` | `0.056784` |
| accepted max margin improvement | `0.020817` | `0.093048` |
| target corpus rows | `1` | `6` |

This supports both prior diagnoses:

```text
M611: one first action is too myopic
M614/M615: source expansion is useful
```

The accepted rows cover:

```text
2 surfaces
2 variants
3 targets
```

This is meaningfully better than M613's one-row result.

## What Still Blocks Training

M617 misses the pre-registered objective-admission breadth target:

| Criterion | Target | M617 |
| --- | ---: | ---: |
| accepted sequences | `>= 8` | `6` |
| physical pairs | `>= 6` | `5` |
| left seeds | `>= 6` | `4` |
| max physical-pair dominance | lower is better | `0.333333` |

The selected action mode is also narrow:

```text
all selected sequences:
  family = constant_delta
  K = 5
  delta = +0.08 steer, 0 throttle, 0 brake
```

This is not enough for a general sequence-target objective. Training from this
corpus would likely teach a narrow extra-steer correction rather than a
general response-aware maneuver model.

## Source-Tier Interpretation

The M617 accepted rows, joined with M616 source tiers:

| Tier | Accepted Rows |
| --- | ---: |
| core_boundary | `1` |
| near_boundary | `3` |
| support_boundary | `2` |

Only one accepted row is from the original M609 core boundary set; the other
accepted rows are from M616's near/support expansion. This validates the source
expansion idea, but it also means the stronger margins partly come from less
fragile rows.

Future sequence runs should carry source-tier metadata directly into
`accepted_sequences.csv` and `unaccepted_rows.csv`. M617 could be joined
manually, but the artifact itself should preserve this provenance.

## Candidate-Level Observation

M617 selected only one best sequence per accepted source row, but the candidate
table contains many accepted candidates:

```text
candidate_acceptance_reason_counts:
  margin_improved: 189
```

Those accepted candidates are concentrated on only six source rows. This means
there may be action-family diversity inside accepted candidate sets, but it is
not yet source-diverse enough to become a training corpus.

The next design should evaluate both:

```text
1. source diversity: more accepted physical pairs and left seeds;
2. candidate diversity: whether multiple accepted candidates per source can be
   represented as a preference/set target without creating conflicting labels.
```

## Remaining Near Misses

The strongest unaccepted rows remain close:

| Source | Best Improvement | Rejection |
| ---: | ---: | --- |
| `1` | `0.025914` | outside_sequence_trust_region |
| `15` | `0.020958` | candidate_collision |
| `30` | `0.019548` | outside_sequence_trust_region |

The dominant rejection patterns remain:

```text
outside_sequence_trust_region: 4555
insufficient_margin_or_risk_improvement: 3946
candidate_collision: 1750
```

Do not lower the trust region or target threshold in response to these near
misses. The safer next branch is to design broader sequence candidates that
keep per-step trust limits but vary horizon and shape.

## Decision

Decision:

```text
expanded_sequence_target_audit_admit_diversity_design
```

M617 is diagnostic-positive but not optimizer-ready.

Blocked:

```text
actor training
PPO
checkpoint promotion
sequence-target optimizer admission
```

Next branch:

```text
m619-expanded-sequence-diversity-design
```

M619 should design a no-training follow-up that:

```text
1. propagates source_tier / expansion_reason into sequence miner outputs;
2. audits accepted candidate-set diversity instead of only best-per-source rows;
3. considers longer low-amplitude sequence families such as K=7 ramps/pulses
   while keeping per-step trust regions and target thresholds unchanged;
4. keeps optimizer admission blocked until accepted physical pairs and left
   seeds pass the pre-registered breadth target.
```

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
```
