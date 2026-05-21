# M64 Stronger Response-History Self-Identification Gate

Last updated: 2026-05-21

## Motivation

M62 made `m62_a250` the current best margin-retention candidate. M63 then
showed that the candidate keeps held-out aggregate success, but the reset,
zero-response, and no-action-history ablations were still too strong. M64
turns that observation into a sharper self-identification diagnostic.

The purpose is not to add a new oracle input or tune aggregate success. The
purpose is to ask whether a human-view recurrent driver actually depends on its
closed-loop response history when friction and vehicle response change.

## Seed-Delta Audit

Command:

```bash
conda run -n autodrift python -m autodrift.seed_delta_audit \
  --episodes-csv runs/m63_m62_broader_driver_audit_seed7000/episodes.csv \
  --baseline-policy m62_a250 \
  --candidate-policy m62_a250_reset \
  --candidate-policy m62_a250_zero_current \
  --candidate-policy m62_a250_zero_all \
  --candidate-policy m62_a250_noact \
  --run-dir runs/m64_m62_ablation_seed_delta_audit
```

Result:

| Candidate | Success Delta | Improved Seeds | Regressed Seeds | Mean Margin Delta |
| --- | ---: | ---: | ---: | ---: |
| `m62_a250_noact` | 0.000000 | 0 | 0 | -0.002298 |
| `m62_a250_reset` | -0.008333 | 1 | 2 | -0.000755 |
| `m62_a250_zero_all` | 0.000000 | 1 | 1 | -0.007306 |
| `m62_a250_zero_current` | 0.000000 | 1 | 1 | -0.007306 |

The ablations have only small seed-level outcome impact. Zeroing response
features hurts mean clearance margin more than resetting hidden state, but it
does not produce a strong success-rate drop.

## Paired Perturbation Gate

Command:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m37_102_reset=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@reset_recurrent_state \
  --checkpoint-policy m37_102_zero_current=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@zero_current_response \
  --checkpoint-policy m37_102_zero_all=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@zero_all_response \
  --checkpoint-policy m37_102_noact=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@zero_action_history \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state \
  --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response \
  --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response \
  --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history \
  --episodes 80 \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m64_m62_paired_perturbation_gate_seed3600
```

Result:

| Policy | Pairs | Nominal Success | Perturbed Success | Success Drop | Return Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `m37_102` | 80 | 0.9375 | 0.6875 | 0.2500 | -0.987676 |
| `m37_102_noact` | 80 | 0.9375 | 0.6750 | 0.2625 | -1.634896 |
| `m37_102_reset` | 80 | 0.9375 | 0.7000 | 0.2375 | 0.730365 |
| `m37_102_zero_all` | 80 | 0.9250 | 0.7000 | 0.2250 | -0.216563 |
| `m37_102_zero_current` | 80 | 0.9250 | 0.7000 | 0.2250 | -0.216563 |
| `m62_a250` | 80 | 0.9375 | 0.6875 | 0.2500 | -0.988940 |
| `m62_a250_noact` | 80 | 0.9375 | 0.6750 | 0.2625 | -1.781823 |
| `m62_a250_reset` | 80 | 0.9375 | 0.7000 | 0.2375 | 0.702021 |
| `m62_a250_zero_all` | 80 | 0.9250 | 0.7000 | 0.2250 | -0.242008 |
| `m62_a250_zero_current` | 80 | 0.9250 | 0.7000 | 0.2250 | -0.242008 |

The paired gate is stricter than the M63 held-out audit because every policy
sees the same nominal and low-friction perturbation seeds. It also evaluates
M37_102 and M62_a250 on the same policy-ablation grid. It still does not prove
driver-like self-identification:

- M37_102 and M62_a250 have effectively the same paired-gate behavior, so the
  M62 margin-retention improvement did not create a stronger response-history
  dependency;
- resetting recurrent hidden does not weaken perturbed success; it is slightly
  higher than the unablated policy on this 80-pair gate for both M37 and M62;
- zeroing response features slightly weakens nominal success but not perturbed
  success;
- removing action history has the clearest perturbed penalty among the tested
  ablations, but the effect is still small.

## Conclusion

M64 is a negative diagnostic, not a current-best promotion. `m62_a250` remains
the current best margin-retention checkpoint, but the recurrent policy still
does not satisfy the ideal-driver self-identification requirement. The policy
can drive well, but these ablations do not show that it must use closed-loop
response history to adapt to changed vehicle and friction response. On this
gate, M62 is not more driver-like than M37.

## Next Step

M65 should target the measured failure directly. The next task should either
mine a response-necessity corpus from paired perturbation episodes or add a
training objective that makes deployable response history behavior-critical,
while keeping actor inputs clean. Aggregate success alone is not enough for the
next promotion.
