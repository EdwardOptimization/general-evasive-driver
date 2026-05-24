# M619 Expanded Sequence Diversity Design

## Purpose

M619 designs the next no-training step after M618 audited M617 as
diagnostic-positive but not optimizer-ready.

M617 facts:

```text
accepted selected sequences: 6
accepted candidate rollouts: 189
accepted physical pairs: 5
accepted left seeds: 4
selected action mode: K=5 constant +0.08 steer
```

The branch has signal, but it needs better evidence governance before another
optimizer or training design.

Scope:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
```

## Main Problem

M617 has two kinds of diversity evidence:

```text
selected best-per-source sequences: 6 rows
accepted candidate rows: 189 rows
```

The selected rows are source-narrow. The candidate rows may contain richer
family/shape diversity, but they are still concentrated on the same six source
rows and are not yet summarized as a first-class artifact.

Also, M617 accepted rows had to be manually joined back to M616 to recover:

```text
source_tier
expansion_reason
original_m609_boundary
m613_accepted_sequence
```

That is an artifact gap. Future sequence mining needs to carry source metadata
directly into all relevant outputs.

## Design Decision

Do not immediately run another larger sequence search.

M620 should first make the sequence miner tier-aware and candidate-set-aware:

```text
1. preserve source metadata in sequence outputs;
2. write a compact accepted_candidate_sequences.csv artifact;
3. summarize accepted candidate-set diversity separately from selected
   best-per-source diversity;
4. keep M613 target thresholds unchanged.
```

This makes the next run auditable before adding new sequence lengths or
families.

## Source Metadata Propagation

When input rows contain these optional columns:

```text
source_tier
expansion_reason
original_m609_boundary
m613_accepted_sequence
```

M620 should propagate them into:

```text
selected_boundary_source_rows.csv
sequence_candidates.csv
accepted_sequences.csv
unaccepted_rows.csv
accepted_candidate_sequences.csv
```

The miner should remain backward-compatible with older source files that do not
contain these columns.

This is metadata only. It must not enter actor input.

## Accepted Candidate-Set Artifact

M620 should add:

```text
runs/<run>/accepted_candidate_sequences.csv
```

This file should include every candidate row that passes acceptance, not only
the selected best sequence per source row.

It should preserve:

```text
source_index
candidate_id
family
sequence_length
steer_delta / throttle_delta / brake_delta
sequence trust metrics
baseline and candidate margin/risk
source metadata columns when present
```

The existing `accepted_sequences.csv` should remain the best-per-source selected
set, so old consumers are not broken.

## Diversity Summaries

M620 summary should distinguish:

```text
accepted_sequence_diversity
accepted_candidate_diversity
accepted_candidate_counts_by_family
accepted_candidate_counts_by_tier
accepted_candidate_counts_by_sequence_length
```

This prevents a future audit from accidentally treating many correlated
candidates on one source row as many independent source examples.

Selected-sequence objective admission should still require source diversity:

```text
accepted selected sequences >= 8
accepted physical pairs >= 6
accepted left seeds >= 6
```

Candidate-set diversity is useful for design, but it does not replace these
source-level thresholds.

## Candidate-Family Policy

M619 does not approve widening trust regions or lowering target thresholds.

Allowed later, after M620 metadata/candidate-set artifacts exist:

```text
add K=7 sequence length
use existing constant_delta and decay_pulse families with K=7
keep per-step action L2 <= 0.10
keep sequence mean L2 <= 0.08
keep sequence max L2 <= 0.10
keep max delta-delta L2 <= 0.08
keep margin/risk acceptance thresholds unchanged
```

Rationale:

```text
M617 near misses are often outside the trust region under K=3/K=5. A longer
low-amplitude prefix may create more integrated effect without allowing a
larger instantaneous action.
```

Not allowed yet:

```text
per-step L2 > 0.10
sequence mean L2 > 0.08
margin threshold < 0.02
risk threshold < 0.05
unconstrained Cartesian sequence search
training from accepted candidates before a later audit
```

## Proposed Milestone Order

M620:

```text
implement tier-aware and candidate-set-aware sequence miner outputs
focused tests
no sequence mining run required except synthetic/unit tests
```

M621:

```text
rerun sequence miner on M616 expanded rows with the same K=3/K=5 settings
only to verify artifact parity and source-tier/candidate-set summaries
```

M622:

```text
optional diagnostic K=7 run with unchanged thresholds if M621 artifacts are
clean
```

M623:

```text
audit source-level and candidate-set diversity before any optimizer design
```

## Contract Checks

```text
actor_input_changed: false
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
expanded_sequence_diversity_design_admit_m620
```

Next blocker:

```text
m620-sequence-tier-aware-miner-implementation
```
