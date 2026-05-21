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

Status: complete as a negative result. M66 full continuation runs from M62_a250
and evaluates all dense checkpoints against the unchanged strict
margin-retention gate. No checkpoint passes. `m65_004` is closest, with no
binary regression but one near-margin regression and negative mean margin
delta. Its paired perturbation gate is effectively unchanged from M62_a250, so
the response-necessity replay did not create stronger self-identification. See
`docs/m66-full-response-necessity-continuation.md`.

### M67-A: Privileged Upper-Bound Before Student Objectives

- Stop treating seed replay alone as sufficient for self-identification.
- First train/evaluate a privileged teacher that sees a teacher-only full hidden
  dynamics packet.
- Compare the teacher against `m62_a250` on M65 response-critical seeds using the
  same seed sequence but separate env configs.
- Use the result to decide whether the current corpus is truly
  self-identification-critical.

Exit criteria:

- full-dynamics privileged observation is implemented without changing the
  deployable 72-value actor frame;
- privileged teacher config trains and writes checkpoints;
- upper-bound harness writes per-seed deltas between human-view and privileged
  policies;
- full teacher evaluation either shows a meaningful upper-bound gap or forces
  M67-B corpus re-mining.

Status: smoke infrastructure complete. The teacher-only `full_dynamics`
privileged packet produces an 82-value observation, the smoke teacher trains on
CUDA, and the `autodrift.privileged_upper_bound` harness compares `m62_a250`
against a privileged checkpoint under different env configs. See
`docs/m67a-privileged-upper-bound-harness.md`.

### M67-B: Full Privileged Teacher Upper-Bound Attempt

- Run the full M67-A privileged teacher training schedule.
- Sweep dense checkpoints on the M65 response-critical corpus.
- Promote the teacher as a real upper-bound only if it beats `m62_a250` on
  success or clearance margin.

Status: complete as a negative upper-bound attempt. The final teacher has M65
success `0.461538` and mean margin `0.191716`; the best swept checkpoint
`m67a_232` reaches success `0.500000` and mean margin `0.213538`. Both are below
`m62_a250` at success `0.615385` and mean margin `0.304161`. The likely blocker
is teacher optimization, not a proof that hidden dynamics is useless: the
from-scratch `online_gru` teacher never reaches M62's retained driving behavior.
See `docs/m67b-full-privileged-upper-bound-training.md`.

### M67-C: Input Profile Audit

- Record the observation-profile review and code-level risks before changing the
  next architecture.
- Keep current 72-value human-view as the main baseline.
- Add a strict self-ID profile that removes obstacle-relative-velocity motion
  proxies from the context branch before using zero-response ablations as strong
  evidence.
- Defer enhanced OSI response features and noisy IMU until strict-context smoke
  is implemented.

Status: complete as a planning/documentation task. The concrete next task is
M67-D strict self-ID context profile. See
`docs/m67c-input-profile-audit.md`.

### M67-D: Strict Self-ID Observation Profile

- Add a config-gated obstacle relative velocity mode:
  `ego` for current behavior and `zero` for strict self-ID diagnostics.
- Preserve the 72-value observation shape for the first strict profile.
- Add tests proving static obstacle rel-vx/rel-vy can be zeroed without changing
  the deployable actor input contract.
- Add a strict-context driver config and smoke benchmark against current 72.

Status: complete as infrastructure and mixed diagnostic. The strict profile
preserves the 72-value shape, zeros obstacle relative velocity, loads M62
strictly, and keeps M62 baseline success unchanged on the M65 corpus. It does
not make reset-hidden or zero-response ablations more behavior-critical, so the
next gate still needs wrong-history or matched-history interventions. See
`docs/m67d-strict-self-id-observation-profile.md`.

### M67-E: Warm-Started Privileged Teacher

- Build a privileged teacher architecture that preserves M62's human-view
  response/context split for the first 72 deployable inputs and appends the
  full hidden dynamics packet as teacher-only context.
- Warm-start or anchor the teacher from `m62_a250` where tensor shapes permit.
- Re-run the M65 upper-bound comparison before any deployable student OSI
  objective.

Status: complete as infrastructure and weak/negative upper-bound evidence.
`privileged_human_view_online_gru` preserves the first 72 M62-compatible inputs,
adds a teacher-only 10-value full-dynamics branch, and zero-initializes the
privileged residual so M62 initialization preserves behavior. A 32768-step run
from `m62_a250` completed, but the best swept checkpoint `m67e_004` only changes
M65 mean clearance margin by `+0.000804` with no success improvement and an even
13/13 improved/regressed seed split. This is retention noise, not a credible
hidden-dynamics upper bound. See
`docs/m67e-warm-started-privileged-teacher.md`.

### M68: Matched Action-Divergent Corpus

- Mine or construct pairs where current visible state and road/obstacle geometry
  are nearly identical, but hidden dynamics require different actions.
- Score candidate pairs by action distance, rollout margin gap under wrong
  hidden/history, and whether wrong-history intervention reduces clearance.
- Use the resulting corpus to decide whether the current M65 proof surface is
  genuinely self-identification-critical.

Exit criteria:

- writes `matched_pairs.csv` and an action-divergence summary;
- reports how often hidden dynamics changes the preferred action or terminal
  margin under matched visible context;
- identifies candidate seeds/snippets for wrong-history intervention gates.

Status: complete as a harness and smoke diagnostic. The new
`autodrift.matched_action_corpus` command writes matched pairs, action-divergent
snippets, summary CSV/JSON, and a manifest. On the M65 corpus with `m67e_004`,
10/26 pairs pass strict visible matching and 6/26 pass action divergence, but all
6 are paired-action differences, only 1 crosses wrong-history action divergence,
and 0 cross privileged-packet action divergence. The privileged packet action
distance mean is only `0.000075`, so this is not yet a useful teacher corpus.
See `docs/m68-matched-action-divergent-corpus.md`.

### M69: Broader Matched Hidden-Dynamics Mining

- Run M68 on broader fresh seed sweeps rather than only the M65 response
  necessity corpus.
- Sweep hidden perturbation axes beyond friction, especially weak braking and
  slow actuator response.
- Rank and select pairs by wrong-history or privileged-packet action divergence,
  not just nominal-versus-perturbed current-action distance.
- Decide whether the simulator task distribution can produce enough causal
  self-ID pairs for a student objective.

Status: complete as a broader negative diagnostic. Fresh 80-seed sweeps across
friction, weak-brake, and slow-actuator axes still produce 0 privileged-packet
divergent pairs. Weak-brake is the most promising axis for wrong-history
divergence, with 3/80 pairs crossing the threshold. See
`docs/m69-broader-matched-hidden-dynamics-mining.md`.

### M70: Wrong-History Continuation Gate

- Replay the M69 wrong-history candidate seeds from matched decision snapshots.
- Compare normal recurrent history against wrong-history, reset, and zero
  response continuations.
- Measure clearance margin, collision, terminal reason, and action-trajectory
  distance.
- Promote snippets only if wrong history degrades outcome, not merely first
  action.

Status: complete as a negative outcome-causality result. `hidden_swap_gate` now
reports `min_clearance_margin` in continuation summaries. On weak-brake
candidates `7019`, `7059`, and `7002`, hidden-swap changes first action but
keeps success at 1.0 and changes mean margin by only `-0.000213 m`. On friction
candidate `6905`, success also stays 1.0 and mean margin delta is `+0.000670 m`.
See `docs/m70-wrong-history-continuation-gate.md`.

### M71: Outcome-Sensitive Matched Scenario Constructor

- Construct or mine near-boundary paired cases where normal-history margin is
  positive but wrong-history margin drops by a preregistered threshold.
- Prefer weak-brake and low-friction contrasts, because M69/M70 showed actuator
  delay and passive wrong-history candidates are too weak.
- Reject candidates where first-action divergence does not affect continuation
  margin or success.

Status: planned after M70. M70 showed that first-action wrong-history candidates
are not enough; the next proof surface must be outcome-sensitive by construction.

Status update: complete as infrastructure and negative smoke. M71 added
`python -m autodrift.outcome_sensitive_corpus`, visible-state matching,
normal-vs-wrong-history success/margin acceptance, obstacle geometry overrides,
and missing-scenario error capture. Four 20-seed smoke runs across baseline and
tight weak-brake / low-friction settings produced zero accepted
outcome-sensitive pairs. See
`docs/m71-outcome-sensitive-matched-scenario-constructor.md`.

### M72: Pre-Emergency Warm-Up History Harness

- Build a gate where hidden dynamics evidence can accumulate before the obstacle
  appears.
- Compare normal warm-up history against wrong matched warm-up history, reset
  history, zero action history, and zero response history.
- Keep actor observations deployable and use hidden parameters only for pairing,
  logging, or teacher diagnostics.
- Require outcome-level success or clearance-margin differences under strict
  visible-state matching before any student OSI distillation.

Status: planned after M71. Passive matched snapshots are still not producing
causal wrong-history outcome gaps, so the next proof surface needs explicit
pre-emergency response evidence.

M72-A status: obstacle perception reveal infrastructure added. The obstacle can
remain physically active while actor obstacle slots stay zero until
`perception_reveal_step` and/or `perception_reveal_distance` pass. This preserves
the actor observation shape and creates the basis for warm-up history gates. See
`docs/m72-pre-emergency-warmup-history-harness.md`.

M72-B status: complete as negative smoke. The outcome-sensitive miner can now
override obstacle reveal controls. Weak-brake and low-friction warm-up reveal
smokes produced zero accepted outcome-sensitive pairs; max margin gaps stayed
below `0.01 m`. The next step is active probing rather than passive warm-up.

### M73: Active-Probing Warm-Up Harness

- Add a harness or task variant where the policy can produce small
  safety-bounded steering/brake/throttle excitations before obstacle reveal.
- Compare normal probing history against wrong matched probing history and
  reset/zero-history interventions.
- Penalize unsafe probing and keep all actor inputs deployable.
- Accept only if probing history changes outcome under strict visible-state
  matching.

Status: complete as infrastructure and mixed negative diagnostic. M73 added
active probing to `outcome_sensitive_corpus` and ran weak-brake, low-friction,
and strong low-friction probing smokes. Mild probing found no accepted snippets.
Strong low-friction probing created up to `0.040596 m` wrong-history margin gap,
but only in invalid collision-to-collision or non-strict-context rows. See
`docs/m73-active-probing-warmup-harness.md`.

### M74: Active-Probe Outcome-Bound Scenario Sweep

- Start from M73 high-gap active-probe near misses.
- Sweep obstacle distance and width around those seeds and hidden-dynamics
  contrasts.
- Search for normal-probing-history success or positive near-boundary margin
  versus wrong-probing-history collision or `>= 0.01 m` margin loss.
- Keep strict visible response/context matching as the promotion gate.

Status: complete as a negative geometry-sweep result. Easier, medium, hard, and
default dense-target sweeps around the M73 near-miss seeds produced zero accepted
outcome-sensitive snippets. The default dense-target sweep reproduced a
`0.045526 m` margin gap, but only in invalid collision-to-collision or
non-strict-context rows. See
`docs/m74-active-probe-outcome-bound-scenario-sweep.md`.

### M75: Snapshot-Level Obstacle Relocation Sweep

- Collect active-probe snapshots that preserve the M73 high-gap probing history.
- Deep-copy the same env and mutate only obstacle position / half-width.
- Replay normal and wrong probing histories from the same ego and recurrent
  state.
- Search for strict visible matches where normal history succeeds or keeps
  positive near-boundary margin and wrong history collides or loses margin.

Status: complete as infrastructure and negative strict diagnostic. M75 added
snapshot-level obstacle relocation to `outcome_sensitive_corpus`, preserving the
copied env, recurrent hidden state, active-probe metadata, and current
action-response history while sweeping obstacle body-frame position and
half-width. Strict sweeps produced stronger margin-gap rows than M74 but zero
accepted outcome-sensitive snippets. A relaxed diagnostic accepted `2`
wrong-history margin-loss snippets, confirming the harness is useful but the
strict same-target snapshot pairing remains too weak. See
`docs/m75-snapshot-level-obstacle-relocation-sweep.md`.

### M76: Snapshot-Bank Visible Matcher

- Collect multiple active-probe snapshots per seed and condition instead of one
  nearest shared target distance.
- Pair nominal and perturbed snapshots by actual visible response/context
  distance.
- Apply M75 snapshot-level obstacle relocation only after a visible-state match
  is selected.
- Rank candidates by strict visible match, normal-success or near-boundary
  margin, and wrong-history margin loss.

Status: complete as infrastructure and negative strict diagnostic. M76 added a
snapshot-bank relocation harness that collects many active-probe snapshots,
pairs nominal/perturbed states by visible response/context distance, and then
applies M75 relocation. The strict smoke improved mean visible distance to
`0.234060` and found `144 / 432` strict visible matches, but still produced zero
accepted outcome-sensitive snippets. A relaxed diagnostic found one
wrong-history margin-loss row, blocked by slightly loose context distance and
large normal margin. See `docs/m76-snapshot-bank-visible-matcher.md`.

### M77: Boundary-Aware Snapshot Relocation

- Start from M76 visible-matched snapshot-bank pairs.
- Adaptively sweep or search obstacle body position / half-width to place the
  normal-history rollout near the clearance boundary.
- Keep the strict visible-state gate; do not accept high-margin relaxed rows as
  proof.
- Promote snippets only when normal history succeeds or has positive
  near-boundary margin and wrong history loses at least the pre-registered
  margin threshold.

Status: complete as a negative gate. M77 reused the M76 snapshot-bank harness
with a dense obstacle half-width sweep around the high-signal relocation region.
It produced `1344` candidates, `448` strict visible matches, and `52`
margin-gap rows, but zero accepted snippets. Large gaps are
collision-to-collision; successful near-boundary rows only lose millimeters
under wrong history. See `docs/m77-boundary-aware-snapshot-relocation.md`.

### M78: Outcome-Weighted Intervention Objective

- Use M76/M77 rows as weighted intervention snippets instead of continuing to
  mine geometry-only cases.
- Weight snippets by wrong-history margin loss and normal-history boundary
  proximity.
- Train a small continuation objective or auxiliary value/preference head that
  makes outcome-relevant history differences affect risk/action estimates.
- Keep strict margin-retention and aggregate-driving gates as guards.

Status: complete as infrastructure and negative smoke. M78 added an
outcome-weighted hidden-intervention auxiliary loss, exports weighted snippet
NPZ files from snapshot-bank relocation, and wires the loss into PPO metrics.
The deployable human-view snippet export contains `671` rows with weight sum
`0.299190`. A 4096-step CPU smoke logs `outcome_intervention_loss_mean`, but
offline loss slightly worsens from `0.039923` to `0.040302`, so the checkpoint is
not a candidate. See `docs/m78-outcome-weighted-intervention-objective.md`.

### M79: Outcome Objective Weight Tuning

- Normalize or sharpen outcome snippet weights so near-boundary rows dominate
  the auxiliary objective.
- Sweep a higher `outcome_intervention_aux_coef` in short CPU smokes.
- Use fixed-batch offline objective loss as a required smoke gate before any
  full continuation.
- Continue to protect M62/M67E retention behavior with baseline-action anchor
  and strict margin-retention gates.

Status: complete as infrastructure and a negative tuning result. M79 added a
fixed-batch `outcome_intervention_eval` harness and reproduced the M78 offline
loss regression. A higher-coefficient 4096-step smoke also worsened the
fixed-batch loss from `0.039923` for `m62_init` to `0.041033` for
`m79_highcoef`, while short eval termination rose to `0.5`. The objective is
therefore still not ready for a long continuation. See
`docs/m79-outcome-objective-weight-tuning.md`.

### M80: Outcome Objective-Only Sanity Check

- Isolate `outcome_weighted_intervention_loss` outside PPO and environment
  rollouts.
- Start from the M62-compatible actor and optimize only the M78 human-view
  snippet NPZ for a short fixed number of steps.
- Compare fixed-batch loss before and after with the M79 evaluator.
- If objective-only training cannot reduce the loss, fix the objective/sign/data
  before touching PPO again.
- If objective-only training can reduce the loss, reintroduce PPO and the
  baseline-action anchor gradually.

Status: planned after M79. M79 shows coefficient scale is not the blocker by
itself; the next evidence step is to prove the loss is locally optimizable in
isolation.

Status: complete with a positive objective-only sanity result. M80 added an
isolated optimizer for `outcome_weighted_intervention_loss`, froze `log_std` by
default, and reduced fixed-batch loss from `0.039923` to `0.008483` over 200
CPU steps from `m62_a250`. A 5-episode same-seed smoke did not show immediate
driving collapse, but this is not a promotion gate. See
`docs/m80-outcome-objective-only-sanity-check.md`.

### M81: Wheel Response Self-ID Input Branch

- Add deployable wheel/tire response signals to the response GRU stream rather
  than the scene context branch.
- Start with front/rear wheel speed, wheel acceleration, slip proxy, brake
  pressure, drive torque, and simple ABS/TCS proxy signals for the current
  bicycle/single-track simulator.
- Keep the deployable actor blind to true friction, true tire limits, oracle
  saturation labels, reference trajectories, and feasibility labels.
- Compare current, command-response-error, front/rear wheel, four-wheel, and
  noisy/delayed sensor profiles.
- Gate the branch with zero-wheel, wrong wheel-history, and high/low-friction
  wheel-history injection tests, not success rate alone.

Status: complete as Stage 1 infrastructure. M81 adds a config-gated
`front_rear` wheel-response observation profile, an 85-value
`wheel_human_view_online_gru` actor, checkpoint loading support, and
`zero_wheel_response` benchmark ablation. The 4096-step smoke trains end to
end, but the checkpoint is not a candidate (`termination_rate = 1.0` on the
2-episode eval). See `docs/m81-wheel-response-input-roadmap.md`.

### M82: PPO Reintroduction For Outcome Objective

- Reintroduce the M78 outcome objective into PPO only after M81 input work or as
  a small guarded branch.
- Use the M80 objective-only result as the reference guard.
- Keep low learning rate, fixed-batch objective checks, short same-seed eval,
  and strict margin-retention gates.
- Freeze or explicitly monitor `log_std` so objective improvement is not a
  variance-only artifact.

Status: complete as a guarded but still negative smoke. M82 adds
`freeze_log_std` and a lower-learning-rate outcome PPO config. It improves the
fixed-batch loss relative to M78/M79 (`0.040120` versus `0.040302`/`0.041033`),
but remains worse than `m62_init` (`0.039923`) and the short driving smoke has
`termination_rate = 0.5`. See
`docs/m82-outcome-objective-ppo-reintroduction.md`.

### M83: Wheel Response Driver Training Gate

- Train the new 85-value wheel-response recurrent driver beyond smoke scale.
- Compare against the 72-value M62 baseline on same-seed obstacle and
  margin-retention gates.
- Run `zero_wheel_response`, `zero_all_response`, and `reset_recurrent_state`
  ablations.
- Do not promote unless wheel/history dependence improves without aggregate
  margin regression.

Status: complete as a negative training gate. A 32k-step CUDA run from scratch
reaches only `success_rate = 0.1` on the 20-episode wheel gate, worse than the
heuristic baseline (`0.4`). `zero_wheel_response`, `zero_all_response`, and
`reset_recurrent_state` produce only weak differences because the normal policy
already fails most episodes. See
`docs/m83-wheel-response-driver-training-gate.md`.

### M84: M62-to-Wheel Partial Initialization

- Add a warm-start path from the retained 72-value `human_view_online_gru`
  checkpoint into the 85-value `wheel_human_view_online_gru` actor.
- Copy the first 12 response columns from the source response encoder and keep
  new wheel-response columns neutral at initialization.
- Copy context encoder, GRU, fusion, actor, critic, and `log_std` where shapes
  match.
- Run the same short wheel-response continuation and zero-wheel/history gates.

Status: complete as a positive retention/infrastructure result. M84 adds
behavior-preserving partial initialization from M62 into the wheel actor. A
4096-step CUDA smoke loads with `partial_wheel_response_encoder` and gets
`termination_rate = 0.0`; the 20-episode gate reaches `success_rate = 0.90`
versus heuristic `0.40` and M83 `0.10`. This is not a wheel self-ID pass because
`m84_zero_wheel` also reaches `0.90`. See
`docs/m84-m62-to-wheel-partial-init.md`.

### M85: Warm-Started Wheel Response Auxiliary Continuation

- Start from the M84 partial initialization path.
- Add a stronger wheel/body response prediction target, such as the full
  25-value response stream or a compact wheel/body response envelope.
- Keep M62/M84 retention guards and avoid hidden dynamics actor inputs.
- Gate normal, `zero_wheel_response`, `zero_all_response`, and reset-hidden
  variants after continuation.

Status: complete as a retention-positive but self-ID-negative smoke. M85
expands the auxiliary target to the full 25-value response stream and keeps
`success_rate = 0.90`, but `m85_zero_wheel` also remains `0.90` and wheel
response encoder columns stay tiny relative to body-response columns. See
`docs/m85-warmstarted-wheel-response-aux.md`.

### M86: Wheel Response Relevance Audit

- Measure whether wheel response adds predictive information beyond body
  response for hidden dynamics or future response.
- Compare body-only and body+wheel probes on the same rollout corpus.
- Mine or construct matched-current-response cases where wheel response differs.
- Use the result to decide between stronger wheel sensors, wrong-wheel-history
  gates, or dropping this front/rear wheel branch as redundant.

Status: complete as an information audit. M86 adds a reusable probe harness and
finds that body+wheel improves `mu_bucket` prediction by about `+0.102` over
body response alone, but mean gain across hidden targets is only `+0.009` and
no non-friction target improves meaningfully. See
`docs/m86-wheel-response-relevance-audit.md`.

### M87: Wheel-Informed Friction/Envelope Objective

- Use the M86 result to target friction or available-authority estimation
  rather than generic wheel-response prediction.
- Mine matched cases where body response is ambiguous but wheel response changes
  friction/envelope prediction.
- Prefer training-time envelope labels over actor-visible hidden parameters.
- Gate whether `zero_wheel_response` or wrong-wheel history hurts those targeted
  cases before making broader self-ID claims.

Status: complete as a retention-positive but self-ID-negative smoke. M87 adds a
training-time friction-bucket auxiliary loss and retains `success_rate = 0.90`,
but `m87_zero_wheel` also remains `0.90`, and the post-training relevance audit
shows body-only `mu_bucket` prediction reaches `0.802372` while body+wheel gain
is `0.0`. See `docs/m87-wheel-informed-friction-envelope-objective.md`.

### M88: Wheel-Masked Friction Auxiliary

- Reuse the M87 friction-bucket label but prevent body-response shortcuts.
- Compute the auxiliary loss from recurrent features generated with body
  response masked and wheel response retained, or mine body-ambiguous
  wheel-different cases.
- Keep the deployable actor observation unchanged.
- Gate whether zero-wheel or wrong-wheel interventions finally reduce targeted
  friction/envelope behavior.

Status: complete as a negative wheel-dependence result. M88 adds a `wheel_only`
mask and `response_hidden` friction auxiliary path. It retains `success_rate =
0.85`, but `m88_zero_wheel` also remains `0.85`; post-training `mu_bucket`
body+wheel gain is only `+0.006160`, and wheel encoder columns remain tiny. See
`docs/m88-wheel-masked-friction-auxiliary.md`.

### M89: Objective-Only Wheel-Masked Friction Sanity

- Load M62 through the wheel partial initialization path.
- Optimize only the wheel-masked friction objective on a rollout batch, without
  PPO reward coupling.
- Measure whether wheel encoder columns and wheel-only `mu_bucket` prediction
  move in isolation.
- Only return to PPO continuation if the isolated objective improves.

Status: complete as a positive objective-only sanity result. M89 improves
wheel-masked `mu_bucket` test accuracy from `0.078199` to `0.668246`, grows
wheel encoder norm by `+2.008215`, retains `success_rate = 0.90`, and produces
a small zero-wheel drop (`0.90` to `0.85`). See
`docs/m89-objective-only-wheel-masked-friction-sanity.md`.

### M90: Guarded PPO From Objective-Only Wheel Checkpoint

- Initialize from
  `runs/m89_wheel_masked_friction_objective_only_seed9200/optimized_checkpoint.pt`.
- Use low learning rate, baseline action anchor, and retention gates.
- Gate normal/reset/zero-wheel/zero-all after continuation.
- Rerun wheel relevance audit and compare against M89.

Status: blocked. M89 gives a useful wheel-aware starting point, but M91/M92
input-observability audits did not justify admitting the current single-track
wheel branch into PPO continuation.

### M91: Input Observability Audit Sequence

- Compare wheel-response profiles against the no-wheel human-view baseline on
  supervised future envelope targets before spending PPO budget.
- Add raw and compact history windows, then learned-history probes.
- Use sensor ablations to identify whether history benefit comes from commands,
  actuator feedback, IMU/body response, or wheel channels.

Status: complete as a no-wheel-primary decision. M91-H showed repeatable
history benefit for braking/yaw targets, but M91-I found that removing wheel
channels improved braking and lateral response in the learned-history ablation.
The current `front_rear_raw` profile remains optional and is not a primary
driver input. See `docs/m91i-learned-history-sensor-ablation.md`.

### M92: Local Wheel Ground-Speed Observability Audit

- Implement clean single-track wheel profiles that expose `Romega` and local
  `v_parallel` without `slip_ratio`, ABS/TCS flags, tire labels, or `mu`.
- Preserve the 85-value wheel-frame shape for apples-to-apples comparison.
- Run P1 `Romega`, P2 `Romega + v_parallel`, and P4 `Romega + v_parallel +
  fixed-scale error` against P0 no-wheel probes.

Status: complete as a negative admission result. P1 `Romega` gives weak mean
R2 lift, but the physically cleaner P2 local-ground-speed profile has mean
P1-vs-P0 R2 lift `-0.062184`, and P4 fixed-scale error regresses further. Keep
the no-wheel human-view response stream as primary until a true four-wheel
profile or better matched corpus proves stable benefit. See
`docs/m92-local-wheel-ground-speed-observability-audit.md`.

### M67-F: Counterfactual Response-Intervention Objective

- Stop treating seed replay alone as sufficient for self-identification.
- Add or prototype an objective that compares normal recurrent rollout against
  reset/zero-response/no-action-history interventions on response-critical
  snippets.
- Penalize cases where ablated-policy behavior is not worse on seeds where
  closed-loop response history should matter.
- Keep the actor input contract unchanged and use intervention signals only as
  training-time losses or gates.

Exit criteria:

- focused unit tests cover the new objective or corpus transformation;
- a smoke run logs the counterfactual/intervention loss;
- full candidates are still gated by strict margin retention before broader
  promotion;
- paired self-identification must improve against M62_a250 without hidden
  actor inputs.

Status: partially superseded by the M78-M80 outcome-weighted intervention track.
M79 shows the PPO-integrated version still moves the fixed-batch objective in
the wrong direction, so M80 must first prove the objective can decrease in
isolation before returning to broader counterfactual intervention training.

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
