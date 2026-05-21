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

## 20260520T210114Z m16-sequence-recurrent-ppo

- status: `completed`
- kind: `training`
- hypothesis: Train online GRU hidden dynamics with sequence backpropagation instead of detached per-step hidden replay
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m16_sequence_recurrent_driver.json --seed 733 --device cuda --run-dir runs/ppo_m16_sequence_recurrent_seed733`
- returncode: `0`
- run dir: `runs/research/m16-sequence-recurrent-ppo_20260520T201650Z`
- command log: `runs/research/m16-sequence-recurrent-ppo_20260520T201650Z/command.log`
- success artifact: `runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt`

Training result:

- wall-clock: about 44 minutes for 1.5M steps;
- final eval return mean: 64.688;
- final eval steps mean: 70.300;
- final eval termination rate: 0.200;
- final eval lateral RMSE mean: 1.181.

M13 paired gate re-run:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt --checkpoint-policy m16=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt --checkpoint-policy m16_reset=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt@reset_recurrent_state --checkpoint-policy m16_zero_current=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt@zero_current_response --checkpoint-policy m16_zero_all=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m16_sequence_recurrent_paired_gate_seed3000`
- run dir: `runs/m16_sequence_recurrent_paired_gate_seed3000`
- M16 nominal success: 0.800;
- M16 perturbed success: 0.375;
- M16 paired success drop: 0.425;
- M16 hidden-reset nominal success: 0.900;
- M16 hidden-reset perturbed success: 0.375;
- M16 zero-current and zero-all nominal success: 0.750;
- M16 zero-current and zero-all perturbed success: 0.350.

Conclusion: sequence PPO fixed the detached-hidden training defect and improved
normal perturbed success to the M11 level, but it still does not prove recurrent
self-identification. Reset remains better nominally, and response masking is
only slightly worse than normal M16. The next hypothesis is to add a deployable
response-prediction auxiliary loss so hidden state is explicitly trained to
encode how the vehicle reacts over time.

## m17-response-prediction-aux

- status: `pending`
- kind: `training`
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m17_response_aux_recurrent_driver.json --seed 733 --device cuda --run-dir runs/ppo_m17_response_aux_recurrent_seed733`
- success artifact: `runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt`

Infrastructure change: `response_prediction_aux_coef` adds a deployable
auxiliary target for online GRU sequence training. The head predicts the next
observation's response features `[vx, vy, yaw_rate, steer_state,
drive_brake_state]` from current recurrent feature and executed action, masked
across done transitions. It does not use hidden simulator parameters, labels,
controller modes, or feasibility oracles.

Smoke result:

- seed 809 smoke: rejected as a poor random-initialization comparison,
  termination rate 1.000 after one update;
- seed 733 smoke: `runs/ppo_m17_response_aux_smoke_seed733`;
- eval return mean: 83.418;
- eval steps mean: 67.500;
- eval termination rate: 0.000;
- eval lateral RMSE mean: 0.258.

## 20260520T220825Z m17-response-prediction-aux

- status: `completed`
- kind: `training`
- hypothesis: Add deployable response-prediction auxiliary loss so online GRU hidden state encodes vehicle reactions
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m17_response_aux_recurrent_driver.json --seed 733 --device cuda --run-dir runs/ppo_m17_response_aux_recurrent_seed733`
- returncode: `0`
- run dir: `runs/research/m17-response-prediction-aux_20260520T211106Z`
- command log: `runs/research/m17-response-prediction-aux_20260520T211106Z/command.log`
- success artifact: `runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt`
- notes: M16 sequence PPO improves perturbed success but reset still wins nominally and response masking is only slightly worse

Training result:

- final eval return mean: 79.977;
- final eval steps mean: 62.800;
- final eval termination rate: 0.000;
- final eval lateral RMSE mean: 0.813;
- final eval beta absolute error mean: 0.132.

M13 paired gate re-run:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt --checkpoint-policy m17=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt --checkpoint-policy m17_reset=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt@reset_recurrent_state --checkpoint-policy m17_zero_current=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt@zero_current_response --checkpoint-policy m17_zero_all=runs/ppo_m17_response_aux_recurrent_seed733/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m17_response_aux_paired_gate_seed3000`
- run dir: `runs/m17_response_aux_paired_gate_seed3000`;
- M17 nominal success: 0.825;
- M17 perturbed success: 0.400;
- M17 paired success drop: 0.425;
- M17 hidden-reset nominal success: 0.900;
- M17 hidden-reset perturbed success: 0.400;
- M17 zero-current and zero-all nominal success: 0.825;
- M17 zero-current and zero-all perturbed success: 0.400.

Conclusion: M17 slightly improves normal perturbed success versus M16 (`0.400`
instead of `0.375`) and matches hidden-reset perturbed success, but it still
does not prove recurrent self-identification. Hidden reset remains better
nominally, and response masking is indistinguishable from normal inference.
Predicting next response is not enough if the policy head can ignore the
response-sensitive latent. The next experiment should make response dependence
behavior-critical in the control objective, not only predictable as an
auxiliary target.

## 20260520T230245Z m18-actuator-response-critical-training

- status: `completed`
- kind: `training`
- hypothesis: Train on wider actuator and vehicle-response randomization so same geometry requires response-dependent control
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m18_actuator_response_recurrent_driver.json --seed 911 --device cuda --run-dir runs/ppo_m18_actuator_response_recurrent_seed911`
- returncode: `0`
- run dir: `runs/research/m18-actuator-response-critical-training_20260520T221756Z`
- command log: `runs/research/m18-actuator-response-critical-training_20260520T221756Z/command.log`
- success artifact: `runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt`
- notes: Seed 911 warmup smoke reaches termination_rate 0.100 after 20480 steps

Training result:

- final eval return mean: 80.380;
- final eval steps mean: 68.600;
- final eval termination rate: 0.100;
- final eval lateral RMSE mean: 0.700;
- final eval beta absolute error mean: 0.136.

Actuator-response paired gate:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --checkpoint-policy m18=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --checkpoint-policy m18_reset=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt@reset_recurrent_state --checkpoint-policy m18_zero_current=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt@zero_current_response --checkpoint-policy m18_zero_all=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt@zero_all_response --device cpu --nominal-friction-mu-range 0.30,0.45 --perturbed-friction-mu-range 0.30,0.45 --nominal-randomization actuator_tau_scale_range=0.60,0.90 --nominal-randomization brake_scale_range=1.20,1.40 --nominal-randomization drive_scale_range=1.10,1.35 --perturbed-randomization actuator_tau_scale_range=2.40,3.20 --perturbed-randomization brake_scale_range=0.45,0.65 --perturbed-randomization drive_scale_range=0.55,0.75 --run-dir runs/m18_actuator_response_gate_seed3000`
- run dir: `runs/m18_actuator_response_gate_seed3000`;
- M18 nominal success: 0.450;
- M18 perturbed success: 0.375;
- M18 hidden-reset perturbed success: 0.225;
- M18 zero-current and zero-all perturbed success: 0.300.

M13 friction paired gate:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --checkpoint-policy m18=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --checkpoint-policy m18_reset=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt@reset_recurrent_state --checkpoint-policy m18_zero_current=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt@zero_current_response --checkpoint-policy m18_zero_all=runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m18_friction_paired_gate_seed3000`
- run dir: `runs/m18_friction_paired_gate_seed3000`;
- M18 nominal success: 0.775;
- M18 perturbed success: 0.375;
- M18 hidden-reset perturbed success: 0.150;
- M18 zero-current and zero-all perturbed success: 0.325.

Same-corpus obstacle benchmark:

- first attempted `configs/m7_obstacle_aes_weighted_holdout_eval.json`, but the
  strict loader rejected it because M18 is an online-GRU 15-dimensional contract
  while that eval config is a 60-dimensional history-stack contract;
- second attempted random sampling under
  `configs/m11_online_recurrent_history_critical_eval.json`, but some seeds
  failed the strict near-threshold sampler;
- final benchmark used the M13 seed corpus:
  `runs/m18_same_contract_obstacle_benchmark_seed3000`;
- `envelope_aes` success: 0.250;
- M18 success: 0.450;
- M18 hidden-reset success: 0.225;
- M18 zero-current success: 0.425;
- M18 high-sideslip fraction: 0.004.

Conclusion: M18 is the first recurrent run here where hidden-state reset and
response masking clearly hurt paired-gate performance. That is progress toward
closed-loop self-identification. It is not enough: actuator-response aggregate
success is low, and M13 perturbed success regresses below M17 (`0.375` vs
`0.400`). The next experiment should keep the response-dependence pressure but
recover aggregate success, likely with a softer actuator curriculum or mixed
fine-tuning from the M18 checkpoint.

## 20260520T233544Z m19-response-retention-finetune

- status: `completed`
- kind: `training`
- hypothesis: Fine-tune M18 on a softer response-retention curriculum to recover success without losing response dependence
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m19_response_retention_finetune_driver.json --seed 919 --device cuda --init-checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --run-dir runs/ppo_m19_response_retention_finetune_seed919`
- returncode: `0`
- run dir: `runs/research/m19-response-retention-finetune_20260520T230853Z`
- command log: `runs/research/m19-response-retention-finetune_20260520T230853Z/command.log`
- success artifact: `runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt`
- notes: M18 gives response-mask degradation but M13 perturbed success remains 0.375

Training result:

- init checkpoint load mode: `strict`;
- final eval return mean: 74.549;
- final eval steps mean: 65.200;
- final eval termination rate: 0.100;
- final eval lateral RMSE mean: 0.761;
- final eval beta absolute error mean: 0.156.

Actuator-response paired gate:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt --checkpoint-policy m19=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt --checkpoint-policy m19_reset=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt@reset_recurrent_state --checkpoint-policy m19_zero_current=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt@zero_current_response --checkpoint-policy m19_zero_all=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt@zero_all_response --device cpu --nominal-friction-mu-range 0.30,0.45 --perturbed-friction-mu-range 0.30,0.45 --nominal-randomization actuator_tau_scale_range=0.60,0.90 --nominal-randomization brake_scale_range=1.20,1.40 --nominal-randomization drive_scale_range=1.10,1.35 --perturbed-randomization actuator_tau_scale_range=2.40,3.20 --perturbed-randomization brake_scale_range=0.45,0.65 --perturbed-randomization drive_scale_range=0.55,0.75 --run-dir runs/m19_actuator_response_gate_seed3000`
- run dir: `runs/m19_actuator_response_gate_seed3000`;
- M19 nominal success: 0.300;
- M19 perturbed success: 0.400;
- M19 hidden-reset perturbed success: 0.375;
- M19 zero-current and zero-all perturbed success: 0.375.

M13 friction paired gate:

- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/m11_online_recurrent_history_critical_eval.json --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv --checkpoint runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt --checkpoint-policy m19=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt --checkpoint-policy m19_reset=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt@reset_recurrent_state --checkpoint-policy m19_zero_current=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt@zero_current_response --checkpoint-policy m19_zero_all=runs/ppo_m19_response_retention_finetune_seed919/checkpoint.pt@zero_all_response --device cpu --run-dir runs/m19_friction_paired_gate_seed3000`
- run dir: `runs/m19_friction_paired_gate_seed3000`;
- M19 nominal success: 0.800;
- M19 perturbed success: 0.375;
- M19 hidden-reset perturbed success: 0.375;
- M19 zero-current and zero-all perturbed success: 0.425.

Same-corpus obstacle benchmark:

- run dir: `runs/m19_same_contract_obstacle_benchmark_seed3000`;
- `envelope_aes` success: 0.250;
- M19 success: 0.450;
- M19 hidden-reset success: 0.400;
- M19 zero-current success: 0.425;
- M19 high-sideslip fraction: 0.047.

Conclusion: M19 is negative. It does not recover aggregate success enough, and
it erases the strongest M18 self-identification evidence. On the friction gate,
zero-response inference is better than normal inference (`0.425` vs `0.375`).
The next step should add periodic checkpoint saving and selection, because a
fine-tune can plausibly pass through useful response-retention states before
the final checkpoint regresses to geometry/open-loop shortcuts.

## 20260521T000131Z m20-periodic-response-retention

- status: `completed`
- kind: `training`
- hypothesis: Save periodic checkpoints during a shorter M18 fine-tune so gates can select response-retention points
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m20_periodic_response_retention_driver.json --seed 929 --device cuda --init-checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --run-dir runs/ppo_m20_periodic_response_retention_seed929`
- returncode: `0`
- run dir: `runs/research/m20-periodic-response-retention_20260520T234036Z`
- command log: `runs/research/m20-periodic-response-retention_20260520T234036Z/command.log`
- success artifact: `runs/ppo_m20_periodic_response_retention_seed929/checkpoint.pt`
- notes: M19 shows endpoint-only fine-tuning can erase response dependence

Training result:

- init checkpoint load mode: `strict`;
- periodic checkpoints: steps 102400, 200704, 303104, 401408, 503808, 602112,
  and 700000;
- final eval return mean: 78.390;
- final eval steps mean: 65.300;
- final eval termination rate: 0.100;
- final eval lateral RMSE mean: 0.464;
- final eval beta absolute error mean: 0.149.

Actuator-response checkpoint sweep:

- run dir: `runs/m20_actuator_response_checkpoint_sweep_seed3000`;
- best aggregate candidate: `m20_700`, with nominal success 0.475 and
  perturbed success 0.400;
- early candidate: `m20_102`, with nominal success 0.450 and perturbed success
  0.400.

Top-candidate actuator-response gate:

- run dir: `runs/m20_top_actuator_response_gate_seed3000`;
- M20_102 nominal/perturbed success: 0.450 / 0.400;
- M20_102 hidden-reset nominal/perturbed success: 0.150 / 0.325;
- M20_102 zero-current and zero-all perturbed success: 0.375;
- M20_700 nominal/perturbed success: 0.475 / 0.400;
- M20_700 hidden-reset nominal/perturbed success: 0.375 / 0.375;
- M20_700 zero-current and zero-all perturbed success: 0.400.

M13 friction paired gate:

- run dir: `runs/m20_top_friction_gate_seed3000`;
- M20_102 nominal/perturbed success: 0.825 / 0.400;
- M20_102 hidden-reset perturbed success: 0.175;
- M20_102 zero-current and zero-all perturbed success: 0.400;
- M20_700 nominal/perturbed success: 0.875 / 0.425;
- M20_700 hidden-reset perturbed success: 0.350;
- M20_700 zero-current and zero-all perturbed success: 0.425.

Same-corpus obstacle benchmark:

- run dir: `runs/m20_same_contract_obstacle_benchmark_seed3000`;
- `envelope_aes` success: 0.250;
- M20_102 success: 0.450;
- M20_700 success: 0.475;
- M20_700 hidden-reset success: 0.400;
- M20_700 zero-current and zero-all success: 0.475;
- M20_700 high-sideslip fraction: 0.000.

Conclusion: M20 is mixed. Periodic checkpointing finds a better same-contract
driver than M18/M19 on the near-threshold corpus: `m20_700` reaches success
0.475 versus `envelope_aes` 0.250 and improves M13 perturbed success to 0.425.
It still does not pass the self-identification gate, because zeroing the
deployable response channels leaves success unchanged. The next step should be
an architecture or loss change that makes response-conditioned hidden state
directly control-critical, not another endpoint fine-tune.

## 20260521T004810Z m21-response-critical-actor

- status: `completed`
- kind: `training`
- hypothesis: Train a response-critical online actor with separate response and context streams
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m21_response_critical_actor.json --seed 1031 --device cuda --run-dir runs/ppo_m21_response_critical_actor_seed1031`
- returncode: `0`
- run dir: `runs/research/m21-response-critical-actor_20260521T001442Z`
- command log: `runs/research/m21-response-critical-actor_20260521T001442Z/command.log`
- success artifact: `runs/ppo_m21_response_critical_actor_seed1031/checkpoint.pt`
- notes: Smoke passed; starts from scratch under the clean 15-value obstacle actor contract

Training result:

- final eval return mean: 77.974;
- final eval steps mean: 73.700;
- final eval termination rate: 0.100;
- final eval lateral RMSE mean: 0.867;
- final eval beta absolute error mean: 0.179;
- periodic checkpoints: steps 102400, 200704, 303104, 401408, 503808, 602112,
  700416, 802816, and 900000.

Actuator-response checkpoint sweep:

- run dir: `runs/m21_actuator_response_checkpoint_sweep_seed3000`;
- M20_700 nominal/perturbed success: 0.475 / 0.400;
- M21_503 nominal/perturbed success: 0.500 / 0.450;
- M21_602 nominal/perturbed success: 0.475 / 0.450;
- M21_900 nominal/perturbed success: 0.425 / 0.450.

Top-candidate actuator-response gate:

- run dir: `runs/m21_top_actuator_response_gate_seed3000`;
- M21_503 nominal/perturbed success: 0.500 / 0.450;
- M21_503 hidden-reset nominal/perturbed success: 0.350 / 0.450;
- M21_503 zero-current and zero-all perturbed success: 0.425;
- M21_602 nominal/perturbed success: 0.475 / 0.450;
- M21_602 hidden-reset nominal/perturbed success: 0.375 / 0.450;
- M21_602 zero-current and zero-all perturbed success: 0.450;
- M21_900 nominal/perturbed success: 0.425 / 0.450;
- M21_900 hidden-reset nominal/perturbed success: 0.275 / 0.450.

M13 friction paired gate:

- run dir: `runs/m21_top_friction_gate_seed3000`;
- M21_503 nominal/perturbed success: 0.900 / 0.450;
- M21_503 hidden-reset perturbed success: 0.400;
- M21_503 zero-current and zero-all perturbed success: 0.450;
- M21_602 nominal/perturbed success: 0.900 / 0.450;
- M21_602 hidden-reset perturbed success: 0.300;
- M21_602 zero-current and zero-all perturbed success: 0.450;
- M21_900 nominal/perturbed success: 0.875 / 0.400;
- M21_900 hidden-reset perturbed success: 0.250.

Same-corpus obstacle benchmark:

- run dir: `runs/m21_same_contract_obstacle_benchmark_seed3000`;
- `envelope_aes` success: 0.250;
- M20_700 success: 0.475;
- M21_503 success: 0.500;
- M21_503 hidden-reset success: 0.450;
- M21_503 zero-current success: 0.500;
- M21_602 success: 0.475;
- M21_602 hidden-reset success: 0.400;
- M21_602 zero-current success: 0.500;
- M21_900 success: 0.425.

Conclusion: M21 is mixed but useful. The response-critical architecture improves
aggregate performance: `m21_503` beats `m20_700` on same-corpus success
(`0.500` vs `0.475`), actuator-response perturbed success (`0.450` vs
`0.400`), and M13 friction perturbed success (`0.450` vs `0.425`). Hidden-state
reset now causes clear drops for some checkpoints, especially M21_602 and
M21_900 on the friction gate. It still does not prove deployable response
channel dependence, because zero-current and zero-all response ablations remain
near normal performance. The next task should build a harder response-dependence
gate or corpus before adding more actor complexity.
