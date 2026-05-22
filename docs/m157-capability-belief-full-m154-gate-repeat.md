# M157 Capability-Belief Full M154 Gate Repeat

M156 admitted the 20-step capability-belief repair to a full M154 gate repeat.
M157 checks whether that candidate is ready for guarded PPO. It is not.

Candidate:

```text
runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt
```

Baseline:

```text
runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt
```

## Already-Passed Cheap Stages From M156

M156 already ran the registered cheap stages:

```text
runs/m156_behavior_prescreen_s20_seed9503
runs/m156_behavior_prescreen_s20_seed9504
runs/m156_critical_key_prescreen_s20_seed9944
```

Summary:

| Stage | Result |
| --- | --- |
| actor input contract | pass: `human_view_online_gru`, obs dim `72` |
| behavior seed 9503 | pass: M142 `0.8625`, M156 `0.8625` |
| behavior seed 9504 | pass: M142 `0.8625`, M156 `0.8625` |
| zero-current / zero-all response gap | pass for PPO admission: M156 drops to `0.8000` on both behavior seeds |
| critical key `9944|perturbed|28|28` | pass: M156 `1/1`, margin gap `0.009455` |

## Matched-History Action Gate

M157 then ran the M154 matched-history action gate on the M156 candidate.

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m157_m156_s20_action_intervention_gate_seed9510
```

Result:

```text
input_pair_count: 408
intervention_row_count: 0
variant_summary_rows: 0
```

This fails the M154 threshold:

```text
wrong_matched_history_physical_pairs_min = 100
wrong_matched_history_above_threshold_fraction_min = 0.70
wrong_matched_history_closer_to_right_fraction_min = 0.65
```

## Calibration Check

Before blaming only M156, M157 calibrated the same action gate against the M142
guarded baseline.

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m157_action_gate_calibration_m142_m156_seed9510
```

Result:

```text
input_pair_count: 408
intervention_row_count: 0
variant_summary_rows: 0
```

M157 also repeated the calibration with the original M118 env config:

```text
runs/m157_action_gate_calibration_m24_m142_m156_seed9510
```

That also produced:

```text
intervention_row_count: 0
variant_summary_rows: 0
```

Interpretation: the broad M118 action surface that worked for M62/M102/M105
does not currently admit M142 or M156. This is not a M156-only regression; it is
a mismatch between the current guarded baseline family and the old M118
action-dependence surface.

## Downstream Gates

The required matched-history action stage failed, so M157 does not admit strict
miners, outcome gates, or PPO. A strict seed9900 run was started before the
action-gate failure was fully interpreted and was terminated because it was no
longer decision-relevant. No strict proof-surface result is claimed for M157.

## Decision

M157 rejects guarded PPO admission.

The useful result is a sharper blocker:

```text
M156 is behavior-safe and critical-key-safe,
but neither M156 nor M142 currently shows broad action-level wrong-history
dependence on the M118 surface.
```

Next step: rebuild or recalibrate a matched-history action surface for the
current guarded baseline family before running another full M154 gate or PPO.
