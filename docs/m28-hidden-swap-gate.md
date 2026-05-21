# M28 Hidden-Swap Self-Identification Gate

Last updated: 2026-05-21

## Decision

M28 should implement a matched-current-observation hidden-swap gate for the
human-view GRU driver. The goal is not to prove that every useful adaptation
must live in the GRU hidden state. The goal is to separate three different
claims:

- the policy can drive the obstacle task;
- the policy adapts from current closed-loop feedback;
- the policy needs accumulated recurrent state to identify hidden dynamics.

The current M26/M27 evidence only supports the first claim and weakly probes the
second. It does not prove the third.

## Why Reset Is Not Enough

Hidden reset is a narrow ablation. It asks whether long-horizon GRU state is
necessary on a specific gate. It does not answer whether the policy uses
closed-loop feedback at all.

Reset can match normal inference when:

- train and test dynamics do not vary enough to require identification;
- the current observation is already close to Markov;
- ego velocity, yaw rate, acceleration, actuator state, and previous physical
  commands contain enough information for a local correction;
- the benchmark is saturated or not near a response-critical threshold.

Therefore a reset tie is a negative result only for recurrent memory dependence
on that gate. It should not be written as proof that the driver cannot adapt.

## Harness Contract

The M28 harness should:

1. Run paired rollouts under hidden dynamics A and B, such as normal friction
   versus low friction or fast versus slow actuator response.
2. Use the same visible geometry seed where possible.
3. Roll out a probing window so the policy can experience vehicle response.
4. Snapshot environment state, visible observation, and GRU hidden state near an
   obstacle decision point.
5. Pair snapshots by visible-observation distance.
6. Replay continuations from the same source environment snapshot with:
   normal hidden state, reset hidden state, zero-response observation, and
   hidden state swapped from the paired hidden dynamics.

The gate must report visible-observation match distance. If observations are
not closely matched, the result is diagnostic only.

## Required Artifacts

- `pairs.csv`: one row per accepted or rejected pair, including seed,
  condition labels, snapshot step, obstacle distance, and visible-observation
  distance.
- `replays.csv`: one row per continuation variant, including return, success,
  collision, off-road, spin-out, terminal reason, and first action.
- `summary.csv`: aggregate success, return, first-action distance, and failure
  counts by source condition and variant.
- `manifest.json`: checkpoint path, config path, command, seed, git revision,
  and artifact paths.

## Pass Criteria

M28 passes as recurrent self-identification evidence only if all are true:

- normal hidden state remains competitive with the best human-view checkpoint
  baseline on the selected hard cases;
- visible-observation distances for accepted pairs are below the documented
  threshold;
- reset or hidden-swap variants reduce success or return on matched cases;
- the action or outcome change favors the hidden state that came from the
  matching hidden dynamics;
- the result is reproduced with commands and artifacts in the research log.

M28 can also produce a useful partial pass:

- if zero-response hurts but reset and hidden-swap do not, the policy is using
  current closed-loop feedback but not accumulated recurrent memory;
- if all variants match, the selected cases are not response-critical enough or
  the trained policy has not learned feedback-based adaptation.

## Planned Command

After the CLI exists, the first run should use the current best human-view
checkpoint:

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --episodes 80 \
  --seed 4200 \
  --device cpu \
  --run-dir runs/m28_hidden_swap_gate_seed4200
```

The command should remain CPU-runnable because it is an evaluation harness, not
a training job.

## Implementation Status

The M28 CLI is implemented as `autodrift.hidden_swap_gate` with script entry
`autodrift-hidden-swap-gate`.

Smoke command:

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --episodes 2 \
  --seed 4200 \
  --device cpu \
  --run-dir runs/m28_hidden_swap_gate_smoke_seed4200
```

Smoke artifacts:

- `runs/m28_hidden_swap_gate_smoke_seed4200/pairs.csv`;
- `runs/m28_hidden_swap_gate_smoke_seed4200/replays.csv`;
- `runs/m28_hidden_swap_gate_smoke_seed4200/summary.csv`;
- `runs/m28_hidden_swap_gate_smoke_seed4200/manifest.json`.

Smoke result:

- 2 paired seeds were collected;
- both visible-observation pairs were accepted under the default 0.75 distance
  threshold;
- mean visible-observation distance: 0.389;
- mean hidden-state distance: 1.205;
- nominal continuations succeeded for all variants;
- perturbed continuations succeeded for one of two seeds across all variants;
- reset and zero-response changed first actions more than hidden-swap did.

This is infrastructure validation only, not a gate result. The important smoke
fix was to require post-friction hidden updates before taking a snapshot.
Without that requirement, the visible current observation could already reflect
the new friction while the GRU hidden state had not yet consumed any post-step
feedback, making hidden-swap distance zero for the wrong reason.

## Next Training Decision

Use the M28 result to choose the next step:

- recurrent self-identification pass: broaden held-out dynamics and train for
  robustness instead of changing architecture;
- current-feedback-only pass: keep the human-view input contract and add harder
  response-critical training cases where memory should matter;
- no feedback dependence: revise training curriculum, reward thresholds, or
  actor loss so different hidden dynamics require different corrective actions
  at the same visible decision point.
