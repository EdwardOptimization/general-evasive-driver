# AutoDrift Implementation Plan

Last updated: 2026-05-21

## Goal

Build a complete simulation-first AutoDrift stack for friction-adaptive drifting
and emergency obstacle avoidance. The project should be usable without a paper
workflow: install the environment, train policies, run deterministic evaluations,
compare against baselines, inspect metrics, and reproduce saved results.

The engineering target is:

> A user can train and evaluate an RL-based drift controller across randomized
> vehicle-road dynamics, then test it on progressively harder tasks up to
> AEB-infeasible obstacle avoidance.

## Non-Goals

- No paper deadline or novelty-first milestone.
- No full-size real-car deployment in the first phase.
- No high-fidelity commercial simulator dependency in the core MVP.
- No claim that pure RL is always safer than constrained control; safety/filter
  layers and model-based baselines remain part of the complete project.

## Current Baseline

The first runnable MVP is in place:

- `src/autodrift/dynamics.py`: RWD single-track dynamics with friction-limited
  nonlinear tires and randomized hidden parameters.
- `src/autodrift/tasks.py`: circular drift tracking task.
- `src/autodrift/env.py`: Gymnasium environment with hidden friction by default.
  Scenario speed targets are friction-limited so low-`mu` cases remain
  physically plausible instead of asking the policy to track impossible speeds.
- `src/autodrift/policies.py`: random and heuristic sanity-check policies.
- `src/autodrift/evaluate.py`: evaluation CLI.
- `src/autodrift/train_ppo.py`: dependency-light PyTorch PPO trainer.
  Current driver work uses the clean online-GRU actor contract; older actor
  variants are historical baselines, not migration targets.
- `src/autodrift/benchmark.py`: shared-seed benchmark runner.
- `src/autodrift/artifacts.py`: run directory, JSON, and CSV artifact helpers.
- `src/autodrift/checkpoints.py`: strict PPO checkpoint loader for evaluation.
  Checkpoints must declare the full model contract and matching observation
  shape; changed actor contracts require retraining.
- `src/autodrift/vector_env.py`: synchronous multi-environment rollout support.
- `src/autodrift/config.py`: JSON config builders for env randomization and
  curricula.
- `configs/`: tracked training configuration templates.
- `tests/`: smoke tests for dynamics, environment, and baseline policy.

## Architecture Direction

Use RL as the main adaptation mechanism, with explicit benchmark baselines and
clean interfaces for later safety layers:

```text
state/action history + path features
  -> RL policy
  -> steering/throttle/brake targets
  -> actuator limits and low-level servo model
  -> vehicle dynamics
```

For later safety and comparison, add model-based baselines:

```text
fixed-model controller
adaptive/estimated-friction controller
NMPC or SQP controller
```

NMPC is not the first main controller in this project; it is a baseline and a
possible safety/filter layer after the RL-first result exists.

The long-term controller target is a universal closed-loop RL operator:

```text
human-view ego response + action history + road/free-space + obstacle geometry
  -> RL actor
  -> steering/throttle/brake
  -> vehicle response
  -> updated human-view observation and recurrent hidden state
```

The deployed actor should not depend on explicit rule branches or true hidden
vehicle parameters. It should infer friction, braking authority, tire response,
mass/CG variation, and actuator lag from recent feedback and its own previous
actions. Rules remain useful for scenario generation, reward shaping, benchmark
labels, diagnostics, and safety monitoring, but they should not become the
normal driving policy. See `docs/m7-universal-closed-loop-operator.md`.

### M24+ Human-View Contract

The current driver branch no longer treats path-tracking scalars as the
deployable actor input. The active contract is the 72-value human-view frame in
`docs/observation-contract.md`:

- ego response and actuator state;
- previous physical steering, throttle, and brake commands;
- ego-frame road-boundary lookahead points;
- ego-frame obstacle slots.

The actor must not receive path lateral error, heading error, path curvature,
along-path speed, required lateral clearance, TTC, `speed_ref`, `beta_target`,
`beta`, `mu`, vehicle parameters, rule labels, or seed/curriculum metadata.

The active output contract is direct three-channel control:

```text
[steering_command, throttle_command, brake_command]
```

Old 15-value-frame checkpoints are historical evidence only. They are not
migration targets for the human-view branch.

### Self-Identification Proof Standard

Aggregate success, ordinary recurrent hidden reset, and response masking are not
enough by themselves to prove a professional-driver-like controller. They answer
different questions:

- aggregate success shows whether the policy can drive the benchmark;
- reset-vs-normal shows whether a gate requires long-horizon GRU memory;
- response masking shows whether current ego response features matter;
- none of those alone proves friction or vehicle-response self-identification.

Because the human-view frame already includes current ego response and previous
physical commands, the task can be close to Markov on many scenarios. In those
cases, resetting hidden state should not necessarily hurt. The stronger proof
must use matched-current-observation gates:

```text
probing window under hidden dynamics A or B
  -> same visible road/obstacle/current-state decision point
  -> compare normal, reset, zero-response, and hidden-swap variants
```

The self-identification gate passes only if the learned hidden or recurrent
state changes actions or outcomes in a way that is beneficial for the matching
hidden dynamics. This is the M28+ validation direction.

Important interpretation boundary:

- If train and test dynamics are fixed, a reset/no-reset comparison cannot prove
  friction or vehicle-response adaptation.
- If current ego response plus previous physical commands are sufficient for a
  local correction, reset and normal inference can match while the policy still
  uses closed-loop feedback.
- A professional-driver claim needs evidence that the policy maps its own
  actions and sensed vehicle response into better future control. That evidence
  can be one-step current-feedback dependence, recurrent hidden-state
  dependence, or both, but the docs must label which form was actually shown.

## Complete Project Deliverables

- `autodrift` Python package with simulator, tasks, policies, training, and
  evaluation modules.
- Reproducible CLI commands for training, evaluation, benchmark sweeps, and
  report generation.
- Saved run artifacts: policy checkpoints, config snapshots, metrics CSV/JSON,
  and plots.
- Task suite:
  circular drift, friction-step drift, figure-eight/transition tracking, and
  pop-up obstacle avoidance.
- Baseline suite:
  random policy, heuristic controller, fixed-friction model controller,
  adaptive-friction controller, and optional NMPC/SQP controller.
- Documentation:
  install guide, task definitions, metric definitions, baseline descriptions,
  and literature notes.
- Tests:
  unit tests for dynamics/tasks, smoke tests for training/evaluation, and
  regression checks for benchmark outputs.

## Infrastructure Status

Already in place:

- GPU-first conda environment with CPU fallback.
- Installable package metadata and command-line entry points.
- Reproducible run directories under `runs/`.
- PPO config templates under `configs/`.
- Synchronous vectorized PPO rollout collection.
- Curriculum config support for staged env difficulty.
- Training artifacts:
  `config.json`, `checkpoint.pt`, `train_metrics.csv`, `eval_summary.json`,
  and `manifest.json`.
- Evaluation artifacts:
  per-episode CSV, summary JSON, and manifest.
- Benchmark artifacts:
  shared-seed episode rows, policy summary, and friction-bucket summary.
- Checkpoint evaluation through `--policy checkpoint`.

Deferred until the project needs them:

- External training framework adapter such as Stable-Baselines3, CleanRL, or
  RL-Games if the in-repo vectorized PPO trainer is not enough.
- Hyperparameter sweep management and experiment database.
- Rich plotting/report generation beyond machine-readable CSV/JSON.
- Scenario corpus versioning for obstacle-avoidance benchmarks.
- High-fidelity simulator adapters.
- NMPC/SQP baseline harness and solver-specific profiling.
- Continuous integration and container images.

## Milestones

### M1: Make the Project Easy to Run

- Add an installable package workflow and documented commands.
- Standardize configuration for tasks, randomization ranges, and training.
- Save checkpoints and evaluation metrics into a run directory.
- Add a short smoke-training command that completes quickly.

Exit criteria:

- `pytest` passes;
- one command trains a tiny policy;
- one command evaluates a saved or baseline policy;
- run artifacts are written in a predictable directory.

Status: mostly complete for the current simulator and PPO trainer. Task/env
configuration is still narrow because only the circular drift task exists.

### M2: Make RL Learn the Circular Drift Task

- Use the vectorized PPO trainer or switch to SB3/CleanRL/RL-Games if the
  in-repo trainer cannot learn reliably.
- Train PPO/SAC on randomized `mu`, mass, CG, tire stiffness, and actuator lag.
- Add curriculum over speed, track width, and beta target.
- Track success rate by friction bucket.

Exit criteria:

- policy survives full episodes on the circle task;
- lateral RMSE and sideslip error improve over heuristic;
- metrics are reported by `mu` bucket;
- plots show trajectory, sideslip, speed, and actions for selected episodes.

Status: pass. The best local checkpoint reaches 100% success over a 200-seed
circular-drift benchmark and beats the heuristic in every friction bucket. See
`docs/m2-circular-drift-results.md`; rollout plots are generated with
`autodrift.rollout`.

### M3: Add Friction Adaptation

- Add observation history stacking or recurrent policy.
- Add privileged teacher option that sees `mu`, mass, CG, and tire stiffness.
- Distill teacher into a student that only sees sensor/history observations.
- Add friction-step episodes where `mu` changes mid-run.

Exit criteria:

- student handles unseen friction and mass/CG combinations better than a
  non-history policy;
- ablation shows history or latent adaptation matters.

Status: first pass complete. A history-stacked policy initialized from the M2
checkpoint reaches 81% success on the 100-episode friction-step benchmark,
beating both the M2 static checkpoint baseline and staged single-frame
fine-tuning. Severe final low-friction transitions remain a known weakness and
should be refined while M4/M5 are added. See
`docs/m3-friction-adaptation-plan.md`.

### M4: Add General Path Tracking

- Add figure-eight and variable-curvature path tasks.
- Add future waypoint/path feature observations.
- Evaluate drift initiation, transition, recovery, and steady-state segments
  separately.

Exit criteria:

- policy can transition drift direction without immediate spin-out;
- metrics are reported per segment type.

Status: in progress. `track_kind="figure_eight"` is implemented with a sampled
closed path, signed curvature, reset support, and rollout curvature/progress
traces. The best trained M4 policy currently reaches 83% success on a
100-episode figure-eight benchmark but does not beat the heuristic's 100%
survival rate. Segment diagnostics show that low friction is the primary
blocker across both left and right curve segments. See
`docs/m4-general-path-tracking.md`.

### M5: Add AEB-Failure Obstacle Avoidance

- Add AEB-only and conventional AES baselines.
- Add pop-up obstacle tasks where braking alone is infeasible.
- Add scenarios where conventional AES is feasible and where only high-sideslip
  control can plausibly avoid collision.
- Track collision, off-road, spin-out, minimum obstacle distance, and residual
  speed at closest approach.

Exit criteria:

- task generator can label AEB-only infeasible cases;
- policies are evaluated on fixed scenario seeds;
- reports separate AEB-feasible, AES-feasible, and drift-required buckets.

Status: scaffolded with environment support. A reproducible obstacle scenario
generator now labels `aeb_feasible`, `aes_feasible`, `drift_required`, and
`unavoidable` cases, can filter for AEB-infeasible scenarios, and is wired into
`AutoDriftEnv` with obstacle observations, collision metrics, and label-bucket
benchmark summaries. AEB-only and heuristic AES baselines are implemented and
both fail the current AEB-infeasible smoke benchmark, giving the first RL
obstacle policy a concrete baseline gate. The first M5 PPO template can
initialize from the M2 checkpoint through partial observation expansion. The
first RL attempt lowers collision rate but only reaches 1% full success under
the original long-horizon tracking metric. With obstacle pass-completion
semantics, the same checkpoint reaches 100% success on the small
`aes_feasible` bucket and 90.9% on `drift_required`; the next gap is
label-filtered/balanced M5 evaluation. Label-filtered benchmarks now show 86%
success on avoidable AEB-infeasible scenarios and 86% success on
`drift_required` scenarios, beating AEB-only and heuristic AES baselines. See
`docs/m5-emergency-avoidance.md`.

### M6: Add Model-Based Baselines

- Implement a fixed-parameter controller.
- Implement an adaptive friction estimator baseline.
- Add NMPC/SQP baseline if the model-based baselines are too weak or if a
  useful engineering comparison requires it.

Exit criteria:

- compare RL, fixed model, and adaptive model across the same randomized test
  set;
- identify where RL wins and where model-based control is still stronger.

Status: first pass complete. `envelope_aes` is implemented as a fixed
friction-envelope AES baseline. On the 100-episode `drift_required` benchmark it
reaches 79% success, beating heuristic AES but trailing the RL checkpoint's 86%
success. See `docs/m6-model-based-baselines.md`.

### M7: Build the Universal Closed-Loop RL Operator

- Upgrade the M5 obstacle policy from single-frame inference to history-stacked
  or recurrent inference.
- Treat previous action and actuator history as required deployable inputs, so
  the actor can associate its own commands with the vehicle's response.
- Make the operator drift-capable rather than drift-seeking: stable AES should
  remain stable, while high-sideslip behavior is used when the scenario demands
  it.
- Keep the deployed actor parameter-blind: no true `mu`, mass, CG, tire, or
  brake parameters as actor inputs.
- Keep the deployed actor rule-label-blind: no `drift_required`, `aes_feasible`,
  `mu_bucket`, or controller-mode labels as actor inputs.
- Use asymmetric PPO or teacher-student training so privileged parameters can
  help training without becoming deployment dependencies.
- Broaden domain randomization across vehicle family, actuator, tire, brake,
  sensor, and road-surface variation.
- Add held-out vehicle and friction benchmark suites.
- Add ablations for no-history, no-action-history, recurrent versus stacked
  history, and privileged-parameter leakage.

Exit criteria:

- one actor checkpoint runs directly as `[steer, drive/brake]` control across
  held-out vehicle and road families;
- it outperforms AEB-only, heuristic AES, and model-based envelope baselines on
  AEB-infeasible obstacle scenarios;
- it handles `aes_feasible` scenarios without unnecessary drift and recovers
  cleanly after `drift_required` maneuvers;
- failure modes are reported by hidden vehicle and road buckets;
- adaptation depends on closed-loop feedback rather than rule branches or
  leaked simulator parameters;
- safety/fallback logic is separated from the main RL controller.

Status: first training and ablation pass complete. M7-A and M7-B
training/evaluation paths now exist, including full action-history
observations, M7-B sequence heads, named checkpoint benchmark comparison,
checkpoint observation ablations, latent self-identification probes, and
held-out vehicle-road bucket summaries. A repeatable M7 gate harness now runs
the benchmark comparison, history ablations, and latent probes into one report,
and a scenario-corpus harness can build label-balanced seed sets.
The first 1M-step M7-A/M7-B checkpoints slightly improve aggregate success on
the AES-weighted held-out benchmark, but they do not yet pass the M7 behavior
gate: both use too much high sideslip on `aes_feasible` cases, and zeroing
action history does not hurt performance. First latent probes show some
friction and tire information, but no convincing temporal/action-history
self-identification signal. Recurrent/latent actors and better stable-AES
objectives remain open. See
`docs/m7-universal-closed-loop-operator.md` and
`docs/m7-first-stage-results.md`; see `docs/m7-gate-harness.md` for the
repeatable gate command.
Validation follows `docs/m7-validation-protocol.md` so a policy is judged by
held-out generalization, ablations, latent self-identification evidence, and
behavior diagnostics rather than aggregate success alone.

### M8: RL Professional Driver v1

- Add a recurrent or latent-state actor that can learn feedback-based
  self-identification rather than only reading a flat stacked vector.
- Keep the actor deployable: no true hidden parameters and no rule labels.
- Make the policy drift-capable but not drift-seeking by shaping `aes_feasible`
  cases toward stable avoidance and reserving high sideslip for scenarios that
  need it.
- Train a new checkpoint and run the full driver gate against AEB, heuristic
  AES, envelope AES, M5, M7-A, and M7-B.

Exit criteria:

- the M8 checkpoint beats M5/M7 on the label-balanced held-out corpus;
- `aes_feasible` high-sideslip behavior is below the gate threshold;
- ablations show that temporal/action feedback matters;
- latent probes show temporal lift over shuffled history;
- negative results are documented if any criterion fails.

Status: historical partial success but not passed. The temporal-GRU M8-A
checkpoint at `runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt` improved
aggregate success from 0.700 to 0.733 on the label-balanced corpus, kept
`aes_feasible` high-sideslip at 0.038, and showed probe temporal lift of 0.022.
It still failed the driver gate because zero-action-history and
shuffled-history ablations did not reduce success. The current blocker is a
clean-contract retrain followed by behavior-level proof of closed-loop
self-identification. See
`docs/m8-rl-professional-driver.md`.

### M24-M28: Human-View Professional Driver Branch

- Replace path-tracking and precomputed obstacle features with ego-frame
  human-view perception.
- Split the action contract into direct steering, throttle, and brake commands.
- Train the first `human_view_online_gru` controller from scratch.
- Use checkpoint sweeps to select the best human-view driver by benchmark
  success, not final checkpoint by default.
- Build a new hard response-dependence gate for the human-view branch.
- Implement a matched-current-observation hidden-swap gate so recurrent
  self-identification is tested directly instead of inferred from aggregate
  success.

Exit criteria:

- human-view policy beats AEB and envelope AES baselines on same-seed obstacle
  benchmarks;
- old 15-value-frame checkpoints and hard corpora are treated as historical and
  not reused as compatible artifacts;
- reset and response-masking ablations are interpreted narrowly;
- matched-current-observation or hidden-swap gates show whether adaptation
  depends on accumulated recurrent state.

Status: M24-M27 are complete as infrastructure, first full training, and first
paired perturbation gate. M26_602 is the current best human-view checkpoint by
success, reaching 0.800 success against envelope AES at 0.675 on the 40-episode
same-seed obstacle benchmark. M27 confirms the low-friction perturbation is hard
in aggregate, but it is not a self-identification pass: hidden reset matches
normal perturbed success, and response masking only lowers perturbed success by
0.025. M28 is the next task: implement and run a matched-current-observation
hidden-swap gate that separates "can drive," "can adapt from current feedback,"
and "requires accumulated recurrent hidden self-identification." See
`docs/m24-human-view-driver-contract.md`,
`docs/m26-human-view-gru-results.md`,
`docs/m27-human-view-self-identification-gate.md`, and
`docs/m28-hidden-swap-gate.md`.

### M28: Matched Hidden-Swap Self-Identification Gate

- Collect paired rollouts under different hidden dynamics, such as normal
  friction versus low friction or fast versus slow actuator response.
- Snapshot the environment, visible observation, and GRU hidden state near an
  obstacle decision point after a probing window.
- Pair snapshots only when visible observations are close enough; otherwise
  record the mismatch and treat the result as diagnostic rather than proof.
- Replay continuations with normal hidden state, reset hidden state,
  zero-response observation, and hidden state swapped from the paired dynamics.
- Report first-action distance, continuation return, success, collision,
  off-road, spin-out, and visible-observation match distance.

Exit criteria:

- the harness writes reproducible `pairs.csv`, `replays.csv`, `summary.csv`,
  and `manifest.json` artifacts;
- matched cases are tight enough to support a self-identification claim;
- normal hidden state improves actions or outcomes relative to reset or swapped
  hidden state on the matching hidden dynamics;
- if the gate fails, the failure mode is recorded and used to choose the next
  training change instead of being treated as a vague negative result.

Status: complete as a gate harness and negative as a self-identification
result. The full 80-seed run collected 80 paired snapshots and 74 accepted
visible matches. Accepted cases had mean hidden-state distance 1.354, but reset,
zero-response, and hidden-swap variants did not change success on any accepted
case. This means `m26_602` still does not pass recurrent self-identification.
The next task should build an M29 response-critical matched corpus or training
curriculum where hidden/current feedback changes the outcome, not just the first
action.

### M29: Matched Response-Critical Corpus

- Mine M28 hidden-swap artifacts for accepted matched seeds.
- Record whether reset, zero-response, or hidden-swap changes success.
- If ablations do not change success, select high-quality condition-change
  seeds where nominal dynamics pass and perturbed dynamics fail.
- Export `scenario_corpus.csv` with a `seed` column so it can be reused by PPO
  training and benchmark commands.

Exit criteria:

- corpus miner has unit tests;
- corpus run writes candidate, selected, edge, summary, and manifest artifacts;
- docs distinguish ablation-outcome-critical seeds from condition-change seeds.

Status: complete as corpus infrastructure. M29 selected 40 seeds from M28:
74 accepted visible matches, 0 ablation success-change seeds, 26
nominal-vs-perturbed condition-change seeds, and 28 perturbed-failure seeds.
This is not a self-identification pass. It is a hard training/gate corpus for
M30. See `docs/m29-matched-response-corpus.md`.

### M30: Mixed Hard-Corpus Training

- Add mixed seed sampling so hard M29 seeds are oversampled without replacing
  ordinary randomized resets.
- Fine-tune `m26_602` with `human_view_online_gru` under the same clean
  human-view input/output contract.
- Select checkpoints by M29 hard-corpus performance, M28 hidden-swap behavior,
  and broad same-seed obstacle success.

Exit criteria:

- mixed sampler has unit tests;
- M30 smoke trains from `m26_602` with the M29 corpus;
- full training writes periodic checkpoints and final checkpoint;
- post-training benchmarks compare M26 and M30 on M28/M29 and broad obstacle
  gates.

Status: partial positive. Full M30 training completed and early checkpoints
improve both M29 hard-corpus success and broad same-seed obstacle success.
`m30_053` reaches 0.875 on the M29 selected corpus versus 0.775 for M26_602,
and 0.825 on the broad 40-seed benchmark versus 0.800 for M26_602. The final
checkpoint regresses, so checkpoint selection matters. M30 still does not pass
recurrent self-identification: hidden-swap changes zero accepted success
outcomes on the M28-style gate. See `docs/m30-mixed-hard-corpus-training.md`.

### M31: Parallel Rollout Harness

- Replace or extend the synchronous vector env so rollout collection can use
  multiple CPU cores.
- Preserve deterministic seed sequencing, including mixed hard-seed sampling.
- Keep the trainer API compatible with existing configs.

Exit criteria:

- current single-process vector-env tests still pass;
- new parallel rollout smoke matches observation/action shapes and reset-seed
  semantics;
- M30-style training can use 8 workers without changing actor inputs.

Status: functional but not yet a proven speedup. `ParallelAutoDriftVectorEnv`
is implemented, tested, and wired into PPO through `vector_env_mode`. An
8-worker 4096-step smoke matches sync behavior exactly, but real time is 9.37s
parallel versus 9.19s sync, so process startup and IPC overhead erase gains at
that scale. The next performance step should benchmark longer rollout-only
sections before defaulting long training to parallel mode. See
`docs/m31-parallel-rollout-harness.md`.

### M32: Rollout Throughput Profile

- Add a rollout-only benchmark CLI so vector-env throughput can be measured
  without PPO update, CUDA, checkpoint, or eval overhead.
- Compare sync and parallel modes across worker counts.
- Decide when parallel mode is worth using.

Exit criteria:

- throughput benchmark has tests;
- profile writes rows, summary, and manifest artifacts;
- docs record the worker-count threshold.

Status: complete. Rollout-only profiling shows parallel mode is slower for
1-4 envs, but faster for 8 and 16 envs. At 8 envs, parallel reaches 11311 env
steps/s versus 10237 for sync; at 16 envs, 11664 versus 10103. This is useful
but modest, so parallel should be used selectively. See
`docs/m32-rollout-throughput-profile.md`.

### M33: Full PPO Parallel Profile

- Compare sync and parallel modes inside a short full PPO run at 16 envs.
- Verify whether rollout-only speedup survives PPO update and CUDA overhead.
- Check whether sync versus parallel changes training results.

Exit criteria:

- same config, seed, checkpoint, env count, and total steps;
- wall-clock timings recorded;
- metrics, eval summary, and model-state diff checked.

Status: complete. Parallel mode is about 4.7% faster on the 20k-step 16-env
full PPO profile: 50.99s versus 53.48s. The training metrics, eval summary, and
model tensors are identical; checkpoint file hashes differ only because the
saved config records `vector_env_mode`. Parallel is safe from a determinism
standpoint in this profile, but the speedup is still modest. See
`docs/m33-full-ppo-parallel-profile.md`.

### M34: Response-Aux Mixed Training

- Add a deployable response-prediction auxiliary objective to the M30 mixed
  hard-corpus path.
- Keep the actor contract clean: the auxiliary target is the next observable
  ego response/action-state stream, not hidden friction, vehicle parameters,
  labels, controller mode, or oracle targets.
- Initialize from `m30_053` while adding only the new prediction head.
- Select checkpoints by M29 hard-corpus performance, broad same-seed success,
  and hidden-swap/reset/zero-response gates.

Exit criteria:

- partial init is tested and restricted to the new response-prediction head;
- M34 smoke trains end to end from `m30_053`;
- full training writes periodic checkpoints and final checkpoint;
- post-training gates test aggregate success and recurrent
  self-identification before claiming progress.

Status: smoke complete; full training queued. The smoke run loaded
`m30_053` with `partial_response_prediction_head`, trained on CUDA for 4096
steps, and reached eval return 70.377 with termination rate 0.200. This proves
the architecture/config path is runnable, not that self-identification is
solved. See `docs/m34-response-aux-mixed-training.md`.

Post-run status: mixed negative. M34_053/M34_102/M34_151 match M30_053 on the
M29 selected corpus at 0.875 success, and M34_053/M34_151 match M30_053 on the
broad 40-seed benchmark at 0.825 success. Hidden-swap still changes zero
accepted success outcomes. Reset and zero-response ablations begin to change a
few perturbed outcomes, so M35 expands response-change corpus mining from
M34_151.

### M35: M34 Response-Critical Corpus

- Re-run hidden-swap mining for M34_151 at 300 episodes.
- Count reset, zero-response, and hidden-swap outcome changes on accepted
  matched cases.
- Mine an 80-seed corpus with higher success-change and condition-change
  density for the next fine-tune.

Exit criteria:

- hidden-swap summary, pairs, and replays are written;
- matched-response corpus is exported as `scenario_corpus.csv`;
- docs clearly mark the result as corpus construction, not a pass.

Status: complete as a corpus-building step. M35 accepted 281 / 300 matched
cases, found 5 success-changed seeds and 9 success-changed edges, and selected
80 seeds. Hidden-swap still changed zero accepted outcomes, so this remains a
negative self-identification result. See
`docs/m35-m34-response-critical-corpus.md`.

### M36: Response-Change Corpus Training

- Fine-tune from M34_151 on the M35 response-change corpus.
- Keep ordinary randomized resets mixed in at 25% to reduce small-corpus
  overfit.
- Keep the response-prediction auxiliary head active.
- Select checkpoints by response-critical gate behavior first, then aggregate
  success.

Exit criteria:

- M36 config is committed;
- full run writes periodic checkpoints;
- post-run gates compare M36 against M30_053 and M34_151;
- progress requires unfavorable reset, zero-response, or hidden-swap
  sensitivity without aggregate regression.

Status: complete as a negative result. M36_028 preserves M34_151-level success
on the M35 response-change corpus, M29 selected corpus, and broad same-seed
benchmark, but it does not improve any gate. Later checkpoints regress.
M36_028 hidden-swap changes zero accepted success outcomes. See
`docs/m36-response-change-corpus-training.md`.

### M37: Multi-Step Response Auxiliary

- Extend response-prediction auxiliary loss from one-step prediction to
  multi-step future observable response prediction.
- Keep targets deployable-observable only: no hidden friction, vehicle
  parameters, rule labels, or controller mode.
- Allow compatible checkpoint initialization while reinitializing a resized
  response-prediction head.

Exit criteria:

- multi-step response target construction is unit-tested;
- done masking and sequence-tail masking are unit-tested;
- M37 smoke can initialize from M34/M36 checkpoints;
- full M37 validation uses M35, M29, broad, and hidden-swap gates.

Status: partial positive. M37_102 improves the M35 response-change corpus to
0.650 success versus 0.6125 for M30_053, M34_151, and M36_028, while
preserving M29 selected-corpus success at 0.875 and broad success at 0.825.
It also makes reset and zero-response ablations unfavorably outcome-critical on
perturbed accepted cases. Hidden-swap still changes zero accepted outcomes, so
this is not a self-identification pass. See
`docs/m37-multistep-response-aux-plan.md`.

### M38: M37 Response-Critical Corpus

- Expand M37_102 hidden-swap mining to 300 episodes.
- Mine a follow-up corpus from seeds where reset/zero-response are now
  unfavorable.
- Keep hidden-swap outcome-neutrality recorded as the blocker.

Exit criteria:

- hidden-swap summary, pairs, and replays are written;
- corpus summary records success-changed seeds and edges;
- docs distinguish response-critical progress from hidden-swap pass.

Status: complete as corpus construction. M38 accepted 280 / 300 cases, found
11 success-changed seeds and 18 success-changed edges, and selected 80 seeds.
Hidden-swap remains zero outcome changes. See
`docs/m38-m37-response-critical-corpus.md`.

### M39: M37 Response-Corpus Training

- Continue from M37_102 on the M38 corpus.
- Keep multi-step response prediction active.
- Use lower learning rate and mixed ordinary resets to avoid M36-style
  regression.

Exit criteria:

- M39 full run writes periodic checkpoints;
- post-run sweeps compare against M37_102 on M38, M35, M29, and broad gates;
- progress requires stronger unfavorable reset/zero-response or hidden-swap
  sensitivity without aggregate regression.

Status: complete as a negative result. M39_028 and M39_053 slightly improve
the M38 corpus success to 0.6375 versus 0.6250 for M37_102, but they do not
improve M35, M29, or broad success. More importantly, reset/zero-response
outcome changes weaken from 2 / 80 for M37_102 to 1 / 80 for M39_028 and
M39_053, while hidden-swap remains zero. See
`docs/m39-m37-response-corpus-training.md`.

### M40: Response-Aux Diagnostics

- Add response auxiliary loss logging to PPO train metrics.
- Add an offline response-prediction evaluator for checkpoints.
- Compare M34, M37_102, and M39 candidates on response-change cases.
- Report prediction loss by future horizon step.

Exit criteria:

- tests cover logged metrics and target/loss shape;
- evaluator writes machine-readable summaries;
- docs use diagnostics to decide the next architecture direction.

Status: complete as diagnostics. M40 logs train-time response auxiliary loss
and adds `autodrift.response_prediction_eval`. On the M38 corpus, M39_053 has
lower multi-step prediction MSE than M37_102 but weaker reset/zero-response
gate sensitivity, so lower MSE alone is not the right selection target. See
`docs/m40-response-aux-diagnostics-plan.md`.

### M41: Behavior-Sensitive Response Objective

- Use M40 diagnostics to design a target that favors behavior-critical hidden
  state, not just low future-response MSE.
- Compare per-seed prediction error against reset/zero-response outcome-change
  seeds.
- Decide whether the next training objective should be contrastive,
  gate-weighted, or intervention-aware.

Exit criteria:

- M41 produces a concrete implementation direction with a smokeable config;
- the direction is justified by M40 diagnostics and M37/M39 gate behavior.

Status: complete as diagnostics. Per-seed MSE does not identify
behavior-critical seeds: M39 lowers prediction error on both success-changed
and non-changed seeds while weakening reset/zero-response ablation sensitivity.
See `docs/m41-behavior-sensitive-response-diagnostics.md`.

### M42: Intervention-Aware Response Objective

- Use reset/zero-response outcome-change labels or action differences as a
  behavior-sensitive training signal.
- Avoid optimizing pure response MSE as the primary proxy.
- Preserve the deployable actor contract: no hidden vehicle parameters or rule
  labels enter actor observations.

Exit criteria:

- design is concrete enough to implement as code/config;
- training signal is tied to behavior-critical interventions or action
  changes;
- validation compares against M37_102, not M39.

Status: complete as a negative result. M42 strict-loads M37_102, logs both
response prediction and hidden-contrast auxiliary losses, and the 200k-step CUDA
run finished cleanly. M42_028 preserves M37_102 on M35, M29, and broad sweeps,
but it does not improve M38, hidden-swap outcome changes remain zero, and reset
sensitivity weakens from 2 unfavorable changes to 1 on the same 80-seed gate.
M37_102 remains the current best checkpoint. See
`docs/m42-hidden-contrast-objective.md`.

### M43: Action-Trajectory Intervention Diagnostics

- Measure deterministic action divergence over the whole continuation, not only
  the first action.
- Compare normal, reset, zero-response, and hidden-swap interventions on the
  same matched snapshots.
- Use the result to decide whether the next objective should target action
  mean divergence, intervention-labeled hard states, or harder partial
  observability.

Exit criteria:

- evaluator writes per-seed action-trajectory distances;
- result is joined against success-change labels;
- next training objective is chosen from evidence, not from loss curves alone.

Status: complete as diagnostics. M43 adds full-continuation action trajectory
distance fields to the hidden-swap gate and reruns M37_102 and M42_028 on the
same 80-seed gate. Perturbed accepted hidden-swap trajectory mean distance is
only 0.005528 for M37_102 and 0.004872 for M42_028, while reset and
zero-response are about 0.18 to 0.22. This explains the blocker: hidden-swap
does not sustain a different closed-loop action trajectory. See
`docs/m43-action-trajectory-intervention-diagnostics.md`.

### M44: Deterministic Action-Contrast Objective

- Replace M42's log-probability contrast with a direct action-mean distance
  contrast between normal recurrent hidden and per-step reset hidden.
- Keep the actor contract clean: no hidden vehicle parameters or rule labels.
- Treat the smoke only as trainability evidence; policy quality requires the
  same corpus, broad, and action-trajectory gates used for M42/M43.

Exit criteria:

- trainer logs `action_contrast_loss_mean`;
- M44 strict-loads M37_102 and completes a CUDA smoke;
- full run is evaluated against M37_102 and M42_028 on M38, M35, M29, broad,
  and action-trajectory gates.

Status: complete as a negative result. The full M44 run completed, but the best
M44 checkpoints only reach 0.6000 on M38 versus 0.6250 for M37_102, 0.6250 on
M35 versus 0.6500, and 0.8000 broad success versus 0.8250. M44 increases reset
and zero-response trajectory distances but hidden-swap outcome changes remain
zero and hidden-swap trajectory mean distance only rises to 0.006230. See
`docs/m44-action-contrast-objective.md`.

### M45: Paired-Hidden Snapshot Export

- Stop contrasting against zero hidden as the primary target.
- Export matched nominal/perturbed observations and recurrent hidden states,
  because M44 shows reset-hidden contrast does not transfer to hidden-swap.
- Keep the dataset deployable-observation compatible: observations plus policy
  recurrent hidden, not hidden vehicle parameters or rule labels.

Exit criteria:

- paired hidden-state snapshots can be exported or regenerated deterministically;
- exported arrays include accepted-pair observations and hidden states;
- docs record smoke and M37_102 300-seed export.

Status: complete as infrastructure. M45 adds
`autodrift.paired_hidden_snapshots`, exports 280 accepted M37_102 paired-hidden
snapshots from 300 seeds, and writes `pairs.csv`, `snapshots.npz`,
`summary.json`, and `manifest.json`. See
`docs/m45-paired-hidden-snapshot-export.md`.

### M46: Paired-Hidden Action Contrast

- Design a conservative objective that compares action means under matched
  nominal/perturbed hidden states.
- Avoid treating old checkpoint hidden vectors as generic labels after major
  representation drift.
- Preserve aggregate success gates before claiming progress.

Exit criteria:

- objective uses paired hidden states generated by the same checkpoint or by
  the current policy;
- validation uses M38, M35, M29, broad, and action-trajectory gates;
- result updates current-best status only if hidden-swap improves without
  aggregate regression.

Status: complete as M46 same-checkpoint objective below. The offline paired
hidden snapshots gave a usable auxiliary source, but fixed old hidden vectors
were not sufficient to pass the aggregate and intervention gates.

### M46: Same-Checkpoint Paired-Hidden Action Contrast

- Use the M45 NPZ as an offline paired-hidden auxiliary source.
- Start from M37_102 so the saved hidden vectors begin in the same latent
  coordinate system as the current policy.
- Keep the coefficient small because stale hidden vectors can become invalid if
  representation drift is large.

Exit criteria:

- trainer logs `paired_hidden_action_contrast_loss_mean`;
- M46 strict-loads M37_102 and completes a CUDA smoke;
- full run is evaluated against M37_102 and M42_028 on M38, M35, M29, broad,
  and action-trajectory gates.

Status: complete as a negative result. The full run strict-loads M37_102 and
finishes cleanly. M46_077 and M46_200 lightly improve the M38 mined corpus to
0.6375 success versus 0.6250 for M37_102, and they preserve M35 at 0.6500 and
M29 at 0.8750. Both regress the broad same-seed benchmark to 0.8000 versus
0.8250 for M37_102/M42_028. Action-trajectory gates show slightly larger
hidden-swap trajectory distances, up to 0.007083 for M46_200, but hidden-swap
outcome changes remain 0. Current best remains M37_102. See
`docs/m46-paired-hidden-action-contrast-objective.md`.

### M47: On-Policy Continuation Evidence

- Stop treating static old hidden vectors as universal labels after M46's
  broad regression.
- Mine or generate continuation-level evidence where an intervention changes
  future closed-loop behavior, not just first-step action means.
- Prefer objectives that preserve broad aggregate success before increasing
  hidden-state sensitivity.

Exit criteria:

- M47 design is based on measured M46 deltas and hidden-swap trajectories;
- any new objective is selected by M38/M35/M29/broad gates plus intervention
  outcome-change counts;
- current-best status changes only if M37_102 aggregate gates are preserved.

Status: complete as diagnostic infrastructure. M47 adds
`autodrift.seed_delta_audit` and uses it to locate M46's one M38 win and one
broad regression. M46 improves seed 4327, a high-friction unavoidable case with
weak brakes, weak tires, front cg, and slow steering. It regresses seed 3037, a
low-friction unavoidable case with strong brakes, nominal tires, nominal cg, and
slow steering. See `docs/m47-seed-delta-audit.md`.

### M48: Continuation-Level Critical Snippets

- Mine short closed-loop snippets around the M47 changed seeds and nearby
  matched cases.
- Compare action and outcome trajectories for M37_102, M42_028, M46_077, and
  M46_200 under the same deployed observation contract.
- Convert the evidence into a training or checkpoint-selection objective that
  protects low-friction unavoidable completion while keeping the high-friction
  weak-actuator improvement.

Exit criteria:

- snippet harness writes per-step observations, actions, rewards, terminal
  reason, and clearance around the obstacle;
- analysis explains the causal difference between seed 4327 and seed 3037;
- next training config or gate is based on continuation evidence, not static
  hidden-vector separation alone.

Status: complete as diagnostic infrastructure. M48 adds
`autodrift.continuation_snippets` and traces seeds 4327 and 3037 across M30_053,
M37_102, M42_028, M46_077, and M46_200. Both M46 outcome flips are millimeter
scale clearance-margin events: M46 wins seed 4327 by 0.000862 to 0.002488 m and
loses seed 3037 by -0.002355 to -0.007670 m. See
`docs/m48-continuation-critical-snippets.md`.

### M49: Clearance-Margin Gate

- Promote clearance margin to a first-class benchmark metric.
- Report collision radius and min-clearance margin in evaluation and benchmark
  outputs.
- Use margin-aware critical seeds to avoid treating millimeter near misses as
  robust driver progress.

Exit criteria:

- evaluator and benchmark outputs include collision radius and min-clearance
  margin when obstacles are enabled;
- tests cover margin computation;
- M37_102, M42_028, and M46 candidates can be compared by success and margin on
  M38, broad, and M48 changed seeds.

Status: complete as first-class metric infrastructure. M49 adds
`obstacle_collision_radius` and `min_clearance_margin` to env/evaluation rows,
benchmark summaries, and seed-delta audits, with unit coverage for each output
path. A changed-seed benchmark confirms the M48 conclusion: M46 has the same
binary success rate as M37_102 on seeds 4327 and 3037, but worse mean clearance
margin. Larger M38 and broad margin-critical corpus mining is split into M50.
See `docs/m49-clearance-margin-gate.md`.

### M50: Margin-Critical Corpus

- Mine a larger corpus where success is near the obstacle boundary or margin
  changes materially between policies.
- Include M38 response-critical seeds, broad same-seed sweeps, and fresh
  randomized obstacle seeds.
- Use margin buckets, not only binary success, for checkpoint promotion.

Exit criteria:

- corpus artifact includes seed, policy outcomes, min-clearance margin, margin
  bucket, road/vehicle buckets, and baseline/candidate deltas;
- M37_102, M42_028, M46_077, and M46_200 are compared on the corpus;
- next training or checkpoint-selection rule explicitly protects
  margin-critical low-friction unavoidable cases.

Status: complete as gate/corpus infrastructure. M50 adds
`autodrift.margin_critical_corpus`, mines M38, broad seed 3000, and fresh seed
5200 margin-aware benchmarks, and writes a top-100 near-boundary corpus from
480 policy pairs. M46 improves mean margin but also creates more near-boundary
margin regressions and still fails broad success, so current best remains
M37_102. See `docs/m50-margin-critical-corpus.md`.

### M51: Margin-Retention Training And Gate

- Convert the M50 corpus into a checkpoint promotion gate.
- Oversample M50 near-boundary rows in continuation training while preserving
  broad success.
- Add margin-aware reward/checkpoint selection for training only, without
  adding margin or oracle fields to actor observations.

Exit criteria:

- gate reports success, near-boundary margin regression count, and margin bucket
  deltas versus M37_102;
- training config consumes the M50 corpus without changing the human-view actor
  observation contract;
- candidate checkpoint is promoted only if broad success and near-boundary
  margin regressions do not regress versus M37_102.

Status: complete as gate and training-config infrastructure. M51 adds
`autodrift.margin_retention_gate`, a strict pass/fail gate over full
margin-critical deltas, plus `configs/ppo_m51_margin_retention_driver.json`.
The current M42/M46 candidates all fail strict margin retention. A 4096-step
M51 smoke strict-loads M37_102 and trains end to end, but its checkpoint also
fails the gate, so it is not promoted. See
`docs/m51-margin-retention-gate.md`.

### M52: Full Margin-Retention Continuation

- Run full M51 training from M37_102.
- Sweep checkpoints through M51 strict gate, M50 margin-critical corpus, broad
  same-seed success, and hidden-swap/action-trajectory diagnostics.
- Promote only if aggregate success is retained and near-boundary margin
  regressions are not introduced.

Exit criteria:

- full M51 run completes and writes checkpoint snapshots;
- checkpoint sweep includes M37_102 baseline and at least two M51 snapshots;
- M51 gate status and failure reasons are recorded for every candidate;
- current best updates only if a checkpoint passes aggregate and
  margin-retention gates.

Status: complete as a negative result. The full M51 run strict-loads M37_102
and completes 200k steps, but every checkpoint fails the strict
margin-retention gate. The least-bad checkpoint, M51_028, still drops combined
success by 0.01875, has 3 binary regressions, 10 near-margin regressions, and
mean margin delta `-0.015016`. Current best remains M37_102. See
`docs/m52-full-margin-retention-continuation.md`.

### M53: Deduplicated Low-Mix Margin Retention

- Convert the row-level M50 corpus into a deduplicated seed-level training
  sequence.
- Reduce hard-seed mix probability so broad randomized retention remains
  dominant.
- Keep M51 strict gate as the promotion gate.

Exit criteria:

- seed-level corpus artifact records unique seed count, source distribution,
  and source/candidate row multiplicity;
- training config uses the deduplicated corpus with lower mix probability;
- smoke train proves the config runs before full continuation.

Status: complete as infrastructure and smoke validation. M53 adds
`autodrift.training_seed_corpus`, produces a 41-seed deduplicated training
sequence from the 100-row M50 corpus, and adds
`configs/ppo_m53_dedup_low_mix_margin_retention_driver.json` with hard-seed mix
reduced to 0.35. The M53 smoke is not promotable, but it is materially less
damaging than M51 smoke: M38 success is retained and combined mean margin is
positive, while broad still regresses by one seed. See
`docs/m53-dedup-low-mix-margin-retention.md`.

### M54: Full Deduplicated Low-Mix Continuation

- Run full M53 training from M37_102.
- Sweep checkpoints through M51 strict margin-retention gate and M50/M53
  margin-critical benchmarks.
- Promote only if broad success, binary regressions, and near-boundary margin
  regressions all pass.

Exit criteria:

- full M53 run completes and writes checkpoint snapshots;
- M38/broad/fresh checkpoint sweep is run against M37_102;
- strict gate reports pass/fail for each checkpoint;
- current best updates only if a checkpoint passes strict gate and does not
  weaken existing aggregate/self-identification evidence.

Status: complete as a negative promotion result. M54 full training completes
and the checkpoint sweep shows that deduplicated low-mix training is less
damaging than M52, but every checkpoint still fails strict margin retention.
The least-damaging checkpoints retain M38 and fresh success and slightly
improve mean margin, but they still introduce two near-boundary binary
regressions, including broad seed `3037` and M38 seed `4457`. Current best
remains M37_102. See `docs/m54-full-dedup-low-mix-continuation.md`.

### M55: Conservative Early-Checkpoint Margin Retention

- Run a short, lower-learning-rate continuation from M37_102.
- Reduce hard-seed mix further so broad randomized retention dominates.
- Save dense early checkpoints to test whether there is a small update window
  that improves margin without flipping near-boundary positive cases.

Exit criteria:

- short M55 run completes and writes 4096-step checkpoint snapshots;
- M38/broad/fresh checkpoint sweep is run against M37_102;
- strict gate reports zero binary regressions and zero near-margin regressions
  before any checkpoint can be promoted;
- if all checkpoints fail, the failed seeds are added to the next diagnosis
  corpus rather than weakening the gate.

Status: complete as a negative promotion result. M55 keeps broad and fresh
success at M37 levels and its earliest checkpoint has zero binary regressions,
but every checkpoint still fails strict margin retention because mean clearance
margin is lower than M37 and near-boundary margin regressions remain. The
failure is now objective-related rather than data-mixture-only. See
`docs/m55-conservative-margin-retention.md`.

M55 uses
`configs/ppo_m55_conservative_dedup_margin_retention_driver.json` with
`learning_rate = 1e-5`, `training_seed_mix_probability = 0.15`, no low-mu-only
curriculum stage, `32768` total steps, and dense `4096`-step checkpoints.

### M56: Terminal Clearance-Margin Reward

- Add an optional terminal clearance-margin reward term to obstacle tasks.
- Keep the actor observation contract unchanged.
- Reuse the M55 conservative schedule so the ablation is isolated to reward
  shaping.

Exit criteria:

- reward term is config-gated and defaults to disabled;
- tests cover reward off/on behavior and ensure observations do not gain margin
  fields;
- M56 training completes from M37_102;
- M38/broad/fresh strict gate is run unchanged;
- promotion requires zero binary regressions, zero near-margin regressions, and
  non-negative mean margin delta.

Status: complete as a negative promotion result and a positive objective
direction. M56 adds the config-gated terminal clearance-margin reward,
tests reward off/on behavior, smoke-trains from M37_102, and completes a full
short continuation. No checkpoint passes strict margin retention. The best
checkpoint, M56_028, has zero binary regressions and zero near-margin
regressions, but still has mean margin delta `-0.001527`. See
`docs/m56-terminal-clearance-margin-reward.md`.

### M57: Stronger Terminal Clearance-Margin Reward

- Rerun the M56 schedule with terminal clearance-margin reward scale increased
  from `2.0` to `4.0`.
- Keep actor observations and strict promotion gate unchanged.
- Treat failure as evidence that sparse terminal reward is insufficient and a
  denser near-obstacle clearance signal is needed.

Exit criteria:

- M57 training completes from M37_102;
- M38/broad/fresh strict gate is run unchanged;
- promotion requires zero binary regressions, zero near-margin regressions, and
  non-negative mean margin delta;
- if no checkpoint passes, document whether stronger sparse reward improves or
  damages the M56_028 near-pass result.

Status: complete as a negative result. M57 keeps broad and fresh success, but
does not improve on the M56 near-pass. Stronger sparse terminal reward still
leaves negative mean margin and introduces more near-margin regressions than
the best M56 checkpoint. See `docs/m57-clearance-margin-reward-scale4.md`.

M57 uses `configs/ppo_m57_clearance_margin_reward_scale4_driver.json`.

### M58: Dense Near-Obstacle Clearance Reward

- Add an optional dense clearance-margin reward active only near the obstacle
  encounter window.
- Keep actor observations clean and leave the strict promotion gate unchanged.
- Compare against the M56/M57 sparse terminal reward results.

Exit criteria:

- dense reward is config-gated and defaults to disabled;
- tests cover reward off/on behavior and observation dimension stability;
- M58 training completes from M37_102;
- strict M38/broad/fresh margin-retention gate is run unchanged;
- if no checkpoint passes, decide whether to pursue a separate margin critic,
  baseline-action distillation, or abandon margin shaping in favor of a larger
  seed distribution.

Status: complete as a negative result. M58 adds the config-gated dense
near-obstacle clearance reward, tests reward off/on behavior, smoke-trains from
M37_102, and completes a full short continuation. It is not promotable: early
checkpoints can have zero binary and near-margin regressions, but mean margin
is worse than M56/M57, and later checkpoints reintroduce binary regressions.
See `docs/m58-dense-near-obstacle-clearance-reward.md`.

### M59: Trust-Region Checkpoint Interpolation

- Build a small interpolation/probe harness between M37_102 and closest
  non-promoted candidates such as M56_028.
- Evaluate interpolated checkpoints through the unchanged strict margin gate.
- Use this as a trust-region diagnostic before more reward shaping.

Exit criteria:

- interpolation artifacts record source checkpoints, alpha values, and output
  paths;
- M38/broad/fresh strict gate is run unchanged;
- if any interpolated checkpoint passes, it is treated as a candidate only
  after the broader driver gates are rerun;
- if none pass, next work should focus on constrained policy updates or
  baseline-action distillation, not further reward-scale tuning.

Status: complete as a negative diagnostic. M59 adds a reusable checkpoint
interpolation harness and evaluates seven M37_102 to M56_028 interpolation
alphas through the unchanged M38/broad/fresh strict margin-retention gate. All
interpolated checkpoints retain success and have zero binary and near-margin
regressions, but every nonzero alpha has negative mean clearance-margin delta;
the strict gate rejects all candidates. See
`docs/m59-trust-region-checkpoint-interpolation.md`.

### M60: Constrained Baseline-Anchored Margin Update

- Use M59/M56 evidence to avoid further reward-scale tuning along the same
  parameter direction.
- Build a constrained update that anchors deterministic actions to M37_102 on
  non-critical states while allowing margin-improving changes on mined
  near-boundary snippets.
- Keep actor observations clean and keep the strict margin-retention gate
  unchanged.

Exit criteria:

- training/evaluation data separates critical margin snippets from retained
  background states;
- action-anchor loss is config-gated and defaults to disabled;
- smoke training logs action-anchor and margin terms;
- M38/broad/fresh strict margin gate is rerun unchanged;
- any candidate that passes margin retention must still rerun broader driver
  gates before promotion.

Status: complete as a negative result. M60 adds the frozen baseline-action
anchor, completes a full continuation from M37_102, and runs the unchanged
M38/broad/fresh strict margin-retention gate. It is not promotable: some
checkpoints reach non-negative mean margin delta, but all such checkpoints
introduce binary or near-margin regressions. The blocker is now concentrated in
specific near-boundary seeds such as 4413, 4378, 4457, and 3019. See
`docs/m60-constrained-baseline-anchor.md`.

### M61: Regression-Seed Retention Replay

- Build a tiny replay/seed corpus from M60 near-boundary regressions.
- Strengthen or schedule the baseline-action anchor so near-boundary failures
  cannot become much deeper while pursuing margin gains elsewhere.
- Keep actor observations clean and keep the strict gate unchanged.

Exit criteria:

- regression seeds are stored as a reproducible seed corpus;
- M60 regression seeds are oversampled in training or used by a dedicated
  retention term;
- smoke training logs the stronger retention setup;
- M38/broad/fresh strict margin gate is rerun unchanged;
- promotion still requires zero binary regressions, zero near-margin
  regressions, and non-negative mean margin delta.

Status: complete as a negative but improved result. M61 replays the M60
regression seeds and strengthens the baseline-action anchor. It does not pass
the strict gate, but `m61_032` has zero binary regressions and positive combined
mean margin delta; the remaining blocker is three near-margin regressions on
unchanged failures. See `docs/m61-regression-seed-retention-replay.md`.

### M62: Positive-Margin Checkpoint Interpolation

- Reuse the M59 checkpoint interpolation harness, but interpolate M37_102 toward
  `m61_032` instead of M56_028.
- Test whether a smaller step preserves M61's positive mean-margin direction
  while eliminating the remaining three near-margin regressions.
- Keep the strict margin-retention gate unchanged.

Exit criteria:

- interpolation artifacts record M37_102, M61_032, alpha values, and output
  paths;
- M38/broad/fresh strict margin gate is run unchanged;
- any passing candidate is treated as a candidate only after broader driver
  gates are rerun;
- if none pass, next work should add an explicit near-boundary failure-depth
  floor rather than more replay alone.

Status: complete as the first positive margin-retention result. M62
interpolates M37_102 toward M61_032 and passes the unchanged strict gate for
`m62_a125` and `m62_a250`. The stronger candidate `m62_a250` keeps M38/broad/
fresh success unchanged, has zero binary and near-margin regressions, and has
positive mean margin delta. Hidden-swap audit does not regress versus M37_102,
but recurrent self-identification remains unsolved. See
`docs/m62-positive-margin-checkpoint-interpolation.md`.

### M63: Broader Driver Audit for M62

- Treat `m62_a250` as the current best margin-retention candidate.
- Rerun broader deployable-driver gates that are compatible with the human-view
  observation contract.
- Compare held-out benchmark, history/action ablations, hidden-swap summary,
  and any existing driver gate artifacts against M37_102.

Exit criteria:

- audit artifacts identify whether M62 can replace M37_102 as the broader
  current-best driver, not only the margin-retention candidate;
- if it passes, update current-best docs and queue state accordingly;
- if it fails, keep M62 as a margin-retention candidate and design the next
  architecture/probe task.

Status: complete. M63 shows `m62_a250` keeps M37 aggregate success and slightly
improves mean clearance margin on a 120-episode held-out audit, but response and
history ablations remain too weak. M62 remains the current best
margin-retention candidate, not an ideal driver. See
`docs/m63-broader-driver-audit.md`.

### M64: Stronger Response-History Self-Identification Gate

- Build a sharper gate for M62-class human-view recurrent policies.
- Focus on scenarios where resetting recurrent state or removing response
  features must change behavior.
- Avoid adding oracle fields to actor observations.

Exit criteria:

- gate uses deployable observations and controlled perturbations only;
- M62 and M37 are both evaluated on the same cases;
- the result clearly separates "can drive" from "uses closed-loop response
  history";
- if the gate is still insensitive, document why and design the next training
  objective around that measured failure.

Status: complete as a negative diagnostic. M64 adds a seed-delta audit over the
M63 broader-driver episodes and a paired nominal/low-friction perturbation gate
for M37_102, `m62_a250`, and their reset, zero-response, and no-action-history
ablations. The ablations remain too strong: reset hidden and zero-response
variants do not meaningfully reduce perturbed success. M37_102 and M62_a250
behave nearly identically on the paired grid. M62 remains the current best
margin-retention candidate, but it is not a self-identification pass. See
`docs/m64-stronger-response-history-self-identification-gate.md`.

### M65: Response-History Necessity Objective

- Target the measured M64 failure directly instead of improving aggregate
  success alone.
- Mine or construct a response-necessity corpus from paired perturbation
  episodes where closed-loop response history should change behavior.
- Add a training objective or continuation setup that makes deployable response
  history behavior-critical without adding hidden vehicle parameters,
  controller mode, oracle labels, or rule inputs to the actor.

Exit criteria:

- corpus or objective artifacts are reproducible from recorded seeds;
- actor observations remain the clean human-view contract;
- M62/M37 baselines and new candidates are evaluated on the same paired
  perturbation, ablation, margin-retention, and broader-driver gates;
- promotion requires both no aggregate regression and stronger degradation
  under response/history ablations.

Status: complete as infrastructure plus smoke validation. M65 adds
`response_necessity_corpus.py`, a CLI entry point, tests, and
`configs/ppo_m65_response_necessity_driver.json`. The real M64 paired episodes
produce 26 critical seeds and 104 repeated training-seed rows. A 4096-step
smoke continuation from M62_a250 succeeds and logs both response-prediction and
baseline-action-anchor losses. See `docs/m65-response-necessity-corpus.md`.

### M66: Full Response-Necessity Continuation

- Run the M65 continuation config at full length from M62_a250.
- Sweep dense checkpoints through the same M38/broad/fresh margin-retention
  gates used for M62.
- Rerun the M63 broader-driver audit and M64 paired self-identification gate on
  any candidate that keeps aggregate success and margin retention.

Exit criteria:

- full training artifact exists and checkpoints are evaluated reproducibly;
- no candidate is promoted unless it keeps strict margin retention;
- self-identification evidence must improve versus both M37_102 and M62_a250;
- if no checkpoint improves the M64 ablation signal, record a negative result
  and redesign the training objective rather than increasing replay alone.

Status: planned.

## Metrics

- episode success rate;
- lateral RMSE and peak error;
- sideslip magnitude and high-sideslip fraction;
- speed error;
- spin-out/off-track rate;
- actuator saturation frequency;
- minimum obstacle distance for avoidance tasks;
- minimum clearance margin for obstacle avoidance tasks;
- collision/off-road/spin-out counts;
- metrics grouped by `mu` bucket, mass bucket, and path segment type.

## Project Quality Gates

- Every task has a deterministic seed-based regression case.
- Every baseline can run through the same evaluation CLI.
- Every benchmark writes machine-readable metrics.
- Long training commands are optional; smoke commands finish quickly.
- Documentation stays aligned with runnable commands.

## Current Commands

```bash
pytest
PYTHONPATH=src python3 -m autodrift.evaluate --episodes 5 --policy heuristic
PYTHONPATH=src python3 -m autodrift.train_ppo --config configs/ppo_smoke.json
PYTHONPATH=src python3 -m autodrift.benchmark --episodes 2 --policies heuristic random
```
