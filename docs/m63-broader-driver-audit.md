# M63 Broader Driver Audit for M62

Last updated: 2026-05-21

## Motivation

M62 produced the first strict margin-retention pass and made `m62_a250` the
current best margin-retention driver candidate. M63 checks whether that
candidate can also be treated as a broader driver promotion.

This audit uses the human-view observation contract rather than the older M7
default gate config, because the old M7 config uses a different history-based
observation setup.

## Held-Out Benchmark

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 120 \
  --seed 7000 \
  --policies envelope_aes \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state \
  --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response \
  --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response \
  --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m63_m62_broader_driver_audit_seed7000
```

## Result

| Policy | Success | Return Mean | Min Margin Mean | Min Margin Min |
| --- | ---: | ---: | ---: | ---: |
| `envelope_aes` | 0.800000 | 67.317306 | 1.728369 | -0.120028 |
| `m37_102` | 0.875000 | 69.896126 | 1.942143 | -0.119647 |
| `m62_a250` | 0.875000 | 69.897474 | 1.942633 | -0.118320 |
| `m62_a250_reset` | 0.866667 | 69.390836 | 1.941878 | -0.117053 |
| `m62_a250_zero_current` | 0.875000 | 70.330232 | 1.935327 | -0.136532 |
| `m62_a250_zero_all` | 0.875000 | 70.330232 | 1.935327 | -0.136532 |
| `m62_a250_noact` | 0.875000 | 70.051968 | 1.940335 | -0.148179 |

M62 retains the M37 aggregate success rate and slightly improves mean clearance
margin on this held-out random benchmark. However, the ablations remain too
weak:

- resetting recurrent hidden reduces success only from `0.875000` to
  `0.866667`;
- zeroing current/all response features does not reduce success;
- zeroing action history does not reduce success.

## Conclusion

M62 should remain the current best margin-retention candidate, but M63 does not
justify calling it a broader ideal driver. The next blocker is not aggregate
avoidance or margin retention. It is still closed-loop self-identification:
the policy can drive well, but the existing ablations do not prove that it uses
response history in a driver-like way.

## Next Step

M64 should build a stronger response-history/self-identification gate for
M62-class human-view recurrent policies. The gate should focus on cases where
resetting recurrent state or removing response features must change behavior,
not just average held-out success.
