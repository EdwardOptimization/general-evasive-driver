# M587 BC5660 History Intervention Action Screen

## Purpose

M587 runs the action-level history-intervention screen pre-registered in M586.
It tests whether delayed or wrong recurrent history changes BC5660's immediate
action on the M586 matched-current pair surfaces.

This milestone is an action screen only:

```text
no outcome rollout
no training
no PPO
no checkpoint promotion
```

## Commands

Fresh route:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --pairs-csv runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 120 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m587_bc5660_history_action_screen_fresh_seed25560
```

Moderate-OOD:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/eval_m574_moderate_ood_l3.json \
  --pairs-csv runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 120 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m587_bc5660_history_action_screen_ood_seed25660
```

## Artifacts

Fresh route:

```text
runs/m587_bc5660_history_action_screen_fresh_seed25560/summary.json
runs/m587_bc5660_history_action_screen_fresh_seed25560/action_interventions.csv
runs/m587_bc5660_history_action_screen_fresh_seed25560/variant_summary.csv
```

Moderate-OOD:

```text
runs/m587_bc5660_history_action_screen_ood_seed25660/summary.json
runs/m587_bc5660_history_action_screen_ood_seed25660/action_interventions.csv
runs/m587_bc5660_history_action_screen_ood_seed25660/variant_summary.csv
```

## Aggregate Results

Fresh route aggregate:

| variant | pairs | mean action distance | above-threshold count | above-threshold fraction | max action distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| delayed_history | 329 | 0.001658 | 0 | 0.000000 | 0.014395 |
| reset_hidden | 329 | 0.015801 | 119 | 0.336361 | 0.021118 |
| wrong_matched_history | 329 | 0.000552 | 0 | 0.000000 | 0.002758 |
| zero_action_history | 329 | 0.018689 | 189 | 0.580150 | 0.028822 |
| zero_current_response | 329 | 0.066799 | 329 | 1.000000 | 0.080203 |

Moderate-OOD aggregate:

| variant | pairs | mean action distance | above-threshold count | above-threshold fraction | max action distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| delayed_history | 287 | 0.001218 | 0 | 0.000000 | 0.014392 |
| reset_hidden | 287 | 0.014932 | 70 | 0.203073 | 0.021829 |
| wrong_matched_history | 287 | 0.000764 | 0 | 0.000000 | 0.004301 |
| zero_action_history | 287 | 0.018867 | 166 | 0.663889 | 0.030789 |
| zero_current_response | 287 | 0.070125 | 287 | 1.000000 | 0.083086 |

Pre-registered M587 pass condition:

```text
at least one surface has wrong_matched_history or delayed_history:
  above_threshold_count >= 16
  action_distance_mean >= 0.02
```

Result:

```text
fresh wrong_matched_history: above_threshold_count = 0, mean = 0.000552
fresh delayed_history:       above_threshold_count = 0, mean = 0.001658
OOD wrong_matched_history:   above_threshold_count = 0, mean = 0.000764
OOD delayed_history:         above_threshold_count = 0, mean = 0.001218
```

M587 therefore fails the action-screen admission condition for persistent
outcome rollout.

## Positive Controls

The screen itself is working. `zero_current_response` is a strong positive
control on both surfaces:

```text
fresh: 329 / 329 above threshold
OOD:   287 / 287 above threshold
```

`zero_action_history` is also action-sensitive on both surfaces:

```text
fresh: 189 / 329 above threshold
OOD:   166 / 287 above threshold
```

`reset_hidden` has some action effect, but it is weaker and mostly near the
threshold:

```text
fresh: 119 / 329 above threshold
OOD:    70 / 287 above threshold
```

## Interpretation

M587 is a negative history-intervention action diagnostic.

It supports this claim:

```text
BC5660 action is sensitive to current response and previous-command slots.
```

It does not support this claim:

```text
BC5660 action changes meaningfully when only delayed or wrong recurrent hidden
history is injected on the M586 matched-current surfaces.
```

Because wrong/delayed history action effects are below threshold on both
surfaces, M587 should not proceed directly to persistent outcome rollout. That
would violate the M587 admission rule and would likely only confirm that there
is no hidden-history action signal on this BC5660 branch.

## Decision

```text
bc5660_history_action_screen_negative_admit_failure_audit
```

M587 completes successfully as an experiment, but the result is negative for
wrong/delayed hidden-history action sensitivity. No checkpoint is promoted, and
M588 should audit the negative result before choosing the next path.

## Next

```text
M588: audit the negative action-screen result and decide whether to revise the
BC training objective, mine a different surface, or test another checkpoint
family.
```
