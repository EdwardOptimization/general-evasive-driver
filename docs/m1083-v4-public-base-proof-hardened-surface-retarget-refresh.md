# M1083 V4 Public Base Proof Hardened Surface Retarget Refresh

## Purpose

M1083 runs the M1082 retargeted surface refresh for the M1078 proof-hardened
public-gate base.

It does not train, run PPO, promote, or use private holdout.

## Command Note

The boundary relocation command was corrected before the successful run to pass
negative offset lists with argparse-safe `--option=value` syntax:

```text
--body-longitudinal-offsets=-2.0,-1.0,0.0,1.0,2.0
--body-lateral-offsets=-0.4,0.0,0.4
```

No training or PPO was started.

## Matched-Current Mining

Retargeting increased source coverage:

```text
candidate_pair_count: 1584399
accepted_pair_count: 7257
accepted_physical_pair_count: 371
accepted_left_step_count: 28
accepted_source_obstacle_bucket_count: 27
ambiguity_surface_found: true
```

Matched-current ambiguity is not the blocker.

## Outcome Gate

```text
input_pair_count: 7257
outcome_row_count: 43542
outcome_summary_rows: 72
```

The retargeted outcome stage completed.

## Boundary Relocation

Retargeting fixed the success-drop quality problem at the raw boundary level:

```text
candidate_count: 425
row_count: 122700
accepted_wrong_history_rows: 626
accepted_wrong_history_pairs: 71
accepted_reset_rows: 977
accepted_zero_current_rows: 862
wrong_history_success_drop_count: 626
surface_found: true
```

Compared with M1081, the accepted wrong-history rows increased and every
accepted wrong-history row became an actual success drop.

## Primary Robustness Gate

The primary `0.005` robustness gate still failed:

```text
decision: reject_duplicate_dominated_boundary_surface
passed: false
accepted_wrong_rows: 626
accepted_wrong_physical_pairs: 6
accepted_wrong_left_steps: 5
accepted_wrong_checkpoints: 4
accepted_wrong_targets: 2
accepted_wrong_normal_margin_buckets: 4
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.3067092652
control_accepted_wrong_rows: 0
```

Passed gates:

```text
accepted_wrong_rows >= 80
left_steps >= 5
checkpoints >= 3
targets >= 2
margin_buckets >= 2
success_drop_fraction == 1.0
control_accepted_wrong_rows == 0
```

Failed gates:

```text
accepted_wrong_physical_pairs: 6 < 10
max_rows_per_physical_pair_fraction: 0.3067092652 > 0.25
```

## Interpretation

M1083 is a partial repair:

```text
success-drop quality fixed;
row count improved;
margin-bucket diversity retained;
source diversity still failed.
```

The next issue is not whether wrong-history sensitivity exists. It does. The
issue is that the robust near-boundary success-drop rows concentrate into too
few physical pairs after boundary relocation.

Per the M1083 fallback plan, the next step should be branch synthesis before
another retarget. Do not convert this surface directly and do not weaken the
physical-pair thresholds.

## Decision

```text
proof_hardened_surface_retarget_duplicate_dominated_route_to_synthesis
```

Next:

```text
m1084-v4-public-base-proof-hardened-surface-refresh-synthesis
```
