# M1084 V4 Public Base Proof Hardened Surface Refresh Synthesis

## Purpose

M1084 synthesizes M1080-M1083 after the proof-hardened public-base surface
refresh found real wrong-history sensitivity but failed robustness on
source-diversity.

This milestone does not train, run PPO, mine rows, promote, or use private
holdout.

## Evidence Summary

M1080 designed a fresh source-diverse protected/preference surface refresh for
the M1078 public-gate base:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

M1081 ran that refresh. It found a non-sparse surface:

```text
matched_current_accepted_pairs: 3129
matched_current_physical_pairs: 220
boundary_accepted_wrong_history_rows: 252
boundary_wrong_history_success_drop_count: 192
```

But the primary robustness gate failed:

```text
physical_pairs: 9 < 10
success_drop_fraction: 0.7619047619 < 1.0
max_rows_per_physical_pair_fraction: 0.253968254 > 0.25
```

M1082 retargeted sampling and boundary relocation without weakening thresholds.

M1083 ran the retarget. It improved the surface:

```text
matched_current_accepted_pairs: 7257
matched_current_physical_pairs: 371
boundary_accepted_wrong_history_rows: 626
boundary_wrong_history_success_drop_count: 626
```

The primary robustness gate still failed, but for a narrower reason:

```text
success_drop_fraction: 1.0
physical_pairs: 6 < 10
max_rows_per_physical_pair_fraction: 0.3067092652 > 0.25
```

## Supported Claims

Wrong-history sensitivity still exists under the M1078 proof-hardened public
base. Both M1081 and M1083 found substantial accepted wrong-history rows.

Retargeting helped. M1083 fixed the success-drop fraction and increased the
number of accepted wrong-history rows from 252 to 626.

The remaining blocker is source diversity after boundary relocation, not lack
of command-response history signal.

## Falsified Claims

M1081 falsified the idea that the first current-base refresh was directly
convertible.

M1083 falsified the idea that source coverage alone fixes the robustness gate.
Even with 371 matched-current physical pairs, the near-boundary accepted rows
collapsed to six robustness physical pairs.

The branch does not justify weakening physical-pair thresholds or accepting
M1083 as a replay/objective corpus.

## Failure Taxonomy Summary

```text
M1081: scenario_sampling_failure
  surface not sparse, but duplicate/source-diversity dominated and success-drop
  fraction below threshold.

M1082: none
  design only; no thresholds weakened.

M1083: scenario_sampling_failure
  success-drop quality repaired, but source-diversity/dominance still failed.
```

No milestone in this branch trained, ran PPO, promoted, or used private holdout.

## Public Gate Overfit Risk

The promoted public base has now been used to mine public proof rows. The
results are valuable for public-gate development, but they should not be treated
as paper-level evidence.

The repeated concentration into few physical pairs is itself a public-overfit
risk signal. Before another PPO proposal, the project needs tooling or a
selection procedure that explicitly controls source diversity during boundary
surface export, not only after export.

## Next Branch Decision

```text
synthesis_decision: promote_to_next_branch
closed_branch: proof_hardened_base_surface_refresh
opened_branch: source_balanced_boundary_tooling
```

Next milestone:

```text
m1085-v4-public-base-source-balanced-boundary-tooling-design
```

M1085 should design tooling or selection logic that enforces source-balance
before final robustness, while preserving the existing robustness thresholds.
It should not run PPO, train, promote, use private holdout, or weaken the
physical-pair gate.
