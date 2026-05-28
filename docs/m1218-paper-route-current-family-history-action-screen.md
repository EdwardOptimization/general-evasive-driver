# M1218 Paper-Route Current-Family History Action Screen

## Summary

M1218 runs the action-level history-intervention screen on the M1217
current-family matched-current surface.

Decision:

```text
current_family_history_action_screen_negative_route_to_audit
```

No outcome intervention, training, PPO, checkpoint repair, promotion, private
holdout, profile tuning, or actor-input change occurs in M1218.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy l3_s111600=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt \
  --checkpoint-policy l3_s111601=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --pairs-csv runs/m1217_current_family_matched_current_export/matched_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 120 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m1218_current_family_history_action_screen
```

## Artifacts

```text
runs/m1218_current_family_history_action_screen/summary.json
runs/m1218_current_family_history_action_screen/action_interventions.csv
runs/m1218_current_family_history_action_screen/variant_summary.csv
```

## Result

Top-level summary:

```text
input matched pairs:        762
intervention rows:         3810
variant summary rows:        45
min action distance:      0.02
delay steps:                 2
```

Aggregate by variant:

| Variant | Rows | Mean Action Distance | P50 | P90 | Max | Above Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| delayed_history | `762` | `0.000154` | `0.000044` | `0.000160` | `0.015598` | `0` |
| wrong_matched_history | `762` | `0.001075` | `0.000998` | `0.001946` | `0.002415` | `0` |
| reset_hidden | `762` | `0.041795` | `0.028329` | `0.076904` | `0.080238` | `629` |
| zero_action_history | `762` | `0.013854` | `0.013454` | `0.015445` | `0.015767` | `0` |
| zero_current_response | `762` | `0.017431` | `0.017601` | `0.019126` | `0.021021` | `20` |

Wrong/delayed history by checkpoint:

| Variant | Checkpoint | Rows | Mean | Above | Max |
| --- | --- | ---: | ---: | ---: | ---: |
| wrong_matched_history | l3_s111600 | `241` | `0.000941` | `0` | `0.002415` |
| wrong_matched_history | l3_s111601 | `244` | `0.000827` | `0` | `0.001940` |
| wrong_matched_history | l3_s111602 | `277` | `0.001410` | `0` | `0.002382` |
| delayed_history | l3_s111600 | `241` | `0.000231` | `0` | `0.015598` |
| delayed_history | l3_s111601 | `244` | `0.000059` | `0` | `0.000552` |
| delayed_history | l3_s111602 | `277` | `0.000171` | `0` | `0.005268` |

No wrong/delayed checkpoint-target group satisfies the pre-registered admission
condition:

```text
mean action distance >= 0.01
above-threshold count >= 16
```

The matching is not dead: `wrong_history_closer_to_right_action` is high for
wrong history (`0.891` aggregate), but the actual action movement is tiny.

## Interpretation

M1218 is a negative action-screen result for matched wrong/delayed history.

Supported:

```text
The current corrected L3 online-GRU checkpoints expose a large reset-hidden
action effect.
```

Not supported:

```text
The same checkpoints change action meaningfully when given a wrong matched
history or a delayed history on M1217 pairs.
```

This distinction matters. Reset hidden sensitivity means the recurrent pathway
can influence action. It does not prove self-identification, because replacing
the hidden state with another matched history barely moves the action.

The likely explanations are:

```text
the actor uses hidden state as a generic recurrent calibration or offset;
matched hidden states are action-equivalent even when future response targets differ;
the corrected-profile PPO budget trained mostly reactive behavior;
M1217 matched pairs are ambiguous in future response but not action-critical;
or the intervention is too weak/too close to expose causal history use.
```

M1218 therefore blocks persistent outcome rollout. Running outcome gates after
the action screen failed would violate the M1218 admission rule and repeat the
BC5660 mistake documented in M587/M588.

## Decision

```text
current_family_history_action_screen_negative_route_to_audit
```

Next blocker:

```text
m1219-paper-route-current-family-action-screen-negative-audit
```
