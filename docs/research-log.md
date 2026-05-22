# AutoDrift Research Log

Last updated: 2026-05-22

## Current Best

- checkpoint:
  `runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt`
- label: `m62_a250`
- status: margin-retention promoted; not ideal-driver passed
- gate artifacts:
  `runs/m62_margin_retention_gate_strict/candidate_gate_summary.csv`,
  `runs/m62_a250_hidden_swap_gate_seed4300/summary.csv`
- blocker: `m62_a250` remains the best margin-retention checkpoint, but the
  project has still not proven professional-driver self-identification. M91/M92
  rejected the current single-track wheel profiles as primary actor inputs;
  M103-M105 found useful outcome/intervention objectives but M106/M107 rejected
  M105 formal admission due probe-seed fragility; M108/M109 showed the current
  hidden-envelope gate is unstable across baseline checkpoints and that current
  response often beats carried recurrent hidden; M110 then fit a
  current-response-anchored objective batch but failed external repeated
  split/multi-seed reliability. M111 now finds a matched-current-response
  ambiguity surface with `702` accepted pairs, but current hidden states do not
  systematically solve that ambiguity by feature distance. M112 then shows a
  positive action-level history-intervention signal on those pairs, including
  wrong-history actions moving closer to the matched-right action in about
  `0.733` of rows. M113 shows that this action signal does not yet change
  rollout outcomes: no success drops and only small margin gaps. The latest
  5.5pro MHTML input review is persisted: future wheel/tire work should use raw
  `Romega_i` plus independent local `v_parallel_i`, while `slip_ratio`,
  controller flags, tire labels, and oracle values stay out of actor inputs.
  M114 finds a near-boundary reset/zero-current outcome surface but no
  wrong-history rows. The next task is M115: construct wrong-history
  boundary-relocation cases.

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

## 20260521 m47-seed-delta-audit

- status: `completed`
- kind: `probe`
- hypothesis: M46's M38 gain and broad regression should be localized to
  concrete scenario seeds before another training objective is designed
- M38 command: `conda run -n autodrift python -m autodrift.seed_delta_audit --episodes-csv runs/m46_m38_corpus_checkpoint_sweep_seed4300/episodes.csv --baseline-policy m37_102 --candidate-policy m46_077 --candidate-policy m46_200 --run-dir runs/m47_m46_m38_seed_delta_audit_seed4300`
- broad command: `conda run -n autodrift python -m autodrift.seed_delta_audit --episodes-csv runs/m46_broad_checkpoint_sweep_seed3000/episodes.csv --baseline-policy m37_102 --candidate-policy m46_077 --candidate-policy m46_200 --run-dir runs/m47_m46_broad_seed_delta_audit_seed3000`
- M38 artifacts:
  `runs/m47_m46_m38_seed_delta_audit_seed4300/seed_deltas.csv`;
- broad artifacts:
  `runs/m47_m46_broad_seed_delta_audit_seed3000/seed_deltas.csv`.

Result:

- M38: M46_077 and M46_200 each improve exactly one seed and regress zero;
- the improved seed is 4327, an `unavoidable` case with current `mu = 1.137`,
  initial `mu = 0.658`, nominal mass, front cg, weak brakes, weak tire
  stiffness, and slow steering;
- on seed 4327, M37_102 collides with return 0.441 while M46_077 and M46_200
  complete with returns 54.718 and 54.033;
- broad: M46_077 and M46_200 each regress exactly one seed and improve zero;
- the regressed seed is 3037, an `unavoidable` case with current `mu = 0.340`,
  initial `mu = 0.324`, nominal mass, nominal cg, strong brakes, nominal tire
  stiffness, and slow steering;
- on seed 3037, M37_102 completes with return 91.586 while M46_077 and M46_200
  collide with returns 36.802 and 35.844.

Conclusion: M46's small gain is not a general recurrent self-identification
improvement. It trades a high-friction weak-actuator unavoidable win for a
low-friction unavoidable regression. M48 should mine continuation snippets
around these changed seeds and design the next objective from closed-loop
trajectory evidence rather than static offline hidden vectors.

## 20260521 m48-continuation-critical-snippets

- status: `completed`
- kind: `probe`
- hypothesis: M46's changed seeds are near-boundary closed-loop clearance
  cases, so the next gate should measure clearance margin instead of binary
  success only
- command: `conda run -n autodrift python -m autodrift.continuation_snippets --env-config configs/ppo_m24_human_view_gru_driver.json --seed 4327 --seed 3037 --checkpoint-policy m30_053=runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt --baseline-policy m37_102 --device cpu --run-dir runs/m48_continuation_snippets_changed_seeds`
- artifacts: `runs/m48_continuation_snippets_changed_seeds/steps.csv`,
  `runs/m48_continuation_snippets_changed_seeds/episodes.csv`,
  `runs/m48_continuation_snippets_changed_seeds/action_delta_summary.csv`,
  `runs/m48_continuation_snippets_changed_seeds/observations.npz`.

Result:

- seed 4327: M37_102 and M42_028 collide with clearance margins -0.003093 and
  -0.002736 m, while M46_077 and M46_200 complete with margins 0.000862 and
  0.002488 m;
- seed 3037: M37_102 and M42_028 complete with margins 0.009387 and
  0.040936 m, while M46_077 and M46_200 collide with margins -0.002355 and
  -0.007670 m;
- action trajectory distances versus M37_102 are modest for M46:
  about 0.066 to 0.074 mean action distance on the two changed seeds.

Conclusion: M46 is moving near-collision trajectories by millimeters, not
creating a robust closed-loop driver improvement. M49 should make clearance
margin a first-class benchmark/gate metric before the next training objective.

## 20260521 m49-clearance-margin-gate

- status: `completed`
- kind: `infrastructure`
- hypothesis: binary obstacle success is too coarse for near-boundary AES and
  drift-avoidance cases, so the driver gate should expose clearance margin
  directly
- targeted test command: `conda run -n autodrift pytest -q tests/test_env.py tests/test_evaluate.py tests/test_benchmark.py tests/test_seed_delta_audit.py tests/test_continuation_snippets.py`
- benchmark command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m24_human_view_gru_driver.json --seed-csv runs/m49_changed_seed_margin_benchmark/changed_seeds.csv --checkpoint-policy m30_053=runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt --device cpu --run-dir runs/m49_changed_seed_margin_benchmark`
- seed-delta command: `conda run -n autodrift python -m autodrift.seed_delta_audit --episodes-csv runs/m49_changed_seed_margin_benchmark/episodes.csv --baseline-policy m37_102 --candidate-policy m46_077 --candidate-policy m46_200 --run-dir runs/m49_changed_seed_margin_delta_audit`
- artifacts: `runs/m49_changed_seed_margin_benchmark/policy_summary.csv`,
  `runs/m49_changed_seed_margin_delta_audit/policy_delta_summary.csv`,
  `runs/m49_changed_seed_margin_delta_audit/seed_deltas.csv`.

Result:

- env/evaluate/benchmark now report `obstacle_collision_radius` and
  `min_clearance_margin`;
- seed-delta audit now reports `min_clearance_margin_delta`;
- targeted validation passed with 42 tests;
- on the two M48 changed seeds, M46_077 and M46_200 have the same binary
  success rate as M37_102, but lower mean clearance-margin deltas:
  - M46_077: `-0.003894 m`;
  - M46_200: `-0.005739 m`.

Conclusion: M49 confirms that M46 is not a robust driver improvement. It moves
near-boundary trajectories across the collision threshold while worsening mean
margin on the changed-seed pair. Current best remains M37_102. M50 should mine
a larger margin-critical corpus from M38, broad same-seed, and fresh randomized
obstacle sweeps before another training objective.

## 20260521 m50-margin-critical-corpus

- status: `completed`
- kind: `gate`
- hypothesis: a useful driver gate needs near-boundary margin-critical seeds,
  not only binary success or aggregate mean margin
- M38 benchmark: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m24_human_view_gru_driver.json --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv --policies envelope_aes --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt --device cpu --run-dir runs/m50_m38_margin_benchmark_seed4300`
- broad benchmark: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m24_human_view_gru_driver.json --episodes 40 --seed 3000 --policies envelope_aes --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt --device cpu --run-dir runs/m50_broad_margin_benchmark_seed3000`
- fresh benchmark: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m24_human_view_gru_driver.json --episodes 40 --seed 5200 --policies envelope_aes --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt --device cpu --run-dir runs/m50_fresh_margin_benchmark_seed5200`
- corpus command: `conda run -n autodrift python -m autodrift.margin_critical_corpus --episodes-csv runs/m50_m38_margin_benchmark_seed4300/episodes.csv --episodes-csv runs/m50_broad_margin_benchmark_seed3000/episodes.csv --episodes-csv runs/m50_fresh_margin_benchmark_seed5200/episodes.csv --baseline-policy m37_102 --candidate-policy m42_028 --candidate-policy m46_077 --candidate-policy m46_200 --near-margin 0.05 --min-abs-margin-delta 0.02 --top-k 100 --run-dir runs/m50_margin_critical_corpus_m38_broad_fresh`
- artifacts: `runs/m50_margin_critical_corpus_m38_broad_fresh/scenario_corpus.csv`,
  `runs/m50_margin_critical_corpus_m38_broad_fresh/policy_margin_summary.csv`,
  `runs/m50_margin_critical_corpus_m38_broad_fresh/seed_margin_deltas.csv`.

Result:

- corpus pairs: 480;
- selected rows: 100;
- critical near-boundary rows: 118;
- raw margin-regressed rows: 24;
- binary outcome-changed rows: 4;
- m42_028 has 38 critical rows and 3 near-margin regressions;
- m46_077 has 39 critical rows and 4 near-margin regressions;
- m46_200 has 41 critical rows and 10 near-margin regressions.

Conclusion: M46 improves mean margin across the combined sweep, but this hides
more near-boundary regressions and the known broad success regression. Current
best remains M37_102. M51 should convert the M50 corpus into a margin-retention
gate and training objective.

## 20260521 m51-margin-retention-gate

- status: `completed`
- kind: `infrastructure`
- hypothesis: checkpoint promotion should fail if a candidate drops broad
  success, creates binary regressions, or introduces near-boundary margin
  regressions versus M37_102
- strict gate command: `conda run -n autodrift python -m autodrift.margin_retention_gate --seed-delta-csv runs/m50_margin_critical_corpus_m38_broad_fresh/seed_margin_deltas.csv --min-success-delta 0.0 --max-binary-regressed-seeds 0 --max-near-margin-regressed-seeds 0 --min-margin-delta-mean 0.0 --run-dir runs/m51_margin_retention_gate_m50_strict`
- smoke train command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m51_margin_retention_driver.json --total-steps 4096 --rollout-steps 128 --seed 2151 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m51_margin_retention_smoke_seed2151`
- smoke gate artifact:
  `runs/m51_smoke_margin_retention_gate_strict/candidate_gate_summary.csv`.

Result:

- strict gate status for M42/M46 candidates: `needs_iteration`;
- m42_028 fails with 3 near-margin regressions;
- m46_077 fails with 1 binary regression and 4 near-margin regressions;
- m46_200 fails with 1 binary regression and 10 near-margin regressions;
- M51 smoke strict-loads M37_102 and trains to 4096 steps;
- M51 smoke also fails promotion: success delta `-0.0125`, 2 binary
  regressions, 6 near-margin regressions, margin delta mean `-0.011257`.

Conclusion: M51 adds the missing promotion gate and proves the margin-retention
training config can run, but no new checkpoint is promotable. Current best
remains M37_102. M52 should run the full M51 continuation and sweep checkpoints
through the strict gate.

## 20260521T074043Z m52-full-margin-retention-continuation

- status: `completed`
- kind: `training`
- hypothesis: Run full M51 continuation from M37_102 and sweep checkpoints through strict margin-retention gates
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m51_margin_retention_driver.json --seed 2151 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m51_margin_retention_seed2151`
- returncode: `0`
- run dir: `runs/research/m52-full-margin-retention-continuation_20260521T072957Z`
- command log: `runs/research/m52-full-margin-retention-continuation_20260521T072957Z/command.log`
- success artifact: `runs/ppo_m51_margin_retention_seed2151/checkpoint.pt`
- notes: Promote only if broad success and near-boundary margin retention both pass versus M37_102

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m52_m38_margin_benchmark_seed4300`,
  `runs/m52_broad_margin_benchmark_seed3000`,
  `runs/m52_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m52_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m52_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- best snapshot by damage is M51_028, but it still has success delta
  `-0.01875`, 3 binary regressions, 10 near-margin regressions, and margin
  delta mean `-0.015016`;
- later snapshots are worse, with success deltas from `-0.02500` to
  `-0.03125` and near-margin regressions from 19 to 28.

Conclusion: M52 is a negative result. Directly oversampling the row-level M50
top-100 corpus with 70% hard-seed probability overweights only 41 unique seeds
and damages the broader M37 behavior. Current best remains M37_102. M53 should
deduplicate the corpus and reduce hard-seed mix before another long run.

## 20260521 m53-dedup-low-mix-margin-retention

- status: `completed`
- kind: `infrastructure`
- hypothesis: M52 failed partly because it replayed 100 row-level corpus entries
  that collapse to 41 unique seeds; a deduplicated lower-mix sequence should
  damage broad behavior less
- seed corpus command: `conda run -n autodrift python -m autodrift.training_seed_corpus --corpus-csv runs/m50_margin_critical_corpus_m38_broad_fresh/scenario_corpus.csv --run-dir runs/m53_dedup_margin_training_seeds`
- smoke train command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m53_dedup_low_mix_margin_retention_driver.json --total-steps 4096 --rollout-steps 128 --seed 2253 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m53_dedup_low_mix_smoke_seed2253`
- smoke gate artifact:
  `runs/m53_smoke_margin_retention_gate_strict/candidate_gate_summary.csv`.

Result:

- deduplicated seed sequence: 41 unique seeds from 100 M50 rows;
- source distribution: 26 M38, 9 broad, 6 fresh;
- M53 config uses `training_seed_mix_probability = 0.35`;
- smoke strict-loads M37_102 and trains to 4096 steps;
- smoke gate status: `needs_iteration`;
- smoke success delta: `-0.00625`;
- smoke binary regressions: 1;
- smoke near-margin regressions: 2;
- smoke mean margin delta: `0.001714`.

Conclusion: M53 smoke is not promotable, but it is a better direction than M51:
M38 success is retained and combined mean margin is positive. The remaining
problem is one broad regression. M54 should run the full deduplicated low-mix
continuation and select checkpoints by the strict gate.

## 20260521T080357Z m54-full-dedup-low-mix-continuation

- status: `completed`
- kind: `training`
- hypothesis: Run full M53 deduplicated low-mix continuation from M37_102 and sweep strict margin-retention gates
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m53_dedup_low_mix_margin_retention_driver.json --seed 2253 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m53_dedup_low_mix_margin_retention_seed2253`
- returncode: `0`
- run dir: `runs/research/m54-full-dedup-low-mix-continuation_20260521T075319Z`
- command log: `runs/research/m54-full-dedup-low-mix-continuation_20260521T075319Z/command.log`
- success artifact: `runs/ppo_m53_dedup_low_mix_margin_retention_seed2253/checkpoint.pt`
- notes: Full run is justified by M53 smoke but promotion still requires zero broad and near-margin regressions

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m54_m38_margin_benchmark_seed4300`,
  `runs/m54_broad_margin_benchmark_seed3000`,
  `runs/m54_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m54_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m54_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- least-damaging snapshots by success delta are M54_028, M54_126, and M54_200,
  each with success delta `-0.00625`, 2 binary regressions, and positive mean
  margin delta;
- M38 and fresh success can be retained, but broad seed3000 regresses from
  `0.825` to at best `0.800`;
- recurrent binary-regression seeds include M38 seed `4457` and broad seed
  `3037`, both near-boundary unavoidable cases where M37 passes by only
  millimeters and M54 crosses into small penetration.

Conclusion: M54 is not promotable, but it improves the M52 failure mode.
Deduplicated low-mix continuation can improve mean margin without destroying
fresh success, yet it still shifts a few near-boundary positive cases. Current
best remains M37_102. M55 should try a lower-learning-rate, lower-mix,
dense-checkpoint continuation to find an early update window with zero binary
and near-margin regressions.

## 20260521T081150Z m55-conservative-margin-retention

- status: `completed`
- kind: `training`
- hypothesis: Run a lower-learning-rate lower-mix dense-checkpoint continuation to find a zero-regression early update window
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m55_conservative_dedup_margin_retention_driver.json --seed 2355 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m55_conservative_margin_retention_seed2355`
- returncode: `0`
- run dir: `runs/research/m55-conservative-margin-retention_20260521T081002Z`
- command log: `runs/research/m55-conservative-margin-retention_20260521T081002Z/command.log`
- success artifact: `runs/ppo_m55_conservative_margin_retention_seed2355/checkpoint.pt`
- notes: Promote only if strict margin-retention gate has zero binary and near-margin regressions

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m55_m38_margin_benchmark_seed4300`,
  `runs/m55_broad_margin_benchmark_seed3000`,
  `runs/m55_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m55_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m55_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- `m55_004` is the least-damaging checkpoint: success delta `0.00000`, zero
  binary regressions, one near-margin regression, and margin delta mean
  `-0.001267`;
- broad and fresh success stay at `0.825` for all checkpoints;
- M38 success stays at `0.625` for early checkpoints but mean margin is lower
  than M37;
- binary outcome changes are reduced to 3 candidate-pairs total, versus 27 for
  M54, but the margin-retention gate correctly rejects every checkpoint.

Conclusion: M55 fixes the broad binary-regression failure mode but does not
learn positive clearance-margin retention. The next change should be objective
level: add a config-gated terminal clearance-margin reward for training while
leaving actor observations and the strict promotion gate unchanged.

## 20260521T082143Z m56-terminal-clearance-margin-reward

- status: `completed`
- kind: `training`
- hypothesis: Run conservative margin-retention continuation with terminal clearance-margin reward shaping
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m56_clearance_margin_reward_driver.json --seed 2456 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m56_clearance_margin_reward_seed2456`
- returncode: `0`
- run dir: `runs/research/m56-terminal-clearance-margin-reward_20260521T081954Z`
- command log: `runs/research/m56-terminal-clearance-margin-reward_20260521T081954Z/command.log`
- success artifact: `runs/ppo_m56_clearance_margin_reward_seed2456/checkpoint.pt`
- notes: Promotion still requires strict zero binary and near-margin regressions

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m56_m38_margin_benchmark_seed4300`,
  `runs/m56_broad_margin_benchmark_seed3000`,
  `runs/m56_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m56_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m56_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- `m56_004` has zero binary regressions but one near-margin regression and
  margin delta mean `-0.000445`;
- `m56_028` has zero binary regressions and zero near-margin regressions, but
  margin delta mean remains negative at `-0.001527`;
- broad and fresh success are mostly retained, but later checkpoints reintroduce
  broad seed `3037` regressions;
- compared with M55, terminal margin reward improves the best near-margin
  regression count from 1 to 0, but does not yet pass mean margin retention.

Conclusion: M56 is not promotable, but it validates the direction. Sparse
terminal clearance-margin reward moves one checkpoint to zero binary and zero
near-margin regressions; its remaining blocker is a small negative combined
mean margin. M57 should increase the terminal margin reward scale to `4.0`
without weakening the strict gate.

## 20260521T082753Z m57-clearance-margin-reward-scale4

- status: `completed`
- kind: `training`
- hypothesis: Run M56 schedule with stronger terminal clearance-margin reward scale 4
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m57_clearance_margin_reward_scale4_driver.json --seed 2557 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m57_clearance_margin_reward_scale4_seed2557`
- returncode: `0`
- run dir: `runs/research/m57-clearance-margin-reward-scale4_20260521T082604Z`
- command log: `runs/research/m57-clearance-margin-reward-scale4_20260521T082604Z/command.log`
- success artifact: `runs/ppo_m57_clearance_margin_reward_scale4_seed2557/checkpoint.pt`
- notes: Promote only if strict gate improves M56_028 to non-negative mean margin without binary or near-margin regressions

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m57_m38_margin_benchmark_seed4300`,
  `runs/m57_broad_margin_benchmark_seed3000`,
  `runs/m57_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m57_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m57_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- best zero-binary checkpoint is `m57_004`: success delta `0.00000`, one
  near-margin regression, and margin delta mean `-0.000729`;
- every M57 checkpoint has negative mean margin delta;
- stronger sparse terminal reward does not improve the M56 near-pass
  `m56_028`, which had zero binary and zero near-margin regressions.

Conclusion: M57 is not promotable. More terminal margin reward scale does not
solve the M38 mean-margin loss and can reintroduce near-margin regressions.
M58 should use a dense near-obstacle clearance reward rather than more sparse
terminal scaling.

## 20260521T083720Z m58-dense-near-obstacle-clearance-reward

- status: `completed`
- kind: `training`
- hypothesis: Run conservative continuation with dense near-obstacle clearance reward shaping
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m58_dense_clearance_margin_reward_driver.json --seed 2658 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m58_dense_clearance_margin_reward_seed2658`
- returncode: `0`
- run dir: `runs/research/m58-dense-near-obstacle-clearance-reward_20260521T083531Z`
- command log: `runs/research/m58-dense-near-obstacle-clearance-reward_20260521T083531Z/command.log`
- success artifact: `runs/ppo_m58_dense_clearance_margin_reward_seed2658/checkpoint.pt`
- notes: Promotion still requires strict zero binary and near-margin regressions plus non-negative mean margin

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m58_m38_margin_benchmark_seed4300`,
  `runs/m58_broad_margin_benchmark_seed3000`,
  `runs/m58_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m58_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m58_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- `m58_004` has zero binary and zero near-margin regressions, but margin delta
  mean is `-0.002749`;
- later checkpoints reintroduce binary regressions, up to 3 regressed seeds;
- dense near-obstacle reward produces worse mean-margin retention than M56 and
  M57.

Conclusion: M58 is not promotable and is a negative objective result. Dense
near-obstacle reward in this simple form does not solve margin retention. M59
should test checkpoint/weight interpolation as a trust-region diagnostic before
more reward shaping.

## 20260521T084940Z m59-trust-region-checkpoint-interpolation

- status: `completed`
- kind: `probe`
- hypothesis: Interpolate M37_102 toward the closest non-promoted checkpoint
  M56_028 to test whether a smaller trust-region move can pass strict margin
  retention.
- command: `conda run -n autodrift python -m autodrift.checkpoint_interpolation --base-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --target-checkpoint runs/ppo_m56_clearance_margin_reward_seed2456/checkpoints/checkpoint_step_28672.pt --alphas 0.125 0.25 0.375 0.5 0.625 0.75 0.875 --base-label m37_102 --target-label m56_028 --label-prefix m59 --run-dir runs/m59_m37_m56_028_interpolated_checkpoints`
- returncode: `0`
- run dir: `runs/m59_m37_m56_028_interpolated_checkpoints`
- success artifact:
  `runs/m59_m37_m56_028_interpolated_checkpoints/manifest.json`
- notes: Generated checkpoints load through the canonical 72-value human-view
  actor contract.

Post-validation:

- focused tests:
  `conda run -n autodrift pytest -q tests/test_checkpoint_interpolation.py tests/test_checkpoints.py`
  -> `31 passed`;
- M38/broad/fresh checkpoint sweeps:
  `runs/m59_m38_margin_benchmark_seed4300`,
  `runs/m59_broad_margin_benchmark_seed3000`,
  `runs/m59_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m59_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m59_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- every alpha retains aggregate success with zero binary regressions and zero
  near-margin regressions;
- best alpha is `m59_a125`, but mean margin delta is still negative at
  `-0.000193`;
- margin loss is nearly monotonic with alpha, reaching `-0.001335` at
  `m59_a875`.

Conclusion: M59 is not promotable. The M37-to-M56_028 parameter direction is a
behaviorally conservative direction but not a positive-margin direction. M60
should stop increasing margin reward scale and instead build a constrained,
baseline-anchored update that allows changes only where mined snippets show a
credible margin-improvement opportunity.

## 20260521T085620Z m60-constrained-baseline-anchor-setup

- status: `completed`
- kind: `infrastructure`
- hypothesis: Add a frozen M37 action anchor so M60 can pursue margin reward
  updates while penalizing deterministic action drift on negative-advantage
  states.
- smoke command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m60_constrained_baseline_anchor_driver.json --total-steps 4096 --rollout-steps 64 --num-envs 4 --vector-env-mode sync --seed 2760 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m60_anchor_smoke_seed2760`
- returncode: `0`
- run dir: `runs/ppo_m60_anchor_smoke_seed2760`
- success artifact: `runs/ppo_m60_anchor_smoke_seed2760/train_metrics.csv`

Post-validation:

- focused tests:
  `conda run -n autodrift pytest -q tests/test_checkpoints.py`
  -> `28 passed`;
- smoke metrics include `baseline_action_anchor_loss_mean`;
- smoke metrics still include `response_prediction_loss_mean`;
- smoke eval return mean is `65.0278`;
- smoke eval termination rate is `0.100`;
- actor observation contract is unchanged; the reference action is an auxiliary
  training target only.

Conclusion: M60 infrastructure is ready for a full continuation. The next run
should train `configs/ppo_m60_constrained_baseline_anchor_driver.json` from
M37_102 and then sweep dense checkpoints through the unchanged strict
margin-retention gate.

## 20260521T090446Z m60-constrained-baseline-anchor-full

- status: `completed`
- kind: `training`
- hypothesis: Run the M60 baseline-action-anchor continuation from M37_102 and
  test whether negative-advantage action retention allows margin improvements
  without broad regressions.
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m60_constrained_baseline_anchor_driver.json --seed 2760 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m60_constrained_baseline_anchor_seed2760`
- returncode: `0`
- run dir: `runs/ppo_m60_constrained_baseline_anchor_seed2760`
- success artifact:
  `runs/ppo_m60_constrained_baseline_anchor_seed2760/checkpoint.pt`

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m60_m38_margin_benchmark_seed4300`,
  `runs/m60_broad_margin_benchmark_seed3000`,
  `runs/m60_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m60_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m60_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- `m60_016` keeps success and reaches positive mean margin delta `0.000062`,
  but has 4 near-margin regressions;
- `m60_020` reaches the best mean margin delta `0.000361`, but has 1 binary
  regression and 4 near-margin regressions;
- `m60_004` is closest to retention but still has one near-margin regression
  and mean margin delta `-0.000118`;
- primary blocker seeds: M38 `4413`, `4378`, `4457`, and broad `3019`.

Conclusion: M60 is not promotable, but it moves the failure mode. The project
now has evidence that baseline anchoring can produce positive mean-margin
deltas, while the strict gate exposes concentrated near-boundary regressions.
M61 should explicitly replay those regression seeds and strengthen the
near-boundary retention floor instead of only increasing reward scale.

## 20260521T090831Z m61-regression-seed-retention-replay-setup

- status: `completed`
- kind: `infrastructure`
- hypothesis: Oversample the M60 regression seeds and strengthen the
  baseline-action anchor before running another full margin continuation.
- replay corpus: `runs/m61_regression_seed_replay/seed_sequence.csv`
- smoke command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m61_regression_seed_retention_driver.json --total-steps 4096 --rollout-steps 64 --num-envs 4 --vector-env-mode sync --seed 2861 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m61_regression_seed_retention_smoke_seed2861`
- returncode: `0`
- run dir: `runs/ppo_m61_regression_seed_retention_smoke_seed2861`
- success artifact:
  `runs/ppo_m61_regression_seed_retention_smoke_seed2861/train_metrics.csv`

Post-validation:

- replay corpus has 89 rows: 41 M53 base rows plus 12 extra repeats for each
  of seeds `4413`, `4378`, `4457`, and `3019`;
- config uses `baseline_action_anchor_coef = 1.0`;
- config uses `training_seed_mix_probability = 0.30`;
- smoke metrics include `baseline_action_anchor_loss_mean`;
- smoke eval return mean is `74.0360`;
- smoke eval termination rate is `0.100`.

Conclusion: M61 infrastructure is ready for a full continuation. The strict
gate remains unchanged; replay and stronger anchoring must eliminate the M60
near-boundary regressions rather than hide them.

## 20260521T091441Z m61-regression-seed-retention-replay-full

- status: `completed`
- kind: `training`
- hypothesis: Full M61 continuation should reduce M60's concentrated
  near-boundary regressions by replaying those seeds and increasing
  baseline-action anchor strength.
- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m61_regression_seed_retention_driver.json --seed 2861 --device cuda --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --run-dir runs/ppo_m61_regression_seed_retention_seed2861`
- returncode: `0`
- run dir: `runs/ppo_m61_regression_seed_retention_seed2861`
- success artifact:
  `runs/ppo_m61_regression_seed_retention_seed2861/checkpoint.pt`

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m61_m38_margin_benchmark_seed4300`,
  `runs/m61_broad_margin_benchmark_seed3000`,
  `runs/m61_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m61_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m61_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `needs_iteration`;
- passed candidates: none;
- `m61_004` and `m61_008` have zero binary and zero near-margin regressions
  but still negative mean margin delta;
- `m61_032` has zero binary regressions and positive mean margin delta
  `0.000294`, but has 3 near-margin regressions;
- remaining blocker seeds for `m61_032`: M38 `4378`, M38 `4413`, and broad
  `3019`.

Conclusion: M61 is not promotable, but it is the strongest retention result so
far because it produces a positive-margin, zero-binary source checkpoint.
M62 should interpolate M37_102 toward `m61_032` to see whether a smaller
trust-region step can keep positive mean margin while removing the three
near-margin regressions.

## 20260521T091951Z m62-positive-margin-checkpoint-interpolation

- status: `completed`
- kind: `probe`
- hypothesis: Interpolate M37_102 toward M61_032 to retain the positive
  mean-margin direction while removing M61's three near-margin regressions.
- command: `conda run -n autodrift python -m autodrift.checkpoint_interpolation --base-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --target-checkpoint runs/ppo_m61_regression_seed_retention_seed2861/checkpoints/checkpoint_step_32768.pt --alphas 0.125 0.25 0.375 0.5 0.625 0.75 0.875 --base-label m37_102 --target-label m61_032 --label-prefix m62 --run-dir runs/m62_m37_m61_032_interpolated_checkpoints`
- returncode: `0`
- run dir: `runs/m62_m37_m61_032_interpolated_checkpoints`
- success artifact:
  `runs/m62_margin_retention_gate_strict/candidate_gate_summary.csv`

Post-validation:

- M38/broad/fresh checkpoint sweeps:
  `runs/m62_m38_margin_benchmark_seed4300`,
  `runs/m62_broad_margin_benchmark_seed3000`,
  `runs/m62_fresh_margin_benchmark_seed5200`;
- margin corpus:
  `runs/m62_margin_critical_corpus/seed_margin_deltas.csv`;
- strict gate:
  `runs/m62_margin_retention_gate_strict/candidate_gate_summary.csv`;
- strict gate status: `passed`;
- passed candidates: `m62_a125`, `m62_a250`;
- `m62_a250` has success delta `0.000000`, zero binary regressions, zero
  near-margin regressions, and mean margin delta `0.000552`;
- source-level mean margin deltas for `m62_a250`: M38 `0.000495`, broad
  `0.000425`, fresh `0.000791`;
- hidden-swap audit:
  `runs/m62_a250_hidden_swap_gate_seed4300/summary.csv`;
- hidden-swap accepted-match success rates match M37_102; hidden-swap remains
  outcome-neutral.

Conclusion: M62 is the first margin-retention pass. `m62_a250` replaces
M37_102 as the current best margin-retention driver candidate, but it is not an
ideal driver. M63 should run a broader driver audit before treating the
checkpoint as a full driver promotion.

## 20260521T092234Z m63-broader-driver-audit-for-m62

- status: `completed`
- kind: `gate`
- hypothesis: M62_a250 should keep M37 aggregate held-out performance, but it
  still needs response-history/self-identification evidence before a broader
  driver promotion.
- command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m24_human_view_gru_driver.json --episodes 120 --seed 7000 --policies envelope_aes --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history --device cpu --run-dir runs/m63_m62_broader_driver_audit_seed7000`
- returncode: `0`
- run dir: `runs/m63_m62_broader_driver_audit_seed7000`
- success artifact: `runs/m63_m62_broader_driver_audit_seed7000/policy_summary.csv`

Result:

- `m37_102` success: `0.875000`;
- `m62_a250` success: `0.875000`;
- `m62_a250` mean clearance margin: `1.942633` versus M37 `1.942143`;
- reset recurrent state success: `0.866667`;
- zero current/all response success: `0.875000`;
- zero action history success: `0.875000`.

Conclusion: M62 keeps aggregate held-out performance and remains the current
best margin-retention candidate, but M63 does not prove driver-like closed-loop
self-identification. M64 should build a stronger response-history gate rather
than relying on average ablation success.

## 20260521T092827Z m64-stronger-response-history-self-identification-gate

- status: `completed`
- kind: `gate`
- hypothesis: A paired nominal/low-friction perturbation gate should expose
  whether M62_a250 depends on recurrent response history and action history,
  rather than only preserving aggregate success.
- seed-delta command: `conda run -n autodrift python -m autodrift.seed_delta_audit --episodes-csv runs/m63_m62_broader_driver_audit_seed7000/episodes.csv --baseline-policy m62_a250 --candidate-policy m62_a250_reset --candidate-policy m62_a250_zero_current --candidate-policy m62_a250_zero_all --candidate-policy m62_a250_noact --run-dir runs/m64_m62_ablation_seed_delta_audit`
- paired gate command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt --checkpoint-policy m37_102_reset=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@reset_recurrent_state --checkpoint-policy m37_102_zero_current=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@zero_current_response --checkpoint-policy m37_102_zero_all=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@zero_all_response --checkpoint-policy m37_102_noact=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt@zero_action_history --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history --episodes 80 --seed 3600 --device cpu --run-dir runs/m64_m62_paired_perturbation_gate_seed3600`
- returncode: `0`
- run dirs: `runs/m64_m62_ablation_seed_delta_audit`,
  `runs/m64_m62_paired_perturbation_gate_seed3600`
- success artifact:
  `runs/m64_m62_paired_perturbation_gate_seed3600/pair_summary.csv`

Result:

- seed-delta audit: `m62_a250_noact`, `m62_a250_zero_current`, and
  `m62_a250_zero_all` have zero aggregate success delta versus `m62_a250`;
- seed-delta audit: reset recurrent state has success delta `-0.008333` with
  1 improved and 2 regressed seeds;
- seed-delta audit: zero current/all response features reduce mean clearance
  margin by `-0.007306` without reducing aggregate success;
- paired gate nominal/perturbed success for `m37_102`: `0.9375` / `0.6875`;
- paired gate perturbed success for M37 reset hidden and zero current/all
  response: `0.7000` / `0.7000`;
- paired gate nominal/perturbed success for `m62_a250`: `0.9375` / `0.6875`;
- paired gate perturbed success for reset hidden: `0.7000`;
- paired gate perturbed success for zero current/all response: `0.7000`;
- paired gate perturbed success for no action history: `0.6750`.

Conclusion: M64 is a negative self-identification diagnostic. The stricter
paired perturbation gate still does not show that removing recurrent response
state reliably weakens the policy. M37_102 and M62_a250 behave nearly
identically on the paired ablation grid. `m62_a250` remains the current best
margin-retention checkpoint, but the ideal-driver blocker is unchanged:
closed-loop response history is not yet behavior-critical. M65 should target
response-history necessity directly with a corpus or training objective rather
than another aggregate-success continuation.

## 20260521T093805Z m65-response-necessity-corpus

- status: `completed`
- kind: `infrastructure`
- hypothesis: M64's paired perturbation episodes can be mined into a focused
  seed corpus for making deployable response history behavior-critical without
  adding oracle actor inputs.
- corpus command: `conda run -n autodrift python -m autodrift.response_necessity_corpus --episodes-csv runs/m64_m62_paired_perturbation_gate_seed3600/episodes.csv --baseline-policy m62_a250 --ablation-policy m62_a250_reset --ablation-policy m62_a250_zero_current --ablation-policy m62_a250_zero_all --ablation-policy m62_a250_noact --top-k 40 --repeat 4 --near-margin 0.05 --margin-scale 0.25 --run-dir runs/m65_response_necessity_corpus_seed3600`
- smoke command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m65_response_necessity_driver.json --total-steps 4096 --rollout-steps 64 --num-envs 4 --vector-env-mode sync --seed 2965 --device cuda --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --run-dir runs/ppo_m65_response_necessity_smoke_seed2965`
- returncode: `0`
- run dirs: `runs/m65_response_necessity_corpus_seed3600`,
  `runs/ppo_m65_response_necessity_smoke_seed2965`
- success artifacts:
  `runs/m65_response_necessity_corpus_seed3600/seed_sequence.csv`,
  `runs/ppo_m65_response_necessity_smoke_seed2965/checkpoint.pt`

Result:

- M65 corpus scored 80 paired seeds;
- selected critical seeds: 26;
- perturbation regressions: 22;
- low perturbed-margin seeds: 26;
- PPO training seed sequence rows after repeat: 104;
- maximum response-necessity score: `29.261055`;
- smoke eval return mean: `70.448440`;
- smoke eval termination rate: `0.100000`;
- final response prediction loss mean: `0.049053`;
- final baseline-action anchor loss mean: `0.000130`.

Conclusion: M65 creates a reusable corpus and validates the continuation path,
but it is not a promotion. The next step is M66 full continuation from
M62_a250, followed by unchanged margin-retention gates and the M64 paired
self-identification gate.

## 20260521T094543Z m66-full-response-necessity-continuation

- status: `completed`
- kind: `training`
- hypothesis: Full M65 continuation from M62_a250 should use the
  response-necessity corpus to improve paired self-identification while keeping
  strict margin retention.
- training command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m65_response_necessity_driver.json --seed 2965 --device cuda --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --run-dir runs/ppo_m65_response_necessity_seed2965`
- paired gate command: `conda run -n autodrift python -m autodrift.paired_perturbation_gate --env-config configs/ppo_m24_human_view_gru_driver.json --checkpoint runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --checkpoint-policy m65_004=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt --checkpoint-policy m65_004_reset=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@reset_recurrent_state --checkpoint-policy m65_004_zero_current=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@zero_current_response --checkpoint-policy m65_004_zero_all=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@zero_all_response --checkpoint-policy m65_004_noact=runs/ppo_m65_response_necessity_seed2965/checkpoints/checkpoint_step_4096.pt@zero_action_history --episodes 80 --seed 3600 --device cpu --run-dir runs/m66_m65_004_paired_perturbation_gate_seed3600`
- returncode: `0`
- run dirs: `runs/ppo_m65_response_necessity_seed2965`,
  `runs/m66_margin_retention_gate_strict`,
  `runs/m66_m65_004_paired_perturbation_gate_seed3600`
- success artifact:
  `runs/m66_margin_retention_gate_strict/candidate_gate_summary.csv`

Result:

- full training final eval return mean: `70.371693`;
- strict margin gate status: `needs_iteration`;
- passed candidates: none;
- closest candidate: `m65_004`;
- `m65_004` success delta: `0.000000`;
- `m65_004` binary regressions: 0;
- `m65_004` near-margin regressions: 1;
- `m65_004` mean margin delta: `-0.000603`;
- later checkpoints `m65_020` through `m65_032` introduce one binary
  regression and negative success delta `-0.006250`;
- paired gate `m65_004` nominal/perturbed success: `0.9375` / `0.6875`;
- paired gate `m65_004_reset` perturbed success: `0.7000`;
- paired gate `m65_004_zero_current` and `m65_004_zero_all` perturbed success:
  `0.7000`.

Conclusion: M66 is negative. Response-necessity seed replay and a stronger
response-prediction auxiliary did not produce a margin-retained checkpoint and
did not improve the self-identification ablation signal. M67 should use a
counterfactual/intervention objective rather than more replay probability.

## 20260521T110000Z m67a-privileged-upper-bound-harness

- status: `completed`
- kind: `infrastructure`
- hypothesis: Before training another deployable recurrent student objective,
  first test whether a privileged teacher with hidden vehicle dynamics can
  outperform `m62_a250` on response-critical seeds.
- teacher smoke command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m67a_privileged_upper_bound_teacher.json --total-steps 1024 --rollout-steps 64 --num-envs 4 --vector-env-mode sync --seed 3067 --device cuda --run-dir runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067 --eval-episodes 2`
- upper-bound smoke command: `conda run -n autodrift python -m autodrift.privileged_upper_bound --baseline-env-config configs/ppo_m24_human_view_gru_driver.json --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --candidate-checkpoint-policy m67a_smoke=runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067/checkpoint.pt --episodes 4 --seed 3600 --device cpu --run-dir runs/m67a_privileged_upper_bound_smoke_seed3600`
- returncode: `0`
- run dirs: `runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067`,
  `runs/m67a_privileged_upper_bound_smoke_seed3600`
- success artifacts:
  `runs/ppo_m67a_privileged_upper_bound_teacher_smoke_seed3067/checkpoint.pt`,
  `runs/m67a_privileged_upper_bound_smoke_seed3600/summary.json`

Result:

- added teacher-only `privileged_observation_mode="full_dynamics"`;
- legacy `include_privileged_params=True` still produces a 76-value observation;
- M67-A full-dynamics teacher observation has 82 values;
- smoke teacher eval return mean: `66.402815`;
- smoke teacher eval termination rate: `0.500000`;
- smoke upper-bound comparison is intentionally negative: `m67a_smoke` success
  `0.250000` versus `m62_a250` success `1.000000` over 4 seeds;
- smoke margin delta: `-1.390342`.

Conclusion: M67-A infrastructure is ready, but the smoke teacher is undertrained
and not a research result. The next step is full privileged teacher training
from `configs/ppo_m67a_privileged_upper_bound_teacher.json`, then an M65 corpus
upper-bound comparison against `m62_a250`. If the trained teacher does not
improve response-critical margin or success, re-mine a matched action-divergent
corpus before building the deployable OSI/student objective.

## 20260521T111500Z m67b-full-privileged-upper-bound-training

- status: `completed`
- kind: `training`
- hypothesis: A full privileged teacher with hidden dynamics should create an
  upper-bound gap over `m62_a250` on the M65 response-critical corpus.
- training command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m67a_privileged_upper_bound_teacher.json --seed 3067 --device cuda --run-dir runs/ppo_m67a_privileged_upper_bound_teacher_seed3067`
- final upper-bound command: `conda run -n autodrift python -m autodrift.privileged_upper_bound --baseline-env-config configs/ppo_m24_human_view_gru_driver.json --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --candidate-checkpoint-policy m67a_teacher=runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoint.pt --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --seed 3600 --device cpu --run-dir runs/m67a_privileged_upper_bound_m65_seed3600`
- checkpoint sweep command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m67a_privileged_upper_bound_teacher.json --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --checkpoint-policy m67a_008=... --checkpoint-policy m67a_256=... --policies heuristic --device cpu --run-dir runs/m67a_privileged_teacher_checkpoint_sweep_m65_seed3600`
- best upper-bound command: `conda run -n autodrift python -m autodrift.privileged_upper_bound --baseline-env-config configs/ppo_m24_human_view_gru_driver.json --candidate-env-config configs/ppo_m67a_privileged_upper_bound_teacher.json --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --candidate-checkpoint-policy m67a_232=runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoints/checkpoint_step_237568.pt --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --seed 3600 --device cpu --run-dir runs/m67a_privileged_upper_bound_best_m65_seed3600`
- returncode: `0`
- run dirs: `runs/ppo_m67a_privileged_upper_bound_teacher_seed3067`,
  `runs/m67a_privileged_upper_bound_m65_seed3600`,
  `runs/m67a_privileged_teacher_checkpoint_sweep_m65_seed3600`,
  `runs/m67a_privileged_upper_bound_best_m65_seed3600`
- success artifact:
  `runs/m67a_privileged_upper_bound_best_m65_seed3600/summary.json`

Result:

- final teacher eval return mean: `71.909091`;
- final teacher eval termination rate: `0.100000`;
- final teacher M65 success: `0.461538` versus M62 `0.615385`;
- final teacher M65 mean margin: `0.191716` versus M62 `0.304161`;
- best swept checkpoint: `m67a_232` at
  `runs/ppo_m67a_privileged_upper_bound_teacher_seed3067/checkpoints/checkpoint_step_237568.pt`;
- `m67a_232` M65 success: `0.500000`;
- `m67a_232` M65 mean margin: `0.213538`;
- `m67a_232` margin improved on 6 seeds and regressed on 20 seeds;
- best swept checkpoint still has success delta `-0.115385` and mean margin
  delta `-0.090623` versus `m62_a250`.

Conclusion: M67-B is negative. A from-scratch privileged `online_gru` teacher
does not produce a credible oracle upper bound over M62. This does not falsify
self-identification value because the teacher never reaches the retained M62
driving behavior. M67-C should build a warm-started or anchored privileged
teacher that preserves the 72-value M62 human-view response/context structure
and appends hidden dynamics as teacher-only context before returning to
student OSI or counterfactual intervention objectives.

## 20260521T112500Z m67-belief-self-identification-roadmap

- status: `completed`
- kind: `planning`
- artifact: `docs/m67-belief-self-identification-roadmap.md`

Conclusion: The 5.5pro recommendation is now recorded as the M67 belief/self-ID
roadmap. The project adopts the core direction: treat the driver as a POMDP
belief-learning problem, establish a credible privileged upper bound first,
mine matched action-divergent cases, then train a deployable recurrent student
with outcome-bound counterfactual interventions. The immediate next task remains
M67-C warm-started privileged teacher because M67-B's from-scratch teacher did
not beat `m62_a250`.

## 20260521T113000Z m67c-input-profile-audit

- status: `completed`
- kind: `planning`
- artifact: `docs/m67c-input-profile-audit.md`

Conclusion: The observation-profile review is now recorded. The main accepted
finding is that the current 72-value profile is deployable and useful, but not
clean enough to make zero-response/reset-hidden ablations decisive: obstacle
`rel_vx` and `rel_vy` are context-side motion proxies for static obstacles. The
next task changes from immediate warm-started teacher work to M67-D strict
self-ID context profile: keep the 72-value shape, add a config mode that zeroes
obstacle relative velocity, then re-run input-profile diagnostics before making
teacher/student self-ID claims.

## 20260521T113500Z m67d-strict-self-id-observation-profile

- status: `completed`
- kind: `infrastructure`
- hypothesis: Removing obstacle-relative-velocity motion proxies should make the
  self-ID diagnostic profile cleaner and may make response/action-history
  ablations more behavior-critical.
- smoke command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m67d_strict_self_id_context_driver.json --total-steps 4096 --rollout-steps 64 --num-envs 4 --vector-env-mode sync --seed 3167 --device cuda --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --run-dir runs/ppo_m67d_strict_context_smoke_seed3167 --eval-episodes 2`
- current-context benchmark command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m65_response_necessity_driver.json --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history --policies heuristic --device cpu --run-dir runs/m67d_m62_current_context_ablation_m65_seed3600`
- strict-context benchmark command: `conda run -n autodrift python -m autodrift.benchmark --env-config configs/ppo_m67d_strict_self_id_context_driver.json --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --checkpoint-policy m62_a250_reset=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@reset_recurrent_state --checkpoint-policy m62_a250_zero_current=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_current_response --checkpoint-policy m62_a250_zero_all=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_all_response --checkpoint-policy m62_a250_noact=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt@zero_action_history --policies heuristic --device cpu --run-dir runs/m67d_m62_strict_context_ablation_m65_seed3600`
- returncode: `0`
- run dirs: `runs/ppo_m67d_strict_context_smoke_seed3167`,
  `runs/m67d_m62_current_context_ablation_m65_seed3600`,
  `runs/m67d_m62_strict_context_ablation_m65_seed3600`,
  `runs/m67d_current_context_seed_delta_audit_m65`,
  `runs/m67d_strict_context_seed_delta_audit_m65`
- success artifacts:
  `runs/ppo_m67d_strict_context_smoke_seed3167/checkpoint.pt`,
  `runs/m67d_m62_strict_context_ablation_m65_seed3600/policy_summary.csv`,
  `runs/m67d_strict_context_seed_delta_audit_m65/policy_delta_summary.csv`

Result:

- new config field: `obstacle_relative_velocity_mode`;
- default mode: `ego`;
- strict mode: `zero`, preserving 72 observation values;
- smoke continuation loaded M62 and baseline anchor with `strict` load mode;
- strict-context M62 baseline success on M65: `0.615385`, unchanged from current
  context;
- strict-context zero-current/zero-all success deltas: `0.000000`;
- strict-context reset-hidden success delta: `0.000000`;
- strict-context no-action-history success delta: `-0.038462`;
- current-context zero-current/zero-all/reset success deltas were each
  `-0.038462`.

Conclusion: M67-D is a useful cleanup but not a self-ID breakthrough. Obstacle
relative velocity was a real context proxy, but removing it alone does not make
M62 history-critical. Keep strict context as the preferred diagnostic profile,
but the next proof gate needs wrong-history or matched-history interventions
rather than relying on reset/zero-response ablations.

## 20260521T121500Z m67-self-id-decision-ledger

- status: `completed`
- kind: `documentation`
- artifact: `docs/m67-self-id-decision-ledger.md`

Conclusion: The M67 belief-learning recommendation, input-profile audit,
strict-context result, deferred enhanced-OSI/noisy-IMU/reward-cleanup work, and
next `m67e-warm-started-privileged-teacher` task are now indexed in one recovery
document. This does not change the research queue; it prevents the adopted
decisions from being scattered across the M67 roadmap and profile-audit notes.

## 20260521T113356Z m67e-warm-started-privileged-teacher

- status: `completed`
- kind: `infrastructure`
- hypothesis: An M62-compatible privileged teacher can preserve the current
  human-view behavior and reveal whether hidden dynamics improves the M65
  response-critical corpus.
- smoke command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m67e_warm_started_privileged_teacher.json --total-steps 4096 --rollout-steps 64 --num-envs 4 --vector-env-mode sync --seed 3267 --device cuda --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --run-dir runs/ppo_m67e_warm_privileged_teacher_smoke_seed3267 --eval-episodes 2`
- full command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m67e_warm_started_privileged_teacher.json --seed 3267 --device cuda --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --run-dir runs/ppo_m67e_warm_privileged_teacher_seed3267`
- best upper-bound command: `conda run -n autodrift python -m autodrift.privileged_upper_bound --baseline-env-config configs/ppo_m67d_strict_self_id_context_driver.json --candidate-env-config configs/ppo_m67e_warm_started_privileged_teacher.json --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt --candidate-checkpoint-policy m67e_004=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --seed 3600 --device cpu --run-dir runs/m67e_warm_privileged_teacher_best_upper_bound_m65_seed3600`
- run dirs: `runs/ppo_m67e_warm_privileged_teacher_smoke_seed3267`,
  `runs/m67e_warm_privileged_teacher_smoke_upper_bound_m65_seed3600`,
  `runs/ppo_m67e_warm_privileged_teacher_seed3267`,
  `runs/m67e_warm_privileged_teacher_checkpoint_sweep_m65_seed3600`,
  `runs/m67e_warm_privileged_teacher_upper_bound_m65_seed3600`,
  `runs/m67e_warm_privileged_teacher_best_upper_bound_m65_seed3600`
- artifact: `docs/m67e-warm-started-privileged-teacher.md`

Result:

- new actor encoder: `privileged_human_view_online_gru`;
- teacher observation: first 72 values keep M62 human-view semantics, last 10
  values are teacher-only full hidden dynamics;
- M62 init load mode: `partial_privileged_human_view_branch`;
- baseline action anchor load mode: `partial_privileged_human_view_branch`;
- smoke M65 success: `0.615385`, mean margin `0.259679`;
- final M65 success: `0.615385`, mean margin `0.258980`;
- best swept checkpoint: `m67e_004`;
- best M65 success: `0.615385` versus M62 `0.615385`;
- best M65 mean margin: `0.260685` versus M62 `0.259881`;
- best mean margin delta: `0.000804`;
- margin-improved/regressed seeds: `13 / 13`.

Conclusion: M67-E is a useful architecture and checkpoint-compatibility step,
but it is not a credible privileged upper-bound breakthrough. The tiny margin
gain is best treated as retention noise. Do not train a deployable student from
this teacher yet. The next task is M68 matched action-divergent corpus mining:
find same-visible-context cases where hidden dynamics or wrong history actually
changes the preferred action or clearance outcome.

## 20260521T114603Z m68-matched-action-divergent-corpus

- status: `completed`
- kind: `infrastructure`
- hypothesis: M65 may contain same-visible-state pairs where hidden dynamics,
  wrong recurrent history, or swapped privileged context changes the teacher
  action.
- smoke command: `conda run -n autodrift python -m autodrift.matched_action_corpus --env-config configs/ppo_m67e_warm_started_privileged_teacher.json --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv --seed 6800 --device cpu --top-k 20 --max-visible-distance 0.75 --max-response-distance 0.25 --max-context-distance 0.05 --min-action-distance 0.05 --run-dir runs/m68_matched_action_corpus_split_smoke_m65_seed6800`
- run dirs: `runs/m68_matched_action_corpus_smoke_m65_seed6800`,
  `runs/m68_matched_action_corpus_strict_smoke_m65_seed6800`,
  `runs/m68_matched_action_corpus_split_smoke_m65_seed6800`
- artifact: `docs/m68-matched-action-divergent-corpus.md`

Result:

- new harness: `src/autodrift/matched_action_corpus.py`;
- tests: `tests/test_matched_action_corpus.py`;
- strict visible matches: `10 / 26`;
- action-divergent pairs: `6 / 26`;
- paired-action divergent pairs: `6 / 26`;
- wrong-history divergent pairs: `1 / 26`;
- privileged-packet divergent pairs: `0 / 26`;
- mean paired-action distance: `0.039916`;
- mean wrong-history action distance: `0.019980`;
- mean privileged-packet action distance: `0.000075`.

Conclusion: M68 validates the matched-action corpus harness, but the initial M65
smoke is a negative teacher-action diagnostic. The current M67-E privileged
branch is not action-relevant; action differences mostly reflect current
response differences rather than hidden dynamics alone. The next task is M69:
broaden matched hidden-dynamics mining across fresh seeds and perturbation axes
before building student OSI or wrong-history training losses.

## 20260521T115016Z m69-broader-matched-hidden-dynamics-mining

- status: `completed`
- kind: `gate`
- hypothesis: broader fresh-seed mining across friction, weak-brake, and
  slow-actuator perturbations may reveal hidden-dynamics action divergence that
  the M65 smoke missed.
- friction command: `conda run -n autodrift python -m autodrift.matched_action_corpus --env-config configs/ppo_m67e_warm_started_privileged_teacher.json --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --episodes 80 --seed 6900 --device cpu --top-k 40 --max-visible-distance 0.75 --max-response-distance 0.25 --max-context-distance 0.05 --min-action-distance 0.05 --nominal-friction-mu-range 0.85,1.15 --perturbed-friction-mu-range 0.25,0.35 --run-dir runs/m69_matched_action_friction_fresh80_seed6900`
- brake command: `conda run -n autodrift python -m autodrift.matched_action_corpus --env-config configs/ppo_m67e_warm_started_privileged_teacher.json --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --episodes 80 --seed 7000 --device cpu --top-k 40 --max-visible-distance 0.75 --max-response-distance 0.25 --max-context-distance 0.05 --min-action-distance 0.05 --nominal-friction-mu-range 0.85,1.15 --perturbed-friction-mu-range 0.85,1.15 --nominal-randomization brake_scale_range=1.20,1.40 --perturbed-randomization brake_scale_range=0.50,0.60 --run-dir runs/m69_matched_action_brake_fresh80_seed7000`
- actuator command: `conda run -n autodrift python -m autodrift.matched_action_corpus --env-config configs/ppo_m67e_warm_started_privileged_teacher.json --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --episodes 80 --seed 7100 --device cpu --top-k 40 --max-visible-distance 0.75 --max-response-distance 0.25 --max-context-distance 0.05 --min-action-distance 0.05 --nominal-friction-mu-range 0.85,1.15 --perturbed-friction-mu-range 0.85,1.15 --nominal-randomization actuator_tau_scale_range=0.55,0.75 --perturbed-randomization actuator_tau_scale_range=2.50,3.20 --run-dir runs/m69_matched_action_actuator_fresh80_seed7100`
- run dirs: `runs/m69_matched_action_friction_fresh80_seed6900`,
  `runs/m69_matched_action_brake_fresh80_seed7000`,
  `runs/m69_matched_action_actuator_fresh80_seed7100`
- artifact: `docs/m69-broader-matched-hidden-dynamics-mining.md`

Result:

- friction: 21/80 visible matches, 13 action-divergent, 1 wrong-history
  divergent, 0 privileged-packet divergent;
- weak brake: 53/80 visible matches, 6 action-divergent, 3 wrong-history
  divergent, 0 privileged-packet divergent;
- slow actuator: 70/80 visible matches, 0 action-divergent, 0 wrong-history
  divergent, 0 privileged-packet divergent;
- best weak-brake wrong-history candidates: seeds `7002`, `7059`, `7019`;
- all axes: privileged-packet action divergence remains effectively zero.

Conclusion: M69 broadens the negative M68 result. The M67-E privileged teacher is
still not using teacher-only hidden dynamics in an action-relevant way. The only
useful next proof surface is the small wrong-history candidate set, especially
weak-brake seeds. M70 should replay those candidates and require outcome-level
margin degradation before any student objective is attempted.

## 20260521T115609Z m70-wrong-history-continuation-gate

- status: `completed`
- kind: `gate`
- hypothesis: M69 wrong-history first-action candidates should degrade
  continuation clearance margin or success if they are useful self-ID snippets.
- code update: `hidden_swap_gate` now records `min_clearance_margin`,
  `obstacle_collision_radius`, and `min_obstacle_clearance` in replay rows and
  summarizes margin means/minima.
- candidate seeds: `experiments/m70_brake_wrong_history_candidate_seeds.csv`,
  `experiments/m70_friction_wrong_history_candidate_seeds.csv`
- brake command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m67e_warm_started_privileged_teacher.json --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --seed-csv experiments/m70_brake_wrong_history_candidate_seeds.csv --seed 7201 --device cpu --nominal-friction-mu-range 0.85,1.15 --perturbed-friction-mu-range 0.85,1.15 --nominal-randomization brake_scale_range=1.20,1.40 --perturbed-randomization brake_scale_range=0.50,0.60 --max-observation-distance 10.0 --max-continuation-steps 0 --run-dir runs/m70_wrong_history_continuation_brake_candidates_margin_seed7201`
- friction command: `conda run -n autodrift python -m autodrift.hidden_swap_gate --env-config configs/ppo_m67e_warm_started_privileged_teacher.json --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt --seed-csv experiments/m70_friction_wrong_history_candidate_seeds.csv --seed 7202 --device cpu --nominal-friction-mu-range 0.85,1.15 --perturbed-friction-mu-range 0.25,0.35 --max-observation-distance 10.0 --max-continuation-steps 0 --run-dir runs/m70_wrong_history_continuation_friction_candidates_margin_seed7202`
- run dirs: `runs/m70_wrong_history_continuation_brake_candidates_margin_seed7201`,
  `runs/m70_wrong_history_continuation_friction_candidates_margin_seed7202`
- artifact: `docs/m70-wrong-history-continuation-gate.md`

Result:

- weak-brake success delta under hidden-swap: `0` for all 6 source-condition
  continuations;
- weak-brake mean margin delta: `-0.000213 m`;
- weak-brake worst margin delta: `-0.001416 m`;
- friction success delta under hidden-swap: `0` for both source-condition
  continuations;
- friction mean margin delta: `+0.000670 m`;
- all terminal reasons remain `obstacle_completed`.

Conclusion: M70 is negative. Wrong-history first-action divergence does not
translate into outcome damage on these candidates. The next task is M71:
construct or mine outcome-sensitive matched scenarios where wrong history
actually reduces clearance margin or success by design.

## 20260521T120931Z m71-outcome-sensitive-matched-scenario-constructor

- status: `completed`
- kind: `infrastructure`
- hypothesis: outcome-sensitive mining can reject first-action-only differences
  and find matched hidden-dynamics cases where wrong history reduces success or
  clearance margin.
- code update: added `src/autodrift/outcome_sensitive_corpus.py`
- tests: added `tests/test_outcome_sensitive_corpus.py`
- artifact: `docs/m71-outcome-sensitive-matched-scenario-constructor.md`

Smoke commands:

- weak-brake baseline geometry:
  `runs/m71_outcome_sensitive_brake_smoke_seed7300`
- low-friction baseline geometry:
  `runs/m71_outcome_sensitive_friction_smoke_seed7400`
- tight weak-brake geometry:
  `runs/m71_outcome_sensitive_tight_brake_smoke_seed7500`
- tight low-friction geometry:
  `runs/m71_outcome_sensitive_tight_friction_smoke_seed7600`

Result:

- baseline weak-brake: `80` candidates, `35` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.003190`;
- baseline low-friction: `80` candidates, `7` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.013007` but not strict-valid;
- tight weak-brake: `80` candidates, `16` paired candidates, `13` visible
  matches, `0` outcome-sensitive pairs;
- tight low-friction: `80` candidates, `28` paired candidates, `5` visible
  matches, `0` outcome-sensitive pairs.

Conclusion: M71 is a useful harness but a negative diagnostic. The current
passive matched-snapshot setup still does not produce causal wrong-history
outcome gaps. The next task is M72: add a pre-emergency warm-up/history harness
so the recurrent state has explicit action-response evidence before obstacle
avoidance is evaluated.

## 20260521T121723Z m72-pre-emergency-warmup-history-harness

- status: `completed`
- kind: `infrastructure`
- hypothesis: passive matched snapshots are too weak because they do not give
  the recurrent state a clean pre-emergency identification phase.
- code update: `ObstacleTaskConfig` now supports `perception_reveal_step` and
  `perception_reveal_distance`; `outcome_sensitive_corpus` can override both
  from the CLI.
- behavior: the obstacle remains physically present and logged, but actor
  obstacle slots stay zero until reveal conditions pass.
- tests: `conda run -n autodrift pytest -q tests/test_env.py tests/test_config.py`
  returned `33 passed`; the expanded M72-B target set returned `40 passed`.
- smoke runs: `runs/m72_warmup_reveal_brake_smoke_seed7700`,
  `runs/m72_warmup_reveal_friction_smoke_seed7800`
- artifact: `docs/m72-pre-emergency-warmup-history-harness.md`

Result:

- weak-brake warm-up reveal: `60` candidates, `33` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.008442`;
- low-friction warm-up reveal: `60` candidates, `7` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.007695`.

Conclusion: M72 is a useful infrastructure pass but a negative diagnostic.
Passive warm-up reveal still does not make wrong-history recurrent state
outcome-causal. The next task is M73: add active, safety-bounded probing during
warm-up or a training objective that makes probing response history
action-relevant.

## 20260521T122640Z m73-active-probing-warmup-harness

- status: `completed`
- kind: `infrastructure`
- hypothesis: safety-bounded probing before obstacle reveal can create stronger
  response-history evidence than passive warm-up.
- code update: `outcome_sensitive_corpus` now supports
  `--probe-strategy`, steer/brake/throttle amplitude controls, probe period, and
  probe-until thresholds.
- tests: `conda run -n autodrift pytest -q tests/test_outcome_sensitive_corpus.py`
  returned `9 passed`.
- artifact: `docs/m73-active-probing-warmup-harness.md`

Smoke results:

- mild weak-brake probe: `60` candidates, `49` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.000881`;
- mild low-friction probe: `60` candidates, `35` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.008426`;
- strong low-friction probe: `60` candidates, `41` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.040596`;
- relaxed strong low-friction diagnostic: `52` visible matches, `0`
  outcome-sensitive pairs, same max margin gap `0.040596`.

Conclusion: M73 is a mixed negative result. Active probing creates more visible
matches and can generate large wrong-history margin gaps, but the large gaps are
not valid self-ID evidence because normal history already collides or context
matching is too weak. The next task is M74: actively sweep obstacle geometry
around M73 near misses to find valid normal-success / wrong-history-loss cases.

## 20260521T123131Z m74-active-probe-outcome-bound-scenario-sweep

- status: `completed`
- kind: `gate`
- hypothesis: sweeping obstacle distance and width around M73 high-gap
  active-probe near misses can create valid normal-success / wrong-history-loss
  cases.
- seed artifact: `experiments/m74_active_probe_near_miss_seeds.csv`
- run dirs:
  `runs/m74_active_probe_sweep_easy_friction_seed8200`,
  `runs/m74_active_probe_sweep_medium_friction_seed8201`,
  `runs/m74_active_probe_sweep_hard_friction_seed8202`,
  `runs/m74_active_probe_sweep_default_friction_seed8203`
- artifact: `docs/m74-active-probe-outcome-bound-scenario-sweep.md`

Result:

- easy geometry: `12` candidates, `8` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.001431`;
- medium geometry: `12` candidates, `10` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.002826`;
- hard geometry: `12` candidates, `11` visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.001620`;
- default dense target: `21` candidates, `4` strict visible matches, `0`
  outcome-sensitive pairs, max margin gap `0.045526`.

Conclusion: M74 is negative. Reset-level geometry sweeps either remove the
active-probe margin signal or leave it only in invalid collision-to-collision /
non-strict-context rows. The next task is M75: snapshot-level obstacle relocation
that preserves ego state, hidden state, and active-probe history while sweeping
only obstacle geometry.

## 20260521T124839Z m75-snapshot-level-obstacle-relocation-sweep

- status: `completed`
- kind: `infrastructure`
- hypothesis: preserving the active-probe snapshot and mutating only obstacle
  geometry can turn M73/M74 near misses into valid normal-history /
  wrong-history outcome-sensitive snippets.
- code update: `outcome_sensitive_corpus` now supports snapshot relocation via
  `--snapshot-relocation-distances`,
  `--snapshot-relocation-lateral-offsets`, and
  `--snapshot-relocation-half-widths`.
- focused test: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_outcome_sensitive_corpus.py`
  returned `11 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  and `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `207 passed`.
- run dirs:
  `runs/m75_snapshot_relocation_smoke_seed8300`,
  `runs/m75_snapshot_relocation_lateral_seed8301`,
  `runs/m75_snapshot_relocation_mid_friction_seed8302`,
  `runs/m75_snapshot_relocation_relaxed_seed8303`,
  `runs/m75_snapshot_relocation_target_refine_seed8304`
- artifact: `docs/m75-snapshot-level-obstacle-relocation-sweep.md`

Result:

- centered strict relocation: `288` candidates, `64` strict visible matches,
  `103` margin-gap rows, `0` accepted outcome-sensitive pairs, max gap
  `0.122641`;
- lateral strict relocation: `810` candidates, `180` strict visible matches,
  `2` source-outcome rows, `0` accepted pairs, max gap `0.227224`;
- mid-friction strict relocation: `810` candidates, `180` strict visible
  matches, `1` source-outcome row, `0` accepted pairs, max gap `0.228434`;
- relaxed lateral diagnostic: `810` candidates, `720` relaxed visible matches,
  `2` accepted pairs, max gap `0.227224`;
- target-refined strict diagnostic: `162` candidates, `12` strict visible
  matches, `7` source-outcome rows, `0` accepted pairs, max gap `0.020358`.

Conclusion: M75 is an infrastructure pass but a negative strict gate result.
Snapshot relocation preserves the M73 active-probe history and can expose
wrong-history margin loss under relaxed matching. Under strict matching, the
useful outcome rows are not visible-state matches, while strict visible rows
have weak or invalid outcome effects. The next task is M76: collect a snapshot
bank and pair by actual visible response/context distance before applying
relocation.

## 20260521T125846Z m76-snapshot-bank-visible-matcher

- status: `completed`
- kind: `infrastructure`
- hypothesis: pairing active-probe snapshots by visible response/context
  distance before relocation can preserve M75's outcome signal while satisfying
  the strict visible-state gate.
- code update: added `autodrift.snapshot_bank_relocation`, which collects
  active-probe snapshot banks, ranks nominal/perturbed pairs by visible-state
  distance, and then applies M75 relocation and wrong-history replay.
- focused tests: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_snapshot_bank_relocation.py tests/test_outcome_sensitive_corpus.py`
  returned `13 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  and `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `209 passed`.
- run dirs:
  `runs/m76_snapshot_bank_relocation_strict_seed8400`,
  `runs/m76_snapshot_bank_relocation_relaxed_seed8401`
- artifact: `docs/m76-snapshot-bank-visible-matcher.md`

Result:

- strict bank relocation: `432` candidates, `144` strict visible matches, `2`
  margin-gap rows, `0` accepted snippets, max gap `0.011437`, mean visible
  distance `0.234060`;
- relaxed bank relocation: `432` candidates, `162` visible matches, `1`
  accepted relaxed snippet, max gap `0.011437`.

Conclusion: M76 is an infrastructure pass but a negative strict gate result. It
improves visible matching versus M75 and can find a relaxed wrong-history
margin-loss row, but the row is not strict evidence because context distance is
just over the strict threshold and normal margin is too large. The next task is
M77: boundary-aware relocation search that places matched snapshots near the
clearance boundary before testing wrong-history margin loss.

## 20260521T130515Z m77-boundary-aware-snapshot-relocation

- status: `completed`
- kind: `gate`
- hypothesis: dense obstacle-width relocation around M76 matched pairs can place
  normal-history rollouts near the clearance boundary while preserving strict
  visible matching and wrong-history margin loss.
- code update: none; reused `autodrift.snapshot_bank_relocation`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  and `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `209 passed`.
- run dir: `runs/m77_boundary_dense_width_strict_seed8500`
- artifact: `docs/m77-boundary-aware-snapshot-relocation.md`

Result:

- `1344` candidates;
- `448` strict visible matches;
- `52` margin-gap rows;
- `0` accepted outcome-sensitive pairs;
- max margin gap `0.105091`;
- mean visible distance `0.234060`.

Conclusion: M77 is negative. Dense width search creates large wrong-history
margin gaps only in collision-to-collision rows. Strict-visible, successful
near-boundary rows exist, but wrong-history margin loss stays below the
pre-registered `0.01` threshold. The next task is M78: implement an
outcome-weighted intervention objective instead of relying on more geometry-only
mining.

## 20260521T132453Z m78-outcome-weighted-intervention-objective

- status: `completed`
- kind: `infrastructure`
- hypothesis: an outcome-weighted hidden-intervention loss can turn weak
  wrong-history margin losses into a training signal without adding oracle actor
  inputs.
- code update: added `OutcomeInterventionSnippets`,
  `load_outcome_intervention_snippets`, `outcome_weighted_intervention_loss`,
  PPO config fields, trainer metric logging, and snapshot-bank NPZ export.
- config: `configs/ppo_m78_outcome_weighted_intervention_driver.json`
- focused tests: `python -m compileall -q src tests` and
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_intervention_objectives.py tests/test_snapshot_bank_relocation.py tests/test_checkpoints.py::test_train_logs_outcome_intervention_loss`
  returned `15 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  and `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `215 passed`.
- snippet exports:
  `runs/m78_outcome_weighted_snippets_seed8601`,
  `runs/m78_human_view_outcome_weighted_snippets_seed8602`
- smoke training:
  `runs/ppo_m78_outcome_weighted_smoke_seed3368`
- artifact: `docs/m78-outcome-weighted-intervention-objective.md`

Result:

- privileged diagnostic snippets: `523` rows, weight sum `0.247269`, max margin
  gap `0.012205`;
- human-view snippets: `671` rows, weight sum `0.299190`, max margin gap
  `0.010836`;
- smoke training logs `outcome_intervention_loss_mean`; final value
  `0.038767`;
- eval smoke: return mean `68.657370`, termination rate `0.0`;
- fixed-batch offline objective check: `m62_init` mean loss `0.039923`,
  `m78_smoke` mean loss `0.040302`.

Conclusion: M78 is an infrastructure pass but a negative smoke result. The
objective is wired and deployable-human-view compatible, but the first short
low-coefficient smoke does not improve the offline intervention loss. The next
task is M79: normalize or sharpen weights, sweep coefficient, and require
fixed-batch offline objective reduction before long continuation training.

## 20260521T133409Z m79-outcome-objective-weight-tuning

- status: `completed`
- kind: `training`
- hypothesis: a fixed-batch evaluator plus a stronger
  `outcome_intervention_aux_coef` can show whether M78's objective simply needs
  coefficient/weight tuning before full continuation.
- code update: added `autodrift.outcome_intervention_eval`, which loads one
  snippet NPZ and multiple checkpoints, resets the Torch RNG for every policy,
  and writes comparable `policy_summary.csv`, `batch_losses.csv`, and
  `summary.json` artifacts.
- config: `configs/ppo_m79_outcome_weighted_highcoef_driver.json`
- focused tests: `python -m compileall -q src tests` and
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_outcome_intervention_eval.py tests/test_intervention_objectives.py`
  returned `12 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  JSON validation, CSV validation, and
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `217 passed`.
- evaluator runs:
  `runs/m79_outcome_intervention_eval_m78_seed0`,
  `runs/m79_outcome_intervention_eval_highcoef_seed0`
- smoke training:
  `runs/ppo_m79_outcome_weighted_highcoef_smoke_seed3469`
- artifact: `docs/m79-outcome-objective-weight-tuning.md`

Result:

- fixed-batch reproduction: `m62_init` mean loss `0.039923`, `m78_smoke` mean
  loss `0.040302`;
- high-coefficient smoke: eval return mean `49.376177`, termination rate `0.5`,
  final train `outcome_intervention_loss_mean` `0.078022`;
- fixed-batch high-coefficient check: `m62_init` mean loss `0.039923`,
  `m78_smoke` mean loss `0.040302`, `m79_highcoef` mean loss `0.041033`.

Conclusion: M79 is an infrastructure pass and a negative coefficient-tuning
result. A stronger auxiliary coefficient does not reduce the offline objective
and also damages the short evaluation, so the next task is M80: optimize only
`outcome_weighted_intervention_loss` on the snippet NPZ to prove the objective
can move in the intended direction before reintroducing PPO.

## 20260521T134840Z external-review-5-5pro-mhtml-ingestion

- status: `completed`
- kind: `planning`
- source: `~/workspace/AutoDrift - 项目评估分析.mhtml`
- artifact:
  `docs/external-review-5-5pro-mhtml.md`,
  `docs/m81-wheel-response-input-roadmap.md`

Result:

- preserved the full MHTML review as a durable project note, including project
  status, engineering backlog, research framing, input sufficiency, solve vs
  verify boundary, warm-up/probing requirement, and proof gates;
- added M81 as the planned wheel/tire response input branch after M80;
- updated the observation contract so wheel response is explicitly allowed as
  deployable vehicle feedback, while true friction, true tire limits, oracle
  saturation labels, and feasibility labels remain forbidden actor inputs.

Conclusion: M80 remains the immediate blocker for the current objective, but
M81 is now the planned larger input-infrastructure branch. The important 5.5pro
review content is no longer only in the MHTML export.

## 20260521T135652Z m80-outcome-objective-only-sanity-check

- status: `completed`
- kind: `gate`
- hypothesis: if the M78 outcome intervention objective is correctly signed and
  the snippets contain signal, direct optimization from `m62_a250` should reduce
  M79's fixed-batch loss.
- code update: added `autodrift.outcome_intervention_optimize`, which freezes
  `log_std` by default, optimizes only `outcome_weighted_intervention_loss`,
  saves an optimized checkpoint, and writes before/after fixed-batch summaries.
- focused tests: `python -m compileall -q src tests`,
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_outcome_intervention_optimize.py tests/test_outcome_intervention_eval.py tests/test_intervention_objectives.py`,
  and `git diff --check` passed with `13 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  JSON validation, CSV validation, and
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `218 passed`.
- run dir: `runs/m80_outcome_objective_only_seed8800`
- eval smoke dirs:
  `runs/m80_m62_eval_seed8800`,
  `runs/m80_outcome_objective_only_eval_seed8800`
- artifact: `docs/m80-outcome-objective-only-sanity-check.md`

Result:

- fixed-batch loss improves from `0.039923` to `0.008483`;
- training loss at step 200 is `0.017400`;
- 5-episode same-seed smoke has termination `0.0` for both M62 and M80;
- smoke return mean is `79.328658` for M62 and `85.073736` for the M80
  objective-only checkpoint.

Conclusion: M80 is a positive objective sanity result, not a promoted driver.
The objective can move in isolation, so the next highest-leverage task is M81:
add wheel/tire response inputs and gates. A later M82 should reintroduce the
outcome objective into PPO with fixed-batch and margin-retention guards.

## 20260521T140554Z m81-wheel-response-self-id-input-branch

- status: `completed`
- kind: `infrastructure`
- hypothesis: adding deployable front/rear wheel-response features to the
  response stream creates a runnable input branch for professional-driver-like
  self-identification without exposing true friction or oracle feasibility.
- code update: added `wheel_observation_mode="front_rear"`,
  `wheel_human_view_online_gru`, wheel checkpoint loading, response-mask
  accounting for wheel features, and `zero_wheel_response` ablation.
- config: `configs/ppo_m81_wheel_response_gru_driver.json`
- focused tests: `python -m compileall -q src tests`,
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_env.py tests/test_checkpoints.py tests/test_hidden_swap_gate.py tests/test_evaluate.py tests/test_benchmark.py`,
  and `git diff --check` passed with `91 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  JSON validation, CSV validation, and
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `225 passed`.
- training smoke: `runs/ppo_m81_wheel_response_smoke_seed3581`
- ablation smoke: `runs/m81_wheel_response_ablation_smoke_seed8810`
- artifact: `docs/m81-wheel-response-input-roadmap.md`

Result:

- wheel actor observation dimension: `85`;
- response stream dimension: `25`;
- context stream dimension: `60`;
- 4096-step smoke trains and saves a checkpoint;
- 2-episode eval after training has return mean `19.778977` and termination
  rate `1.0`, so the checkpoint is not a candidate;
- zero-wheel benchmark path executes with `m81_smoke` and `m81_zero_wheel`.

Conclusion: M81 completes Stage 1 wheel-response infrastructure, but not a
useful wheel-response driver. The next queued task is M82, the guarded PPO
reintroduction of the outcome objective; a later M83 should train and gate the
wheel-response driver at meaningful scale.

## 20260521T141057Z m82-outcome-objective-ppo-reintroduction

- status: `completed`
- kind: `training`
- hypothesis: freezing `log_std` and lowering learning rate will let PPO use
  the M80-validated outcome objective without worsening the fixed-batch guard.
- code update: added `PPOConfig.freeze_log_std` and optimized only trainable
  parameters.
- config: `configs/ppo_m82_outcome_guarded_reintro_driver.json`
- focused tests: `python -m json.tool`, `python -m compileall -q src tests`,
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_checkpoints.py::test_train_can_freeze_log_std tests/test_checkpoints.py::test_train_logs_outcome_intervention_loss tests/test_outcome_intervention_eval.py`,
  and `git diff --check` passed with `4 passed`.
- final validation: `git diff --check`, `python -m compileall -q src tests`,
  JSON validation, CSV validation, and
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q`
  returned `226 passed`.
- training smoke: `runs/ppo_m82_outcome_guarded_smoke_seed3682`
- objective eval: `runs/m82_outcome_intervention_eval_seed0`
- artifact: `docs/m82-outcome-objective-ppo-reintroduction.md`

Result:

- short eval return mean `30.307775`;
- short eval termination rate `0.5`;
- fixed-batch loss: `m62_init` `0.039923`, `m78_smoke` `0.040302`,
  `m79_highcoef` `0.041033`, `m82_guarded` `0.040120`.

Conclusion: M82 is slightly better than M78/M79 on the fixed-batch objective but
still worse than M62 and not a driving candidate. The next task is M83:
meaningful wheel-response driver training and zero-wheel/history gates.

## 20260521T141626Z m83-wheel-response-driver-training-gate

- status: `completed`
- kind: `training`
- hypothesis: the M81 wheel-response actor can train at meaningful smoke scale
  and expose useful dependence on wheel/action-response history.
- config: `configs/ppo_m81_wheel_response_gru_driver.json`
- training run: `runs/ppo_m83_wheel_response_driver_seed3783`
- ablation gate: `runs/m83_wheel_response_gate_seed8830`
- artifact: `docs/m83-wheel-response-driver-training-gate.md`

Result:

- 32k-step CUDA run final eval return mean `27.553417`;
- final eval termination rate `0.9`;
- 20-episode gate success: heuristic `0.4`, M83 `0.1`;
- clearance margin mean: heuristic `0.479831`, M83 `0.285214`;
- M83 ablations remain weak: reset success `0.1`, zero-all success `0.1`,
  zero-wheel success `0.1`.

Conclusion: M83 is negative. From-scratch 85-value wheel-response training loses
too much driving behavior to support a wheel self-identification claim. The next
task is M84: add an M62-to-wheel partial initialization path so the wheel branch
starts from retained M62 behavior before testing whether wheel response adds
useful adaptation evidence.

## 20260521T142450Z m84-m62-to-wheel-partial-init

- status: `completed`
- kind: `infrastructure`
- hypothesis: the wheel-response actor should be initialized from retained M62
  behavior before judging whether wheel feedback helps self-identification.
- code update: `load_init_checkpoint_state(...)` can now copy the first 12
  human-view response encoder columns into the 25-value wheel response encoder
  and zero the new wheel columns.
- config: `configs/ppo_m84_wheel_response_warmstart_driver.json`
- focused test:
  `tests/test_checkpoints.py::test_wheel_human_view_init_preserves_human_view_behavior`
- training smoke: `runs/ppo_m84_wheel_warmstart_smoke_seed3884`
- ablation gate: `runs/m84_wheel_warmstart_gate_seed8830`
- artifact: `docs/m84-m62-to-wheel-partial-init.md`

Result:

- real M62 checkpoint loads with `load_mode=partial_wheel_response_encoder`;
- 4096-step CUDA smoke final eval termination rate `0.0`;
- 20-episode gate success: heuristic `0.40`, M84 `0.90`;
- M84 clearance margin mean `2.107145`;
- ablations are not self-ID-positive: reset `0.85`, zero-all `0.90`,
  zero-wheel `0.90`.

Conclusion: M84 is positive for behavior retention and M62-to-wheel
infrastructure, but not a wheel self-identification pass. The next task is M85:
use a warm-started wheel/body response auxiliary target or envelope objective so
wheel feedback becomes behavior-relevant under zero-wheel and wrong-history
gates.

## 20260521T143420Z m85-warmstarted-wheel-response-aux

- status: `completed`
- kind: `training`
- hypothesis: expanding the warm-started response-prediction target to the full
  25-value response stream can make wheel feedback behavior-relevant while
  preserving M84/M62 behavior.
- config: `configs/ppo_m85_wheel_response_aux_driver.json`
- code update: added a focused checkpoint test for resizing the response
  prediction head during 72-to-85 wheel initialization.
- focused test:
  `tests/test_checkpoints.py::test_wheel_human_view_init_can_resize_response_prediction_head`
- training smoke: `runs/ppo_m85_wheel_response_aux_smoke_seed3985`
- ablation gate: `runs/m85_wheel_response_aux_gate_seed8830`
- artifact: `docs/m85-warmstarted-wheel-response-aux.md`

Result:

- real M62 checkpoint and anchor both load with
  `partial_wheel_response_encoder_response_prediction_head`;
- 4096-step smoke final eval termination rate `0.25`;
- 20-episode gate success: heuristic `0.40`, M85 `0.90`;
- M85 return mean `70.645276`;
- ablations remain negative for wheel self-ID: reset `0.90`, zero-all `0.85`,
  zero-wheel `0.90`;
- response encoder norms: body `7.809560`, wheel `0.058681`.

Conclusion: M85 retains good aggregate behavior but does not create wheel
dependence. The next task is M86: audit whether the current front/rear wheel
features contain useful information beyond body response before adding more
training pressure.

## 20260521T144310Z m86-wheel-response-relevance-audit

- status: `completed`
- kind: `gate`
- hypothesis: if the current front/rear wheel response features are useful, a
  body+wheel offline probe should outperform a body-only probe on hidden
  dynamics or future-response-relevant buckets.
- code update: added `autodrift.wheel_response_relevance_audit` and focused
  tests for wheel feature slicing and gain summaries.
- focused tests: `tests/test_wheel_response_relevance_audit.py`
- audit run: `runs/m86_wheel_response_relevance_audit_seed9100`
- artifact: `docs/m86-wheel-response-relevance-audit.md`

Result:

- samples: `1500`;
- mean body+wheel gain over body-only: `0.009371`;
- max body+wheel gain: `0.102410`;
- only target with gain above `0.02`: `mu_bucket`;
- `mu_bucket` body accuracy `0.706827`, body+wheel accuracy `0.809237`;
- brake, mass, tire, and steering-tau buckets do not improve.

Conclusion: M86 is mixed but mostly negative. The current front/rear wheel
features have narrow friction-bucket information, but they do not provide broad
hidden-dynamics information beyond body response. The next task is M87:
target friction/envelope estimation or mine matched ambiguous body-response
cases instead of increasing generic wheel auxiliary loss.

## 20260521T145925Z m87-wheel-informed-friction-envelope-objective

- status: `completed`
- kind: `training`
- hypothesis: the narrow M86 wheel friction signal can be converted into a
  training-time friction-bucket auxiliary objective without exposing `mu` to the
  deployable actor.
- code update: added `friction_bucket_aux_coef`,
  `friction_bucket_labels_from_mu`, recurrent feature sequence support, and
  per-step friction labels from env info.
- config: `configs/ppo_m87_wheel_friction_bucket_aux_driver.json`
- focused tests:
  `tests/test_checkpoints.py::test_friction_bucket_labels_use_m86_boundaries`
  and
  `tests/test_checkpoints.py::test_train_logs_friction_bucket_auxiliary_loss`
- training smoke: `runs/ppo_m87_wheel_friction_bucket_aux_smoke_seed4087`
- ablation gate: `runs/m87_wheel_friction_bucket_aux_gate_seed8830`
- relevance audit: `runs/m87_wheel_friction_relevance_audit_seed9100`
- artifact: `docs/m87-wheel-informed-friction-envelope-objective.md`

Result:

- M62 loads with `partial_wheel_response_encoder`;
- 4096-step built-in eval termination rate `0.0`;
- final friction aux accuracy is unstable and ends at `0.0`;
- 20-episode gate success: M87 `0.90`, reset `0.85`, zero-all `0.90`,
  zero-wheel `0.90`;
- post-training `mu_bucket` audit: body `0.802372`, body+wheel `0.802372`,
  body+wheel gain `0.0`;
- response encoder norms: body `7.812276`, wheel `0.071743`.

Conclusion: M87 preserves behavior but does not create wheel dependence. The
friction auxiliary is solved by body response rather than wheel response. The
next task is M88: mask body response or mine body-ambiguous wheel-different
cases so the friction/envelope objective cannot ignore wheel evidence.

## 20260521T151030Z m88-wheel-masked-friction-auxiliary

- status: `completed`
- kind: `training`
- hypothesis: masking body response in the friction auxiliary branch and using
  response GRU hidden should force the friction objective to use wheel evidence.
- code update: added `friction_bucket_aux_observation_mask`,
  `friction_bucket_aux_feature_source`, `mask_friction_aux_observations`, and
  `recurrent_response_hidden_sequence`.
- config: `configs/ppo_m88_wheel_masked_friction_aux_driver.json`
- focused tests:
  `tests/test_checkpoints.py::test_wheel_only_friction_aux_mask_zeros_body_response_only`
  and
  `tests/test_checkpoints.py::test_train_logs_wheel_masked_friction_bucket_auxiliary_loss`
- training smoke: `runs/ppo_m88_wheel_masked_friction_aux_smoke_seed4188`
- ablation gate: `runs/m88_wheel_masked_friction_aux_gate_seed8830`
- relevance audit: `runs/m88_wheel_masked_friction_relevance_audit_seed9100`
- artifact: `docs/m88-wheel-masked-friction-auxiliary.md`

Result:

- built-in eval termination rate `0.25`;
- final friction aux accuracy `0.285156`;
- 20-episode gate success: M88 `0.85`, reset `0.80`, zero-all `0.85`,
  zero-wheel `0.85`;
- post-training `mu_bucket` audit: body `0.819302`, wheel `0.636550`,
  body+wheel `0.825462`, gain `0.006160`;
- response encoder norms: body `7.807649`, wheel `0.073712`.

Conclusion: M88 is negative for wheel self-identification. The masked auxiliary
path works but still does not make wheel response behavior-critical. The next
task is M89: isolate the wheel-masked friction objective outside PPO, as M80 did
for the outcome objective.

## 20260521T151800Z m89-objective-only-wheel-masked-friction-sanity

- status: `completed`
- kind: `gate`
- hypothesis: the M88 wheel-masked friction objective can move in isolation even
  though PPO coupling did not make wheel response behavior-critical.
- code update: added `autodrift.wheel_masked_friction_optimize`, an objective-
  only harness that updates response encoder, online GRU, and a temporary
  classifier while leaving actor head, critic, context encoder, and `log_std`
  untouched.
- focused tests: `tests/test_wheel_masked_friction_optimize.py`
- objective run: `runs/m89_wheel_masked_friction_objective_only_seed9200`
- behavior gate: `runs/m89_wheel_masked_friction_objective_gate_seed8830`
- relevance audit: `runs/m89_wheel_masked_friction_relevance_audit_seed9100`
- artifact: `docs/m89-objective-only-wheel-masked-friction-sanity.md`

Result:

- objective test accuracy improves from `0.078199` to `0.668246`;
- wheel response encoder norm grows from `0.0` to `2.008215`;
- 20-episode behavior gate success: M89 `0.90`, reset `0.80`,
  zero-all `0.90`, zero-wheel `0.85`;
- `mu_bucket` relevance audit body+wheel gain reaches `+0.137014`.

Conclusion: M89 is the first positive wheel objective result. It is not a full
self-ID pass, but it proves the masked wheel friction objective can move in
isolation and creates a small behavior-level zero-wheel drop. The next task is
M90: guarded PPO continuation from the M89 optimized checkpoint.

## 20260521T152900Z m89b-research-process-enforcement

- status: `completed`
- kind: `infrastructure`
- hypothesis: research workflow rules should be enforced by local repository
  checks instead of only being documented.
- code update: added `autodrift.research_validate`, manifest validation,
  scoreboard validation, M90 manifest, and pre-commit integration.
- focused tests: `tests/test_research_validate.py`
- artifact: `docs/research-process-enforcement.md`

Result:

- `make research-validate` passes with `enforce_from_priority=870`;
- M90 is now pre-registered in
  `experiments/manifests/m90-guarded-ppo-from-wheel-objective-checkpoint.json`;
- `experiments/scoreboard.csv` has the fixed schema and an M89 reference row;
- tracked and installed pre-commit hooks run the research validator before
  lightweight tests.

Conclusion: M90+ research tasks now fail closed on missing manifest,
scoreboard, status-count, or required-artifact metadata. Historical M8-M89
records remain legacy-compatible.

## 20260521T164207Z m92-local-wheel-ground-speed-observability-audit

- status: `completed`
- kind: `gate`
- hypothesis: M91-I rejected the current single-track raw wheel proxy, not wheel
  sensing in general; a cleaner `Romega_i + v_parallel_i` profile may improve
  future handling-envelope observability without feeding slip diagnostics.
- code update: added `front_rear_omega`, `front_rear_omega_ground`, and
  `front_rear_omega_ground_error` observation modes while preserving the
  85-value wheel frame.
- configs:
  `configs/m92_front_rear_omega_profile.json`,
  `configs/m92_front_rear_omega_ground_profile.json`,
  `configs/m92_front_rear_omega_ground_error_profile.json`
- audit runs:
  `runs/m92_omega_observability_seed9390`,
  `runs/m92_omega_ground_observability_seed9391`,
  `runs/m92_omega_ground_error_observability_seed9392`
- artifact: `docs/m92-local-wheel-ground-speed-observability-audit.md`

Result:

- `front_rear_omega` mean P1-vs-P0 R2 lift: `+0.151403`;
- `front_rear_omega_ground` mean P1-vs-P0 R2 lift: `-0.062184`;
- `front_rear_omega_ground_error` mean P1-vs-P0 R2 lift: `-0.344659`;
- fixed-scale speed error regresses mean MAE-improvement by `-0.054854`.

Conclusion: M92 is negative for admitting the current single-track local
wheel/ground-speed branch into the primary PPO driver input. Keep the no-wheel
human-view response stream as primary until a true four-wheel profile or a
better matched corpus proves stable benefit.

## 20260521T165246Z m93-m62-hidden-envelope-probe

- status: `completed`
- kind: `gate`
- hypothesis: M62 may already encode useful no-wheel response history in its
  recurrent hidden state even though prior behavior gates were weak.
- code update: added `autodrift.hidden_envelope_probe`, which compares normal
  carried recurrent hidden against same-frame reset hidden on future envelope
  targets.
- focused tests: `tests/test_hidden_envelope_probe.py`
- diagnostic run: `runs/m93_m62_hidden_envelope_probe_seed9410`
- artifact: `docs/m93-m62-hidden-envelope-probe.md`

Result:

- sampled `704` states across `30` episodes;
- braking `response_hidden - reset_response_hidden` R2 lift: `-0.102351`;
- lateral acceleration R2 lift: `+0.056331`;
- yaw R2 lift: `-0.272739`;
- policy fused features are worse than reset fused features on all targets.

Conclusion: M93 is negative for treating M62 hidden state as a stable
future-envelope belief. The next no-wheel branch should test an objective-only
or pretraining path that explicitly makes response hidden predict braking/yaw/
lateral authority before returning to PPO.

## 20260521T170652Z m94-hidden-envelope-objective-only

- status: `completed`
- kind: `objective_sanity`
- hypothesis: after M93 rejected M62 hidden as an existing envelope belief, a
  fixed-batch objective-only pass may make no-wheel response hidden predict
  future braking, yaw, and lateral handling envelope better than same-frame
  reset hidden before PPO.
- code update: added `autodrift.hidden_envelope_optimize`, which freezes the
  actor head, critic, context encoder, and `log_std`, then trains only
  `response_encoder`, `online_gru_cell`, and a temporary envelope head.
- focused tests: `tests/test_hidden_envelope_optimize.py`
- diagnostic runs:
  `runs/m94_hidden_envelope_objective_seed9430`,
  `runs/m94_hidden_envelope_objective_seed9431`,
  `runs/m94_hidden_envelope_objective_seed9432`
- artifact: `docs/m94-hidden-envelope-objective-only.md`

Result:

- seed `9430`: braking/lateral/yaw R2 lift deltas
  `+0.181666`, `+0.103870`, `+0.089349`;
- seed `9431`: braking/lateral/yaw R2 lift deltas
  `-0.583329`, `+0.213520`, `+1.113093`;
- seed `9432`: braking/lateral/yaw R2 lift deltas
  `-0.590820`, `+1.482785`, `+0.757101`;
- after optimization, 7/9 target-seed pairs have positive
  `response_hidden - reset_response_hidden` R2 lift.

Conclusion: M94 is a qualified positive objective-only result. The harness can
move no-wheel response hidden toward future-envelope belief, especially yaw and
lateral authority, but braking is unstable across seeds. Do not proceed
directly to PPO continuation; first run a braking-aware or per-target balanced
objective iteration and require stable braking plus yaw lift before behavior
retention and wrong-history gates.

## 20260521T171251Z m95-braking-weighted-hidden-envelope-objective

- status: `completed`
- kind: `objective_sanity`
- hypothesis: per-target contrast with higher braking weight can fix the M94
  braking instability without losing yaw or lateral future-envelope belief.
- code update: added `--contrast-mode per_target` and
  `--target-loss-weights` to `autodrift.hidden_envelope_optimize`. Defaults
  preserve the M94 scalar-mean contrast behavior.
- focused tests: `tests/test_hidden_envelope_optimize.py`
- diagnostic runs:
  `runs/m95_braking_weighted_hidden_envelope_seed9450`,
  `runs/m95_braking_weighted_hidden_envelope_seed9451`,
  `runs/m95_braking_weighted_hidden_envelope_seed9452`
- artifact: `docs/m95-braking-weighted-hidden-envelope-objective.md`

Result:

- seed `9450`: braking/lateral/yaw R2 lift after values
  `+0.093007`, `-0.230815`, `-0.004631`;
- seed `9451`: braking/lateral/yaw R2 lift after values
  `+0.059400`, `+0.045079`, `+0.059469`;
- seed `9452`: braking/lateral/yaw R2 lift after values
  `+0.644474`, `-0.207891`, `+0.494708`;
- braking is positive in 3/3 seeds, but lateral is negative in 2/3 and yaw is
  slightly negative once.

Conclusion: M95 fixes the immediate braking instability but creates an
unacceptable target tradeoff. Do not start PPO. M96 should decouple the three
future-envelope targets more strongly, then admit behavior training only if
braking, yaw, and lateral all beat same-frame reset hidden across repeated
seeds.

## 20260521T171652Z m96-per-target-hidden-envelope-objective

- status: `completed`
- kind: `objective_sanity`
- hypothesis: equal per-target contrast can preserve the M95 braking gain
  without the M95 lateral/yaw tradeoff.
- objective settings: `contrast_mode=per_target`,
  `target_loss_weights=1.0 1.0 1.0`.
- diagnostic runs:
  `runs/m96_per_target_balanced_hidden_envelope_seed9460`,
  `runs/m96_per_target_balanced_hidden_envelope_seed9461`,
  `runs/m96_per_target_balanced_hidden_envelope_seed9462`
- artifact: `docs/m96-per-target-hidden-envelope-objective.md`

Result:

- seed `9460`: braking/lateral/yaw R2 lift after values
  `+0.086932`, `-0.040365`, `+0.016726`;
- seed `9461`: braking/lateral/yaw R2 lift after values
  `+0.066797`, `+0.004757`, `+0.075936`;
- seed `9462`: braking/lateral/yaw R2 lift after values
  `+0.079167`, `+0.010814`, `+0.151876`;
- braking and yaw are positive in 3/3 seeds; lateral is positive in 2/3 seeds
  and improves but remains negative in seed `9460`.

Conclusion: M96 is the best no-wheel hidden-envelope objective so far, but it
is still not a strict pass. Do not start PPO. M97 should keep equal per-target
contrast and add a small minimum-lift or lateral floor guard, with rejection if
braking or yaw stability regresses.

## 20260521T172008Z m97-minlift-hidden-envelope-objective

- status: `completed`
- kind: `objective_sanity`
- hypothesis: a small lateral floor can fix the remaining M96 lateral negative
  seed while preserving braking and yaw stability.
- objective settings: `contrast_mode=per_target`,
  `target_loss_weights=1.0 1.0 1.25`.
- diagnostic runs:
  `runs/m97_lateral_floor_hidden_envelope_seed9470`,
  `runs/m97_lateral_floor_hidden_envelope_seed9471`,
  `runs/m97_lateral_floor_hidden_envelope_seed9472`
- artifact: `docs/m97-minlift-hidden-envelope-objective.md`

Result:

- seed `9470`: braking/lateral/yaw R2 lift after values
  `-0.015814`, `+0.070606`, `+0.008445`;
- seed `9471`: braking/lateral/yaw R2 lift after values
  `+0.042498`, `+0.067743`, `+0.114699`;
- seed `9472`: braking/lateral/yaw R2 lift after values
  `+0.290312`, `-0.683934`, `-2.387921`;
- only seed `9471` passes all three after-lift checks.

Conclusion: M97 is negative. Target-weight tuning is not the right next lever.
M96 remains the best objective recipe; M98 should repeat M96 with larger batches
and more held-out samples to separate sample variance from objective weakness.

## 20260521T172325Z m98-larger-batch-per-target-objective

- status: `completed`
- kind: `objective_sanity`
- hypothesis: M96 equal per-target contrast may pass the strict objective gate
  with more rollout samples and lower held-out variance.
- objective settings: same as M96, with `contrast_mode=per_target` and
  `target_loss_weights=1.0 1.0 1.0`.
- data setting: `episodes=60`, `max_samples=1600`, `steps=200`.
- diagnostic runs:
  `runs/m98_larger_batch_per_target_seed9480`,
  `runs/m98_larger_batch_per_target_seed9481`,
  `runs/m98_larger_batch_per_target_seed9482`
- artifact: `docs/m98-larger-batch-per-target-objective.md`

Result:

- seed `9480`: braking/lateral/yaw R2 lift after values
  `+0.285544`, `+0.068964`, `+0.005246`;
- seed `9481`: braking/lateral/yaw R2 lift after values
  `+0.087432`, `+0.066624`, `+0.059191`;
- seed `9482`: braking/lateral/yaw R2 lift after values
  `+0.082257`, `+0.083511`, `+0.064771`;
- all three future-envelope targets have positive after-lift in all three
  repeated seeds.

Conclusion: M98 is the first strict objective-only hidden-envelope pass. It
supports the M96 equal per-target contrast recipe and rejects more target-weight
tuning for now. This is not a driver pass: M99 must benchmark M98 objective
checkpoints against M62 under normal and ablated behavior before any guarded PPO
continuation.

## 20260521T172856Z m99-m98-behavior-retention-gate

- status: `completed`
- kind: `gate`
- hypothesis: M98 objective-only checkpoints may preserve M62 behavior while
  adding better hidden-envelope belief.
- code hardening: `hidden_envelope_optimize.save_checkpoint_like` now writes
  JSON-safe metadata with `to_jsonable`, after a PyTorch `weights_only=True`
  loader failure on `pathlib.Path` metadata.
- focused tests: `tests/test_hidden_envelope_optimize.py`
- benchmark run: `runs/m99_m98_behavior_retention_gate_seed9500`
- artifact: `docs/m99-m98-behavior-retention-gate.md`

Result:

- M62 success: `0.8625`, mean clearance margin: `1.852887`;
- M98 seed9480 success: `0.8625`, margin: `1.853319`;
- M98 seed9481 success: `0.8750`, margin: `1.866000`;
- M98 seed9482 success: `0.8750`, margin: `1.848101`;
- seed9480 reset/zero-current/zero-all ablations do not degrade success
  (`0.8750`), and no-action stays at `0.8625`.

Conclusion: M99 passes behavior retention but fails behavior-level
self-identification. M98 hidden state is predictive, but the actor has not
learned to depend on that belief. M100 should train actor coupling from M98
under strict retention and ablation gates.

## 20260521T173430Z m100-m98-actor-coupling-continuation

- status: `completed`
- kind: `driver_candidate`
- hypothesis: a guarded PPO continuation from M98 can make the actor use the
  learned hidden-envelope belief without losing M62 behavior.
- config: `configs/ppo_m100_m98_actor_coupling_smoke.json`
- training run: `runs/ppo_m100_m98_actor_coupling_smoke_seed4100`
- behavior gate: `runs/m100_m98_actor_coupling_smoke_gate_seed9500`
- hidden probe: `runs/m100_smoke_hidden_envelope_probe_seed9510`
- artifact: `docs/m100-m98-actor-coupling-continuation.md`

Result:

- training loaded M98 init and M62 baseline anchor with strict checkpoint loads;
- short eval termination rate: `0.0`;
- shared 80-seed behavior success:
  M62 `0.8625`, M98 `0.8625`, M100 `0.8625`;
- M100 reset and zero-response success: `0.8750`, so behavior still does not
  depend on recurrent response history;
- same-seed hidden probe weakens relative to M98:
  braking lift `0.358433 -> 0.271200`, lateral `0.682472 -> 0.438872`, yaw
  `-0.014135 -> -0.032174`.

Conclusion: M100 is negative for actor coupling. Do not run a longer PPO version
of this recipe. The next step should be M101: objective-only actor coupling on
fixed batches, with a normal-action anchor and reset-action divergence gate
before another PPO continuation.

## 20260521T174702Z m101-objective-only-actor-coupling

- status: `completed`
- kind: `objective_sanity`
- hypothesis: fixed-batch actor coupling can make the actor use M98's
  hidden-envelope belief more directly than PPO plus a weak action-contrast
  term.
- implementation: `src/autodrift/actor_coupling_optimize.py`
- test: `tests/test_actor_coupling_optimize.py`
- objective runs:
  `runs/m101_actor_coupling_objective_seed9530`,
  `runs/m101_actor_coupling_objective_seed9531`,
  `runs/m101_actor_coupling_objective_seed9532`
- behavior gate: `runs/m101_actor_coupling_behavior_gate_seed9500`
- hidden probe: `runs/m101_actor_coupling_hidden_envelope_probe_seed9510`
- artifact: `docs/m101-objective-only-actor-coupling.md`

Result:

- objective-only actor coupling increases held-out normal-vs-reset action
  distance in all three formal seeds:
  `+0.847957`, `+0.824294`, `+0.730874`;
- behavior retention passes on the shared 80-seed gate:
  M62 `0.8625`, M98 `0.8625`, M101 seeds `0.8625`;
- seed9530 reset and zero-response behavior finally degrade:
  reset success `0.7875`, zero-current/zero-all success `0.7750`;
- no-action-history success remains `0.8625`, so command-history dependence is
  not yet established;
- the hidden-envelope probe regresses on braking and lateral response-hidden
  lift versus M98:
  braking `0.358433 -> -0.411792`, lateral `0.682472 -> -0.148631`, yaw
  `-0.014135 -> 0.160665`.

Conclusion: M101 is the first clear behavior-level recurrent-dependence signal,
but it is not a PPO-admitted driver candidate. The next step should be M102:
retention-aware actor coupling that keeps M101's reset/zero-response degradation
while preserving M98's braking/lateral hidden-envelope belief.

## 20260521T175702Z m102-retention-aware-actor-coupling

- status: `completed`
- kind: `objective_sanity`
- hypothesis: stronger action anchoring or a softer reset-action contrast can
  preserve M98 hidden-envelope belief while keeping M101 behavior dependence.
- conservative objective runs:
  `runs/m102_retention_actor_coupling_seed9550`,
  `runs/m102_retention_actor_coupling_seed9551`,
  `runs/m102_retention_actor_coupling_seed9552`
- conservative behavior gate:
  `runs/m102_retention_actor_coupling_behavior_gate_seed9500`
- conservative hidden probe:
  `runs/m102_retention_actor_coupling_hidden_envelope_probe_seed9510`
- pareto objective runs:
  `runs/m102_pareto_actor_coupling_seed9560`,
  `runs/m102_pareto_actor_coupling_seed9561`,
  `runs/m102_pareto_actor_coupling_seed9562`
- pareto behavior gate:
  `runs/m102_pareto_actor_coupling_behavior_gate_seed9500`
- pareto hidden probe:
  `runs/m102_pareto_actor_coupling_hidden_envelope_probe_seed9510`
- artifact: `docs/m102-retention-aware-actor-coupling.md`

Result:

- conservative action coupling (`anchor=50`, `contrast=0.25`) increases
  fixed-batch action distance in all three seeds while keeping low anchor MSE;
- conservative behavior retention passes, but reset hidden improves success to
  `0.8750`, and zero-response only drops to `0.8500`;
- conservative hidden probe retains M98-style braking/lateral response-hidden
  lift: braking `0.404079`, lateral `0.801162`;
- middle point (`anchor=30`, `contrast=0.5`) also retains hidden-envelope
  belief, but reset and zero-response both improve success to `0.8750`.

Conclusion: M102 is negative for simple retention-aware actor-coupling. Softer
action coupling can retain hidden-envelope belief, but it removes the M101
behavior-dependence signal. The next step should be M103: an outcome-aware
actor-coupling objective that applies recurrent-action pressure only where
normal history is actually better than reset, zero-response, delayed-history,
or wrong-history interventions.

## 20260522T000000Z m104-minimum-observable-input-contract

- status: `planned`
- kind: `design`
- source: `/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml`,
  snapshot saved 2026-05-21 23:50 +0800
- artifact: `docs/m104-minimum-observable-input-contract.md`

Decision:

- deployable actor inputs should be sensor-direct or minimally calibrated/fused;
- minimum observability chain is known commands, actual actuator feedback, raw
  wheel/contact response when available, body inertial response, and
  road/obstacle geometry;
- `slip_ratio`, `slip_angle`, `slip_proxy`, ABS/TCS/ESC flags, tire-force
  labels, `mu`, oracle feasibility, and reference trajectories stay out of the
  actor;
- future wheel work should use raw `Romega_i` and independently fused local
  `v_parallel_i`, not wheel-speed averages or diagnostic ratios.

This is not a result and does not change the active M103 path. It prevents the
historical M81 proxy branch from being mistaken for the final minimum actor
contract.

## 20260521T181755Z m103-outcome-aware-actor-coupling

- status: `completed`
- kind: `objective_sanity`
- implementation:
  `src/autodrift/history_ablation_snippets.py`,
  `src/autodrift/outcome_intervention_optimize.py`
- tests:
  `tests/test_history_ablation_snippets.py`,
  `tests/test_outcome_intervention_optimize.py`
- snippet run: `runs/m103_history_ablation_snippets_m101_smoke_seed9600`
- objective runs:
  `runs/m103_outcome_actor_coupling_m102_seed9610`,
  `runs/m103_outcome_actor_coupling_m102_seed9611`,
  `runs/m103_outcome_actor_coupling_m102_seed9612`
- behavior gate:
  `runs/m103_outcome_actor_coupling_behavior_gate_seed9500`
- hidden probe:
  `runs/m103_outcome_actor_coupling_hidden_envelope_probe_seed9510`
- artifact: `docs/m103-outcome-aware-actor-coupling.md`

Result:

- M103 snippet mining finds `87` accepted outcome-sensitive rows from `180`
  candidates and exports `57` reset-hidden outcome snippets;
- fixed-batch outcome loss from the M102 checkpoint drops from `0.045645` to
  `0.000102` in all three deterministic repeats;
- behavior retention passes: M103 success is `0.8750` versus M62/M98/M101/M102
  at `0.8625`;
- zero-response success drops to `0.8500`, but reset-hidden success stays
  `0.8750`;
- hidden-envelope retention fails on braking and lateral:
  `-0.070796` and `-0.110616` response-hidden-minus-reset R2 lift.

Conclusion: M103 is not a PPO-admitted driver. Outcome-sensitive snippets are
now a useful harness, but fitting them alone does not prove recurrent
self-identification. The next planned step is M105: add a broad behavior or
hidden-envelope retention constraint to the outcome actor-coupling objective.

## 20260521T183134Z m105-retention-constrained-outcome-coupling

- status: `completed`
- kind: `objective_sanity`
- implementation: `src/autodrift/outcome_intervention_optimize.py`
- tests: `tests/test_outcome_intervention_optimize.py`
- objective runs:
  `runs/m105_anchor10_outcome_coupling_smoke_seed9710`,
  `runs/m105_anchor10_outcome_coupling_smoke_seed9711`,
  `runs/m105_anchor10_outcome_coupling_smoke_seed9712`
- behavior gate: `runs/m105_anchor10_behavior_gate_seed9500`
- hidden probe: `runs/m105_anchor10_hidden_envelope_probe_seed9510`
- artifact: `docs/m105-retention-constrained-outcome-coupling.md`

Result:

- added action-anchor constrained outcome optimization:
  `loss = outcome_intervention_loss + coef * action_anchor_mse`;
- actor input contract is unchanged, and the run trains only
  `response_context_fusion` and `actor_mean`;
- all three objective repeats reduce outcome loss from `0.045645` to about
  `0.0027`, with after-anchor MSE near `2.6e-4` to `2.8e-4`;
- behavior gate on seed `9500` retains normal success at `0.8625`, matching
  M62/M102, while reset-hidden drops to `0.8500` and zero-response drops to
  `0.8250`;
- hidden-envelope probe on seed `9510` restores positive
  response-hidden-minus-reset R2 lift: braking `0.211398`, lateral `0.557126`,
  yaw `0.033114`.

Conclusion: M105 is the first M101-M105 qualified positive line with both
behavior-dependence evidence and hidden-envelope-retention evidence on the same
checkpoint. It is not full driver admission yet because only seed `9710` has
completed the full behavior/probe gate. The next pending task is M106: repeat
the gates across `9711`/`9712` and add stronger delayed-history or wrong-history
interventions before any PPO continuation claim.

## 20260521T184051Z m106-formal-retention-constrained-repeat-gates

- status: `completed`
- kind: `gate`
- behavior gate: `runs/m106_m105_repeat_behavior_gate_seed9500`
- fixed probe repeats:
  `runs/m106_m105_9711_hidden_envelope_probe_seed9510`,
  `runs/m106_m105_9712_hidden_envelope_probe_seed9510`
- fresh probe repeats:
  `runs/m106_m105_9710_hidden_envelope_probe_seed9511`,
  `runs/m106_m105_9711_hidden_envelope_probe_seed9511`,
  `runs/m106_m105_9710_hidden_envelope_probe_seed9512`,
  `runs/m106_m105_9712_hidden_envelope_probe_seed9512`
- artifact: `docs/m106-formal-retention-constrained-repeat-gates.md`

Result:

- behavior dependence repeats: `9711` and `9712` both keep normal success
  `0.8625` and reset-hidden drops to `0.8500`;
- zero-response degradation repeats: `9711` drops to `0.8375`, `9712` drops to
  `0.8250`;
- no-action-history remains behavior-neutral;
- strict margin retention is borderline and fails for `9712`:
  `1.851823 < 1.852887`;
- on the original probe seed `9510`, hidden-envelope lift remains positive for
  `9711` and `9712`;
- on fresh probe seeds `9511` and `9512`, lateral/yaw or braking lift becomes
  negative across M105 checkpoints.

Conclusion: M106 rejects formal admission of M105 for PPO continuation. The
behavior signal is real enough to keep the line alive, but the hidden-envelope
proof is seed-fragile. The next pending step is M107: replace single-seed
hidden-envelope admission with a multi-seed aggregate gate before another
objective or PPO run.

## 20260521T184818Z m107-multiseed-hidden-envelope-gate

- status: `completed`
- kind: `gate`
- implementation: `src/autodrift/hidden_envelope_multiseed_gate.py`
- tests: `tests/test_hidden_envelope_multiseed_gate.py`
- run: `runs/m107_multiseed_hidden_envelope_gate_seed9510`
- artifact: `docs/m107-multiseed-hidden-envelope-gate.md`

Result:

- M107 evaluates M105 checkpoints `9710`, `9711`, and `9712` across probe seeds
  `9510`, `9511`, and `9512`;
- no checkpoint-target pair passes the strict aggregate gate;
- braking mean lift is positive because seed `9511` is strongly positive, but
  worst-case braking lift is negative for all checkpoints;
- lateral mean lift is negative for all checkpoints: about `-0.79`, `-0.80`,
  and `-0.84`;
- yaw mean lift is negative for all checkpoints: about `-0.87`, `-0.85`, and
  `-0.88`;
- lateral/yaw pass fraction is only `0.3333` for all checkpoints.

Conclusion: M107 rejects M105 under multi-seed hidden-envelope admission. The
next task is M108: run the same aggregate gate on M98/M102/M105/M62 to
distinguish model-specific hidden-belief damage from a generally unstable
probe surface.

## 20260521T185245Z m108-baseline-multiseed-hidden-envelope-audit

- status: `completed`
- kind: `gate`
- run: `runs/m108_baseline_multiseed_hidden_envelope_gate_seed9510`
- artifact: `docs/m108-baseline-multiseed-hidden-envelope-audit.md`

Result:

- M62, M98, M102, and M105 all fail the strict multi-seed hidden-envelope gate;
- M62 lateral mean lift is only `-0.073465`, but yaw pass fraction is `0.0`;
- M98 and M102 lateral/yaw mean lifts are strongly negative;
- M105 is not uniquely worse: it improves lateral mean relative to M98/M102 but
  still fails the aggregate gate;
- braking mean lift is positive for all checkpoints, but every checkpoint has
  negative worst-case braking lift.

Conclusion: the current hidden-envelope proof surface is not reliable enough
for admission decisions. The next pending step is M109: audit target
distributions, train/test split variance, and sample-count sensitivity before
training another hidden-retention objective.

## 20260521T190009Z m109-hidden-envelope-probe-reliability-audit

- status: `completed`
- kind: `gate`
- implementation: `src/autodrift/hidden_envelope_reliability_audit.py`
- tests: `tests/test_hidden_envelope_reliability_audit.py`
- run: `runs/m109_hidden_envelope_reliability_audit_seed9510`
- artifact: `docs/m109-hidden-envelope-probe-reliability-audit.md`

Result:

- target means are stable at `800` samples across probe seeds; yaw target mean
  range is only about `0.007` for M62/M102/M105;
- increasing sample limit from `400` to `800` reduces lift variance, but the
  response-hidden-minus-reset lift remains negative for M62/M102/M105 on most
  targets;
- at `800` samples, M105 split-averaged lift is braking `-0.138505`, lateral
  `-0.459649`, yaw `-0.457534`;
- current-response features often beat both carried response hidden and reset
  hidden on mean test R2;
- therefore the current recurrent hidden is not a stable future-envelope belief
  and does not reliably add information beyond the current response frame.

Conclusion: M109 rejects another same-style hidden-retention objective and
points to M110: a current-response anchored objective/gate where response
hidden must beat both reset hidden and current response under repeated split
and multi-seed evaluation.

## 20260521T191032Z m110-current-response-anchored-hidden-envelope-objective

- status: `completed`
- kind: `objective_sanity`
- implementation:
  `src/autodrift/hidden_envelope_optimize.py`,
  `src/autodrift/hidden_envelope_reliability_audit.py`
- tests:
  `tests/test_hidden_envelope_optimize.py`,
  `tests/test_hidden_envelope_reliability_audit.py`
- objective runs:
  `runs/m110_current_response_anchor_objective_seed9730`,
  `runs/m110_current_response_anchor_broad_objective_seed9700`
- reliability gates:
  `runs/m110_current_response_anchor_reliability_seed9510`,
  `runs/m110_broad_current_response_anchor_reliability_seed9510`
- artifact: `docs/m110-current-response-anchored-hidden-envelope-objective.md`

Result:

- added a current-response baseline head and contrast loss to the hidden
  envelope objective;
- added current-response lift aggregation to the reliability audit;
- first variant makes hidden beat current response on its own objective batch,
  but fails against reset on braking/lateral;
- broad variant beats both reset and current response internally on all targets;
- both variants fail the external repeated split / multi-seed reliability gate;
- broad variant external hidden-current lift remains negative:
  braking `-0.518338`, lateral `-0.653002`, yaw `-0.730686`.

Conclusion: M110 rejects same-style current-response anchored objective-only
tuning. The next pending task is M111: construct a matched-current-response
ambiguity proof surface where current response is insufficient by construction.

## 20260521T192617Z m111-matched-current-response-ambiguity-audit

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/matched_current_response_ambiguity.py`
- tests:
  `tests/test_matched_current_response_ambiguity.py`
- smoke run:
  `runs/m111_smoke_matched_current_response_ambiguity_seed9510`
- formal run:
  `runs/m111_matched_current_response_ambiguity_seed9510`
- artifact: `docs/m111-matched-current-response-ambiguity-audit.md`

Result:

- formal audit used M62, M102, and M105 checkpoints with probe seeds
  `9510,9511`;
- candidate pair count: `89343`;
- accepted matched-current-response pair count: `702`;
- accepted by target: braking `303`, yaw `184`, lateral `215`;
- aggregate target z-delta means: braking `1.385`, yaw `1.819`,
  lateral `2.286`;
- carried response hidden is not a stable solution to the ambiguity:
  response-hidden distance correlations with target delta are negative on all
  aggregate targets.

Conclusion: M111 finds the proof surface that M110 was missing, but current
checkpoints do not encode it reliably in recurrent hidden state. The next task
is M112: replay or construct normal/reset/delayed/zero-action/wrong-history
interventions on the M111 matched surface and gate action/outcome degradation,
not only feature-distance separation.

## 20260521T193337Z m112-matched-history-intervention-gate

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/matched_history_intervention_gate.py`
- tests:
  `tests/test_matched_history_intervention_gate.py`
- run:
  `runs/m112_matched_history_intervention_gate_seed9510`
- artifact: `docs/m112-matched-history-intervention-gate.md`

Result:

- consumed M111 `matched_pairs.csv`;
- reconstructed M62/M102/M105 recurrent snapshots deterministically;
- input pairs after per-checkpoint/target cap: `639`;
- intervention rows: `3195`;
- reset-hidden mean action distance: `0.517`, above-threshold fraction `0.932`;
- zero-current-response mean action distance: `0.124`, above-threshold fraction
  `0.985`;
- delayed-history mean action distance: `0.097`, above-threshold fraction
  `0.892`;
- wrong matched-history mean action distance: `0.066`, above-threshold fraction
  `0.771`;
- wrong matched-history action is closer to the matched-right normal action in
  about `0.733` of rows.

Conclusion: M112 is a positive action-level history-sensitivity gate. It does
not prove driver-level self-identification yet because action changes may not
improve rollout outcome. The next pending task is M113: replay these
interventions through continuations and measure clearance, collision, success,
and mitigation.

## 20260521T193904Z m113-matched-history-outcome-gate

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/matched_history_outcome_gate.py`
- tests:
  `tests/test_matched_history_outcome_gate.py`
- run:
  `runs/m113_matched_history_outcome_gate_seed9510`
- artifact: `docs/m113-matched-history-outcome-gate.md`

Result:

- consumed M111 matched pairs with a cap of `40` pairs per checkpoint/target;
- input pairs: `360`;
- outcome rows: `2160`;
- no intervention variant produced success drops;
- aggregate normal-better fraction:
  - reset hidden: `0.158`;
  - zero-current-response: `0.244`;
  - delayed-history: `0.006`;
  - wrong matched-history: `0.000`;
  - zero-action-history: `0.017`;
- aggregate mean margin gap:
  - reset hidden: `0.01098`;
  - zero-current-response: `0.01113`;
  - wrong matched-history: `0.00045`.

Conclusion: M113 rejects M111/M112 pairs as an outcome-weighted training
surface. The pairs are useful for action diagnostics, but they are not
outcome-critical enough. The next pending task is M114: mine or construct a
near-boundary matched-history surface where normal history has measurable
clearance or success advantage.

## 20260521T194345Z m114-near-boundary-matched-history-outcome-surface

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/near_boundary_outcome_surface.py`
- tests:
  `tests/test_near_boundary_outcome_surface.py`
- run:
  `runs/m114_near_boundary_outcome_surface_seed9510`
- artifact: `docs/m114-near-boundary-matched-history-outcome-surface.md`

Result:

- consumed M113 `outcome_interventions.csv`;
- filter: `normal_margin <= 0.20`, `margin_gap >= 0.02`,
  `normal_success == true`;
- accepted rows: `119`;
- unique pairs: `51`;
- aggregate normal margin mean: `0.186675`;
- aggregate margin gap mean: `0.029944`;
- accepted variant counts:
  - `reset_hidden`: `39`;
  - `zero_current_response`: `78`;
  - `delayed_history`: `2`;
  - `wrong_matched_history`: `0`;
- success drop count: `0`.

Conclusion: M114 finds a usable near-boundary surface for reset/zeroed-history
outcome pressure, but it still does not support the stronger wrong-history
self-identification claim. The next pending task is M115: relocate or tighten
obstacle geometry around matched pairs until wrong matched history creates
clearance, collision, or mitigation degradation while normal history remains
valid.

## 20260521T195500Z mhtml-input-sensor-contract-extract

- status: `completed`
- kind: `documentation`
- source: `/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml`
- artifact: `docs/mhtml-input-sensor-contract-2026-05-21.md`

Persisted the latest visible 5.5pro input discussion as a durable input
contract. The important decision is that the actor should see sensor-direct or
minimally fused closed-loop evidence, not engineered diagnostics.

Captured contract:

- actor branch should keep commands, actual actuator states, wheel/contact raw
  response, body inertial response, and scene geometry separated;
- `slip_ratio`, `slip_angle`, ABS/TCS/ESC flags, per-wheel pressure split,
  tire-force labels, `mu`, oracle feasibility, and reference trajectories stay
  out of actor input;
- future strict wheel branch is four-wheel `Romega_i` plus independent local
  `v_parallel_i`, not center speed and not wheel-speed average;
- `v_perp_i`, steering torque/EPS current, roll/pitch/vertical acceleration,
  and suspension travel are optional admission-gated sensors;
- input profile comparisons must use supervised probes first, then a frozen
  PPO recipe, matched wrong-history counterfactuals, and optional-sensor
  admission gates.

Current implication: M91/M92 still reject the current single-track wheel
profiles as primary PPO inputs. That negative result does not reject the future
four-wheel sensor contract. The active actor input remains the clean no-wheel
human-view branch until a richer wheel model or matched corpus justifies
reopening wheel inputs.

## 20260521T195936Z m115-wrong-history-boundary-relocation-surface

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/wrong_history_boundary_relocation_surface.py`
- tests:
  `tests/test_wrong_history_boundary_relocation_surface.py`
- run:
  `runs/m115_wrong_history_boundary_relocation_surface_seed9510`
- artifact: `docs/m115-wrong-history-boundary-relocation-surface.md`

M115 targets the M114 blocker directly: passive M113 continuations had no
`wrong_matched_history` outcome-critical rows. The new harness reconstructs the
M113 snapshots, tightens obstacle half-width at the snapshot-level boundary,
and replays normal, wrong-history, reset, zero-current, zero-action, and delayed
variants.

Formal result:

- candidate rows: `90`;
- relocation replay rows: `3045`;
- accepted wrong-history rows: `12`;
- accepted wrong-history source pairs: `11`;
- wrong-history success drops: `12`;
- accepted reset rows: `275`;
- accepted zero-current rows: `332`;
- M62 accepted wrong-history rows: `0`;
- M102 accepted wrong-history rows: `6`;
- M105 accepted wrong-history rows: `6`.

Interpretation: M115 is a positive construction gate. It proves that a
boundary-tightened matched surface exists where normal history succeeds and
wrong matched history collides. It is not yet broad self-ID evidence: accepted
normal margins are only about `0.006 m`, wrong-history gaps are below
`0.009 m`, and the signal is absent without relocation.

Conclusion: proceed to M116 robustness before training. M116 should split or
repeat the M115 surface, deduplicate source pairs, and verify that the
wrong-history success-drop signal survives held-out geometry/target-margin
choices.

## 20260521T200538Z m116-boundary-wrong-history-surface-robustness-gate

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/boundary_wrong_history_surface_robustness.py`
- tests:
  `tests/test_boundary_wrong_history_surface_robustness.py`
- run:
  `runs/m116_boundary_wrong_history_robustness_seed9510`
- artifact: `docs/m116-boundary-wrong-history-surface-robustness-gate.md`

M116 audits the M115 boundary-tightened surface before any objective training.
It treats physical source pair diversity as:

```text
(left_seed, left_step, right_seed, right_step)
```

Result:

- accepted wrong-history rows: `12`;
- accepted physical source pairs: `3`;
- accepted left steps: `3`;
- accepted checkpoints: `2`;
- accepted target groups: `3`;
- accepted normal-margin buckets: `1`;
- success-drop fraction: `1.0`;
- max rows from one physical pair: `6`;
- max rows per physical pair fraction: `0.5`;
- M62 accepted wrong-history rows: `0`;
- accepted reset rows: `275`;
- accepted zero-current rows: `332`;
- decision: `reject_duplicate_dominated_boundary_surface`.

Failed gates:

- physical source pairs: `3 < 6`;
- distinct left steps: `3 < 5`;
- normal-margin buckets: `1 < 2`;
- max rows per physical pair fraction: `0.5 > 0.4`.

Conclusion: do not train a boundary-aware wrong-history objective yet. M115 is
a valid construction proof but not a robust corpus. The next pending task is
M117: broaden the source/geometry search until wrong-history success drops pass
M116-style diversity gates.

## 20260521T201729Z m117-source-diverse-wrong-history-boundary-mining

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/wrong_history_boundary_relocation_surface.py`
- tests:
  `tests/test_wrong_history_boundary_relocation_surface.py`
- runs:
  - `runs/m117_source_diverse_source_only_seed9510`
  - `runs/m117_source_diverse_source_only_robustness_seed9510`
  - `runs/m117_source_diverse_relative_lateral_seed9510`
  - `runs/m117_source_diverse_relative_lateral_robustness_seed9510`
  - `runs/m117_source_diverse_relative_longitudinal_seed9510`
  - `runs/m117_source_diverse_relative_longitudinal_robustness_seed9510`
  - diagnostic: `runs/m117_source_diverse_lateral_offsets_seed9510`
- artifact: `docs/m117-source-diverse-wrong-history-boundary-mining.md`

M117 tests whether M116 failed only because M115's candidate filtering or
geometry sweep was too narrow. It adds relative obstacle offsets:

```text
--body-lateral-offsets
--body-longitudinal-offsets
```

Results:

| Variant | Candidate rows | Replay rows | Accepted wrong rows | Physical pairs | Margin buckets | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| source-only all candidates | 360 | 2383 | 12 | 3 | 1 | reject duplicate-dominated |
| relative lateral offsets | 360 | 11915 | 12 | 3 | 1 | reject duplicate-dominated |
| relative longitudinal offsets | 360 | 11628 | 12 | 3 | 1 | reject duplicate-dominated |
| absolute lateral diagnostic | 360 | 11915 | 0 | 0 | 0 | no surface |

Conclusion: the current M113/M115 surface is exhausted. More boundary tuning
around those rows does not produce a source-diverse wrong-history corpus. The
next pending task is M118: mine a fresh source-diverse matched-current-response
corpus before repeating action/outcome/boundary gates.

## 20260521T202236Z m118-fresh-source-diverse-matched-current-corpus

- status: `completed`
- kind: `gate`
- implementation:
  `src/autodrift/matched_current_response_ambiguity.py`
- tests:
  `tests/test_matched_current_response_ambiguity.py`
- runs:
  - `runs/m118_source_diverse_matched_current_seed9510`
  - `runs/m118_source_diverse_action_intervention_seed9510`
- artifact: `docs/m118-fresh-source-diverse-matched-current-corpus.md`

M118 adds `--max-pairs-per-physical-pair` to matched-current-response mining.
The new physical source key is:

```text
(left_seed, left_step, right_seed, right_step)
```

Fresh corpus result:

- candidate pairs: `89343`;
- accepted pairs: `471`;
- accepted physical pairs: `155`;
- max rows per physical pair: `6`;
- accepted by target:
  - braking: `303` rows, `107` physical pairs;
  - lateral: `97` rows, `31` physical pairs;
  - yaw: `71` rows, `18` physical pairs.

Action-level wrong-history result on the fresh corpus:

- wrong-history rows: `408`;
- physical pairs: `140`;
- mean action distance: `0.066306`;
- above-threshold fraction: `0.772059`;
- closer-to-right fraction: `0.737745`.

Conclusion: M118 is positive. It restores source diversity while preserving
action-level history sensitivity. The next pending task is M119: run
continuation outcomes and boundary robustness gates on the fresh corpus.

## 20260521T203143Z m119-fresh-corpus-outcome-boundary-gates

- status: `completed`
- kind: `gate`
- implementation:
  - `src/autodrift/matched_history_outcome_gate.py`
  - `src/autodrift/wrong_history_boundary_relocation_surface.py`
  - `src/autodrift/boundary_wrong_history_surface_robustness.py`
- runs:
  - `runs/m119_fresh_corpus_outcome_gate_seed9510`
  - `runs/m119_fresh_corpus_boundary_relocation_seed9510`
  - `runs/m119_fresh_corpus_boundary_robustness_seed9510`
  - `runs/m119_fresh_corpus_boundary_all_candidates_seed9510`
  - `runs/m119_fresh_corpus_boundary_all_candidates_robustness_seed9510`
- artifact: `docs/m119-fresh-corpus-outcome-boundary-gates.md`

M119 repeats outcome and boundary gates on the M118 source-diverse corpus.

Passive outcome result:

- input pairs: `408`;
- outcome rows: `2448`;
- wrong-history physical pairs: `140`;
- wrong-history success drops: `0`;
- wrong-history normal-better fraction: `0.000`;
- wrong-history mean margin gap: `0.000165`;
- reset-hidden mean margin gap: `0.009007`;
- zero-current-response mean margin gap: `0.009643`.

Boundary tightening result:

| Pass | Candidates | Rows | Accepted wrong rows | Accepted wrong pairs | Surface |
| --- | ---: | ---: | ---: | ---: | --- |
| capped | `171` | `5630` | `6` | `4` | false |
| all-candidate | `315` | `8720` | `6` | `4` | false |

All-candidate robustness decision:

```text
reject_duplicate_dominated_boundary_surface
```

Failed gates:

- accepted wrong rows: `6 < 10`;
- physical pairs: `3 < 6`;
- left steps: `3 < 5`;
- target groups: `2 < 3`;
- margin buckets: `1 < 2`.

Conclusion: M119 is negative. M118's action-level source diversity does not
become outcome-level source diversity. Accepted wrong-history boundary rows
still collapse to the old `9530/9540` physical pairs. The next pending task is
M120: mine outcome-critical wrong-history candidates directly with
source-diversity constraints.

## 20260521T205537Z m120-outcome-critical-source-diverse-miner

- status: `completed`
- kind: `gate`
- implementation:
  - `src/autodrift/outcome_sensitive_corpus.py`
  - `src/autodrift/snapshot_bank_relocation.py`
- tests:
  - `tests/test_outcome_sensitive_corpus.py`
  - `tests/test_snapshot_bank_relocation.py`
- runs:
  - `runs/m120_active_probe_snapshot_bank_m105_strict_exportclean_10ep_seed9720`
  - `runs/m120_active_probe_snapshot_bank_m105_relaxed_exportclean_10ep_seed9720`
  - `runs/m120_active_probe_snapshot_bank_m102_strict_exportclean_10ep_seed9720`
  - `runs/m120_active_probe_snapshot_bank_m62_strict_exportclean_10ep_seed9720`
- artifact: `docs/m120-outcome-critical-source-diverse-miner.md`

M120 adds direct outcome-miner source-diverse selection:

```text
--max-selected-per-physical-pair
--max-selected-per-seed
```

It also adds clean snippet export:

```text
--export-only-accepted-outcomes
```

This prevents non-visible rows with margin gaps from entering
`outcome_intervention_snippets.npz`.

Focused validation:

```text
17 passed
```

Strict context results:

| Policy | Candidates | Visible | Accepted | Selected physical pairs | Snippets |
| --- | ---: | ---: | ---: | ---: | ---: |
| M105 | `507` | `24` | `0` | `0` | `0` |
| M102 | `507` | `24` | `0` | `0` | `0` |
| M62 control | `507` | `24` | `0` | `0` | `0` |

Relaxed M105 diagnostic with `max_context_distance=0.30`:

- candidates: `507`;
- visible matches: `408`;
- accepted outcome rows: `7`;
- selected rows: `3`;
- selected physical pairs: `3`;
- selected seeds: `2`;
- clean accepted-only snippets: `7`;
- largest selected margin gap: `0.023294`.

Conclusion: M120 is a useful infrastructure pass but a negative strict gate.
The relaxed rows show margin-gap signal exists, but they are blocked by context
distance (`~0.25-0.29`) and are too concentrated. The next pending task is M121:
make the direct outcome miner context-aligned instead of relaxing the context
contract.

## 20260521T211032Z m121-context-aligned-outcome-critical-miner

M121 tested whether the M120 relaxed rows failed strict context because the
obstacle geometry was not aligned, or because another context field was acting
as a response proxy.

Implementation:

- `visible_observation_distances(...)` now breaks context distance into road,
  obstacle, obstacle geometry, and obstacle relative-velocity components;
- `tests/test_matched_action_corpus.py` covers the new diagnostic components;
- `configs/m121_human_view_zero_obstacle_relvel.json` keeps the M24 human-view
  profile but sets `obstacle_relative_velocity_mode` to `zero`.

Diagnostic result:

- M105 relaxed context run still finds `7` accepted rows, `3` selected physical
  pairs, and `2` seeds;
- accepted rows have zero obstacle geometry distance;
- their context mismatch is almost entirely obstacle relative velocity
  (`~0.245-0.266`), with road distance only `~0.027`.

Strict zero-relvel result:

- M105 10ep: `7` accepted rows, `3` selected physical pairs, `2` seeds;
- M102 10ep: `5` accepted rows, `2` selected physical pairs, `2` seeds;
- M62 10ep control: `0` accepted rows;
- M105 30ep: `9` accepted rows, `4` selected physical pairs, `3` seeds, max
  snippet margin gap `0.027255`.

Conclusion: zero obstacle relative velocity is the cleaner strict
self-identification context profile. It restores strict accepted rows without
admitting the M62 control, so the M120 context issue was real and actionable.
However, the selected surface is still below the diversity gate of `6` physical
pairs and `5` source decision steps. M121 is therefore a diagnostic positive but
a training-surface rejection. Do not train an objective from these snippets yet.

## 20260521T212526Z m122-zero-relvel-source-diverse-outcome-surface

M122 repeats the M121 zero-relvel strict miner at a broader 60-episode scale
without relaxing the response or context thresholds.

M105 run:

- run: `runs/m122_zero_relvel_m105_strict_60ep_seed9720`;
- candidates: `3134`;
- visible matches: `1680`;
- accepted outcome rows: `12`;
- success-drop pairs: `9`;
- selected rows: `6`;
- selected physical pairs: `6`;
- selected seeds: `5`;
- accepted source steps: `8`;
- accepted-only intervention snippets: `11`;
- max snippet margin gap: `0.027255`.

M62 control:

- run: `runs/m122_zero_relvel_m62_strict_60ep_seed9720`;
- candidates: `3134`;
- visible matches: `1608`;
- accepted outcome rows: `0`;
- selected rows: `0`;
- snippets: `0`.

Conclusion: M122 is a positive corpus gate. The M105 zero-relvel strict surface
now crosses the source-diversity target, while the M62 control remains clean
under identical broad settings. This admits the M122 corpus for the next
objective-sanity experiment only. It does not admit a driver checkpoint, and it
does not justify PPO continuation before objective/retention gates.

## 20260521T213249Z m123-m122-zero-relvel-objective-sanity

M123 optimizes the admitted M122 zero-relvel snippets from the M105 checkpoint
with the same action-anchor style used in M105.

Objective repeats:

| seed | before loss | after loss | improvement | after anchor MSE |
| ---: | ---: | ---: | ---: | ---: |
| 9810 | 0.086424 | 0.055829 | 0.030595 | 0.000744 |
| 9811 | 0.086424 | 0.054460 | 0.031964 | 0.000826 |
| 9812 | 0.086424 | 0.056457 | 0.029967 | 0.000763 |

Behavior gate on `configs/m121_human_view_zero_obstacle_relvel.json`:

- M105 success: `0.8625`, mean margin `1.859915`;
- M123 9810/9811/9812 success: all `0.8625`;
- M123 9811 reset success: `0.8500`;
- M123 9811 zero-current/zero-all success: `0.8000`;
- M123 9811 no-action success: `0.8625`.

Hidden-envelope probe comparison, M105 versus M123 9811:

| target | M105 hidden-reset R2 | M123 hidden-reset R2 |
| --- | ---: | ---: |
| braking | -0.259482 | -0.193512 |
| lateral | 0.368120 | 0.442902 |
| yaw | 0.133647 | 0.031559 |

Conclusion: M123 is a qualified objective-sanity positive. The M122 snippets
are trainable, behavior retention passes on the zero-relvel gate, and
zero-response ablation degrades success. It is not a driver/PPO admission:
yaw hidden-envelope lift regresses, braking hidden-reset lift remains negative,
and no-action history is still neutral. The next pending task is M124:
retention-calibrate the M122 objective instead of starting PPO.

## 20260521T213842Z m124-retention-calibrated-zero-relvel-objective

M124 tests smaller M122 objective updates after M123's yaw hidden-envelope
regression.

Objective sweep:

| run | after loss | improvement | after anchor MSE |
| --- | ---: | ---: | ---: |
| s80 lr5e-5 anchor20 seed9820 | 0.081277 | 0.005147 | 0.000055 |
| s120 lr5e-5 anchor10 seed9821 | 0.072802 | 0.013622 | 0.000368 |
| s120 lr5e-5 anchor10 seed9822 | 0.073205 | 0.013219 | 0.000328 |
| s120 lr5e-5 anchor10 seed9823 | 0.073274 | 0.013150 | 0.000336 |

Hidden-envelope lift, response hidden minus reset:

| policy | braking | lateral | yaw |
| --- | ---: | ---: | ---: |
| M105 | -0.259482 | 0.368120 | 0.133647 |
| M123 9811 | -0.193512 | 0.442902 | 0.031559 |
| M124 9821 | -0.212614 | 0.543924 | 0.115071 |
| M124 9822 | -0.231874 | 0.554479 | 0.119341 |
| M124 9823 | -0.262513 | 0.534689 | 0.114265 |

Behavior:

- M124 9821/9822/9823 all retain `0.8625` success on the zero-relvel behavior
  gate;
- M124 9821 reset success is `0.8500`;
- M124 9821 zero-current/zero-all success is `0.8000`;
- no-action history remains neutral at `0.8625`.

Conclusion: M124 is the best current objective candidate. The calibrated update
keeps enough M122 loss improvement, preserves normal behavior, keeps the
zero-response behavior gap, and avoids the M123 yaw collapse. It is still not a
driver or PPO admission: braking hidden-reset lift is weak, no-action history is
neutral, and the evaluation still needs fresh behavior/probe seeds. The next
task is M125 formal repeat gate.

## 20260521T214240Z m125-formal-m124-repeat-gate

M125 repeats M124 on fresh behavior and hidden-envelope seeds before any PPO
continuation.

Behavior repeats:

- seed `9501`: M105 success `0.8625`, M124 9821/9822/9823 all `0.8625`;
- seed `9501`: M124 9821 reset `0.8500`, zero-current/zero-all `0.8000`,
  no-action `0.8625`;
- seed `9502`: M105 success `0.8625`, M124 9821/9822/9823 all `0.8625`;
- seed `9502`: M124 9821 reset `0.8500`, zero-current/zero-all `0.8000`,
  no-action `0.8625`.

Hidden-envelope repeats, response-hidden minus reset R2:

| policy/probe seed | braking | lateral | yaw |
| --- | ---: | ---: | ---: |
| M105 9510 | -0.259482 | 0.368120 | 0.133647 |
| M124 9510 | -0.212614 | 0.543924 | 0.115071 |
| M105 9511 | 25.655085 | -3.663584 | -0.482697 |
| M124 9511 | 14.011373 | -2.982733 | -0.570959 |
| M105 9512 | -0.762989 | -0.353693 | -1.952766 |
| M124 9512 | -1.694324 | -0.303982 | -2.534112 |

Conclusion: reject PPO/continuation admission. M124 behavior retention and
zero-response degradation repeat, but yaw/lateral hidden-envelope lift fails
fresh probe seeds, no-action history remains neutral, and the probe surface is
still seed fragile. The next task is M126: audit or rebuild the zero-relvel
belief proof surface instead of tuning PPO.

## 20260521T215134Z m126-zero-relvel-belief-proof-surface-audit

M126 audits the zero-relvel belief proof surface after M125 rejects PPO
admission.

Hidden-envelope reliability audit:

- run: `runs/m126_zero_relvel_hidden_envelope_reliability_audit_seed9510`;
- checkpoints: M105 9710 and M124 9821;
- probe seeds: `9510,9511,9512`;
- split seeds: `9610-9614`;
- sample limits: `400,800`;
- result: `passed=False`.

At `800` samples, target means are stable across probe seeds:

- M105 target mean ranges: braking `0.021480`, lateral `0.040924`, yaw
  `0.006224`;
- M124 target mean ranges: braking `0.022244`, lateral `0.041717`, yaw
  `0.006415`.

But aggregate response-hidden minus reset-hidden lift fails:

| checkpoint | braking mean | lateral mean | yaw mean |
| --- | ---: | ---: | ---: |
| M105 | -0.202113 | -0.336667 | -0.946768 |
| M124 | -0.272462 | -0.305144 | -0.924079 |

Current-response mean R2 is stronger than response hidden for all targets:

| checkpoint | target | current response | response hidden |
| --- | --- | ---: | ---: |
| M105 | braking | 0.3050 | -0.0831 |
| M105 | lateral | 0.0743 | -0.2867 |
| M105 | yaw | 0.2676 | -0.9126 |
| M124 | braking | 0.3030 | -0.1464 |
| M124 | lateral | 0.0669 | -0.3010 |
| M124 | yaw | 0.2773 | -0.8823 |

Outcome-critical wrong-history check:

- run: `runs/m126_zero_relvel_m124_strict_60ep_seed9720`;
- candidates: `3134`;
- accepted outcome rows: `15`;
- success-drop pairs: `12`;
- selected rows: `7`;
- selected physical pairs: `7`;
- selected seeds: `6`;
- accepted-only snippets: `14`;
- max snippet margin gap: `0.046191`;
- source side: all exported snippets are perturbed-source.

Conclusion: hidden-envelope R2 is not a reliable primary admission gate for the
zero-relvel line. Target means are stable, but response hidden loses to reset
and current-response baselines. The stronger proof surface is strict
outcome-critical wrong-history degradation. The next pending task is M127:
formalize an outcome-centric self-ID proof gate with repeat miners and controls.

## 20260521T221617Z m127-outcome-centric-self-id-proof-gate

M127 formalizes the strict zero-relvel wrong-history outcome surface as the
current self-identification proof gate. It repeats the M124 miner on fresh seeds
and compares against matching M62 controls.

M124 repeat results:

| Run | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| seed 9720 | 15 | 12 | 7 | 6 | 14 | 0.046191 |
| seed 9820 | 25 | 14 | 10 | 8 | 24 | 0.035959 |
| seed 9840 | 25 | 11 | 8 | 7 | 24 | 0.035959 |

M62 controls:

| Run | Accepted rows | Success-drop pairs | Selected pairs | Snippets |
| --- | ---: | ---: | ---: | ---: |
| seed 9720 | 0 | 0 | 0 | 0 |
| seed 9820 | 0 | 2 | 0 | 0 |
| seed 9840 | 0 | 3 | 0 | 0 |

Decision: admit the strict zero-relvel outcome-critical wrong-history proof
surface for the next stage. This is not driver success and not PPO admission.
The important positive signal is repeated outcome degradation under wrong
history while M62 exports zero snippets. The important limitation is source-side
coverage: all exported snippets are perturbed-source rows. No-action history
also remains neutral from M125, so M127 proves the wrong-history outcome surface
rather than every history channel.

The next task is M128: build a combined accepted-only M127 outcome snippet corpus
with source metadata and row-count checks before testing an outcome-centric
objective.

## 20260521T222320Z m128-combined-outcome-snippet-corpus

M128 builds the combined accepted-only corpus required before the next
outcome-centric objective sanity run.

Command:

```text
PYTHONPATH=src python -m autodrift.outcome_snippet_corpus \
  --input-run runs/m126_zero_relvel_m124_strict_60ep_seed9720 \
  --input-run runs/m127_zero_relvel_m124_strict_60ep_seed9820 \
  --input-run runs/m127_zero_relvel_m124_strict_60ep_seed9840 \
  --deduplicate \
  --run-dir runs/m128_combined_outcome_snippet_corpus
```

Result:

| Metric | Value |
| --- | ---: |
| Input runs | 3 |
| Input rows | 62 |
| Output rows | 44 |
| Duplicate rows removed | 18 |
| Unique seeds | 13 |
| Weight sum | 0.419241 |

The combined corpus loads as `44` snippets with shapes `(44, 72)`, `(44, 128)`,
`(44, 128)`, `(44, 3)`, and `(44,)`. Source-side coverage is still
`{'perturbed': 44}`.

Decision: M128 passes as corpus infrastructure. The next pending task is M129:
test a retention-anchored outcome objective on
`runs/m128_combined_outcome_snippet_corpus/outcome_intervention_snippets.npz`
before any PPO continuation.

## 20260521T222925Z m129-combined-outcome-objective-sanity

M129 tests a retention-anchored objective on the deduplicated M128 corpus.

Objective repeats:

| Run | Before loss | After loss | Improvement | After anchor MSE |
| --- | ---: | ---: | ---: | ---: |
| seed 9830 | 0.281314 | 0.171088 | 0.110226 | 0.002512 |
| seed 9831 | 0.281314 | 0.175752 | 0.105563 | 0.002225 |
| seed 9832 | 0.281314 | 0.178909 | 0.102405 | 0.002170 |

Behavior gate summary:

- seed `9500`: M124 and M129 normal policies all have success `0.8625`;
- seed `9501`: M124 and M129 9830 both have success `0.8625`;
- M129 9830 reset success is `0.8375` on both behavior seeds;
- M129 9830 zero-current and zero-all success are `0.8000` on both behavior
  seeds;
- M129 9830 no-action remains `0.8625`.

Decision: positive objective sanity only. M129 9830 is admitted to a formal
repeat gate because the combined objective improves repeatably and behavior
retention holds. It is not admitted to PPO: no-action history remains neutral,
the source surface is still perturbed-only, and the wrong-history proof surface
must repeat after the objective update. The next pending task is M130.

## 20260521T223730Z m130-combined-outcome-formal-repeat-gate

M130 tests whether M129 is PPO-ready. It is not.

Behavior repeat on seed `9502`:

- M124 success `0.8625`, clearance mean `1.849902`;
- M129 success `0.8625`, clearance mean `1.843562`;
- M129 reset success `0.8375`;
- M129 zero-current/zero-all success `0.8000`;
- M129 no-action success `0.8625`.

Strict outcome-surface repeat:

| Run | Accepted rows | Selected pairs | Selected seeds | Snippets |
| --- | ---: | ---: | ---: | ---: |
| M129 seed 9860 | 14 | 5 | 4 | 14 |
| M129 seed 9880 | 9 | 3 | 3 | 9 |
| M124 seed 9860 | 23 | 6 | 4 | 23 |
| M62 seed 9860 | 0 | 0 | 0 | 0 |
| M62 seed 9880 | 0 | 0 | 0 | 0 |

Decision: reject PPO readiness. Behavior and M62 controls pass, but fresh M129
strict proof-surface diversity is below the prior diversity standard and weaker
than same-seed M124. The next pending task is M131: diagnose and repair
proof-surface retention before PPO.

## 20260521T224730Z m131-proof-surface-retention-repair

M131 diagnoses why M129 loses fresh strict proof-surface diversity.

Seed `9860` comparison:

| Policy | Visible gap rows | Gap mean | Gap max | First-action mean | Trajectory mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 | 158 | 0.020974 | 0.188070 | 0.087288 | 0.032974 |
| M129 | 156 | 0.009717 | 0.023838 | 0.099090 | 0.026182 |

Strict accepted rows:

| Policy | Rows | Selected pairs | Gap mean | Gap max | First-action mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 | 23 | 6 | 0.017592 | 0.035959 | 0.101018 |
| M129 | 14 | 5 | 0.008877 | 0.015155 | 0.109515 |

Diagnosis: M129 does not simply lose action separation. It increases one-step
first-action distance, but shrinks trajectory distance and rollout margin gaps.
The fixed logprob objective is therefore not aligned tightly enough with the
fresh rollout-level proof surface. The next pending task is M132: repair
proof-surface retention using rollout margin evidence before PPO.

## 20260521T230043Z m132-rollout-margin-retention-repair

M132 tests conservative M128-objective updates from M124 with a stronger action
anchor.

Objective candidates:

| Candidate | Improvement | After anchor MSE |
| --- | ---: | ---: |
| s40 anchor20 seed 9840 | 0.021312 | 0.000289 |
| s60 anchor20 seed 9841 | 0.029004 | 0.000341 |

Strict proof-surface result:

| Policy | Miner seed | Accepted rows | Selected pairs | Selected seeds | Snippets | Max gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M129 | 9860 | 14 | 5 | 4 | 14 | 0.015155 |
| M129 | 9880 | 9 | 3 | 3 | 9 | 0.015155 |
| s40 anchor20 | 9860 | 20 | 6 | 4 | 20 | 0.031289 |
| s60 anchor20 | 9860 | 21 | 7 | 5 | 21 | 0.032615 |
| s60 anchor20 | 9880 | 13 | 5 | 4 | 13 | 0.029413 |

Behavior seed `9502`: s60 normal success `0.8625`, reset `0.8500`,
zero-current/zero-all `0.8000`, no-action `0.8625`.

Decision: admit s60/anchor20 to formal repeat only. It repairs much of M129's
fresh proof-surface shrinkage and keeps behavior, but PPO remains blocked until
the repair repeats on fresh formal gate seeds. The next pending task is M133.

## 20260521T231547Z m133-s60-rollout-margin-formal-repeat-gate

M133 formally repeats the M132 s60/anchor20 repair before PPO.

Behavior repeat on seed `9503`:

- M124 success `0.8625`, clearance mean `1.843230`;
- M132 s60 success `0.8625`, clearance mean `1.841558`;
- M132 s60 reset success `0.8500`;
- M132 s60 zero-current/zero-all success `0.8000`;
- M132 s60 no-action success `0.8625`.

Strict outcome-surface repeat:

| Policy | Miner seed | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M132 s60 | 9900 | 18 | 5 | 10 | 8 | 17 | 0.029413 |
| M132 s60 | 9920 | 15 | 4 | 9 | 8 | 14 | 0.029413 |
| M62 control | 9900 | 0 | 2 | 0 | 0 | 0 | 0.000000 |
| M62 control | 9920 | 0 | 1 | 0 | 0 | 0 | 0.000000 |

Decision: admit guarded PPO readiness, not driver success. The behavior gate
passes, zero-response degradation repeats, and strict s60 proof-surface
diversity repeats on two fresh seeds while M62 controls export zero snippets.
The limitations remain important: no-action history is still neutral and all
accepted snippets are perturbed-source. The next pending task is M134, a small
guarded PPO continuation from M132 s60 with immediate post-PPO retention gates.

## 20260521T233408Z m134-guarded-ppo-continuation-from-s60

M134 runs the first guarded PPO smoke continuation from M132 s60.

Training:

- config: `configs/ppo_m134_guarded_s60_smoke.json`;
- init checkpoint: `runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt`;
- run dir: `runs/ppo_m134_guarded_s60_smoke_seed5134`;
- built-in eval termination rate: `0.0000` over 5 episodes.

Behavior seed `9503` passes:

- M132 s60 success `0.8625`, clearance mean `1.841558`;
- M134 final success `0.8625`, clearance mean `1.843000`;
- M134 final reset success `0.8500`;
- M134 final zero-current/zero-all success `0.8000`;
- M134 final no-action success `0.8625`.

Fixed-batch M128 outcome loss changes only slightly:

| Policy | Loss mean |
| --- | ---: |
| M132 s60 | 0.252310 |
| M134 step4096 | 0.251846 |
| M134 final | 0.251741 |

Strict proof-surface repeat:

| Policy | Miner seed | Selected pairs | Selected seeds | Snippets |
| --- | ---: | ---: | ---: | ---: |
| M133 M132 s60 | 9900 | 10 | 8 | 17 |
| M133 M132 s60 | 9920 | 9 | 8 | 14 |
| M134 step4096 | 9900 | 9 | 6 | 17 |
| M134 step4096 | 9920 | 9 | 7 | 17 |
| M134 final | 9900 | 8 | 5 | 17 |
| M134 final | 9920 | 8 | 6 | 17 |

Decision: reject continuation beyond smoke. M134 keeps behavior and slightly
improves the fixed M128 loss, but it shrinks strict selected-seed diversity
below M133. The next pending task is M135: a PPO step/anchor sensitivity gate
before any longer PPO continuation.

## 20260521T235318Z m135-ppo-step-anchor-sensitivity-gate

M135 tests whether smaller PPO steps or stronger anchors can preserve the M133
proof surface.

Candidate grid:

| Candidate | Steps | Anchor |
| --- | ---: | --- |
| s2048 a1 | 2048 | coef 1.0 negative-advantage only |
| s2048 a20 | 2048 | coef 20.0 all-state |
| s4096 a20 | 4096 | coef 20.0 all-state |

Behavior seed `9503`: all candidates retain normal success `0.8625`, reset
success `0.8500`, zero-response success `0.8000`, and no-action success
`0.8625`.

Fixed M128 outcome loss:

| Policy | Loss mean |
| --- | ---: |
| M132 s60 | 0.252310 |
| M134 step4096 | 0.251846 |
| M134 final | 0.251741 |
| M135 s2048 a1 | 0.252178 |
| M135 s2048 a20 | 0.252404 |
| M135 s4096 a20 | 0.252389 |

Strict proof-surface summary:

| Policy | Miner seed | Selected pairs | Selected seeds | Snippets |
| --- | ---: | ---: | ---: | ---: |
| M133 M132 s60 | 9900 | 10 | 8 | 17 |
| M133 M132 s60 | 9920 | 9 | 8 | 14 |
| M135 s2048 a1 | 9900 | 9 | 7 | 16 |
| M135 s2048 a1 | 9920 | 9 | 8 | 16 |
| M135 s2048 a20 | 9900 | 8 | 6 | 16 |
| M135 s2048 a20 | 9920 | 8 | 7 | 16 |
| M135 s4096 a20 | 9900 | 9 | 6 | 17 |
| M135 s4096 a20 | 9920 | 9 | 7 | 17 |

Decision: reject the PPO sensitivity branch. Smaller steps help but still fail
M133 selected-seed diversity on seed `9900`; strong all-state anchoring worsens
fixed M128 loss and does not restore proof-surface diversity. The next pending
task is M136: make the M133 proof-surface rows an explicit retention corpus or
guard before PPO resumes.

## 20260521T235725Z m136-m133-proof-surface-retention-corpus

M136 builds the explicit M133 proof-surface retention corpus.

Corpus:

- input runs: M133 strict seed `9900` and `9920`;
- input rows: `31`;
- output rows after deduplication: `20`;
- duplicate rows removed: `11`;
- unique seeds: `9`;
- source coverage: perturbed-only.

M62 controls remain clean with zero accepted rows and zero exported snippets on
both strict seeds.

Retention coverage over 11 unique M133 keys:

| Candidate run | Retained keys | Lost keys |
| --- | ---: | ---: |
| M134 final 9900 | 7 | 4 |
| M134 final 9920 | 7 | 4 |
| M134 step4096 9900 | 8 | 3 |
| M134 step4096 9920 | 8 | 3 |
| M135 s2048 a1 9900 | 8 | 3 |
| M135 s2048 a1 9920 | 8 | 3 |
| M135 s2048 a20 9900 | 8 | 3 |
| M135 s2048 a20 9920 | 8 | 3 |
| M135 s4096 a20 9900 | 8 | 3 |
| M135 s4096 a20 9920 | 8 | 3 |

Decision: corpus ready for objective-sanity work, not promotion. The next
pending task is M137: optimize or gate directly against this M133 retention
corpus before PPO resumes.

## 20260522T001343Z m137-m133-retention-objective-sanity

M137 tests objective-only updates on the M136 M133 retention corpus.

Fixed losses:

| Policy | M136 loss | M128 loss |
| --- | ---: | ---: |
| M132 s60 | 0.106838 | 0.252310 |
| s20 a20 | 0.104333 | 0.247032 |
| s40 a20 | 0.102648 | 0.243741 |
| s40 a50 | 0.105241 | 0.248916 |

Behavior seed `9503`: all candidates retain normal success `0.8625`. The best
fixed-loss candidate `s40 a20` keeps reset success `0.8500`, zero-response
success `0.8000`, and no-action success `0.8625`.

Strict proof-surface result:

| Policy | Miner seed | Selected pairs | Selected seeds | Snippets |
| --- | ---: | ---: | ---: | ---: |
| M133 M132 s60 | 9900 | 10 | 8 | 17 |
| M133 M132 s60 | 9920 | 9 | 8 | 14 |
| s20 a20 | 9900 | 6 | 5 | 13 |
| s20 a20 | 9920 | 5 | 4 | 11 |
| s40 a20 | 9900 | 7 | 6 | 12 |
| s40 a20 | 9920 | 6 | 5 | 10 |
| s40 a50 | 9900 | 7 | 5 | 15 |
| s40 a50 | 9920 | 5 | 4 | 11 |

Decision: reject M137 as a proof-surface repair. Fixed M136/M128 losses improve
and behavior passes, but strict rollout proof-surface diversity collapses. The
next pending task is M138: audit the mismatch between fixed retention loss and
rollout-level margin/key retention before designing another objective.

## 20260522T002036Z m138-retention-loss-rollout-misalignment-audit

M138 audits why M137 fixed-loss improvements shrink rollout proof-surface
diversity.

Aggregate retained-key audit:

| Policy | Objective loss | Delta vs M132 | Retained keys | Lost keys |
| --- | ---: | ---: | ---: | ---: |
| M132 s60 | 0.105571 | 0.000000 | 11 | 0 |
| M137 s20 a20 | 0.103103 | -0.002467 | 7 | 4 |
| M137 s40 a20 | 0.101464 | -0.004106 | 7 | 4 |
| M137 s40 a50 | 0.104001 | -0.001569 | 8 | 3 |

Lost-key rows can have lower penalties than M132. For example, `s40 a20` loses
the duplicated seed `9906` step `44 -> 44` rows while lowering their per-row
penalties by about `0.058-0.060`.

Decision: diagnostic positive. Fixed retained-snippet logprob is not a safe
proxy for rollout-level proof-surface retention. The next pending task is M139:
prototype a key-action anchor or rollout-aware retention objective.

## 20260522T002753Z mhtml-input-contract-recheck

Rechecked the latest local MHTML snapshot:

```text
/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml
```

No new actor oracle fields are admitted. The latest input discussion is now
explicitly tied into the formal M91 protocol:

- final wheel profiles should use `Romega_i` and local `v_parallel_i`;
- `v_parallel_i` is a per-wheel contact-patch ground-speed estimate, not
  vehicle-center speed and not a wheel-speed average;
- `slip_ratio` remains out of the deployable actor because its division,
  clipping, low-speed singularities, and sign switches can create numerical and
  distribution artifacts;
- optional `v_perp_i`, steering torque, vertical dynamics, and suspension
  channels still require admission gates;
- the reliable experiment order remains probe first, then frozen-recipe RL
  comparison, then matched hidden-dynamics wrong-history gates.

Updated `docs/m91-input-observability-audit-protocol.md` and
`docs/observation-contract.md` so future input-profile work does not drift back
to slip-ratio or shortcut features.

## 20260522T005900Z m139-m136-key-action-anchor-objective

M139 added snippet-level action anchoring to the outcome intervention optimizer
and tested whether direct retained-key action preservation can repair the M137
rollout proof-surface regression.

Focused tests:

```text
tests/test_outcome_intervention_optimize.py: 4 passed
```

Best behavior candidate:

```text
runs/m139_m136_s20_env20_snip1000_seed7141/optimized_checkpoint.pt
```

It keeps behavior on seed `9503`: normal success `0.8625`, reset `0.8500`,
zero-response `0.8000`, no-action `0.8625`.

Strict proof-surface result is negative. M133 reference is `10 pairs / 8 seeds`
on miner seed `9900` and `9 / 8` on seed `9920`. M139 reaches only:

```text
s40 snip100:   8 / 6 and 7 / 6
s40 snip500:   9 / 7 and 8 / 7
s20 snip1000:  9 / 7 and 8 / 7
```

Decision: reject M139 as a repair. Even retained-key action MSE near
`2.19e-7` does not preserve the strict rollout proof surface. The next task is
M140, a rollout-key survival audit that should look at selected-key survival
and rollout margin signals directly.
