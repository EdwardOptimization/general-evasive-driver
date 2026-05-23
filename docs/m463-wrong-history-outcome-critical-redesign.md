# M463 Wrong-History Outcome-Critical Redesign

## Purpose

M463 turns the M461/M462 audits into a next implementation plan. The goal is to
make wrong-history interventions test a real belief/self-identification claim
instead of being diluted by reset/zero-current diagnostics.

No training, PPO, checkpoint interpolation, actor-input change, or promotion is
allowed in this milestone.

## Evidence From M461/M462

M461 selector smoke on M459 rows:

```text
compact rows:                  20
compact variants:              reset_hidden, zero_current_response
wrong-history compact rows:     0
success-drop compact rows:      0
```

M462 fresh repeat on seed windows `10200`, `10300`, and `10400`:

```text
matched-current accepted pairs:       422
selector candidate rows:              900
outcome-critical rows:                140
accepted rows:                         70
compact rows:                          34
compact variants:                      reset_hidden, zero_current_response
wrong-history raw accepted rows:         8
wrong-history compact rows:              0
wrong-history success-drop rows:         0
wrong-history collision-gap rows:        0
wrong-history completion-drop rows:      1
wrong-history positive-margin rows:      7
wrong-history source seeds:              10300 only
wrong-history labels:                    aes_feasible only
```

This is a useful repeat for reset/zero-current diagnostics, but it is not a
wrong-history proof gate.

## Diagnosis

### 1. Wrong history is too action-subtle

M462 wrong-history rows have mean action distance around `0.044`, while reset
and zero-current produce much larger action and trajectory differences. The
policy is not being pushed into a clearly wrong belief state often enough.

### 2. Selected wrong-history rows have too much normal margin slack

The strongest accepted wrong-history examples have normal margins around
`3.55 m` or `7.12 m`. A small action shift can produce a measurable margin gap
without changing success or collision outcome. That is not the boundary regime
needed for self-ID proof.

### 3. The compact selector is shared with reset/zero-current

Reset and zero-current rows are stronger and source-diverse, so they dominate
the compact corpus. A joint compact corpus is useful for general
response-dependence diagnostics, but wrong-history proof needs a separate
reserved surface.

### 4. Pair selection optimizes matched-current ambiguity, not wrong-history
harm

M459/M462 choose matched-current pairs by current response/context similarity
and future-response target delta. That is necessary but insufficient. The
chosen right-side history must also move the actor toward a harmful maneuver
under the left-side current observation.

### 5. Source diversity is the central missing evidence

M462 wrong-history accepted rows are concentrated in one probe seed and one
label. Even if those rows are real, they are diagnostic candidates, not a gate.

## Redesign

The next branch should split wrong-history proof from reset/zero-current
diagnostics.

### A. Wrong-History Targeted Pair Triage

Create a reusable pair triage tool that consumes `candidate_pairs.csv`, not only
the already compact `matched_pairs.csv`.

Hard filters:

```text
visible_distance <= per-run visible threshold
target_z_delta >= 1.0
same episode excluded
current_response_context similarity preserved
no actor-input contract changes
```

Wrong-history priority score:

```text
score =
  response_hidden_minus_current_response_distance
+ response_hidden_more_separated_than_current_response bonus
+ target_z_delta
+ near-boundary obstacle proxy
+ label/seed/source diversity bonus
```

Near-boundary proxy can only use mining-time metadata, not actor inputs:

```text
smaller left_obstacle_distance
drift_required or unavoidable label
later reveal / lower obstacle completion slack
larger obstacle lateral ambiguity
```

The output should be a source-diverse `wrong_history_targeted_pairs.csv`, not a
checkpoint candidate.

### B. Wrong-History Reserved Outcome Probe

Run the existing action and outcome intervention gates on targeted pairs, but
evaluate wrong-history separately from reset/zero-current.

Required accepted wrong-history row criteria:

```text
matched-current pass
wrong-history action distance >= threshold
normal current/history continuation succeeds
wrong-history continuation causes one of:
  success drop
  collision gap
  obstacle-completion drop with nontrivial return/margin degradation
  near-boundary margin sign or margin gap under a normal-margin ceiling
```

Margin-only rows are allowed only if they are near-boundary:

```text
0 < normal_margin <= margin_ceiling
margin_gap >= min_margin_gap
```

High-margin rows, even with positive margin gap, stay diagnostic.

### C. Separate Compact Outputs

The selector should write separate corpora:

```text
wrong_history_compact.csv
reset_zero_diagnostic_compact.csv
all_candidates.csv
summary.json
```

Wrong-history gate criteria must be based on `wrong_history_compact.csv` only.
Reset/zero-current rows can support response-dependence diagnostics, but cannot
stand in for wrong-history belief proof.

### D. Source-Diversity Requirements

A wrong-history gate expansion requires at least:

```text
wrong_history_compact_rows >= 16
probe_seed_count >= 3
obstacle_label_count >= 2
target_count >= 2
physical_pair_count >= 16
success_drop_or_collision_rows >= 4
single_seed_share <= 0.50
single_label_share <= 0.60
```

If these fail, the correct conclusion is task-family redesign, not proof-gate
expansion.

## Next Implementation

M464 should implement the wrong-history targeted pair triage first. It should
not run PPO or promote a checkpoint.

Expected M464 outputs:

```text
runs/m464_wrong_history_targeted_pair_triage/targeted_pairs.csv
runs/m464_wrong_history_targeted_pair_triage/summary.json
```

Minimum M464 pass criteria:

```text
targeted pairs >= 180
probe_seed_count >= 3
obstacle_label_count >= 2
target_count >= 3
single_seed_share <= 0.50
single_label_share <= 0.60
no actor contract change
```

M465 can then run action/outcome gates on that targeted pair set and decide
whether wrong-history proof expansion is real.

## Decision

```text
admit_m464_wrong_history_targeted_pair_triage
```

Do not expand wrong-history gates from M462. The project needs a targeted
wrong-history surface before any self-ID proof claim.
