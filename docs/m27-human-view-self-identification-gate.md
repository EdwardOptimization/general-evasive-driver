# M27 Human-View Self-Identification Gate

Last updated: 2026-05-21

## Motivation

M26 proved that the human-view GRU driver can drive the obstacle benchmark:
`m26_602` reaches 0.800 success against `envelope_aes` at 0.675. It did not
prove professional-driver-style self-identification. Hidden reset does not
reduce success, and masking the response stream only drops success to 0.775.

That result has a narrow meaning. The human-view observation already includes
ego response and previous physical commands, so many scenes can be solved as a
nearly Markov control problem. Resetting hidden state is only a test of whether
long-horizon GRU memory is necessary for the current gate.

M27 and the follow-up M28 gate must distinguish:

- the policy can drive well;
- the policy can adapt to different hidden dynamics;
- the policy needs accumulated recurrent state for that adaptation.

This distinction matters because reset/no-reset is not a universal adaptation
test. If train and test do not vary hidden dynamics, or if the current
human-view response stream is already sufficient for local correction, reset can
match normal inference. That does not prove the policy is blind to feedback. It
only says the current gate did not require long-horizon recurrent memory.

## Current Best Candidate

```text
runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt
```

Current evidence:

- same-seed obstacle benchmark success: 0.800;
- hidden-reset success: 0.800;
- zero-current-response success: 0.775;
- zero-all-response success: 0.775;
- old M22 hard seeds are saturated and no longer useful under the human-view
  contract.

## Proof Standard

A self-identification gate should not rely on aggregate success alone. It should
use matched-current-observation cases:

1. Run a probing window under hidden dynamics A or B.
2. Bring the vehicle to a similar visible road, obstacle, ego-state, and action
   decision point.
3. Compare policy variants at that decision point.
4. Verify that the hidden state changes action or outcome in the direction that
   helps the matching hidden dynamics.

Required policy variants:

- normal GRU hidden state;
- hidden reset each step;
- zero current response features;
- zero all response features;
- hidden swap between dynamics A and dynamics B.

The gate passes only if normal hidden state improves outcome relative to reset
or swapped hidden state on cases where the current visible observation is
matched closely enough. A hidden-swap action change without outcome improvement
is interesting but not sufficient.

## First Runnable Gate

The first M27 task was a weaker paired perturbation baseline:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --checkpoint-policy m26_602=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --checkpoint-policy m26_602_reset=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@reset_recurrent_state \
  --checkpoint-policy m26_602_zero_current=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@zero_current_response \
  --checkpoint-policy m26_602_zero_all=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@zero_all_response \
  --episodes 80 \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m27_human_view_paired_gate_seed3600
```

This is useful as a baseline, but it is not a complete proof because the paired
runner does not force matched-current-observation decision points or hidden
swaps.

## Required Harness Upgrade

If the first paired gate is weak or saturated, implement a dedicated matched
state gate:

- collect candidate seeds with paired hidden dynamics, such as high/low friction
  or fast/slow actuator response;
- roll out a short probing window before the obstacle decision;
- snapshot current observation, hidden state, and environment state near the
  decision point;
- match candidate pairs by visible observation distance;
- replay the matched decision with normal, reset, zero-response, and hidden-swap
  variants;
- report action distance, success difference, return difference, and whether
  the swapped hidden state hurts the matching dynamics.

This harness is now the M28 proof route because the M27 paired baseline did not
expose hidden-state dependence.

## Pass Criteria

The human-view branch should not be marked as a self-identification pass unless
all are true:

- normal M26-family policy remains above the envelope AES baseline on the
  selected hard corpus;
- reset or hidden-swap variants reduce success or return on matched cases;
- zero-response ablation reduces success or return when current response
  feedback is necessary;
- the same evidence is recorded in docs with commands, run dirs, and tables.

If these criteria fail, record the failure and use the matched cases to design
the next training or architecture changes.

## Paired Baseline Result

Command run:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --checkpoint-policy m26_602=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --checkpoint-policy m26_602_reset=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@reset_recurrent_state \
  --checkpoint-policy m26_602_zero_current=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@zero_current_response \
  --checkpoint-policy m26_602_zero_all=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@zero_all_response \
  --episodes 80 \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m27_human_view_paired_gate_seed3600
```

Result:

| Policy | Nominal success | Perturbed success | Success drop |
| --- | ---: | ---: | ---: |
| M26_602 | 0.938 | 0.663 | 0.275 |
| M26_602 reset hidden | 0.925 | 0.663 | 0.263 |
| M26_602 zero current response | 0.925 | 0.638 | 0.288 |
| M26_602 zero all response | 0.925 | 0.638 | 0.288 |

This is a weak/negative self-identification result. The paired friction
perturbation is hard in aggregate, but it does not show that normal recurrent
hidden state is necessary. Reset hidden matches normal perturbed success, and
zero-response variants are only slightly lower.

The result confirms the need for the required harness upgrade above:
matched-current-observation and hidden-swap tests are the next evidence path.

## M28 Follow-Up

M28 should implement the hidden-swap gate described above as a runnable CLI. The
minimum artifact contract is:

- `pairs.csv`: source condition, paired condition, seed, snapshot step,
  obstacle distance, and visible-observation distance;
- `replays.csv`: per-pair continuation results for normal, reset,
  zero-response, and hidden-swap variants;
- `summary.csv`: success, return, collision, off-road, spin-out, and
  first-action distance grouped by source condition and variant;
- `manifest.json`: config, checkpoint, command, seed, and artifact metadata.

The M28 result should be interpreted in three separate buckets:

- matched-current cases where hidden swap or reset hurts outcome: evidence for
  recurrent self-identification;
- matched-current cases where zero-response hurts but reset does not: evidence
  for current-feedback adaptation without long-horizon memory;
- unmatched or saturated cases: diagnostic only, not a proof.
