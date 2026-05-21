# M67-A Privileged Upper-Bound Harness

M66 showed that response-necessity replay and a larger response-prediction loss
did not make recurrent response history behavior-critical. M67-A changes the
question before adding another student objective:

```text
Does a teacher with hidden vehicle dynamics actually outperform m62_a250 on the
response-critical seeds?
```

If the privileged teacher cannot improve the M64/M65 seeds, the current corpus is
not a good self-identification corpus and the next step should be re-mining
matched action-divergent scenarios, not training a student harder.

## Added Harness

- `DriftEnvConfig.privileged_observation_mode` now supports:
  - `basic`: legacy four-value privileged packet, preserving the old 76-value
    observation when `include_privileged_params=True`;
  - `full_dynamics`: teacher-only ten-value hidden packet, producing an 82-value
    M67-A observation.
- `configs/ppo_m67a_privileged_upper_bound_teacher.json` trains an `online_gru`
  privileged teacher from scratch on the M65 response-necessity seed mix.
- `python -m autodrift.privileged_upper_bound` evaluates a human-view baseline
  and a privileged teacher under different env configs on the same seed sequence,
  then writes:
  - `episodes.csv`;
  - `policy_summary.csv`;
  - `seed_delta.csv`;
  - `summary.json`;
  - `manifest.json`.

## Smoke Validation

Teacher smoke command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --total-steps 1024 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3067 \
  --device cuda \
  --run-dir runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067 \
  --eval-episodes 2
```

Result:

- return mean: `66.402815`;
- termination rate: `0.500000`;
- response prediction loss at step 1024: `0.135043`;
- checkpoint:
  `runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067/checkpoint.pt`.

Upper-bound harness smoke command:

```bash
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m24_human_view_gru_driver.json \
  --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67a_smoke=runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067/checkpoint.pt \
  --episodes 4 \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67a_privileged_upper_bound_smoke_seed3600
```

Result:

| Policy | Episodes | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: | ---: |
| `m62_a250` | 4 | 1.000000 | 0.000000 | 1.736576 |
| `m67a_smoke` | 4 | 0.250000 | 0.750000 | 0.346235 |

The smoke teacher is intentionally undertrained and is not a research result. It
only validates the full-dynamics observation, training, checkpoint, and
per-env-config comparison path.

## Next Step

M67-B ran this step and recorded the negative result in
`docs/m67b-full-privileged-upper-bound-training.md`. The original next-step
commands are kept here for reproducibility.

Run the full M67-A teacher training:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --seed 3067 \
  --device cuda \
  --run-dir runs/ppo_m67a_privileged_upper_bound_teacher_seed3067
```

Then compare against M62 on the M65 response-necessity corpus:

```bash
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m24_human_view_gru_driver.json \
  --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67a_teacher=runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoint.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67a_privileged_upper_bound_m65_seed3600
```

Pass condition:

- privileged teacher improves success or mean clearance margin on response-critical
  seeds;
- action/behavior divergence is large enough to justify a matched
  action-divergent corpus;
- no deployable actor uses the hidden packet.

If the teacher does not improve, M67-B should re-mine the corpus before any
student OSI or intervention-loss work.
