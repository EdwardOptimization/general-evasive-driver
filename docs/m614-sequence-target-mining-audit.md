# M614 Sequence Target Mining Audit

## Purpose

M614 audits the M613 diagnostic-positive sequence target result before any
optimizer or training step.

Question:

```text
Is one accepted sequence enough to train or should the next step expand source
diversity / repeatability first?
```

Scope:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
```

## Evidence

M613 artifacts:

```text
runs/m613_sequence_target_miner/summary.json
runs/m613_sequence_target_miner/accepted_sequences.csv
runs/m613_sequence_target_miner/unaccepted_rows.csv
runs/m613_sequence_target_miner/sequence_candidates.csv
runs/m613_sequence_target_miner/sequence_target_corpus.npz
```

M613 evaluated `5916` sequence candidates across `17` M609 boundary rows.

## Positive Signal

M613 found a real sequence-target signal:

| Metric | Value |
| --- | ---: |
| accepted candidate rows | `2` |
| selected accepted sequences | `1` |
| accepted margin improvement | `0.020817` |
| accepted family | `constant_delta` |
| accepted sequence length | `5` |
| accepted target corpus rows | `1` |

Accepted row:

```text
source_index: 7
surface: fresh
variant: delayed_history
target: future_braking_deceleration
left_seed / step: 25567 / 3
sequence: K=5, constant +0.08 steer
baseline_margin: 0.274439
target_margin: 0.295255
margin_improvement: 0.020817
```

This supports the M611 diagnosis:

```text
short sequence target > single first-action target
```

because M610 found zero accepted first-action targets on the same boundary
source set.

## Limitations

The accepted evidence is too narrow:

| Diversity metric | Value |
| --- | ---: |
| accepted source rows | `1` |
| accepted physical pairs | `1` |
| accepted left seeds | `1` |
| accepted surfaces | `1` |
| accepted variants | `1` |
| accepted targets | `1` |

The best unaccepted candidates show why this should not be promoted into
training yet:

```text
best unaccepted improvement: 0.025914
main blocker: outside sequence trust region
second blocker: candidate collision
```

So the branch has signal, but not enough breadth or safety evidence.

## Decision

Decision:

```text
sequence_target_mining_audit_admit_source_expansion_design
```

Do not train on the one accepted sequence. Do not design an optimizer yet.

Next branch:

```text
m615-sequence-source-expansion-design
```

M615 should design how to expand the sequence-target source set before another
sequence miner run.

## Requirements For M615

M615 should consider:

```text
1. lower source-screen capability_z threshold only for source selection,
   not for target acceptance;
2. scan additional boundary windows, e.g. margin <= 0.75 or <= 1.0;
3. include deterministic shuffled-history only if hidden provenance can be
   recorded;
4. add neighboring left steps around accepted source rows;
5. keep source-diversity minimums explicit;
6. rerun sequence mining only after the source set is larger and auditable.
```

M615 must keep M613 target acceptance thresholds unchanged:

```text
margin_improvement >= 0.02
or risk_improvement >= 0.05
```

The next sequence run should aim for at least:

```text
accepted sequences >= 8
accepted physical pairs >= 6
accepted left seeds >= 6
accepted surfaces >= 2 where available
accepted variants >= 2 where available
```

These are not promotion thresholds; they are minimum criteria for considering
an objective/corpus design later.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
```
