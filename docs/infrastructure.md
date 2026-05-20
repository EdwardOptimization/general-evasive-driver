# AutoDrift Infrastructure

Last updated: 2026-05-20

## Current Baseline

The repository now has enough project infrastructure for iterative development:

- GPU-first conda environment, with CPU fallback.
- Installable Python package and console entry points.
- Smoke tests for dynamics, environment, artifacts, and checkpoint loading.
- PPO smoke training that writes a complete run directory.
- Checkpoint evaluation through the same evaluator used by built-in policies.
- Shared-seed benchmark CLI for policy comparisons.
- Machine-readable outputs for later plotting and reports.

## Run Directory Contract

Training writes:

- `config.json`: resolved command and PPO configuration.
- `checkpoint.pt`: CPU-portable policy checkpoint.
- `train_metrics.csv`: per-update training metrics.
- `eval_summary.json`: deterministic post-training evaluation summary.
- `manifest.json`: artifact index.

Evaluation writes:

- `episodes.csv`: one row per scenario seed.
- `summary.json`: aggregate metrics.
- `manifest.json`: artifact index.

Benchmarking writes:

- `episodes.csv`: all policy/seed rows.
- `policy_summary.csv`: aggregate metrics by policy.
- `mu_bucket_summary.csv`: aggregate metrics by policy and friction bucket.
- `manifest.json`: artifact index.

## Commands

```bash
make test
make train-smoke
make eval-heuristic
make benchmark-smoke
```

Longer local PPO run:

```bash
PYTHONPATH=src python -m autodrift.train_ppo --config configs/ppo_circle_mvp.json
```

Evaluate a checkpoint:

```bash
PYTHONPATH=src python -m autodrift.evaluate \
  --policy checkpoint \
  --checkpoint runs/<run>/checkpoint.pt \
  --episodes 10
```

Compare policies on shared seeds:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --policies heuristic checkpoint \
  --checkpoint runs/<run>/checkpoint.pt \
  --episodes 20
```

## Deferred Infrastructure

Add these only when the project reaches the relevant milestone:

- Vectorized env/training framework adapter for serious RL training.
- Scenario corpus versioning once obstacle tasks exist.
- Plot/report generation once metrics stabilize.
- Hyperparameter sweep tooling once a first policy learns reliably.
- NMPC/SQP benchmark harness once model-based baselines are ready.
- Simulator adapter layer when moving beyond the built-in single-track model.
- CI/container packaging when the command set stabilizes.
