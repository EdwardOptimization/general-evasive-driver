# M377 Cumulative Gap-Tail V2 Corpus Refresh

M377 converts the M376 alpha `0.2` cumulative old-key boundary into a refreshed
old-key feedback overlay and preference corpus. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Overlay

Input rows:

```text
runs/m376_alpha02_cumulative_old_key_boundary_audit/gap_tail_rows.csv
```

Output overlay:

```text
runs/m377_cumulative_gap_tail_v2_overlay/old_key_feedback_overlay.csv
```

The v2 overlay keeps the prior accepted-regression hard row and replaces the
gap-tail rows with the M376 current-boundary rows:

```text
hard rows: 1
gap-tail rows: 4
```

The branch-weight formula remains the M372 policy:

```text
gap_weight_multiplier = 4.0
normal_branch_weight_multiplier =
  1.0 + 8.0 * clip(-candidate_normal_delta / 0.001, 0, 2)
wrong_branch_weight_multiplier =
  1.0 + 8.0 * clip(candidate_wrong_delta / 0.001, 0, 2)
```

## Corpus Export

Current promoted base:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

Weighted corpus:

```text
runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.csv
runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/summary.json
```

Summary:

| Metric | Value |
| --- | ---: |
| rows | 40 |
| hard rows | 1 |
| gap-tail rows | 4 |
| preferred branch weight sum | 76.765991 |
| wrong branch weight sum | 56.656788 |
| total sample weight sum | 83.699730 |
| actor inputs changed | false |
| PPO or actor update run | false |

## No-Update Exact Repair Smoke

Run dir:

```text
runs/m377_cumulative_gap_tail_v2_repair_smoke
```

Result versus M375 base:

| Metric | Value |
| --- | ---: |
| selected step | 0 |
| exact M297 delta | -0.000014186 |
| exact M270 delta | -0.000006676 |
| old-key surrogate delta | -0.003332615 |
| exact lexicographic pass | true |

This verifies that the v2 old-key corpus is readable by exact repair and that
the refreshed branch weights are active. It is not a repair result.

## Interpretation

M377 is a positive infrastructure/corpus refresh. The current M375 boundary is
now represented in the repair surrogate without changing the deployable actor
contract. The next step is a no-PPO repair probe from alpha `0.2` using this v2
corpus, followed by cumulative old-key replay before any wider proof gates.

## Decision

Admit:

```text
m378-cumulative-gap-tail-v2-repair-probe
```

Decision:

```text
admit_m378_cumulative_gap_tail_v2_repair_probe
```
