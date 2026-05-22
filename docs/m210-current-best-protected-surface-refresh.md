# M210 Current-Best Protected Surface Refresh

M210 attempts to refresh the protected proof surface around the current retained
M199/M202/M204 family before any further PPO.

No PPO, actor update, or actor input change is run in this milestone.

## Checkpoints

```text
m199_5201  runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt
m202_5206  runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt
m204_5209  runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

M204 remains the current best retained checkpoint.

## Matched-Current Mining

Artifact:

```text
runs/m210_current_family_matched_current_seed10020
```

Fresh probe seeds:

```text
10020,10021,10022,10023
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 298884 |
| Accepted pairs | 1837 |
| Accepted physical pairs | 209 |
| Accepted left steps | 30 |
| Accepted obstacle buckets | 26 |
| Surface found | true |

Accepted by target:

| Target | Rows |
| --- | ---: |
| future braking deceleration | 1218 |
| future lateral accel response | 221 |
| future yaw response | 398 |

The matched-current ambiguity surface is healthy. The negative result happens
later, at boundary outcome conversion.

## Direct Outcome Gate

Artifact:

```text
runs/m210_current_family_outcome_seed10020
```

The direct continuation gate produced `11022` rows. As expected for non-relocated
geometry, wrong-history variants did not create success drops. This stage served
as the snapshot source for boundary relocation.

## Boundary Relocation

Artifact:

```text
runs/m210_current_family_boundary_surface_seed10020
```

Boundary relocation uses target normal margins:

```text
0.005, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20
```

Result:

| Metric | Value |
| --- | ---: |
| Candidate pairs | 1837 |
| Boundary replay rows | 24170 |
| Wrong-history rows | 4834 |
| Accepted wrong-history rows | 0 |
| Accepted wrong-history pairs | 0 |
| Wrong-history success drops | 0 |
| Accepted reset rows | 680 |
| Accepted zero-current rows | 261 |
| Surface found | false |

The failure is specific to wrong-history near-boundary conversion. Reset-hidden
and zero-current-response interventions still produce many accepted rows.

## Failure Mechanism

Wrong-history has some positive margin-gap rows, but those rows are far from
the near-boundary window:

| Subset | Rows | Near-boundary rows | Gap >= 0.02 rows | Near-boundary gap >= 0.02 rows | Max gap | Normal margin at max gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all wrong-history rows | 4834 | 2655 | 135 | 0 | 0.090092 | 8.889845 |

Within the pre-registered near-boundary window:

| Metric | Value |
| --- | ---: |
| Near-boundary wrong-history rows | 2655 |
| Max near-boundary margin gap | 0.001786 |
| Mean near-boundary margin gap | -0.001244 |
| Wrong-history success drops | 0 |

So the issue is not simply a threshold that is too strict. Under fresh M210
seeds, wrong-history action differences do not become near-boundary outcome
differences for the current M199/M202/M204 family.

## Robustness Gate

Artifact:

```text
runs/m210_current_family_boundary_robustness_seed10020
```

| Gate metric | Observed | Threshold | Pass |
| --- | ---: | ---: | --- |
| accepted wrong rows | 0 | >= 40 | false |
| physical pairs | 0 | >= 10 | false |
| left steps | 0 | >= 5 | false |
| checkpoints | 0 | >= 3 | false |
| targets | 0 | >= 2 | false |
| margin buckets | 0 | >= 2 | false |
| success-drop fraction | 0.0 | >= 1.0 | false |
| max rows per pair fraction | 0.0 | <= 0.25 | true |
| control accepted rows | 0 | <= 0 | true |

Decision:

```text
reject_duplicate_dominated_boundary_surface
```

The decision label is produced by the robustness script. The substantive reason
is stronger: there are no accepted wrong-history rows to diversify.

## Decision

M210 is negative. It does not justify objective conversion or PPO.

What it proves:

- fresh current-family matched-current ambiguity can still be mined;
- current-family reset-hidden and zero-current-response near-boundary
  interventions remain outcome-relevant;
- fresh wrong-history near-boundary outcome evidence was not found under the
  M210 seeds and relocation settings.

What it does not prove:

- that all current-family wrong-history evidence is gone;
- that M204 cannot retain the old M193 surface;
- that PPO should resume.

Next step:

```text
m211-m192-seed-control-protected-surface-audit
```

M211 should repeat the protected-surface refresh with the M192 probe seeds while
keeping the current M199/M202/M204 checkpoint family. This controls for seed and
corpus effects before deciding whether the current family has truly lost fresh
wrong-history near-boundary evidence.
