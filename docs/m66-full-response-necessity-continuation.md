# M66 Full Response-Necessity Continuation

Last updated: 2026-05-21

## Motivation

M65 created a response-necessity seed corpus from the M64 paired perturbation
gate and validated that PPO can train on it. M66 runs the full continuation from
M62_a250 and checks whether this replay-style objective can both preserve
margin retention and make response history more behavior-critical.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m65_response_necessity_driver.json \
  --seed 2965 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m65_response_necessity_seed2965
```

Result:

- returncode: `0`;
- run dir: `runs/ppo_m65_response_necessity_seed2965`;
- final checkpoint: `runs/ppo_m65_response_necessity_seed2965/checkpoint.pt`;
- dense checkpoints: `m65_004` through `m65_032`;
- eval return mean: `70.371693`;
- eval termination rate: `0.100000`.

## Strict Margin-Retention Gate

Validation artifacts:

- `runs/m66_m38_margin_benchmark_seed4300`;
- `runs/m66_broad_margin_benchmark_seed3000`;
- `runs/m66_fresh_margin_benchmark_seed5200`;
- `runs/m66_margin_critical_corpus`;
- `runs/m66_margin_retention_gate_strict`.

Strict gate result: `needs_iteration`.

| Candidate | Success Delta | Binary Regressions | Near-Margin Regressions | Mean Margin Delta | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| `m65_004` | 0.000000 | 0 | 1 | -0.000603 | false |
| `m65_008` | 0.000000 | 0 | 3 | -0.001333 | false |
| `m65_012` | 0.000000 | 0 | 3 | -0.000563 | false |
| `m65_016` | 0.000000 | 0 | 5 | -0.000741 | false |
| `m65_020` | -0.006250 | 1 | 5 | -0.000441 | false |
| `m65_024` | -0.006250 | 1 | 6 | -0.001355 | false |
| `m65_028` | -0.006250 | 1 | 7 | -0.002107 | false |
| `m65_032` | -0.006250 | 1 | 7 | -0.001567 | false |

The closest candidate is `m65_004`: it preserves aggregate success and has no
binary regression, but still has one near-margin regression and negative mean
margin delta versus M62_a250. Later checkpoints add a binary regression on the
M38 shared-seed source.

## Paired Self-Identification Check

Because no checkpoint passed margin retention, only the closest candidate,
`m65_004`, was rerun through the M64 paired perturbation gate.

Command:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m65_004=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt \
  --checkpoint-policy m65_004_reset=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@reset_recurrent_state \
  --checkpoint-policy m65_004_zero_current=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@zero_current_response \
  --checkpoint-policy m65_004_zero_all=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@zero_all_response \
  --checkpoint-policy m65_004_noact=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@zero_action_history \
  --episodes 80 \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m66_m65_004_paired_perturbation_gate_seed3600
```

Result:

| Policy | Nominal Success | Perturbed Success | Success Drop | Return Delta |
| --- | ---: | ---: | ---: | ---: |
| `m62_a250` | 0.9375 | 0.6875 | 0.2500 | -0.988940 |
| `m65_004` | 0.9375 | 0.6875 | 0.2500 | -1.011246 |
| `m65_004_noact` | 0.9375 | 0.6750 | 0.2625 | -1.817004 |
| `m65_004_reset` | 0.9375 | 0.7000 | 0.2375 | 0.696396 |
| `m65_004_zero_all` | 0.9250 | 0.7000 | 0.2250 | -0.281000 |
| `m65_004_zero_current` | 0.9250 | 0.7000 | 0.2250 | -0.281000 |

The ablation pattern is effectively unchanged from M62_a250. Reset and
zero-response still do not weaken perturbed success.

## Conclusion

M66 is a negative result. Replay of response-necessity seeds with a stronger
response-prediction auxiliary is not enough:

- no checkpoint passes strict margin retention versus M62_a250;
- the closest candidate does not improve the M64 paired ablation signal;
- the failure appears concentrated in near-boundary M38 seeds, especially
  `4457`, while broad/fresh sources are mostly retained.

The next step should not simply increase replay probability. M67 should change
the objective so that the recurrent state is trained against counterfactual
closed-loop evidence, for example by adding paired intervention snippets or an
explicit ablated-policy disadvantage term on response-critical seeds. Actor
inputs must remain clean.
