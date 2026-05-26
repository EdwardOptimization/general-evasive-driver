# M995 V4 Public Base Capability-Step Temporal-History Audit

## Purpose

M995 audits the M994 result before any corpus export, objective design,
training, PPO, or promotion.

M994 is useful, but the claim scope must be precise:

```text
positive:
  temporal-history dependence under capability-step events

not positive:
  cross-fault wrong-history self-identification
```

## Evidence Split

M994 summary:

```text
result_class: sequence_temporal_history_positive
accepted_sequence_rows: 277
accepted_cross_fault_sequence_rows: 0
accepted_temporal_sequence_rows: 277
unique_accepted_fault_pairs: 9
unique_accepted_seeds: 17
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Accepted variants:

```text
reset_then_warm_history: 253
delayed_capability_history: 24
```

Zero-accepted variants:

```text
cross_fault_response_window: 0
wrong_commands_preferred_response: 0
wrong_response_preferred_commands: 0
zero_command_history_window: 0
```

## Claim Scope

Allowed claim:

```text
The M974 recurrent actor has outcome-relevant temporal-history dependence in
capability-step scenarios. Resetting hidden state shortly before the decision
and warming it for 4-12 frames, or using delayed capability history, can reduce
clearance margin relative to uninterrupted normal history.
```

Blocked claim:

```text
The actor has demonstrated source-diverse cross-fault wrong-history
self-identification.
```

The blocked claim remains false because all cross-fault/action-response
mismatch sequence variants have zero accepted rows.

## Source Diversity

M994 temporal accepted rows are source-diverse enough to justify a corpus export
design:

```text
accepted temporal rows: 277
accepted fault pairs: 9
accepted seeds: 17
normal_failed_rows: 0
rejected_trace_rows: 0
```

Top accepted groups include:

```text
global_mu_drop -> brake_authority_drop: 53
front_lateral_authority_drop -> global_mu_drop: 43
combined_fault -> brake_authority_drop: 32
delay_noise_fault -> steering_fault: 30
global_mu_drop -> front_lateral_authority_drop: 30
brake_authority_drop -> global_mu_drop: 29
drive_authority_drop -> rear_lateral_authority_drop: 29
combined_fault -> front_lateral_authority_drop: 28
```

This is not a single-seed or single-pair artifact.

## Meaning For The Driver Hypothesis

M994 supports a narrower but still important driver-like claim:

```text
The policy's recurrent state is not just a one-frame filter. It carries
behavior-relevant temporal evidence under hidden capability changes.
```

This is aligned with the human-driver framing:

```text
a driver needs continuous recent feel of the car;
after a sudden capability change, a few frames of fresh observation may be
insufficient to restore the same internal belief/action state.
```

But M994 does not yet prove:

```text
if the policy is given a plausible history from the wrong vehicle/fault, it
will make the wrong emergency maneuver.
```

## Route Decision

Decision:

```text
route_to_temporal_sequence_corpus_export_design
```

Reasoning:

```text
Temporal evidence is source-diverse and outcome-relevant.
Cross-fault evidence remains absent.
The next artifact should preserve the temporal evidence in a trainable/auditable
corpus format before any objective update.
```

Do not train directly from M994 CSVs. They contain metrics, not enough structured
arrays for exact objective sanity.

## M996 Requirements

M996 should design a temporal sequence corpus export.

It must include:

```text
normal observation at decision
normal hidden at decision
normal action sequence
variant name
variant initial hidden
variant action sequence
sequence mask
history_length
terminal margin gap
success_drop
fault pair / seed metadata
weight
```

It must also define:

```text
exact objective sanity on the exported corpus
source-diversity gates
no actor-input contract changes
no hidden labels as actor inputs
no PPO
no promotion
```

The first corpus should include temporal accepted variants only:

```text
reset_then_warm_history
delayed_capability_history
```

Cross-fault zero variants should remain diagnostic hard negatives, not positive
targets.

## Blocked Routes

Do not:

```text
run PPO;
promote;
call M994 cross-fault positive;
export cross-fault rows as positives;
use private holdout;
claim per-wheel/asymmetric fault support;
train from CSV metrics without exact corpus sanity.
```

## Next

```text
m996-v4-public-base-temporal-sequence-corpus-export-design
```
