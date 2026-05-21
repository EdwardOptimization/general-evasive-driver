# M67-D Strict Self-ID Observation Profile

M67-C identified a concrete weakness in the self-identification evidence chain:
for static obstacles, obstacle `rel_vx` and `rel_vy` are context-side proxies for
ego velocity and yaw rate. M67-D adds a strict context profile that removes this
proxy without changing the canonical 72-value observation shape.

## Implementation

`DriftEnvConfig` now has:

```text
obstacle_relative_velocity_mode = "ego"   # default historical behavior
obstacle_relative_velocity_mode = "zero"  # strict self-ID diagnostic profile
```

`zero` preserves the 7-value obstacle slot layout:

```text
[present, x, y, rel_vx, rel_vy, half_width, half_length]
```

but writes:

```text
rel_vx = 0
rel_vy = 0
```

for the obstacle slot. This keeps old shape assumptions intact while removing
the most direct context-side motion proxy.

New config:

```text
configs/ppo_m67d_strict_self_id_context_driver.json
```

It is the M65 response-necessity continuation setup with
`obstacle_relative_velocity_mode="zero"`.

## Smoke Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m67d_strict_self_id_context_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3167 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m67d_strict_context_smoke_seed3167 \
  --eval-episodes 2
```

Result:

- init checkpoint load mode: `strict`;
- baseline-action anchor load mode: `strict`;
- smoke checkpoint:
  `runs/ppo_m67d_strict_context_smoke_seed3167/checkpoint.pt`;
- eval return mean: `43.662071`;
- eval termination rate: `0.500000`;
- final response prediction loss mean: `0.054092`;
- final baseline-action anchor loss mean: `0.000252`.

This validates that strict context keeps the 72-value shape and can load M62
without tensor surgery.

## M62 Ablation Diagnostic

Current context command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m65_response_necessity_driver.json \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state \
  --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response \
  --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response \
  --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history \
  --policies heuristic \
  --device cpu \
  --run-dir runs/m67d_m62_current_context_ablation_m65_seed3600
```

Strict context command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m67d_strict_self_id_context_driver.json \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state \
  --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response \
  --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response \
  --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history \
  --policies heuristic \
  --device cpu \
  --run-dir runs/m67d_m62_strict_context_ablation_m65_seed3600
```

Policy summary:

| Profile | Policy | Success | Mean margin | Collision |
| --- | --- | ---: | ---: | ---: |
| current | `m62_a250` | 0.615385 | 0.259857 | 0.384615 |
| current | `m62_a250_reset` | 0.576923 | 0.260361 | 0.423077 |
| current | `m62_a250_zero_current` | 0.576923 | 0.251726 | 0.423077 |
| current | `m62_a250_zero_all` | 0.576923 | 0.251726 | 0.423077 |
| current | `m62_a250_noact` | 0.615385 | 0.259164 | 0.384615 |
| strict | `m62_a250` | 0.615385 | 0.259881 | 0.384615 |
| strict | `m62_a250_reset` | 0.615385 | 0.261148 | 0.384615 |
| strict | `m62_a250_zero_current` | 0.615385 | 0.254910 | 0.384615 |
| strict | `m62_a250_zero_all` | 0.615385 | 0.254910 | 0.384615 |
| strict | `m62_a250_noact` | 0.576923 | 0.257737 | 0.423077 |

Seed-delta audits:

```bash
conda run -n autodrift python -m autodrift.seed_delta_audit \
  --episodes-csv runs/m67d_m62_current_context_ablation_m65_seed3600/episodes.csv \
  --baseline-policy m62_a250 \
  --candidate-policy m62_a250_reset \
  --candidate-policy m62_a250_zero_current \
  --candidate-policy m62_a250_zero_all \
  --candidate-policy m62_a250_noact \
  --run-dir runs/m67d_current_context_seed_delta_audit_m65

conda run -n autodrift python -m autodrift.seed_delta_audit \
  --episodes-csv runs/m67d_m62_strict_context_ablation_m65_seed3600/episodes.csv \
  --baseline-policy m62_a250 \
  --candidate-policy m62_a250_reset \
  --candidate-policy m62_a250_zero_current \
  --candidate-policy m62_a250_zero_all \
  --candidate-policy m62_a250_noact \
  --run-dir runs/m67d_strict_context_seed_delta_audit_m65
```

Delta summary:

| Profile | Candidate | Success delta | Regressed seeds | Mean margin delta |
| --- | --- | ---: | ---: | ---: |
| current | `m62_a250_noact` | 0.000000 | 0 | -0.000694 |
| current | `m62_a250_reset` | -0.038462 | 1 | 0.000503 |
| current | `m62_a250_zero_all` | -0.038462 | 1 | -0.008131 |
| current | `m62_a250_zero_current` | -0.038462 | 1 | -0.008131 |
| strict | `m62_a250_noact` | -0.038462 | 1 | -0.002144 |
| strict | `m62_a250_reset` | 0.000000 | 0 | 0.001267 |
| strict | `m62_a250_zero_all` | 0.000000 | 0 | -0.004971 |
| strict | `m62_a250_zero_current` | 0.000000 | 0 | -0.004971 |

## Conclusion

M67-D is an infrastructure pass and a mixed diagnostic result.

Positive:

- strict context removes the direct obstacle relative-velocity motion proxy;
- the 72-value observation shape is preserved;
- M62 loads without checkpoint surgery;
- M62 baseline success is unchanged on the M65 corpus.

Negative:

- strict context does not make reset-hidden or zero-response ablations more
  behavior-critical for M62;
- zero-current and zero-all response success deltas are `0.000000` under strict
  context;
- no-action history becomes slightly more harmful, but only by one seed.

Interpretation:

```text
Obstacle relative velocity was a real cleanliness issue, but it was not the main
reason M62 lacks strong self-identification evidence. Current state, road
geometry, and single-frame response are still enough for most M65 decisions.
```

Next:

- keep strict context as the preferred self-ID diagnostic profile;
- build the warm-started privileged teacher on top of strict context;
- add wrong-history / matched-history interventions before treating reset or
  zero-response as decisive;
- defer enhanced OSI response features until the teacher upper-bound and
  wrong-history gates are clearer.
