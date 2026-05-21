# M112 Matched History Intervention Gate

## Question

M111 found matched-current-response pairs where visible current response and
scene are close but future-envelope targets differ. M112 asks whether current
policies are at least action-sensitive to history interventions on that surface:

```text
If the current observation is held fixed, does reset, delayed, missing, or wrong
matched history change the first action?
```

This is an action-level gate. It is not yet a rollout/outcome gate.

## Harness

Added:

```text
src/autodrift/matched_history_intervention_gate.py
tests/test_matched_history_intervention_gate.py
```

The harness consumes M111 `matched_pairs.csv`, reconstructs the requested
snapshots by rolling the same checkpoint deterministically from each episode
seed, and evaluates first-action variants:

```text
normal
reset_hidden
wrong_matched_history
delayed_history
zero_current_response
zero_action_history
```

For `wrong_matched_history`, the left observation is held fixed while the
right-side matched pair's recurrent hidden is injected. This tests whether the
policy action is causally sensitive to a different command-response history
under a similar current response and scene.

The actor input contract is unchanged. Hidden parameters and oracle labels are
not actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --pairs-csv runs/m111_matched_current_response_ambiguity_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m112_matched_history_intervention_gate_seed9510
```

Artifacts:

```text
runs/m112_matched_history_intervention_gate_seed9510/summary.json
runs/m112_matched_history_intervention_gate_seed9510/action_interventions.csv
runs/m112_matched_history_intervention_gate_seed9510/variant_summary.csv
```

Top-level result:

```text
input_pair_count: 639
intervention_row_count: 3195
variant_summary_rows: 45
```

## Aggregate Variant Readout

| variant | pairs | mean action distance | above 0.02 fraction | wrong closer to matched-right action | mean steer delta | mean throttle delta | mean brake delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reset_hidden | 639 | 0.517 | 0.932 | 0.000 | 0.105 | 0.376 | 0.327 |
| zero_current_response | 639 | 0.124 | 0.985 | 0.000 | 0.047 | 0.100 | 0.040 |
| delayed_history | 639 | 0.097 | 0.892 | 0.000 | 0.029 | 0.078 | 0.036 |
| wrong_matched_history | 639 | 0.066 | 0.771 | 0.733 | 0.019 | 0.052 | 0.027 |
| zero_action_history | 639 | 0.032 | 0.814 | 0.000 | 0.010 | 0.015 | 0.021 |

By checkpoint:

| checkpoint | variant | mean action distance | above 0.02 fraction | wrong closer fraction |
| --- | --- | ---: | ---: | ---: |
| M62 | reset_hidden | 0.151 | 0.921 | 0.000 |
| M62 | wrong_matched_history | 0.069 | 0.813 | 0.642 |
| M102 | reset_hidden | 0.624 | 0.940 | 0.000 |
| M102 | wrong_matched_history | 0.066 | 0.739 | 0.774 |
| M105 | reset_hidden | 0.778 | 0.934 | 0.000 |
| M105 | wrong_matched_history | 0.064 | 0.760 | 0.785 |

## Interpretation

M112 is a positive action-level gate:

- reset hidden changes actions strongly on the M111 matched surface;
- zeroing current response changes actions almost everywhere;
- delayed history changes actions with a moderate mean distance;
- wrong matched history changes actions in `77%` of rows above the action
  threshold and moves the action closer to the matched-right action in about
  `73%` of rows.

This is stronger than the previous behavior gates that saw no rollout-level
reset degradation. It shows the policy action is sensitive to hidden/history on
a matched-current-response surface.

However, this is not enough for driver admission:

```text
action sensitivity != safer rollout outcome
```

The reset/wrong-history action changes may be useful, harmful, or irrelevant
after rollout. M112 therefore does not admit another PPO continuation by itself.

## Decision

Status: completed, positive action-level signal.

Next task: M113 should replay these same matched interventions through
continuations and measure clearance, collision, success, and mitigation. Only if
normal history has better outcome than reset/delayed/wrong history should this
surface become a training objective.
