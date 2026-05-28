# M1168 V4 Public Base Row15 Promoted Relocation Target Microgrid Design

## Purpose

M1168 designs a tiny target-margin microgrid diagnostic after M1167 found two
facts:

1. M1166 selected both M1161 accepted physical pairs, so the pilot did not fail
   by missing the old sensitive active set.
2. M1166 omitted the fine `0.0005` target-normal-margin value, which likely
   caused one old accepted pair to become a false negative.

This milestone is design-only. It does not run relocation replay, rerun mining,
rerun the outcome gate, train actor weights, run PPO, promote, use private
holdout, convert a surface, weaken thresholds, or change actor inputs.

## Diagnostic Question

M1169 should answer:

```text
Was M1166 mostly a target-grid false negative,
or does the row15-promoted family still have broad wrong-history scarcity
after fine target margins are restored?
```

The diagnostic is intentionally not a full surface gate. It should restore the
fine near-boundary target margins but avoid the M1164-style expansion cross
product.

## M1169 Scope

```text
input:
  runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv

max_candidates: 240
max_candidates_per_physical_pair: 4
max_candidates_per_checkpoint_target: 64
target margins:
  0.00025,0.0005,0.00075,0.001,0.00125,0.0015,
  0.002,0.0025,0.003,0.004,0.005
body longitudinal offsets: 0.0
body lateral offsets: 0.0
report variants: wrong_matched_history only
```

This keeps the same candidate budget as M1166, restores fine target margins,
and removes body-offset expansion. The expected resource cost is much smaller
than M1164 and should be comparable to or smaller than M1166.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy row15_current=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy row15_previous_alpha015=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 240 \
  --max-candidates-per-physical-pair 4 \
  --max-candidates-per-checkpoint-target 64 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.25 \
  --min-eligible-physical-pairs 12 \
  --max-candidate-pair-fraction 0.25 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --target-normal-margins 0.00025,0.0005,0.00075,0.001,0.00125,0.0015,0.002,0.0025,0.003,0.004,0.005 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=0.0 \
  --body-lateral-offsets=0.0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1169_row15_promoted_target_microgrid_seed116100
```

## Result Interpretation

M1169 should compare against both M1161 and M1166:

```text
M1161 accepted rows: 15
M1161 accepted physical pairs: 2
M1161 accepted normal-margin max: 0.002483

M1166 accepted rows: 1
M1166 accepted physical pairs: 1
M1166 accepted normal-margin max: 0.002457
```

Possible outcomes:

```text
recovers neither old pair:
  target-grid artifact is not enough; route to stronger wrong-history construction audit.

recovers exactly the old two pairs, with no new source-diverse pairs:
  M1166 was partly a target-grid false negative, but same-shape relocation is
  still exhausted; route to branch synthesis and stronger wrong-history construction.

recovers more than two physical pairs or a materially broader target family:
  route to staged conversion design, not direct conversion or PPO.
```

M1169 must not claim a full surface pass. Even a positive microgrid result is
only evidence about target-margin sensitivity.

## Decision

```text
decision: row15_promoted_target_microgrid_design_admit_m1169_run
next: m1169-v4-public-base-row15-promoted-relocation-target-microgrid-run
```
