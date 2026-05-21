# M108 Baseline Multi-Seed Hidden-Envelope Audit

M108 compares M62, M98, M102, and M105 under the same M107 multi-seed
hidden-envelope gate.

The question is:

```text
Did M105 damage hidden belief,
or is the current hidden-envelope proof surface unstable for all checkpoints?
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_multiseed_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m98_9480=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --checkpoint-policy m102_9550=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105_9710=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --probe-seeds 9510,9511,9512 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --mean-lift-threshold 0.0 \
  --min-lift-threshold 0.0 \
  --pass-fraction-threshold 1.0 \
  --run-dir runs/m108_baseline_multiseed_hidden_envelope_gate_seed9510
```

## Results

| checkpoint | target | mean lift | min lift | max lift | pass fraction |
| --- | --- | ---: | ---: | ---: | ---: |
| M62 | braking | 12.125411 | -0.187838 | 36.719135 | 0.3333 |
| M62 | lateral | -0.073465 | -0.268978 | 0.174679 | 0.3333 |
| M62 | yaw | -0.223845 | -0.422949 | -0.036225 | 0.0000 |
| M98 | braking | 3.662754 | -0.471472 | 11.101300 | 0.6667 |
| M98 | lateral | -0.990467 | -2.944666 | 0.682472 | 0.3333 |
| M98 | yaw | -0.855895 | -1.504834 | -0.014135 | 0.0000 |
| M102 | braking | 3.817077 | -0.320965 | 11.368116 | 0.6667 |
| M102 | lateral | -0.952357 | -2.920255 | 0.801162 | 0.3333 |
| M102 | yaw | -0.863584 | -1.491405 | -0.065070 | 0.0000 |
| M105 | braking | 4.081331 | -0.266590 | 12.299186 | 0.6667 |
| M105 | lateral | -0.787382 | -2.270934 | 0.557126 | 0.3333 |
| M105 | yaw | -0.865335 | -1.595636 | 0.033114 | 0.3333 |

All tested checkpoints fail the strict aggregate gate. M62 has a smaller
lateral/yaw failure magnitude than the hidden-envelope-objective checkpoints,
but it still fails mean, minimum, and pass-fraction criteria on yaw and lateral.

## Decision

M108 rejects the idea that M105 alone caused the hidden-envelope blocker.

Interpretation:

- the M105 behavior-dependence signal remains worth preserving;
- the current single-probe hidden-envelope success story was too weak;
- M98/M102 hidden-envelope objective wins were not robust under this aggregate
  proof surface;
- the next step should diagnose and redesign the hidden-envelope proof surface
  before training another hidden-retention objective.

M109 should focus on probe reliability:

```text
inspect target distributions by probe seed;
inspect train/test split variance;
compare current-response, response-hidden, and reset-hidden baselines;
test larger sample counts or repeated train/test splits;
pre-register a less seed-fragile envelope gate.
```
