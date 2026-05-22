# M179 Dual-Checkpoint Boundary-Relocated Outcome Proof Surface

M178 showed that the raw matched-current continuation surface is
outcome-neutral: wrong matched history changes actions, but does not change
success or clearance margin enough to prove outcome-level self-identification.

M179 relocates the obstacle boundary near the normal policy margin and asks
whether the same history-dependent actions become safety-critical near the
boundary.

Result: boundary relocation finds a real wrong-history success-drop surface, but
the accepted rows are lateral-only and duplicate-dominated after strict
robustness checks. This is a useful proof signal, not yet a reusable training or
paper-grade proof surface.

## Boundary Relocation Run

Run:

```text
runs/m179_dual_checkpoint_boundary_relocation_seed9510
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m178_dual_checkpoint_outcome_proof_surface_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m179_dual_checkpoint_boundary_relocation_seed9510
```

Aggregate:

| Metric | Value |
| --- | ---: |
| candidate rows | 658 |
| replay rows | 16880 |
| accepted wrong-history rows | 48 |
| accepted wrong-history source pairs | 20 |
| wrong-history success drops | 48 |
| accepted reset rows | 1448 |
| accepted zero-current rows | 704 |
| surface found | true |

## Checkpoint Results

Wrong-history accepted rows only appear on `future_lateral_accel_response`.

| Checkpoint | Target | Accepted rows | Source pairs | Success drops | Normal margin mean | Variant margin mean | Margin gap mean | Margin gap max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| m168_strict | future_lateral_accel_response | 24 | 20 | 24 | 0.006062 | -0.002433 | 0.008496 | 0.010628 |
| m170_split | future_lateral_accel_response | 24 | 20 | 24 | 0.006052 | -0.002496 | 0.008547 | 0.010718 |

The accepted source-pair set is the same for M168 and M170. M170 is slightly
larger in margin gap, but the difference is too small to select M170 over M168.

Variant-level aggregate:

| Checkpoint | Variant | Rows | Accepted | Success drops | Accepted source pairs | Margin gap mean | Margin gap max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| m168_strict | wrong_matched_history | 1684 | 24 | 24 | 20 | 0.000820 | 0.010995 |
| m170_split | wrong_matched_history | 1692 | 24 | 24 | 20 | 0.000820 | 0.011079 |
| m168_strict | reset_hidden | 1684 | 720 | 373 | 134 | 0.015191 | 0.078501 |
| m170_split | reset_hidden | 1692 | 728 | 373 | 134 | 0.015158 | 0.078599 |
| m168_strict | zero_current_response | 1684 | 346 | 182 | 80 | 0.006965 | 0.059944 |
| m170_split | zero_current_response | 1692 | 358 | 182 | 80 | 0.007272 | 0.060178 |

Reset-hidden and zero-current-response are much more outcome-critical than
wrong-history on this surface. That means the policy is sensitive to response
state, but the matched wrong-history causal signal is still sparse.

## Robustness Check

Run:

```text
runs/m179_boundary_relocation_lateral_robustness_seed9510
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m179_dual_checkpoint_boundary_relocation_seed9510/boundary_relocation_rows.csv \
  --control-checkpoint-label none \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 40 \
  --min-physical-pairs 10 \
  --min-left-steps 5 \
  --min-checkpoints 2 \
  --min-targets 1 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.25 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m179_boundary_relocation_lateral_robustness_seed9510
```

Result:

| Gate | Observed | Threshold | Passed |
| --- | ---: | ---: | --- |
| accepted wrong rows | 48 | 40 | true |
| accepted wrong physical pairs | 3 | 10 | false |
| accepted wrong left steps | 2 | 5 | false |
| accepted wrong checkpoints | 2 | 2 | true |
| accepted wrong targets | 1 | 1 | true |
| accepted wrong normal-margin buckets | 2 | 2 | true |
| success-drop fraction | 1.000000 | 1.000000 | true |
| max rows per physical pair fraction | 0.333333 | 0.250000 | false |
| control accepted rows | 0 | 0 | true |

Decision from robustness gate:

```text
reject_duplicate_dominated_boundary_surface
```

## Interpretation

What M179 proves:

- M178's raw outcome-neutral action surface can become outcome-critical when
  obstacle geometry is tightened to near-boundary margins.
- Both M168 and M170 have matched wrong-history cases that turn normal success
  into collision under boundary relocation.
- The signal is not caused by reading hidden parameters or oracle labels; it is
  a gate-time relocation using the existing human-view zero-relvel input
  contract.

What M179 does not prove:

- it is not a robust cross-target proof surface;
- it is not diverse enough for a new training objective or PPO admission;
- it does not justify replacing M168 with M170;
- it does not yet prove a broad closed-loop self-identification driver.

## Decision

Complete M179 as a mixed result:

- positive local outcome proof signal;
- negative robustness result due duplicate domination;
- keep M168/M170 dual-track status;
- do not run PPO or build a corpus from this surface yet.

The next step should mine a diversified boundary outcome surface, likely using
relative lateral/longitudinal obstacle offsets or explicit source-pair diversity
constraints, before any actor update or PPO continuation.
