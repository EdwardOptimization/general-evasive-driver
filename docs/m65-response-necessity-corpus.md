# M65 Response-History Necessity Corpus

Last updated: 2026-05-21

## Motivation

M64 showed that M37_102 and M62_a250 behave almost identically under paired
response/history ablations. The policy can drive, and M62 improves
margin-retention, but response history is still not behavior-critical.

M65 builds a reusable corpus miner for that failure mode. It turns paired
nominal/low-friction perturbation episodes into a ranked seed sequence for
continuation training. This does not add hidden vehicle parameters, controller
mode, friction labels, or oracle values to the actor.

## Harness

New module:

- `src/autodrift/response_necessity_corpus.py`

New CLI:

- `autodrift-response-necessity-corpus`

The miner scores each shared seed by:

- whether the baseline succeeds nominally but fails under low-friction
  perturbation;
- perturbed clearance margin;
- nominal-to-perturbed return and margin drop;
- whether reset, zero-response, or no-action-history ablations are not worse on
  the perturbed case.

Outputs:

- `seed_response_necessity.csv`: all scored paired seeds;
- `scenario_corpus.csv`: selected critical seeds;
- `seed_sequence.csv`: repeated seed list consumable by PPO;
- `summary.csv` and `manifest.json`.

## Corpus Command

```bash
conda run -n autodrift python -m autodrift.response_necessity_corpus \
  --episodes-csv runs/m64_m62_paired_perturbation_gate_seed3600/episodes.csv \
  --baseline-policy m62_a250 \
  --ablation-policy m62_a250_reset \
  --ablation-policy m62_a250_zero_current \
  --ablation-policy m62_a250_zero_all \
  --ablation-policy m62_a250_noact \
  --top-k 40 \
  --repeat 4 \
  --near-margin 0.05 \
  --margin-scale 0.25 \
  --run-dir runs/m65_response_necessity_corpus_seed3600
```

Result:

| Metric | Value |
| --- | ---: |
| Scored paired seeds | 80 |
| Critical seeds | 26 |
| Perturbation regressions | 22 |
| Low perturbed-margin seeds | 26 |
| Seed sequence rows | 104 |
| Max score | 29.261055 |

The top seeds are cases where M62_a250 succeeds in the nominal condition, fails
or becomes near-margin under low friction, and the ablated policies are often
not worse. Those are exactly the cases where the next continuation should make
closed-loop response history matter.

## Training Smoke

New config:

- `configs/ppo_m65_response_necessity_driver.json`

Smoke command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m65_response_necessity_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 2965 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m65_response_necessity_smoke_seed2965
```

Result:

- returncode: `0`;
- checkpoint: `runs/ppo_m65_response_necessity_smoke_seed2965/checkpoint.pt`;
- eval return mean: `70.448440`;
- eval termination rate: `0.100000`;
- final response prediction loss mean: `0.049053`;
- final baseline-action anchor loss mean: `0.000130`.

## Conclusion

M65 is an infrastructure and smoke-training step, not a driver promotion. The
project now has a reusable response-necessity corpus that targets the exact M64
failure: perturbation-critical seeds where ablations do not reliably hurt.

The next task should run a full M65 continuation from M62_a250, then evaluate
the resulting checkpoints on the unchanged strict margin-retention gate,
broader driver audit, and M64 paired self-identification gate. Promotion should
require both no aggregate regression and stronger response/history ablation
degradation.
