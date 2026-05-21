# M94 Hidden-Envelope Objective-Only Sanity

M94 is the no-wheel follow-up to M93.

M93 showed that the M62 recurrent hidden state is not yet a reliable
future-envelope belief: normal carried hidden lost to same-frame reset hidden on
braking and yaw. M94 tests whether a fixed-batch objective can move the
response encoder and GRU in the right direction before any PPO continuation.

This is not a promoted driver. It does not change the actor observation
contract and does not prove behavior-level self-identification.

## Objective

Load the M62 current-best margin-retention checkpoint:

```text
runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt
```

Collect fixed rollout batches under the no-wheel human-view environment, then
train only:

```text
response_encoder
online_gru_cell
temporary envelope head
```

Frozen:

```text
actor head
critic
context encoder
log_std
```

Targets:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

The training loss predicts normalized future-envelope targets from normal
`response_hidden` and adds a contrast term that requires normal hidden to beat
same-frame reset hidden:

```text
loss =
  MSE(envelope_head(response_hidden), target)
  + contrast_coef * relu(
      contrast_margin
      + normal_hidden_error
      - detached_reset_hidden_error
    )
```

The reset branch is detached in the contrast term so the objective cannot pass
only by deliberately damaging the reset-hidden baseline.

## Commands

All runs use the same settings. Seeds are independent repeats, not tuned
variants.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9430 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --train-fraction 0.70 \
  --ridge 0.1 \
  --steps 200 \
  --batch-size 256 \
  --learning-rate 0.0003 \
  --contrast-coef 0.5 \
  --contrast-margin 0.02 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m94_hidden_envelope_objective_seed9430
```

Repeat with `--seed 9431 --run-dir runs/m94_hidden_envelope_objective_seed9431`
and `--seed 9432 --run-dir runs/m94_hidden_envelope_objective_seed9432`.

Artifacts per seed:

```text
samples.csv
train_metrics.csv
head_metrics.csv
probe_summary.csv
hidden_gain_summary.csv
optimized_checkpoint.pt
summary.json
manifest.json
```

## Results

The table reports `response_hidden - reset_response_hidden` held-out R2 lift.
Positive means normal carried history is more predictive than same-frame reset
hidden.

| seed | samples | target | before | after | delta |
| ---: | ---: | --- | ---: | ---: | ---: |
| 9430 | 711 | braking | -0.010529 | 0.171137 | 0.181666 |
| 9430 | 711 | lateral accel | 0.008380 | 0.112249 | 0.103870 |
| 9430 | 711 | yaw | -0.076165 | 0.013184 | 0.089349 |
| 9431 | 720 | braking | 0.110757 | -0.472573 | -0.583329 |
| 9431 | 720 | lateral accel | -0.125954 | 0.087567 | 0.213520 |
| 9431 | 720 | yaw | -1.065823 | 0.047270 | 1.113093 |
| 9432 | 724 | braking | 1.000962 | 0.410143 | -0.590820 |
| 9432 | 724 | lateral accel | 1.000244 | 2.483029 | 1.482785 |
| 9432 | 724 | yaw | -0.940303 | -0.183202 | 0.757101 |

After optimization:

```text
7 / 9 target-seed pairs have positive normal-vs-reset R2 lift.
Yaw improves on all three seeds.
Lateral acceleration improves on all three seeds.
Braking improves on only one of three seeds.
```

## Interpretation

M94 is a qualified positive objective-only result.

What worked:

- The objective can move no-wheel response hidden in the intended direction.
- Yaw and lateral future-envelope belief improve repeatably across three seeds.
- The fixed-batch harness writes before/after ridge probes, not only training
  loss, so the result is not just a temporary-head artifact.

What did not work:

- Braking authority prediction is unstable. Two seeds have worse
  normal-vs-reset braking lift after optimization.
- Policy fused features are not a promotion metric here; the actor head was
  frozen, but response encoder and GRU changed, so behavior still needs a
  separate retention and intervention gate.
- This is fixed-batch evidence only. It is not yet a PPO recipe.

## Decision

Do not proceed directly to PPO continuation from M94.

M94 justifies a follow-up objective iteration focused on braking stability:

```text
keep the no-wheel input contract;
keep fixed-batch objective-only testing before PPO;
weight or separate braking/yaw/lateral heads;
require positive normal-vs-reset lift on braking and yaw across repeated seeds;
then run behavior retention and reset/wrong-history gates.
```

The current M94 checkpoint artifacts are useful diagnostics, not driver
candidates.
