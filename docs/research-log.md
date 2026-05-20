# AutoDrift Research Log

Last updated: 2026-05-21

## Current Best

- checkpoint: `runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt`
- status: not ideal-driver passed
- gate artifact: `runs/m8_driver_gate_seed227/summary.json`
- blocker: behavior does not degrade under no-action-history,
  shuffled-history, single-frame-history, or response-feature masking
  ablations.

## Standing Loop

The long-running research cycle is:

```text
hypothesis
  -> code/config change
  -> training
  -> benchmark
  -> ablation
  -> latent/self-identification probe
  -> documentation
  -> commit
  -> next hypothesis
```

The tracked queue is `experiments/research_queue.csv`. Use
`make research-plan` to inspect the next task and `make research-run-next` to
execute one queued task.

## long-term-goal-start

- status: `active`
- current best checkpoint: `runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt`
- next focus: make the driver gate history-critical before running another
  similar long training job.

## 20260520T183427Z m9-history-critical-gate-smoke

- status: `completed`
- kind: `benchmark`
- hypothesis: Repeat the current history-critical probe through the research queue
- command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/m8_history_critical_obstacle_holdout_eval.json --episodes 20 --seed 1500 --policies envelope_aes --checkpoint-policy m5=runs/ppo_m5_obstacle_seed83/checkpoint.pt --checkpoint-policy m8=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt --checkpoint-policy m8_noact=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@zero_action_history --checkpoint-policy m8_shuffle=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@shuffled_history --checkpoint-policy m8_single=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@single_frame_history --device cpu --run-dir runs/research_m9_history_critical_gate_smoke`
- returncode: `0`
- run dir: `runs/research/m9-history-critical-gate-smoke_20260520T183423Z`
- command log: `runs/research/m9-history-critical-gate-smoke_20260520T183423Z/command.log`
- success artifact: `runs/research_m9_history_critical_gate_smoke/policy_summary.csv`
- notes: First runnable task for the long research harness

## 20260520T184110Z m9-observation-degradation-gate

- status: `completed`
- kind: `gate`
- hypothesis: Mask current-frame response and all response history to expose single-frame shortcuts
- command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/m8_history_critical_obstacle_holdout_eval.json --episodes 40 --seed 1600 --policies envelope_aes --checkpoint-policy m8=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt --checkpoint-policy m8_zero_current=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@zero_current_response --checkpoint-policy m8_zero_all=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@zero_all_response --checkpoint-policy m8_single=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@single_frame_history --checkpoint-policy m8_shuffle=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@shuffled_history --device cpu --run-dir runs/research_m9_observation_degradation_gate`
- returncode: `0`
- run dir: `runs/research/m9-observation-degradation-gate_20260520T184106Z`
- command log: `runs/research/m9-observation-degradation-gate_20260520T184106Z/command.log`
- success artifact: `runs/research_m9_observation_degradation_gate/policy_summary.csv`
- notes: Current-response ablation becomes the first formal observation-degradation gate

Conclusion: response-feature masking is also not enough. M8 success stays
0.275 for the base policy, `zero_current_response`, `zero_all_response`,
`single_frame_history`, and `shuffled_history`. The next gate must use an online
perturbation or carried recurrent hidden state; static observation masking still
does not prove professional-driver-like self-identification.

## observation-contract-review

- `aeb_stop_distance` is removed from actor observations because it is computed
  from hidden friction and braking assumptions.
- Explicit sideslip `beta`, `speed_ref`, and `beta_target` are also removed
  from actor observations. They remain reward/logging quantities only.
- M8 historical obstacle observations were 76-dimensional; the current clean
  full-action-history obstacle driver contract is 60-dimensional.
- Checkpoint compatibility for changed observation contracts is intentionally
  removed. Old M8 is historical; the clean driver must be retrained.
- Driver configs must keep `include_privileged_params=false` and
  `friction_limited_speed=false`; otherwise the actor can receive hidden
  simulator state or friction-conditioned speed commands.
- Next training task is a clean-observation temporal driver retrain before an
  online recurrent hidden-state gate.

## 20260520T191508Z m10-clean-observation-retrain

- status: `completed`
- kind: `training`
- hypothesis: Retrain the temporal driver under the clean 60-dimensional obstacle-driver observation
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m8_temporal_gru_driver.json --seed 327 --device cuda --run-dir runs/ppo_m10_clean_temporal_gru_driver_seed327`
- returncode: `0`
- run dir: `runs/research/m10-clean-observation-retrain_20260520T191136Z`
- command log: `runs/research/m10-clean-observation-retrain_20260520T191136Z/command.log`
- success artifact: `runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt`
- notes: Clean 60-dim contract; train from scratch with no init checkpoint

Conclusion: M10 is the first valid clean-contract temporal-GRU checkpoint. It
trained successfully and wrote
`runs/ppo_m10_clean_temporal_gru_driver_seed327/checkpoint.pt`, but built-in
eval is weak: return mean 10.787 and termination rate 0.800.

Follow-up benchmark:

- run dir: `runs/m10_clean_observation_degradation_gate_seed1600`
- M10 success: 0.275
- envelope AES success: 0.225
- M10 zero-current response success: 0.275
- M10 zero-all response success: 0.275
- M10 single-frame history success: 0.275
- M10 shuffled-history success: 0.275

Label diagnosis: M10 solves all 9 sampled `drift_required` cases but only 2 of
31 `unavoidable` cases. The gain over envelope AES is real but narrow.

Latent probe:

- run dir: `runs/m10_clean_latent_probe_seed1700`
- latent friction lift: 0.076
- single-frame friction lift: 0.037
- shuffled-history latent friction lift: 0.086
- latent brake lift: 0.116
- shuffled-history latent brake lift: 0.124

The ordered latent is not clearly stronger than shuffled-history latent.
Therefore M10 is a clean baseline, not evidence of closed-loop
self-identification.

Next hypothesis: build an online recurrent hidden-state gate with hidden-state
reset ablation and paired perturbation scenarios. Static observation masking is
not enough.

## 20260520T192744Z m11-online-recurrent-actor

- status: `completed`
- kind: `training`
- hypothesis: Train an online recurrent driver and test hidden-state reset ablation
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m11_online_recurrent_driver.json --seed 411 --device cuda --run-dir runs/ppo_m11_online_recurrent_driver_seed411`
- returncode: `0`
- run dir: `runs/research/m11-online-recurrent-actor_20260520T192417Z`
- command log: `runs/research/m11-online-recurrent-actor_20260520T192417Z/command.log`
- success artifact: `runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt`
- notes: M10 clean baseline is negative; online_gru carries hidden state instead of stacked observation history

Conclusion: M11 trained successfully and wrote
`runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt`. Built-in eval is
still weak: return mean 13.208 and termination rate 0.700.

Hidden-state gate:

- run dir: `runs/m11_online_recurrent_gate_seed1600`
- M11 success: 0.275
- M11 reset recurrent state success: 0.275
- M11 zero-current response success: 0.250
- M11 zero-all response success: 0.250
- envelope AES success: 0.225

Label diagnosis: M11 solves all 9 sampled `drift_required` cases and only 2 of
31 `unavoidable` cases. Resetting recurrent state does not change those counts.

M11 establishes the stateful actor infrastructure, but it does not prove
behavior-level recurrent self-identification. Current response matters slightly;
carried hidden state does not yet matter on this gate.

Next hypothesis: create paired perturbation scenarios where obstacle geometry is
held fixed but road friction, actuator lag, or brake capacity changes after the
first control actions. The gate should compare normal recurrent state,
hidden-reset, and response-masked policies on those paired cases.

## m12-paired-perturbation-gate

- status: `completed`
- kind: `gate`
- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --checkpoint runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state --checkpoint-policy m11_zero_current=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_current_response --checkpoint-policy m11_zero_all=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_all_response --episodes 40 --seed 1600 --device cpu --run-dir runs/m12_paired_perturbation_gate_seed1600`
- run dir: `runs/m12_paired_perturbation_gate_seed1600`

Result:

- M11 nominal success: 0.275
- M11 perturbed success: 0.275
- M11 paired success drop: 0.000
- M11 reset paired success drop: 0.000
- M11 zero-current paired success drop: 0.000
- M11 zero-all paired success drop: 0.000

Conclusion: paired perturbation infrastructure works, but this friction-range
pair is still not behavior-critical. Success counts remain label dominated.
The next gate should target near-threshold cases and delayed actuator/brake
perturbations that can change the outcome after the policy has already acted.

## m13-near-threshold-paired-gate

- status: `completed`
- kind: `gate`
- corpus command: `conda run -n autodrift python -m autodrift.near_threshold_corpus --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-start 3000 --max-candidates 5000 --count 40 --max-threshold-score 0.20 --min-time-after-step 0.10 --label drift_required --label unavoidable --run-dir runs/m13_near_threshold_corpus_seed3000`
- gate command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state --checkpoint-policy m11_zero_current=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_current_response --checkpoint-policy m11_zero_all=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m13_near_threshold_paired_gate_seed3000`

Corpus result:

- selected seeds: 40
- candidates searched: 5000
- label counts: 19 `drift_required`, 21 `unavoidable`
- max threshold score: 0.009
- mean threshold score: 0.005

Gate result:

- M11 nominal success: 0.750
- M11 perturbed success: 0.375
- M11 paired success drop: 0.375
- M11 reset paired success drop: 0.375
- M11 zero-current paired success drop: 0.375
- M11 zero-all paired success drop: 0.375
- M11 pair counts: 15 nominal-success/perturbed-fail, 0 nominal-fail/perturbed-success,
  15 both-success, 10 both-fail.

Conclusion: M13 finally creates a behavior-critical hidden-response stressor,
but the current M11 driver still does not show a recurrent-state advantage.
Normal recurrent inference, hidden reset, and response-masked inference all
drop by the same amount. Next work should train on near-threshold perturbation
cases, then re-run this exact corpus as the gate.

## m14-near-threshold-training

- status: `pending`
- kind: `training`
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m14_online_recurrent_near_threshold_driver.json --seed 517 --device cuda --run-dir runs/ppo_m14_online_recurrent_near_threshold_seed517`
- success artifact: `runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt`

Infrastructure result:

- clean action-history contract now supports only `full` and `none`;
- `legacy` action history is rejected at config construction;
- near-threshold obstacle sampling is strict, with no best-effort fallback;
- M14 training samples non-AEB near-threshold labels:
  `aes_feasible`, `drift_required`, and `unavoidable`;
- smoke run: `runs/ppo_m14_near_threshold_smoke`;
- smoke eval return mean: 14.449;
- smoke eval termination rate: 1.000.

This is an infrastructure pass, not a policy-quality claim. The next action is
the full CUDA M14 run followed by the exact M13 paired corpus gate.

## 20260520T195244Z m14-near-threshold-training

- status: `failed`
- kind: `training`
- hypothesis: Train online recurrent driver on near-threshold hidden perturbation cases and re-run M13 gate
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m14_online_recurrent_near_threshold_driver.json --seed 517 --device cuda --run-dir runs/ppo_m14_online_recurrent_near_threshold_seed517`
- returncode: `1`
- run dir: `runs/research/m14-near-threshold-training_20260520T195212Z`
- command log: `runs/research/m14-near-threshold-training_20260520T195212Z/command.log`
- success artifact: `runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt`
- notes: M13 gate is strong; train on near-threshold perturbation distribution

Diagnosis: the strict sampler was correct to fail. With
`friction_step.step_range=[8, 40]`, some seeds have no geometry that is both
AEB-infeasible and at least 0.10 s after the friction change. The clean fix is
to move the hidden perturbation earlier to `step_range=[4, 16]`; no fallback or
checkpoint compatibility path is added.

## 20260520T195945Z m14-near-threshold-training

- status: `completed`
- kind: `training`
- hypothesis: Train online recurrent driver on near-threshold hidden perturbation cases and re-run M13 gate
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m14_online_recurrent_near_threshold_driver.json --seed 517 --device cuda --run-dir runs/ppo_m14_online_recurrent_near_threshold_seed517`
- returncode: `0`
- run dir: `runs/research/m14-near-threshold-training_20260520T195616Z`
- command log: `runs/research/m14-near-threshold-training_20260520T195616Z/command.log`
- success artifact: `runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt`
- notes: M13 gate is strong; train on near-threshold perturbation distribution after early-step sampler fix

Training result:

- final eval return mean: 53.519;
- final eval steps mean: 90.900;
- final eval termination rate: 0.300;
- final eval lateral RMSE mean: 2.461.

M13 paired gate re-run:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt --checkpoint-policy m14=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt --checkpoint-policy m14_reset=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt@reset_recurrent_state --checkpoint-policy m14_zero_current=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt@zero_current_response --checkpoint-policy m14_zero_all=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m14_near_threshold_paired_gate_seed3000`
- run dir: `runs/m14_near_threshold_paired_gate_seed3000`
- M14 nominal success: 0.600;
- M14 perturbed success: 0.300;
- M14 paired success drop: 0.300;
- M14 hidden-reset nominal success: 0.900;
- M14 hidden-reset perturbed success: 0.450;
- M14 zero-current and zero-all nominal success: 0.375;
- M14 zero-current and zero-all perturbed success: 0.300.

Conclusion: M14 is a useful negative result. The actor uses current response
features, because masking response drops nominal success from 0.600 to 0.375.
However carried recurrent state is not yet beneficial: resetting hidden state
before every action is better than normal recurrent inference on both nominal
and perturbed pairs. This fails the self-identification proof target.

Next hypothesis: M14's early friction-step fix removed sampler failures but
also shifted the training distribution away from the M13 gate's later
perturbation timing. M15 should sample friction-step timing from the accepted
obstacle geometry so every episode is strict and feasible without forcing an
early-step-only distribution.

## m15-obstacle-aligned-perturbation-sampler

- status: `pending`
- kind: `training`
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m15_obstacle_aligned_recurrent_driver.json --seed 619 --device cuda --run-dir runs/ppo_m15_obstacle_aligned_recurrent_seed619`
- success artifact: `runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt`

Infrastructure change: when `min_time_after_friction_step` is active, the
environment samples the friction step from the accepted obstacle geometry. This
keeps the M13-like late perturbation timing while preserving strict rejection:
if no step in the configured range satisfies the obstacle-time constraint, that
candidate obstacle is rejected.

Smoke result:

- run dir: `runs/ppo_m15_obstacle_aligned_smoke`;
- eval return mean: 60.886;
- eval steps mean: 66.500;
- eval termination rate: 0.500;
- eval lateral RMSE mean: 0.348.

## 20260520T200959Z m15-obstacle-aligned-perturbation-sampler

- status: `completed`
- kind: `training`
- hypothesis: Train with friction-step timing sampled from accepted obstacle geometry so late perturbations stay strict and feasible
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m15_obstacle_aligned_recurrent_driver.json --seed 619 --device cuda --run-dir runs/ppo_m15_obstacle_aligned_recurrent_seed619`
- returncode: `0`
- run dir: `runs/research/m15-obstacle-aligned-perturbation-sampler_20260520T200628Z`
- command log: `runs/research/m15-obstacle-aligned-perturbation-sampler_20260520T200628Z/command.log`
- success artifact: `runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt`

Training result:

- final eval return mean: 59.862;
- final eval steps mean: 62.200;
- final eval termination rate: 0.400;
- final eval lateral RMSE mean: 0.600.

M13 paired gate re-run:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt --checkpoint-policy m15=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt --checkpoint-policy m15_reset=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt@reset_recurrent_state --checkpoint-policy m15_zero_current=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt@zero_current_response --checkpoint-policy m15_zero_all=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m15_obstacle_aligned_paired_gate_seed3000`
- run dir: `runs/m15_obstacle_aligned_paired_gate_seed3000`
- M15 nominal success: 0.725;
- M15 perturbed success: 0.325;
- M15 paired success drop: 0.400;
- M15 hidden-reset nominal success: 0.825;
- M15 hidden-reset perturbed success: 0.400;
- M15 zero-current and zero-all nominal success: 0.525;
- M15 zero-current and zero-all perturbed success: 0.125.

Conclusion: M15 is better than M14 normal inference and proves response features
matter under perturbation, but it still fails the recurrent-state proof. Hidden
reset remains better than normal recurrent inference. The next blocker is
probably the PPO update path: online GRU updates currently replay detached
hidden states per step, so hidden dynamics are not trained with sequence
backpropagation.

## m16-sequence-recurrent-ppo

- status: `pending`
- kind: `training`
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m16_sequence_recurrent_driver.json --seed 733 --device cuda --run-dir runs/ppo_m16_sequence_recurrent_seed733`
- success artifact: `runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt`

Infrastructure change: `recurrent_sequence_training=true` trains online GRU
rollouts as environment sequences. PPO losses still use the same rollout data,
but the update unrolls hidden state through time and zeroes hidden state after
done transitions. A focused gradient test verifies that a loss at t+1 can
backpropagate to t through the recurrent state when no done boundary is present.

Smoke result:

- run dir: `runs/ppo_m16_sequence_recurrent_smoke`;
- eval return mean: 83.584;
- eval steps mean: 67.500;
- eval termination rate: 0.000;
- eval lateral RMSE mean: 0.213.

## 20260520T200959Z m15-obstacle-aligned-perturbation-sampler

- status: `completed`
- kind: `training`
- hypothesis: Train with friction-step timing sampled from accepted obstacle geometry so late perturbations stay strict and feasible
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m15_obstacle_aligned_recurrent_driver.json --seed 619 --device cuda --run-dir runs/ppo_m15_obstacle_aligned_recurrent_seed619`
- returncode: `0`
- run dir: `runs/research/m15-obstacle-aligned-perturbation-sampler_20260520T200628Z`
- command log: `runs/research/m15-obstacle-aligned-perturbation-sampler_20260520T200628Z/command.log`
- success artifact: `runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt`
- notes: M14 reset-hidden beats normal recurrent inference so align training timing with the M13 gate instead of forcing early friction steps
