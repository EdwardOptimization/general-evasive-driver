# AutoDrift Research Log

Last updated: 2026-05-21

## Current Best

- checkpoint: `runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt`
- status: not ideal-driver passed
- gate artifact: `runs/m37_102_hidden_swap_gate_seed4300/summary.csv`
- blocker: M37_102 preserves M30/M34 aggregate success and improves the M35
  response-change corpus, with reset and zero-response ablations now hurting
  perturbed accepted outcomes. It still does not pass recurrent
  self-identification because hidden-swap changes zero accepted success
  outcomes. M42 was evaluated and did not replace it.

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

## 20260521T005803Z m22-hard-response-dependence-gate

- status: `completed`
- kind: `gate`
- hypothesis: Mine or construct paired cases where identical geometry requires different response-conditioned corrective actions
- implementation: `src/autodrift/hard_response_corpus.py`
- primary corpus: `runs/m22_hard_response_corpus_m21_503_seed3000/scenario_corpus.csv`
- secondary corpus: `runs/m22_hard_response_corpus_m21_602_seed3000/scenario_corpus.csv`

Mining result:

- M21_503 selected hard seeds: 7;
- M21_503 selected success-changing rows: 10;
- M21_602 selected hard seeds: 6;
- M21_602 selected success-changing rows: 8.

Hard gate result:

- M21_503 hard actuator gate: normal 1.000 / 0.714, reset 0.143 / 0.714,
  zero-current 0.857 / 0.571;
- M21_503 hard friction gate: normal 1.000 / 0.714, reset 1.000 / 0.571,
  zero-current 1.000 / 0.714;
- M21_602 hard actuator gate: normal 0.833 / 0.667, reset 0.167 / 0.667,
  zero-current 0.833 / 0.667;
- M21_602 hard friction gate: normal 1.000 / 0.667, reset 1.000 / 0.000,
  zero-current 1.000 / 0.667.

Conclusion: M22 is a useful gate-construction success. It finds a small hard
actuator corpus where response masking visibly hurts `m21_503`, and it finds
hard friction cases where hidden-state reset hurts `m21_602`. This is not an
ideal-driver pass because the corpus is small and mined from the current gate
outputs. The next step should scale hard-case mining and add a clean training
or fine-tuning path that oversamples hard response-dependent cases.

## 20260521T012159Z m23-hard-corpus-training

- status: `completed`
- kind: `training`
- hypothesis: Fine-tune M21_503 on the mined hard response seed corpus
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m23_hard_response_corpus_driver.json --seed 1223 --device cuda --init-checkpoint runs/ppo_m21_response_critical_actor_seed1031/checkpoints/checkpoint_step_503808.pt --run-dir runs/ppo_m23_hard_response_corpus_seed1223`
- returncode: `0`
- run dir: `runs/research/m23-hard-corpus-training_20260521T010313Z`
- command log: `runs/research/m23-hard-corpus-training_20260521T010313Z/command.log`
- success artifact: `runs/ppo_m23_hard_response_corpus_seed1223/checkpoint.pt`
- notes: Uses training_seed_csv for hard-case reset oversampling without actor oracle inputs

Training result:

- final eval return mean: 43.382;
- final eval steps mean: 60.300;
- final eval termination rate: 0.200;
- final eval lateral RMSE mean: 0.595;
- final eval beta absolute error mean: 0.209;
- periodic checkpoints: steps 102400, 200704, 303104, 401408, and 500000.

Hard actuator gate:

- run dir: `runs/m23_hard_actuator_checkpoint_sweep_seed3000`;
- M21_503 nominal/perturbed success: 1.000 / 0.714;
- M23_102 nominal/perturbed success: 0.714 / 0.571;
- M23_200 nominal/perturbed success: 0.429 / 0.571;
- M23_303 nominal/perturbed success: 0.000 / 0.286;
- M23_401 nominal/perturbed success: 0.143 / 0.286;
- M23_500 nominal/perturbed success: 0.286 / 0.429.

Hard friction gate:

- run dir: `runs/m23_hard_friction_checkpoint_sweep_seed3000`;
- M21_503 nominal/perturbed success: 1.000 / 0.714;
- M23_102 nominal/perturbed success: 1.000 / 0.714;
- M23_200 nominal/perturbed success: 0.857 / 0.429;
- M23_303 nominal/perturbed success: 0.857 / 0.143;
- M23_401 nominal/perturbed success: 0.857 / 0.143;
- M23_500 nominal/perturbed success: 0.857 / 0.143.

Same-corpus obstacle benchmark:

- run dir: `runs/m23_same_contract_obstacle_benchmark_seed3000`;
- `envelope_aes` success/termination: 0.250 / 0.750;
- M21_503 success/termination: 0.500 / 0.500;
- M23_102 success/termination: 0.500 / 0.500;
- M23_500 success/termination: 0.300 / 0.700.

Conclusion: M23 is a negative result. Hard-only replay proves the strict reset
seed infrastructure works, but it overfits the small mined corpus and damages
the general obstacle policy. The next step is M24 mixed hard replay: sample hard
response seeds only part of the time, keep ordinary randomized resets active,
and select periodic checkpoints by both hard response gates and same-corpus
success.

## 20260521 m24-human-view-driver-contract

- status: `completed`
- kind: `infrastructure`
- hypothesis: A professional-driver RL actor should receive ego-frame
  human-view perception instead of path-tracking errors and precomputed obstacle
  answers.
- implementation: `src/autodrift/env.py`, `src/autodrift/dynamics.py`,
  `src/autodrift/train_ppo.py`, `src/autodrift/checkpoints.py`
- config: `configs/ppo_m24_human_view_gru_driver.json`

M24 supersedes the previous mixed-hard-replay plan. The next training run should
start from scratch under the human-view contract rather than fine-tuning M21 or
M23 checkpoints.

Implemented contract:

- actor observation is 72 values: ego response, previous physical controls,
  ego-frame road boundaries, and ego-frame obstacle slots;
- action is 3 values: steering, throttle, and brake;
- path lateral error, heading error, curvature, along-path speed, required
  clearance, and TTC are removed from the actor frame;
- `human_view_online_gru` requires the 72-value frame strictly.

Validation:

- targeted interface tests passed: `conda run -n autodrift pytest -q
  tests/test_env.py tests/test_dynamics.py tests/test_policies.py
  tests/test_evaluate.py tests/test_checkpoints.py tests/test_vector_env.py`
  returned 52 passed.

## 20260521T020037Z m25-human-view-gru-smoke

- status: `completed`
- kind: `training`
- hypothesis: Smoke-train the human-view online GRU driver from scratch under the 72-value frame
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m24_human_view_gru_driver.json --total-steps 20480 --seed 2024 --device cuda --run-dir runs/ppo_m25_human_view_gru_smoke_seed2024`
- returncode: `0`
- run dir: `runs/research/m25-human-view-gru-smoke_20260521T015946Z`
- command log: `runs/research/m25-human-view-gru-smoke_20260521T015946Z/command.log`
- success artifact: `runs/ppo_m25_human_view_gru_smoke_seed2024/checkpoint.pt`
- notes: First validation that the new human-view observation and 3-channel action contract train end to end

Smoke result:

- training device: `cuda`;
- final step: 20480;
- final rollout return mean: 43.762;
- final rollout termination rate: 0.648;
- eval return mean: 50.532;
- eval steps mean: 53.700;
- eval termination rate: 0.500;
- eval lateral RMSE mean: 0.455;
- eval beta absolute error mean: 0.146.

Conclusion: M25 passes as infrastructure only. The human-view observation and
3-channel action contract can train end to end with `human_view_online_gru`, but
20k steps is not a quality result. The next step is a full M26 training run from
scratch under the same contract, then same-corpus benchmarks and hidden-state
ablations.

## 20260521T023606Z m26-human-view-gru-full-train

- status: `completed`
- kind: `training`
- hypothesis: Full-train the human-view online GRU driver from scratch under the 72-value frame
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m24_human_view_gru_driver.json --seed 2024 --device cuda --run-dir runs/ppo_m26_human_view_gru_seed2024`
- returncode: `0`
- run dir: `runs/research/m26-human-view-gru-full-train_20260521T020206Z`
- command log: `runs/research/m26-human-view-gru-full-train_20260521T020206Z/command.log`
- success artifact: `runs/ppo_m26_human_view_gru_seed2024/checkpoint.pt`

Training result:

- final eval return mean: 66.240;
- final eval steps mean: 59.100;
- final eval termination rate: 0.200;
- final eval lateral RMSE mean: 0.777;
- final eval beta absolute error mean: 0.132;
- periodic checkpoints: steps 102400, 200704, 303104, 401408, 503808,
  602112, 700416, 802816, and 900000.

Checkpoint sweep:

- run dir: `runs/m26_human_view_checkpoint_sweep_seed3000`;
- `envelope_aes` success: 0.675;
- M26_102 / 200 / 303 success: 0.725 / 0.725 / 0.725;
- M26_401 / 503 / 602 success: 0.775 / 0.775 / 0.800;
- M26_700 / 802 / 900 / final success: 0.775 / 0.775 / 0.775 / 0.775.

Ablation:

- run dir: `runs/m26_602_human_view_ablation_seed3000`;
- M26_602 success: 0.800;
- M26_602 hidden-reset success: 0.800;
- M26_602 zero-current and zero-all response success: 0.775.

Old hard-seed check:

- run dir: `runs/m26_602_human_view_m22_hard_seed_benchmark_seed3000`;
- old M22 hard seeds are saturated under the human-view contract:
  `envelope_aes`, M26_602, reset, and response-masked variants all reach
  success 1.000.

Conclusion: M26 is a positive aggregate result but not a self-identification
pass. `m26_602` beats `envelope_aes` on the same human-view obstacle benchmark
(`0.800` vs `0.675` success), but hidden reset does not reduce success and
response masking only drops success by 0.025. The next milestone must build a
new human-view hard response-dependence gate; the old M22 hard corpus is no
longer valid for this actor contract.

Interpretation boundary: reset-vs-normal only tests whether the current gate
requires long-horizon GRU memory. It does not rule out one-step adaptation from
current ego response and previous physical command inputs. If dynamics are fixed,
or if the current observation is nearly Markov, reset and normal inference should
be similar. The next gate should use matched-current-observation cases and
hidden-swap ablations to separate "can adapt" from "requires recurrent
self-identification."

## 20260521T025100Z m27-human-view-hard-response-gate

- status: `completed`
- kind: `gate`
- hypothesis: Build a new response-dependence gate for the human-view contract because old M22 hard seeds saturate
- command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --checkpoint-policy m26_602=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --checkpoint-policy m26_602_reset=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@reset_recurrent_state --checkpoint-policy m26_602_zero_current=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@zero_current_response --checkpoint-policy m26_602_zero_all=runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt@zero_all_response --episodes 80 --seed 3600 --device cpu --run-dir runs/m27_human_view_paired_gate_seed3600`
- returncode: `0`
- run dir: `runs/research/m27-human-view-hard-response-gate_20260521T025048Z`
- command log: `runs/research/m27-human-view-hard-response-gate_20260521T025048Z/command.log`
- success artifact: `runs/m27_human_view_paired_gate_seed3600/pair_summary.csv`
- notes: First paired baseline; if weak then implement matched-current-observation hidden-swap gate

Result:

- normal M26_602 nominal/perturbed success: 0.938 / 0.663;
- M26_602 hidden-reset nominal/perturbed success: 0.925 / 0.663;
- M26_602 zero-current and zero-all nominal/perturbed success: 0.925 / 0.638.

Conclusion: M27 paired baseline is a weak/negative self-identification result.
The low-friction perturbation makes the task harder, but it does not show that
normal recurrent hidden state is necessary. Reset hidden matches normal
perturbed success, and response masking only lowers perturbed success by 0.025.
The next step should implement the matched-current-observation hidden-swap gate
described in `docs/m27-human-view-self-identification-gate.md`.

## 20260521 m28-hidden-swap-gate-plan

- status: `planned`
- kind: `gate`
- hypothesis: Matched-current-observation hidden-swap continuations can separate current-feedback adaptation from accumulated recurrent self-identification
- planned command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --episodes 80 --seed 4200 --device cpu --run-dir runs/m28_hidden_swap_gate_seed4200`
- planned artifact: `runs/m28_hidden_swap_gate_seed4200/summary.csv`
- notes: M27 is not a self-identification pass because reset matches normal perturbed success. M28 must snapshot matched visible decision points, replay normal/reset/zero-response/hidden-swap continuations, and report visible-observation distance so unmatched cases are treated as diagnostic only.

Interpretation boundary:

- reset/no-reset only tests long-horizon recurrent memory dependence;
- zero-response tests current closed-loop feedback dependence;
- hidden-swap on matched visible observations tests whether the accumulated
  hidden state helps the matching hidden dynamics;
- if training or testing has no meaningful hidden-dynamics variation, no gate
  can prove friction or vehicle-response adaptation.

## 20260521 m28-hidden-swap-gate-implementation-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: The hidden-swap gate can snapshot post-perturbation recurrent
  states and replay normal/reset/zero-response/hidden-swap continuations from a
  shared environment state
- command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --episodes 2 --seed 4200 --device cpu --run-dir runs/m28_hidden_swap_gate_smoke_seed4200`
- run dir: `runs/m28_hidden_swap_gate_smoke_seed4200`
- success artifact: `runs/m28_hidden_swap_gate_smoke_seed4200/summary.csv`
- notes: This is a CLI smoke, not a gate result. The harness requires
  post-friction hidden updates before snapshotting so the hidden state has
  consumed feedback under the changed dynamics.

Smoke result:

- accepted pairs: 2 / 2;
- mean visible-observation distance: 0.389;
- mean hidden-state distance: 1.205;
- nominal success: 1.000 for all variants;
- perturbed success: 0.500 for all variants;
- reset first-action distance: 0.346-0.376;
- zero-response first-action distance: 0.087-0.098;
- hidden-swap first-action distance: 0.034-0.046.

Conclusion: the M28 harness is runnable and records the right diagnostics. The
smoke result shows nonzero hidden-state distance and small hidden-swap action
change, while reset and zero-response alter the first action more strongly.
Full M28 is now queued to determine whether this pattern holds over 80 paired
seeds.

## 20260521T030628Z m28-hidden-swap-gate

- status: `completed`
- kind: `gate`
- hypothesis: Run the matched-current-observation hidden-swap gate for human-view self-identification
- command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --episodes 80 --seed 4200 --device cpu --run-dir runs/m28_hidden_swap_gate_seed4200`
- returncode: `0`
- run dir: `runs/research/m28-hidden-swap-gate_20260521T030619Z`
- command log: `runs/research/m28-hidden-swap-gate_20260521T030619Z/command.log`
- success artifact: `runs/m28_hidden_swap_gate_seed4200/summary.csv`
- notes: CLI smoke passed; hidden snapshots require post-friction hidden updates and report visible-observation plus hidden-state distance

Full result:

- paired snapshots: 80 / 80;
- accepted visible matches: 74 / 80;
- accepted mean visible-observation distance: 0.410;
- accepted mean hidden-state distance: 1.354;
- accepted nominal normal/reset/zero-response/hidden-swap success:
  0.973 / 0.973 / 0.973 / 0.973;
- accepted perturbed normal/reset/zero-response/hidden-swap success:
  0.622 / 0.622 / 0.622 / 0.622;
- accepted nominal first-action distance for reset/zero-response/hidden-swap:
  0.393 / 0.167 / 0.064;
- accepted perturbed first-action distance for reset/zero-response/hidden-swap:
  0.275 / 0.121 / 0.050;
- accepted cases with success changed by any ablation: 0.

Conclusion: M28 is a negative recurrent self-identification result for
`m26_602`. The new gate works and records nonzero post-perturbation hidden-state
distance, but hidden-swap does not change outcome and reset/zero-response do not
change success. The next experiment should create an M29 matched
response-critical corpus or curriculum where different hidden dynamics require
different corrective action at the same visible decision point.

## 20260521T031118Z m29-response-critical-matched-corpus

- status: `completed`
- kind: `gate`
- hypothesis: Mine a matched response-critical seed corpus from M28 hidden-swap artifacts
- command: `conda run -n autodrift python -m autodrift.matched_response_corpus --pairs-csv runs/m28_hidden_swap_gate_seed4200/pairs.csv --replays-csv runs/m28_hidden_swap_gate_seed4200/replays.csv --top-k 40 --min-hidden-state-distance 1.0 --max-context-observation-distance 0.15 --run-dir runs/m29_matched_response_corpus_seed4200`
- returncode: `0`
- run dir: `runs/research/m29-response-critical-matched-corpus_20260521T031117Z`
- command log: `runs/research/m29-response-critical-matched-corpus_20260521T031117Z/command.log`
- success artifact: `runs/m29_matched_response_corpus_seed4200/scenario_corpus.csv`
- notes: M28 has zero ablation success changes; select accepted condition-change and perturbed-failure seeds for harder follow-up training

Result:

- candidate seeds: 80;
- accepted visible matches: 74;
- selected seeds: 40;
- ablation success-change seeds: 0;
- ablation success-change edges: 0;
- nominal-vs-perturbed condition-change seeds: 26;
- perturbed-failure seeds: 28;
- accepted mean hidden-state distance: 1.354;
- selected score mean: 6.036.

Conclusion: M29 does not create proof of self-identification; it creates a
harder follow-up corpus. Because no ablation changes success, the selected
seeds are condition-change and perturbed-failure cases, not recurrent-memory
critical cases. The next training path should mix this hard corpus with ordinary
randomized resets instead of replaying it exclusively.

## 20260521 m30-mixed-hard-corpus-training-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: M29 hard seeds can be mixed with ordinary randomized resets
  during PPO training without leaking actor inputs or repeating M23 hard-only
  overfit mechanics
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m30_mixed_matched_response_driver.json --total-steps 20480 --seed 1330 --device cuda --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --run-dir runs/ppo_m30_mixed_matched_response_smoke_seed1330`
- run dir: `runs/ppo_m30_mixed_matched_response_smoke_seed1330`
- checkpoint: `runs/ppo_m30_mixed_matched_response_smoke_seed1330/checkpoint.pt`

Smoke result:

- strict init checkpoint load succeeded from `m26_602`;
- training device: `cuda`;
- final step: 20480;
- rollout return mean: 59.95;
- eval return mean: 69.080;
- eval steps mean: 61.900;
- eval termination rate: 0.100.

Conclusion: M30 mixed seed sampling and config are trainable. The full M30 run
is now the next training task.

## 20260521T032905Z m30-mixed-hard-corpus-training

- status: `completed`
- kind: `training`
- hypothesis: Train human-view GRU with M29 hard seeds mixed with ordinary randomized resets
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m30_mixed_matched_response_driver.json --seed 1330 --device cuda --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --run-dir runs/ppo_m30_mixed_matched_response_seed1330`
- returncode: `0`
- run dir: `runs/research/m30-mixed-hard-corpus-training_20260521T031733Z`
- command log: `runs/research/m30-mixed-hard-corpus-training_20260521T031733Z/command.log`
- success artifact: `runs/ppo_m30_mixed_matched_response_seed1330/checkpoint.pt`
- notes: M30 mixed sampler smoke passed; full run should preserve broad success while improving M29 hard corpus

Training result:

- final eval return mean: 63.764;
- final eval steps mean: 60.400;
- final eval termination rate: 0.200;
- periodic checkpoints: 53248, 102400, 151552, 200704, 253952, and 300000.

M29 selected-corpus sweep:

- M26_602 success: 0.775;
- M30_053 / 102 / 151 / 200 success: 0.875 / 0.875 / 0.875 / 0.875;
- M30_253 / final success: 0.850 / 0.800.

Broad same-seed sweep:

- envelope AES success: 0.675;
- M26_602 success: 0.800;
- M30_053 / 102 / 200 success: 0.825 / 0.825 / 0.825;
- M30_final success: 0.750.

M30_053 hidden-swap gate:

- accepted visible matches: 73 / 80;
- accepted nominal normal/reset/zero-response/hidden-swap success:
  0.973 / 0.973 / 0.973 / 0.973;
- accepted perturbed normal/reset/zero-response/hidden-swap success:
  0.644 / 0.658 / 0.658 / 0.644;
- hidden-swap changed zero accepted success outcomes.

Conclusion: M30 is a partial positive aggregate result. The early M30_053
checkpoint improves both M29 selected-corpus success and broad benchmark
success over M26_602. It is still not a self-identification pass: hidden-swap is
outcome-neutral, and reset/zero-response do not hurt. The next engineering
blocker is rollout throughput; current training effectively uses one CPU core,
so M31 should add an 8-core parallel rollout harness before longer training.

## 20260521 m31-parallel-rollout-harness

- status: `completed`
- kind: `infrastructure`
- hypothesis: PPO rollout collection can use multiple CPU worker processes
  without changing actor inputs or hard-seed mix semantics
- implementation: `ParallelAutoDriftVectorEnv`
- config fields: `vector_env_mode`, `vector_env_start_method`
- CLI overrides: `--num-envs`, `--vector-env-mode`, `--vector-env-start-method`

Smoke commands:

- parallel: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m30_mixed_matched_response_driver.json --total-steps 4096 --rollout-steps 128 --num-envs 8 --seed 1331 --device cuda --vector-env-mode parallel --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --run-dir runs/ppo_m31_parallel_rollout_smoke_seed1331`
- sync: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m30_mixed_matched_response_driver.json --total-steps 4096 --rollout-steps 128 --num-envs 8 --seed 1331 --device cuda --vector-env-mode sync --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --run-dir runs/ppo_m31_sync_rollout_smoke_seed1331`

Result:

- parallel real time: 9.37s;
- sync real time: 9.19s;
- both runs produced identical eval return 67.979 and termination 0.100.

Conclusion: M31 is a functional harness, not a speedup proof. The next
performance task should isolate rollout-only throughput on longer horizons and
tune worker count before using parallel mode by default.

## 20260521 m32-rollout-throughput-profile

- status: `completed`
- kind: `benchmark`
- hypothesis: process-based rollout is only useful when enough env work is
  batched per step to amortize IPC overhead
- command: `conda run -n autodrift python -m autodrift.rollout_throughput --env-config configs/ppo_m24_human_view_gru_driver.json --modes sync parallel --num-envs 1,2,4,8,16 --rollout-steps 2048 --repeats 2 --seed 5100 --run-dir runs/m32_rollout_throughput_seed5100`
- run dir: `runs/m32_rollout_throughput_seed5100`
- success artifact: `runs/m32_rollout_throughput_seed5100/throughput_summary.csv`

Result:

- sync 1 / 2 / 4 / 8 / 16 env steps/s:
  9835 / 10113 / 10240 / 10237 / 10103;
- parallel 1 / 2 / 4 / 8 / 16 env steps/s:
  3041 / 5195 / 8195 / 11311 / 11664.

Conclusion: parallel rollout is useful only at higher env counts. It is slower
for 1-4 envs, about 10% faster at 8 envs, and about 15% faster at 16 envs.
This supports selective use, not a default switch. The next profile should be a
short full PPO run at 16 envs to see whether rollout-only gains survive PPO
update and CUDA overhead.

## 20260521 m33-full-ppo-parallel-profile

- status: `completed`
- kind: `benchmark`
- hypothesis: rollout-only gains at 16 envs produce a small but real full PPO
  runtime improvement without changing learned model state
- parallel command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m30_mixed_matched_response_driver.json --total-steps 20480 --rollout-steps 256 --num-envs 16 --seed 1332 --device cuda --vector-env-mode parallel --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --run-dir runs/m33_parallel_ppo_profile_seed1332`
- sync command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m30_mixed_matched_response_driver.json --total-steps 20480 --rollout-steps 256 --num-envs 16 --seed 1332 --device cuda --vector-env-mode sync --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt --run-dir runs/m33_sync_ppo_profile_seed1332`

Result:

- parallel real/user/sys seconds: 50.99 / 47.31 / 11.43;
- sync real/user/sys seconds: 53.48 / 44.80 / 10.44;
- eval return and termination: identical at 61.042 and 0.100;
- `train_metrics.csv`: byte-identical;
- `eval_summary.json`: byte-identical;
- checkpoint model tensors: max absolute difference 0.0;
- checkpoint file hash differs only because `vector_env_mode` differs in saved
  config metadata.

Conclusion: parallel mode is deterministic for this profile and yields a small
4.7% full-training speedup at 16 envs. It is safe to use for long runs when the
small speed gain is worth extra worker-process complexity.

## 20260521 m34-response-aux-mixed-training-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: adding a deployable response-prediction auxiliary loss to the
  M30 mixed hard-corpus path can force the recurrent state to model ego
  response without giving the actor hidden vehicle or road parameters
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m34_response_aux_mixed_driver.json --total-steps 4096 --rollout-steps 128 --seed 1434 --device cuda --init-checkpoint runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt --run-dir runs/ppo_m34_response_aux_smoke_seed1434`
- run dir: `runs/ppo_m34_response_aux_smoke_seed1434`
- checkpoint: `runs/ppo_m34_response_aux_smoke_seed1434/checkpoint.pt`

Smoke result:

- init load mode: `partial_response_prediction_head`;
- training device: `cuda`;
- final step: 4096;
- rollout return mean: 76.98;
- eval return mean: 70.377;
- eval steps mean: 65.400;
- eval termination rate: 0.200.

Conclusion: M34 is runnable and can initialize from `m30_053` while adding only
the response-prediction auxiliary head. The full M34 run is now the next queued
training task. Post-run evaluation must compare M34 checkpoints against
envelope AES, M26_602, and M30_053 on the M29 selected corpus, broad same-seed
benchmark, and hidden-swap/reset/zero-response gates.

## 20260521T040736Z m34-response-aux-mixed-training

- status: `completed`
- kind: `training`
- hypothesis: Train a human-view driver with mixed hard seeds plus response-prediction auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m34_response_aux_mixed_driver.json --seed 1434 --device cuda --init-checkpoint runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt --run-dir runs/ppo_m34_response_aux_mixed_seed1434`
- returncode: `0`
- run dir: `runs/research/m34-response-aux-mixed-training_20260521T035144Z`
- command log: `runs/research/m34-response-aux-mixed-training_20260521T035144Z/command.log`
- success artifact: `runs/ppo_m34_response_aux_mixed_seed1434/checkpoint.pt`
- notes: Smoke passed with partial_response_prediction_head; post-run gate hidden-swap reset and zero-response behavior

Post-run result:

- final eval return mean: 70.148;
- final eval termination rate: 0.200;
- periodic checkpoints: 53248, 102400, 151552, 200704, 253952, and 300000.

M29 selected-corpus sweep:

- M30_053 success: 0.875;
- M34_053 / 102 / 151 success: 0.875 / 0.875 / 0.875;
- M34_200 / 253 / final success: 0.850 / 0.850 / 0.850.

Broad same-seed sweep:

- M30_053 success: 0.825;
- M34_053 / 102 / 151 / final success: 0.825 / 0.800 / 0.825 / 0.775.

Hidden-swap gates:

- M34_053, M34_102, and M34_151 all accepted 73 / 80 matched cases;
- hidden-swap outcome changes: 0 for all three checkpoints;
- perturbed reset outcome changes: 1, 2, and 3;
- perturbed zero-response outcome changes: 2, 3, and 3.

Conclusion: M34 is not an ideal-driver improvement. It preserves early M30
aggregate success but still fails recurrent self-identification. The useful
signal is weak response-ablation sensitivity, so the next step is larger M34
response-change corpus mining.

## 20260521 m35-m34-response-critical-corpus

- status: `completed`
- kind: `gate`
- hypothesis: enlarge the M34_151 hidden-swap sample to mine seeds where
  reset or zero-response ablation changes outcome, then reuse those seeds for
  follow-up training
- hidden-swap command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt --episodes 300 --seed 4300 --device cpu --run-dir runs/m35_m34_151_hidden_swap_gate_seed4300`
- corpus command: `conda run -n autodrift python -m autodrift.matched_response_corpus --pairs-csv runs/m35_m34_151_hidden_swap_gate_seed4300/pairs.csv --replays-csv runs/m35_m34_151_hidden_swap_gate_seed4300/replays.csv --top-k 80 --min-hidden-state-distance 0.8 --max-context-observation-distance 0.15 --run-dir runs/m35_m34_151_matched_response_corpus_seed4300`
- corpus artifact: `runs/m35_m34_151_matched_response_corpus_seed4300/scenario_corpus.csv`

Result:

- accepted matches: 281 / 300;
- hidden-swap outcome changes: 0;
- perturbed reset outcome changes: 4, with 1 unfavorable and 3 favorable;
- perturbed zero-response outcome changes: 5, with 2 unfavorable and 3
  favorable;
- selected corpus seeds: 80;
- success-changed seeds: 5;
- success-changed edges: 9;
- condition-changed seeds: 76;
- perturbed-failure seeds: 95.

Conclusion: M35 is still a negative self-identification result, but it yields a
better response-change training corpus than M29 for the M34 line. M36 should
fine-tune from M34_151 on this corpus and then re-run the same aggregate and
hidden-swap gates.

## 20260521T042602Z m36-response-change-corpus-training

- status: `completed`
- kind: `training`
- hypothesis: Fine-tune M34_151 on the M35 response-change corpus with response-prediction auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m36_response_change_corpus_driver.json --seed 1536 --device cuda --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt --run-dir runs/ppo_m36_response_change_corpus_seed1536`
- returncode: `0`
- run dir: `runs/research/m36-response-change-corpus-training_20260521T041525Z`
- command log: `runs/research/m36-response-change-corpus-training_20260521T041525Z/command.log`
- success artifact: `runs/ppo_m36_response_change_corpus_seed1536/checkpoint.pt`

Training result:

- final eval return mean: 65.342;
- final eval termination rate: 0.200;
- periodic checkpoints: 28672, 53248, 77824, 102400, 126976, 151552, 176128,
  and 200000.

M35 response-change corpus sweep:

- M30_053 success: 0.6125;
- M34_151 success: 0.6125;
- M36_028 / 053 / 077 / 102 / 126 / 151 / 176 / final success:
  0.6125 / 0.6000 / 0.5875 / 0.6000 / 0.6125 / 0.6000 / 0.6000 / 0.6000.

M29 selected-corpus sweep:

- M30_053 success: 0.875;
- M34_151 success: 0.875;
- M36_028 / 126 / final success: 0.875 / 0.850 / 0.850.

Broad same-seed sweep:

- M30_053 success: 0.825;
- M34_151 success: 0.825;
- M36_028 / 126 / final success: 0.825 / 0.800 / 0.800.

M36_028 hidden-swap:

- accepted visible matches: 73 / 80;
- hidden-swap outcome changes: 0;
- perturbed reset outcome changes: 3, with 1 unfavorable and 2 favorable;
- perturbed zero-response outcome changes: 3, with 1 unfavorable and 2
  favorable.

Conclusion: M36 is a negative result. Fine-tuning on response-change seeds does
not beat M30/M34 aggregate success and does not make hidden-swap
behavior-critical. The next hypothesis should change the auxiliary objective,
not keep replaying the same hard seeds: M37 should use multi-step future
response prediction so the GRU hidden state must encode a longer dynamics
belief.

## 20260521 m37-multistep-response-aux-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: multi-step future response prediction can create a stronger
  deployable recurrent dynamics-belief objective than one-step response
  prediction
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m37_multistep_response_aux_driver.json --total-steps 4096 --rollout-steps 128 --seed 1637 --device cuda --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt --run-dir runs/ppo_m37_multistep_response_aux_smoke_seed1637`
- run dir: `runs/ppo_m37_multistep_response_aux_smoke_seed1637`
- checkpoint: `runs/ppo_m37_multistep_response_aux_smoke_seed1637/checkpoint.pt`

Smoke result:

- init load mode: `partial_response_prediction_head`;
- training device: `cuda`;
- final step: 4096;
- rollout return mean: 34.42;
- eval return mean: 70.445;
- eval termination rate: 0.100.

Conclusion: M37 infrastructure is runnable. The full M37 training run is now
the next queued task. Validation must compare M37 checkpoints against M30_053,
M34_151, and M36_028 on M35, M29, broad, and hidden-swap gates.

## 20260521T042602Z m36-response-change-corpus-training

- status: `completed`
- kind: `training`
- hypothesis: Fine-tune M34_151 on the M35 response-change corpus with response-prediction auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m36_response_change_corpus_driver.json --seed 1536 --device cuda --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt --run-dir runs/ppo_m36_response_change_corpus_seed1536`
- returncode: `0`
- run dir: `runs/research/m36-response-change-corpus-training_20260521T041525Z`
- command log: `runs/research/m36-response-change-corpus-training_20260521T041525Z/command.log`
- success artifact: `runs/ppo_m36_response_change_corpus_seed1536/checkpoint.pt`
- notes: Use M35 response-change seeds to test whether weak response sensitivity can become behavior-critical recurrent control

## 20260521T045049Z m37-multistep-response-aux

- status: `completed`
- kind: `training`
- hypothesis: Train M34_151 with multi-step future-response auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m37_multistep_response_aux_driver.json --seed 1637 --device cuda --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt --run-dir runs/ppo_m37_multistep_response_aux_seed1637`
- returncode: `0`
- run dir: `runs/research/m37-multistep-response-aux_20260521T043446Z`
- command log: `runs/research/m37-multistep-response-aux_20260521T043446Z/command.log`
- success artifact: `runs/ppo_m37_multistep_response_aux_seed1637/checkpoint.pt`
- notes: Smoke passed with resized response_prediction_head; validate with M35 M29 broad and hidden-swap gates

Post-run result:

- final eval return mean: 70.028;
- final eval termination rate: 0.100;
- periodic checkpoints: 53248, 102400, 151552, 200704, 253952, and 300000.

M35 response-change corpus sweep:

- M30_053 / M34_151 / M36_028 success: 0.6125 / 0.6125 / 0.6125;
- M37_053 / 102 / 151 / 200 / 253 / final success:
  0.6375 / 0.6500 / 0.6125 / 0.6250 / 0.6250 / 0.6125.

M29 selected-corpus sweep:

- M30_053 success: 0.875;
- M34_151 success: 0.875;
- M37_053 / 102 / final success: 0.875 / 0.875 / 0.875.

Broad same-seed sweep:

- M30_053 success: 0.825;
- M34_151 success: 0.825;
- M37_053 / 102 / final success: 0.825 / 0.825 / 0.800.

M37_102 hidden-swap:

- 80-episode accepted matches: 73 / 80;
- 80-episode hidden-swap outcome changes: 0;
- 80-episode perturbed reset and zero-response changes: 2 each, all
  unfavorable;
- 300-episode accepted matches: 280 / 300;
- 300-episode hidden-swap outcome changes: 0;
- 300-episode perturbed reset and zero-response changes: 5 each, all
  unfavorable.

Conclusion: M37 is the strongest response-critical result so far, but not an
ideal-driver pass. Multi-step response prediction improves the M35
response-change corpus and makes reset/zero-response ablations reliably harmful
on perturbed accepted cases. Hidden-swap remains outcome-neutral, so M38 mines
a sharper M37_102 corpus and M39 should test whether this signal can be
reinforced.

## 20260521 m38-m37-response-critical-corpus

- status: `completed`
- kind: `gate`
- hypothesis: mine M37_102 hidden-swap replays after the first clean
  reset/zero-response unfavorable outcome changes
- hidden-swap command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --episodes 300 --seed 4300 --device cpu --run-dir runs/m37_102_hidden_swap_gate_seed4300`
- corpus command: `conda run -n autodrift python -m autodrift.matched_response_corpus --pairs-csv runs/m37_102_hidden_swap_gate_seed4300/pairs.csv --replays-csv runs/m37_102_hidden_swap_gate_seed4300/replays.csv --top-k 80 --min-hidden-state-distance 0.8 --max-context-observation-distance 0.15 --run-dir runs/m38_m37_102_matched_response_corpus_seed4300`
- corpus artifact: `runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv`

Result:

- accepted matches: 280 / 300;
- hidden-swap outcome changes: 0;
- perturbed reset outcome changes: 5, all unfavorable;
- perturbed zero-response outcome changes: 5, all unfavorable;
- selected corpus seeds: 80;
- success-changed seeds: 11;
- success-changed edges: 18;
- condition-changed seeds: 76;
- perturbed-failure seeds: 91.

Conclusion: M38 is a better response-critical corpus than M35, but still not a
hidden-swap pass. M39 should continue from M37_102 on this corpus with the
multi-step response objective.

## 20260521T050730Z m39-m37-response-corpus-training

- status: `completed`
- kind: `training`
- hypothesis: Continue M37_102 on the M38 response-critical corpus with multi-step auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m39_m37_response_corpus_driver.json --seed 1739 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m39_m37_response_corpus_seed1739`
- returncode: `0`
- run dir: `runs/research/m39-m37-response-corpus-training_20260521T045647Z`
- command log: `runs/research/m39-m37-response-corpus-training_20260521T045647Z/command.log`
- success artifact: `runs/ppo_m39_m37_response_corpus_seed1739/checkpoint.pt`

Result:

- final eval return mean: 69.884;
- final eval termination rate: 0.100;
- best M38 corpus success: M39_028/M39_053 at 0.6375 versus M37_102 at 0.6250;
- M35 corpus success: M39_028/M39_053 0.6500, same as M37_102;
- M29 success: M39_028/M39_053 0.875, same as M37_102;
- broad success: M39_028/M39_053 0.825, same as M37_102;
- hidden-swap outcome changes: 0 for M39_028 and M39_053;
- perturbed reset and zero-response outcome changes: 1 each for M39_028 and
  M39_053, all unfavorable.

Conclusion: M39 is not progress on the core driver gate. It slightly improves
the mined M38 corpus but weakens the M37_102 response-critical ablation signal.
The next step should instrument the response auxiliary objective directly:
M40 should log train-time aux loss and add an offline multi-step response
prediction evaluator before another training change.

## 20260521 m40-response-aux-diagnostics

- status: `completed`
- kind: `infrastructure`
- hypothesis: response-prediction error can explain why M37 creates a stronger
  ablation signal than M39 despite M39 continuing the same auxiliary objective
- command: `conda run -n autodrift python -m autodrift.response_prediction_eval --env-config configs/ppo_m24_human_view_gru_driver.json --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv --checkpoint-policy m34_151=runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m39_053=runs/ppo_m39_m37_response_corpus_seed1739/checkpoints/checkpoint_step_53248.pt --device cpu --run-dir runs/m40_response_prediction_eval_m38_seed4300`
- success artifact: `runs/m40_response_prediction_eval_m38_seed4300/prediction_summary.csv`

Result:

- M34_151 one-step MSE: 0.015019;
- M37_102 multi-step total MSE: 0.019116;
- M39_053 multi-step total MSE: 0.011935;
- M37_102 has stronger reset/zero-response ablation signal than M39_053 even
  though M39_053 has lower prediction error.

Conclusion: future-response prediction MSE is not enough as a driver objective
or checkpoint-selection metric. The next step should inspect behavior-sensitive
diagnostics and design an objective that rewards action-relevant hidden state,
not merely smooth future-response reconstruction.

## 20260521 m41-behavior-sensitive-response-diagnostics

- status: `completed`
- kind: `probe`
- hypothesis: per-seed response prediction error may correlate with
  behavior-critical reset/zero-response outcome-change seeds
- command: `conda run -n autodrift python -m autodrift.response_prediction_eval --env-config configs/ppo_m24_human_view_gru_driver.json --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m39_053=runs/ppo_m39_m37_response_corpus_seed1739/checkpoints/checkpoint_step_53248.pt --device cpu --run-dir runs/m41_response_prediction_per_seed_m38_seed4300`
- success artifact: `runs/m41_response_prediction_per_seed_m38_seed4300/prediction_episodes.csv`

Result:

- M37_102 MSE on success-changed / non-changed selected seeds:
  0.017595 / 0.018401;
- M39_053 MSE on success-changed / non-changed selected seeds:
  0.011282 / 0.011254;
- M39 reduces MSE versus M37 by about 0.006 to 0.007 in both seed groups.

Conclusion: response prediction error does not explain behavior-criticality.
The next objective should use intervention-aware or action-difference signals,
not pure prediction MSE. M37_102 remains the best current candidate because it
has stronger reset/zero-response ablation sensitivity despite worse response
prediction MSE.

## 20260521 m42-hidden-contrast-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: an auxiliary loss contrasting normal recurrent hidden against
  per-step reset hidden can make hidden state more action-relevant than pure
  response-prediction MSE
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m42_hidden_contrast_driver.json --total-steps 4096 --rollout-steps 128 --seed 1842 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m42_hidden_contrast_smoke_seed1842`
- run dir: `runs/ppo_m42_hidden_contrast_smoke_seed1842`
- checkpoint: `runs/ppo_m42_hidden_contrast_smoke_seed1842/checkpoint.pt`

Smoke result:

- init load mode: `strict`;
- final eval return mean: 78.432;
- final eval termination rate: 0.000;
- final train `response_prediction_loss_mean`: 0.024953;
- final train `hidden_contrast_loss_mean`: 0.640056.

Conclusion: M42 infrastructure is trainable and writes the intended metrics.
The full M42 run is queued. The pass/fail check is whether M42 improves
M37_102's reset/zero-response or hidden-swap behavior without aggregate
regression.

## 20260521T050730Z m39-m37-response-corpus-training

- status: `completed`
- kind: `training`
- hypothesis: Continue M37_102 on the M38 response-critical corpus with multi-step auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m39_m37_response_corpus_driver.json --seed 1739 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m39_m37_response_corpus_seed1739`
- returncode: `0`
- run dir: `runs/research/m39-m37-response-corpus-training_20260521T045647Z`
- command log: `runs/research/m39-m37-response-corpus-training_20260521T045647Z/command.log`
- success artifact: `runs/ppo_m39_m37_response_corpus_seed1739/checkpoint.pt`
- notes: Test whether M37 reset zero-response sensitivity can be strengthened without broad regression

## 20260521T054016Z m42-hidden-contrast-objective

- status: `completed`
- kind: `training`
- hypothesis: Train M37_102 with hidden-reset contrast auxiliary loss
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m42_hidden_contrast_driver.json --seed 1842 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m42_hidden_contrast_seed1842`
- returncode: `0`
- run dir: `runs/research/m42-hidden-contrast-objective_20260521T052240Z`
- command log: `runs/research/m42-hidden-contrast-objective_20260521T052240Z/command.log`
- success artifact: `runs/ppo_m42_hidden_contrast_seed1842/checkpoint.pt`
- notes: Smoke passed and metrics include hidden_contrast_loss_mean

Post-validation:

- M42 final eval return mean: 78.523250;
- M42 final eval termination rate: 0.000;
- M42 final response prediction loss mean: 0.016727;
- M42 final hidden contrast loss mean: 0.530701;
- M38 corpus best M42 checkpoint: M42_028 at 0.6250 success, equal to
  M37_102 and below M39_053 at 0.6375;
- M35 corpus: M42_028 0.6500, equal to M37_102;
- M29 selected corpus: M42_028 and M42_final 0.8750, equal to M37_102;
- broad same-seed sweep: M42_028 0.8250, equal to M37_102, while M42_final
  regresses to 0.8000;
- same 80-seed hidden-swap gate: M37_102 has 2 perturbed reset unfavorable
  changes and 2 perturbed zero-response unfavorable changes; M42_028 has
  1 reset and 2 zero-response unfavorable changes;
- hidden-swap outcome changes: 0 for M42_028.

Conclusion: M42 is a negative result. Hidden-contrast loss is trainable, but
it does not make the deterministic deployed policy more hidden-state critical.
M37_102 remains the current best checkpoint. M43 should measure full
action-trajectory divergence under interventions before choosing the next
training objective.

## 20260521 m43-action-trajectory-intervention-diagnostics

- status: `completed`
- kind: `probe`
- hypothesis: first-action distance is not enough to explain hidden-swap
  behavior; full-continuation action distance should show whether hidden-swap
  causes sustained closed-loop control changes
- artifacts:
  - `runs/m43_m37_102_action_trajectory_gate_seed4200/summary.csv`
  - `runs/m43_m42_028_action_trajectory_gate_seed4200/summary.csv`

Perturbed accepted matches:

- M37_102 hidden-swap first-action distance: 0.029597;
- M37_102 hidden-swap trajectory mean distance: 0.005528;
- M37_102 reset / zero-response trajectory mean distances:
  0.219339 / 0.199217;
- M42_028 hidden-swap first-action distance: 0.030208;
- M42_028 hidden-swap trajectory mean distance: 0.004872;
- M42_028 reset / zero-response trajectory mean distances:
  0.200152 / 0.180518.

Conclusion: the hidden-swap blocker is sustained closed-loop action collapse.
The policy can make a small first-step change under hidden-swap, but over the
continuation it returns to almost the same action trajectory. The next objective
should train sustained behavior differences on matched latent-response cases,
not just log-prob contrast.

## 20260521 m44-action-contrast-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: direct deterministic action-mean contrast against reset hidden may
  target the M43 sustained-action-collapse blocker better than M42 log-prob
  contrast
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m44_action_contrast_driver.json --total-steps 4096 --rollout-steps 128 --seed 1944 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m44_action_contrast_smoke_seed1944`
- run dir: `runs/ppo_m44_action_contrast_smoke_seed1944`
- checkpoint: `runs/ppo_m44_action_contrast_smoke_seed1944/checkpoint.pt`

Smoke result:

- init load mode: `strict`;
- final eval return mean: 61.995;
- final eval termination rate: 0.200;
- final train `response_prediction_loss_mean`: 0.023666;
- final train `action_contrast_loss_mean`: 0.680256.

Conclusion: M44 infrastructure is trainable and writes the intended metrics.
The short smoke is not a positive policy result. The full run must be judged by
M38/M35/M29/broad success and the M43 action-trajectory gate.

## 20260521T061710Z m44-action-contrast-objective

- status: `completed`
- kind: `training`
- hypothesis: Train M37_102 with deterministic action-mean contrast against reset hidden
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m44_action_contrast_driver.json --seed 1944 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m44_action_contrast_seed1944`
- returncode: `0`
- run dir: `runs/research/m44-action-contrast-objective_20260521T055743Z`
- command log: `runs/research/m44-action-contrast-objective_20260521T055743Z/command.log`
- success artifact: `runs/ppo_m44_action_contrast_seed1944/checkpoint.pt`
- notes: Smoke trainable but short eval weaker so full run needs strict post-run gates

Post-validation:

- final eval return mean: 61.818865;
- final eval termination rate: 0.200;
- final train `response_prediction_loss_mean`: 0.019623;
- final train `action_contrast_loss_mean`: 0.621962;
- M38 best M44 checkpoint: M44_077/M44_102 at 0.6000 success versus
  M37_102/M42_028 at 0.6250;
- M35 best M44 checkpoint: M44_077/M44_102 at 0.6250 success versus
  M37_102/M42_028 at 0.6500;
- M29 selected corpus: M44_077/M44_102/M44_final all preserve 0.8750 success;
- broad same-seed sweep: M44_077/M44_102 reach 0.8000 versus 0.8250 for
  M37_102/M42_028;
- action-trajectory gate: M44_077 raises perturbed hidden-swap trajectory mean
  distance only to 0.006230 and hidden-swap outcome changes remain 0;
- M44_077 raises reset / zero-response trajectory mean distances to
  0.305656 / 0.246570, but this does not transfer to hidden-swap.

Conclusion: M44 is a negative result. Direct action-mean contrast against reset
hidden increases sensitivity to reset and zero-response interventions but
hurts aggregate success and does not solve hidden-swap. The next objective
should compare matched nominal/perturbed hidden states directly rather than
contrasting against zero hidden.

## 20260521 m45-paired-hidden-snapshot-export

- status: `completed`
- kind: `infrastructure`
- hypothesis: paired nominal/perturbed hidden-state snapshots are needed before
  a direct paired-hidden training objective can be designed safely
- smoke run dir: `runs/m45_paired_hidden_snapshot_smoke_seed4200`
- M37_102 export run dir:
  `runs/m45_m37_102_paired_hidden_snapshots_seed4300`

Smoke result:

- seeds: 5;
- accepted matches: 4;
- exported observation shape: `(4, 72)`;
- exported hidden shape: `(4, 128)`.

M37_102 300-seed export:

- seeds: 300;
- paired seeds: 300;
- accepted matches: 280;
- exported pairs: 280;
- exported accepted-pair mean hidden distance: 1.269070;
- exported accepted-pair mean observation distance: 0.328693;
- exported accepted-pair mean context observation distance: 0.096270;
- exported observation shape: `(280, 72)`;
- exported hidden shape: `(280, 128)`.

Conclusion: M45 completes the paired-hidden data harness. The next step should
not blindly train on old hidden vectors as universal labels; saved hidden states
are checkpoint-specific. M46 should either fine-tune conservatively from the
same checkpoint or generate paired hidden states on policy.

## 20260521 m46-paired-hidden-action-contrast-smoke

- status: `completed`
- kind: `infrastructure`
- hypothesis: direct paired nominal/perturbed hidden action contrast targets
  hidden-swap better than zero-hidden reset contrast
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m46_paired_hidden_action_contrast_driver.json --total-steps 4096 --rollout-steps 128 --seed 2046 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m46_paired_hidden_action_contrast_smoke_seed2046`
- run dir: `runs/ppo_m46_paired_hidden_action_contrast_smoke_seed2046`
- checkpoint:
  `runs/ppo_m46_paired_hidden_action_contrast_smoke_seed2046/checkpoint.pt`

Smoke result:

- init load mode: `strict`;
- final eval return mean: 82.897;
- final eval termination rate: 0.000;
- final train `response_prediction_loss_mean`: 0.025627;
- final train `paired_hidden_action_contrast_loss_mean`: 0.718800.

Conclusion: M46 infrastructure is trainable and writes the intended metric.
The full run is queued. The pass/fail check remains the M38/M35/M29/broad
sweeps plus the M43 action-trajectory gate.

## 20260521T064448Z m46-paired-hidden-action-contrast

- status: `completed`
- kind: `training`
- hypothesis: Train M37_102 with same-checkpoint paired-hidden action contrast
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m46_paired_hidden_action_contrast_driver.json --seed 2046 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m46_paired_hidden_action_contrast_seed2046`
- returncode: `0`
- run dir: `runs/research/m46-paired-hidden-action-contrast_20260521T063355Z`
- command log: `runs/research/m46-paired-hidden-action-contrast_20260521T063355Z/command.log`
- success artifact: `runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoint.pt`
- notes: Smoke trainable and short eval clean but full run must pass M38 M35 M29 broad and action-trajectory gates

Post-validation:

- final eval return mean: 83.167580;
- final eval termination rate: 0.000;
- final response prediction loss mean: 0.022801;
- final paired-hidden action contrast loss mean: 0.709751;
- M38 response-critical corpus: M46_077 and M46_200 reach 0.6375 success
  versus 0.6250 for M37_102/M42_028;
- M35 response-change corpus: M46_077 and M46_200 preserve 0.6500 success,
  equal to M37_102/M42_028;
- M29 selected corpus: M46_077 and M46_200 preserve 0.8750 success, equal to
  M30_053/M37_102/M42_028;
- broad same-seed sweep: M46_077 and M46_200 regress to 0.8000 versus 0.8250
  for M37_102/M42_028;
- action-trajectory gate: M46_077 and M46_200 raise perturbed hidden-swap
  trajectory mean distance to 0.006379 and 0.007083, but hidden-swap outcome
  changes remain 0;
- perturbed reset / zero-response outcome changes are 1 / 2 unfavorable for
  M46_077 and 2 / 2 unfavorable for M46_200.

Conclusion: M46 is a negative result. The direct paired-hidden action contrast
creates a small hidden-swap action-distance signal and improves the mined M38
corpus slightly, but it fails the broad aggregate gate and does not create
hidden-swap outcome sensitivity. Current best remains M37_102. The next step
should audit seed-level M46 wins/losses and use on-policy or continuation-level
evidence instead of fixed old hidden vectors.
