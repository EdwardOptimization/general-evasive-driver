# M459 Late-Reveal Matched-Current Mining

## Purpose

M458 showed weak aggregate history necessity on the M457 late-reveal config.
M459 asks whether row-level matched-current ambiguity still exists:

```text
current visible response/context close,
future response envelope different,
action or outcome changes under history interventions.
```

No checkpoint is trained or promoted.

## Matched-Current Mining

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --probe-seeds 9600,9900,10150 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m459_late_reveal_matched_current_seed9600
```

Artifacts:

```text
runs/m459_late_reveal_matched_current_seed9600/summary.json
runs/m459_late_reveal_matched_current_seed9600/matched_pairs.csv
runs/m459_late_reveal_matched_current_seed9600/target_summary.csv
```

Results:

| metric | value |
| --- | ---: |
| candidate pairs | 74784 |
| accepted pairs | 503 |
| accepted physical pairs | 503 |
| accepted left steps | 36 |
| accepted obstacle buckets | 33 |
| future braking decel pairs | 206 |
| future yaw response pairs | 219 |
| future lateral accel pairs | 78 |

This passes the surface-discovery part of M459: the M457 task family contains
source-diverse matched-current pairs with different future response envelopes.

## Action Intervention Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m459_late_reveal_matched_current_seed9600/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m459_late_reveal_matched_history_action_gate
```

Weighted action summary:

| variant | action distance | above threshold | wrong-history closer to right |
| --- | ---: | ---: | ---: |
| delayed history | 0.239746 | 0.739496 | 0.000000 |
| reset hidden | 0.708045 | 0.848739 | 0.000000 |
| wrong matched history | 0.035114 | 0.588235 | 0.630252 |
| zero action history | 0.026357 | 0.521008 | 0.000000 |
| zero current response | 0.119922 | 1.000000 | 0.000000 |

This is a positive action-level signal. Reset and zero-current strongly change
actions, and wrong matched history moves closer to the right-pair action in
`0.630252` of weighted rows.

## Outcome Intervention Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m459_late_reveal_matched_current_seed9600/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 60 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m459_late_reveal_matched_history_outcome_gate
```

Weighted outcome summary:

| variant | normal success | variant success | success drop | margin gap | trajectory distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| delayed history | 0.900000 | 0.900000 | 0.000000 | -0.015288 | 0.059905 |
| reset hidden | 0.900000 | 0.900000 | 0.000000 | -0.061470 | 0.964184 |
| wrong matched history | 0.900000 | 0.900000 | 0.000000 | -0.000991 | 0.038518 |
| zero action history | 0.900000 | 0.905556 | 0.000000 | 0.004293 | 0.133350 |
| zero current response | 0.900000 | 0.900000 | 0.000000 | -0.097896 | 0.467309 |

The outcome gate is negative for proof. It finds action and trajectory
differences, but no success-drop rows and no reliable normal-history margin
advantage. Several variants have negative mean margin gap, meaning the
intervention is not worse on average.

## Interpretation

M459 finds a real matched-current response/action ambiguity surface, but it is
not yet an outcome-critical self-ID surface.

What this supports:

- M457 can produce source-diverse matched-current rows.
- The recurrent/action-response pathway affects policy actions on those rows.
- Wrong matched history has a measurable directional effect at the action level.

What this does not support:

- a claim that current M399 needs history for closed-loop success on this
  surface;
- a wrong-history proof gate;
- PPO or any training continuation.

The next step should change the selection objective. Instead of selecting pairs
only by future response-envelope target z-delta, M460 should design an
outcome-critical matched-current selector that ranks or filters pairs by
continuation margin/success degradation under reset, zero-current, delayed, and
wrong-history interventions.

## Decision

Decision:

```text
action_surface_found_outcome_weak_admit_m460_outcome_critical_selector_design
```

No checkpoint is promoted.
