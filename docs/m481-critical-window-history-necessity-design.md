# M481 Critical-Window History-Necessity Design

## Purpose

M481 designs the next wrong-history diagnostic after M480 found a real but
insufficient late one-shot signal:

```text
wrong_late_*_once:
  proof-style rows: 16
  event rows:        0
  probe seeds:       2
```

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## M480 Diagnosis

M480 reduced artificiality compared with M478, but did not pass the natural-late
proof gate. The important asymmetry is:

```text
wrong_once:        0 proof rows
wrong_late_*_once: 16 margin-only rows
wrong_hold_16:    25 proof rows, including 10 event rows
```

This says timing matters, but a one-shot wrong hidden state still usually gets
corrected before producing a closed-loop event. The late-one-shot rows are also
source-narrow, dominated by seeds `10300` and `10800`.

## Key Issue

M480 late-one-shot injection is not fully tail-aligned. At continuation step
`S`, the gate injects the original right hidden state from the matched pair:

```text
left physical state: advanced S steps under normal left rollout
wrong hidden state:  right hidden from original pair step
```

That is useful as a diagnostic, but it may be a stale-history mismatch rather
than the strongest natural wrong-belief intervention. If the question is whether
wrong belief at the critical instant matters, the cleaner test is:

```text
left physical state: advanced S steps under normal left rollout
wrong hidden state:  advanced S steps under the right rollout
```

Then the one-shot swap happens at the critical tail state with a temporally
aligned wrong history.

## Selected M482 Path

Implement a tail-aligned one-shot wrong-history gate.

For each source pair and tail offset `S`:

```text
left_tail_snapshot  = left_seed at left_step + S
right_tail_snapshot = right_seed at right_step + S

normal:
  action_hidden = left_tail_hidden

wrong_tail_once:
  action_hidden = right_tail_hidden for the first action only
  next hidden then follows normal recurrent update from left_tail observation
```

Candidate tail offsets:

```text
S = 4, 8, 12, 16
```

Controls:

```text
normal_tail
wrong_tail_once
reset_tail
zero_current_tail
optional wrong_tail_hold_4 diagnostic, not counted as natural proof
```

This isolates timing while avoiding persistent hidden-state clamping in the
main natural proof claim.

## Why This Before A New Config

A new critical-window environment config would change multiple things at once:

```text
obstacle distance
perception reveal distance
time-to-obstacle
normal margin slack
scenario label mix
```

The tail-aligned gate first tests whether M480 failed because the wrong hidden
state was stale at the late injection point. If tail-aligned one-shot still
remains margin-only and source-narrow, then M483 should design a stricter
critical-window task config.

## M482 Implementation Requirements

Implement a new diagnostic module or extend the persistent gate with explicit
tail alignment. The implementation must:

```text
collect left_step + S and right_step + S snapshots
skip pairs that terminate before the requested tail offset
record the valid tail pair count per offset
record normal margin and wrong-tail margin per offset
separate one-shot rows from held/clamped rows
preserve the P0 actor-input contract
avoid training and checkpoint promotion
```

Suggested artifact layout:

```text
runs/m482_tail_aligned_wrong_history_gate/summary.json
runs/m482_tail_aligned_wrong_history_gate/tail_outcomes.csv
runs/m482_tail_aligned_wrong_history_gate/tail_variant_summary.csv
```

## Pass / Fail Criteria

Natural tail-aligned positive evidence requires:

```text
wrong_tail_*_once proof_candidate_count >= 16
success/collision/completion rows >= 4
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
```

Diagnostic-only evidence:

```text
margin-only proof rows with 0 event rows
source-narrow rows with probe_seed_count < 6
signal only from held/clamped variants
```

Negative evidence:

```text
wrong_tail_*_once proof_candidate_count == 0
or action/trajectory perturbation remains no-effect across all offsets
```

If M482 is positive, the next step can be a source-diverse tail-aligned proof
surface export. If M482 is diagnostic-only or negative, M483 should design a new
critical-window task config with less recovery time before obstacle encounter.

## Guardrails

M482 must not:

```text
train or update a checkpoint
promote a checkpoint
change actor inputs
count clamped rows as natural proof
relax source-diversity gates to fit M480/M482
turn private holdout evidence into repair targets
```

## Decision

```text
admit_m482_tail_aligned_wrong_history_gate_implementation
```

No checkpoint is promoted.
