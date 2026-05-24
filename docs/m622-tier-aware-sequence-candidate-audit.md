# M622 Tier-Aware Sequence Candidate Audit

## Purpose

M622 audits the tier-aware accepted candidate-set evidence from M621.

Question:

```text
Can the 189 accepted candidate rows justify optimizer admission?
```

Answer:

```text
No. They show useful candidate-family diversity, but source-level diversity is
still too narrow.
```

## Evidence

M621 artifacts:

```text
runs/m621_tier_aware_sequence_target_miner/summary.json
runs/m621_tier_aware_sequence_target_miner/accepted_candidate_sequences.csv
runs/m621_tier_aware_sequence_target_miner/accepted_sequences.csv
runs/m621_tier_aware_sequence_target_miner/unaccepted_rows.csv
```

M621 selected-sequence result:

```text
selected accepted sequences: 6
physical pairs: 5
left seeds: 4
surfaces: 2
variants: 2
targets: 3
```

M621 accepted candidate-set result:

```text
accepted candidate sequences: 189
physical pairs: 5
left seeds: 4
surfaces: 2
variants: 2
targets: 3
```

## Candidate-Level Diversity

Accepted candidate families:

| Family | Count |
| --- | ---: |
| decay_pulse | `86` |
| constant_delta | `64` |
| steer_then_brake | `22` |
| brake_release_then_steer | `17` |

Accepted candidate tiers:

| Tier | Count |
| --- | ---: |
| support_boundary | `98` |
| near_boundary | `89` |
| core_boundary | `2` |

Accepted candidate lengths:

| Length | Count |
| --- | ---: |
| K=5 | `108` |
| K=3 | `81` |

This shows there are multiple sequence shapes that can improve margin on the
same small set of source states.

## Source-Level Limitation

The candidate-level evidence is highly correlated:

```text
189 accepted candidates
5 physical pairs
4 left seeds
max physical-pair dominance: 0.349206
```

Therefore it does not satisfy the objective-admission requirements:

```text
selected accepted sequences >= 8
physical pairs >= 6
left seeds >= 6
```

It also does not solve the core-boundary scarcity:

```text
accepted candidates by tier:
  core_boundary: 2
  near_boundary: 89
  support_boundary: 98
```

Most accepted candidates are from less fragile near/support rows. That is still
useful for diagnostics, but it is not enough to train a handling-limit recovery
objective.

## Decision

Decision:

```text
tier_aware_candidate_audit_admit_longer_sequence_design
```

Blocked:

```text
optimizer admission
actor training
PPO
checkpoint promotion
```

Next branch:

```text
m623-longer-low-amplitude-sequence-design
```

Rationale:

```text
M617/M621 near misses often improve margin but fail the trust-region check.
Do not widen the trust region. Instead, test whether longer K=7 low-amplitude
prefixes can create more integrated effect while preserving per-step and
sequence trust limits.
```

M623 should design only; it should not run training.

## Requirements For M623

M623 should preserve:

```text
per-step action L2 <= 0.10
sequence mean L2 <= 0.08
sequence max L2 <= 0.10
max delta-delta L2 <= 0.08
margin improvement threshold >= 0.02
risk improvement threshold >= 0.05
```

M623 may add:

```text
K=7 sequence length
low-amplitude constant_delta candidates
K=7 decay_pulse candidates
ramp_hold or smooth_pulse family if trust-region metrics are explicit
```

M623 should pre-register a later run to compare:

```text
M621 K=3/5 baseline
vs
K=3/5/7 longer-low-amplitude diagnostic
```

Acceptance for optimizer design remains source-level:

```text
selected accepted sequences >= 8
physical pairs >= 6
left seeds >= 6
selected action/tier distribution audited
```

Candidate-level rows remain diagnostic unless a later objective explicitly
handles multi-candidate preference/set targets.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```
