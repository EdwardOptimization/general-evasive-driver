# M12 Paired Perturbation Gate

Last updated: 2026-05-21

## Purpose

M10 and M11 both failed to prove behavior-level closed-loop
self-identification. Static history and response ablations did not meaningfully
change success, and M11 hidden-state reset did not reduce success.

M12 adds a paired hidden-perturbation gate. For each seed, the gate evaluates
the same policy under two conditions:

- `nominal`: friction step samples post-step friction from a high range;
- `perturbed`: friction step samples post-step friction from a low range.

The initial seed, obstacle geometry, initial vehicle parameters, and friction
step timing are kept paired. The only intended difference is the hidden road
response after the friction step.

## Implementation

New CLI:

```bash
python -m autodrift.paired_perturbation_gate
```

The gate writes:

- `episodes.csv`;
- `condition_summary.csv`;
- `obstacle_label_summary.csv`;
- `pair_summary.csv`;
- `manifest.json`.

The key output is `pair_summary.csv`, which reports nominal success,
perturbed success, paired success drop, and return delta by policy.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --checkpoint runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state \
  --episodes 4 \
  --seed 1600 \
  --device cpu \
  --run-dir /tmp/autodrift_m12_paired_gate_smoke
```

Result: smoke completed and wrote paired summaries.

## Full Gate

Command:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --checkpoint runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m11_zero_current=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_current_response \
  --checkpoint-policy m11_zero_all=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_all_response \
  --episodes 40 \
  --seed 1600 \
  --device cpu \
  --run-dir runs/m12_paired_perturbation_gate_seed1600
```

Paired result:

| policy | nominal success | perturbed success | success drop | return delta |
| --- | ---: | ---: | ---: | ---: |
| M11 | 0.275 | 0.275 | 0.000 | 1.892 |
| M11 reset recurrent state | 0.275 | 0.275 | 0.000 | 2.431 |
| M11 zero current response | 0.250 | 0.250 | 0.000 | 2.085 |
| M11 zero all response | 0.250 | 0.250 | 0.000 | 2.085 |

Label result:

| condition | policy | drift_required success | unavoidable success |
| --- | --- | ---: | ---: |
| nominal | M11 | 1.000 | 0.065 |
| nominal | M11 reset recurrent state | 1.000 | 0.065 |
| nominal | M11 zero current/all response | 0.889 | 0.065 |
| perturbed | M11 | 1.000 | 0.065 |
| perturbed | M11 reset recurrent state | 1.000 | 0.065 |
| perturbed | M11 zero current/all response | 0.889 | 0.065 |

## Conclusion

The paired gate infrastructure works, but this first paired perturbation is
still not strong enough. Post-step friction range changes do not alter success
counts for M11 or its hidden/reset response ablations. The benchmark remains
label dominated: every normal/reset M11 variant solves all sampled
`drift_required` cases and only 2 of 31 `unavoidable` cases.

M12 is therefore a negative validation result, not a driver improvement.

The next gate should construct near-threshold paired cases where the same static
geometry can be solved or failed depending on the hidden response after the
first control actions. Useful directions:

- sample only near-boundary `aes_feasible` and `drift_required` cases;
- delay the friction or actuator perturbation until the policy has already
  committed to an action;
- compare pairs with identical obstacle distance/width but different post-step
  brake or steering delay;
- add a metric for pair disagreement rather than aggregate label success alone.
