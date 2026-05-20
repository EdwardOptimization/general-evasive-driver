# AutoDrift

AutoDrift is a simulation-first engineering project for friction-adaptive
autonomous drifting, emergency obstacle avoidance, and reproducible policy
evaluation.

The first implementation target is deliberately narrow and practical:

- provide a reliable vehicle simulation environment with randomized road
  friction, vehicle mass, center-of-gravity, tire stiffness, and actuator delay;
- train and evaluate RL policies on circular drift, friction-change, and later
  AEB-infeasible obstacle-avoidance tasks;
- compare those policies against model-based and rule-based baselines;
- keep real hardware out of the first milestone, while keeping interfaces clean
  enough to add high-fidelity simulators or hardware later.

## Current MVP

The repository currently contains:

- `autodrift.dynamics`: single-track RWD vehicle dynamics with nonlinear tire
  saturation and randomized physical parameters.
- `autodrift.tasks`: simple path tasks, starting with a circular drift track.
- `autodrift.env`: a Gymnasium environment for drift tracking.
- `autodrift.vector_env`: synchronous multi-environment rollout support.
- `autodrift.config`: JSON config builders for env randomization and curricula.
- `autodrift.policies`: baseline policies for sanity checks.
- `autodrift.evaluate`: command-line evaluator.
- `autodrift.benchmark`: shared-seed benchmark runner with CSV/JSON artifacts.
- `autodrift.artifacts`: run directory, JSON, and CSV helpers.
- `docs/`: literature notes and PDFs.

The project definition is in `docs/implementation-plan.md`. The target outcome
is a complete runnable stack, not a paper prototype: simulator, training,
evaluation, saved policies, benchmark reports, and documentation.

Setup details are in `docs/setup.md`. The default environment targets the local
NVIDIA GPU stack; a CPU-only fallback is also provided.

## Quick Check

```bash
pytest
PYTHONPATH=src python -m autodrift.evaluate --episodes 5 --policy heuristic
PYTHONPATH=src python -m autodrift.train_ppo --config configs/ppo_smoke.json
PYTHONPATH=src python -m autodrift.benchmark --episodes 2 --policies heuristic random
```

The environment intentionally hides friction by default. A learning policy must
infer it from state/action history rather than reading a privileged `mu` value.

Training, evaluation, and benchmark commands write reproducible artifacts under
`runs/` by default. That directory is ignored by git; tracked configuration
templates live under `configs/`.
