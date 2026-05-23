# M393 Current-Family Rejected Boundary Target Export

M393 exports replay-selected local action targets for the active M267/M264
wrong-history boundary rows. It does not run PPO, promote a checkpoint, lower
thresholds, or change actor inputs.

## Inputs

Current public-gate base:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

Boundary source:

```text
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

Rows searched:

```text
15, 6
```

## Export Result

The local wrong-history first-action search evaluated `630` rollout candidates.
Both requested rows received collision-side targets, with `153` accepted local
candidates per row.

| Row | Baseline wrong-history margin | Selected margin | Margin decrease | Action L2 |
| --- | ---: | ---: | ---: | ---: |
| 15 | -0.000000469 | -0.002112566 | 0.002112096 | 0.131149 |
| 6 | -0.000059089 | -0.002463502 | 0.002404414 | 0.131149 |

The selected target in both rows is a small local perturbation of the current
wrong-history action:

```text
steer_delta=+0.06
throttle_delta=+0.06
brake_delta=-0.10
```

This is not a deployable rule. It is a training-only target for the
current-family conflict residual, so the actor observation contract is
unchanged.

Exported artifacts:

```text
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_rows.csv
runs/m393_current_family_rejected_boundary_targets/rejected_boundary_candidates.csv
runs/m393_current_family_rejected_boundary_targets/summary.json
```

## No-Update Smoke

The refreshed corpus is readable by the exact-repair path:

```text
runs/m393_rejected_boundary_targets_no_update_smoke
```

| Metric | Value |
| --- | ---: |
| exact M297 delta vs base | 0.000000000 |
| exact M270 delta vs base | 0.000000000 |
| old-key surrogate delta vs base | 0.000000000 |
| exact lexicographic pass | true |
| current-family conflict rows | 2 |
| current-family conflict loss | 0.006180852 |
| current-family conflict rejected loss | 0.001545213 |

The finite nonzero rejected loss is expected: unlike M389, this corpus no
longer anchors the rejected branch to the current near-cliff wrong-history
action. It anchors the rejected branch to a local action that keeps the
wrong-history rollout on the collision side with millimeter-scale slack.

## Interpretation

M393 confirms that the active row15 boundary is not lacking local
collision-side actions. The previous M389/M390 conflict corpus was weak because
its rejected-branch target was the base wrong-history action, whose row15
margin under M391 is only about `-4.7e-7`. The new targets give the next repair
probe a direct residual for keeping wrong-history rollouts failed rather than
merely slowing proof washout.

Closed-loop replay remains authoritative. M393 only exports a training corpus
and verifies no-update loading.

## Decision

Classify:

```text
infrastructure_success
```

Admit:

```text
m394-rejected-boundary-target-repair-probe
```

Decision:

```text
admit_m394_rejected_boundary_target_repair_probe
```
