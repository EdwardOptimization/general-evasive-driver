# AutoDrift Implementation Plan

Last updated: 2026-05-20

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
- `src/autodrift/benchmark.py`: shared-seed benchmark runner.
- `src/autodrift/artifacts.py`: run directory, JSON, and CSV artifact helpers.
- `src/autodrift/checkpoints.py`: PPO checkpoint loader for evaluation.
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
sensor/action history
  -> RL actor
  -> steering/throttle/brake
  -> vehicle response
  -> updated sensor/action history
```

The deployed actor should not depend on explicit rule branches or true hidden
vehicle parameters. It should infer friction, braking authority, tire response,
mass/CG variation, and actuator lag from recent feedback and its own previous
actions. Rules remain useful for scenario generation, reward shaping, benchmark
labels, diagnostics, and safety monitoring, but they should not become the
normal driving policy. See `docs/m7-universal-closed-loop-operator.md`.

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
- failure modes are reported by hidden vehicle and road buckets;
- adaptation depends on closed-loop feedback rather than rule branches or
  leaked simulator parameters;
- safety/fallback logic is separated from the main RL controller.

Status: planned. See `docs/m7-universal-closed-loop-operator.md`.
Validation will follow `docs/m7-validation-protocol.md` so a policy is judged by
held-out generalization, ablations, latent self-identification evidence, and
behavior diagnostics rather than aggregate success alone.

## Metrics

- episode success rate;
- lateral RMSE and peak error;
- sideslip target absolute error;
- speed error;
- spin-out/off-track rate;
- actuator saturation frequency;
- minimum obstacle distance for avoidance tasks;
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
