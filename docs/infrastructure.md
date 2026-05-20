# AutoDrift Infrastructure

Last updated: 2026-05-21

## Current Baseline

The repository now has enough project infrastructure for iterative development:

- GPU-first conda environment, with CPU fallback.
- Installable Python package and console entry points.
- Smoke tests for dynamics, environment, artifacts, and checkpoint loading.
- Synchronous vectorized environment support for PPO rollout collection.
- JSON-driven environment randomization and curriculum stages.
- Friction-limited speed target sampling for circular tracking scenarios.
- Optional observation history stacking for later adaptation experiments.
- PPO smoke training that writes a complete run directory.
- Checkpoint evaluation through the same evaluator used by built-in policies.
- Shared-seed benchmark CLI for policy comparisons.
- Checkpoint observation ablations for M7 validation.
- Frozen-rollout latent probe CLI for hidden-condition diagnostics.
- Label-balanced scenario corpus CLI for fixed benchmark seed sets.
- M7 gate CLI that runs benchmark comparison, history ablation, and latent
  probes into one report.
- Rollout trace and plot generation for selected policy episodes.
- Machine-readable outputs for later reports.

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
- `vehicle_road_bucket_summary.csv`: optional aggregate metrics by hidden
  vehicle-road buckets when the required columns are present.
- `manifest.json`: artifact index.

Checkpoint benchmark specs support the following observation ablations through
`--checkpoint-policy name=path@ablation`: `zero_action_history`,
`single_frame_history`, `shuffled_history`, `zero_current_response`, and
`zero_all_response`. Oracle-like model features should be removed from the actor
observation instead of handled as ablations.

Checkpoint initialization is strict. If the actor observation or action contract
changes, old checkpoints are historical artifacts and must not be shape-adapted
into the new policy.

Checkpoint loading is strict too: the checkpoint config must explicitly declare
the model contract. Missing actor encoder, history length, action-sequence
horizon, response-prediction dimension, or log-std bounds is a load failure, not
a compatibility fallback.

Experiment config files are explicit as well. Training configs must have
top-level `ppo` and `env` sections. Evaluation configs must have a top-level
`env` section; raw env-root JSON is not accepted.

Latent probing writes:

- `samples.csv`: frozen rollout sample metadata and hidden bucket labels.
- `probe_summary.csv`: probe accuracy by target and feature set.
- `summary.json`: compact machine-readable result summary.
- `manifest.json`: artifact index.

Scenario corpus generation writes:

- `scenario_corpus.csv`: selected deterministic scenario seeds and hidden
  condition metadata.
- `label_summary.csv`: obstacle-label counts.
- `vehicle_road_summary.csv`: hidden bucket counts.
- `summary.json`: compact machine-readable result summary.
- `manifest.json`: artifact index.

M7 gate writes:

- `benchmark_comparison/`: shared-seed AEB/AES/envelope/M5/M7 comparison.
- `history_ablation/`: no-action, single-frame, and shuffled-history ablation.
- `latent_probe_m7a/` and `latent_probe_m7b/`: frozen rollout probe outputs.
- `gate_summary.md`: human-readable gate report.
- `summary.json`: pass/fail checks and key metrics.
- `manifest.json`: artifact index.

## Commands

```bash
make test
make test-light
make train-smoke
make eval-heuristic
make benchmark-smoke
make rollout-smoke
```

Install the lightweight local pre-commit hook:

```bash
make hooks-install
```

The hook only runs staged whitespace checks and lightweight harness tests. It
does not run training or the full M7 gate. For emergency commits, skip the test
portion with:

```bash
AUTODRIFT_SKIP_PRECOMMIT_TESTS=1 git commit ...
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

Probe hidden-condition information in a frozen actor:

```bash
PYTHONPATH=src python -m autodrift.latent_probe \
  --checkpoint runs/<run>/checkpoint.pt \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --episodes 100
```

Build a label-balanced M7 scenario corpus:

```bash
make m7-corpus
```

Run the complete M7 validation gate:

```bash
make m7-gate
```

Run a quick M7 gate smoke check:

```bash
make m7-gate-smoke
```

Plan the next long-running research task:

```bash
make research-plan
```

Run exactly one queued research task:

```bash
make research-run-next
```

The research harness uses `experiments/research_queue.csv` as the tracked queue,
writes generated status to `experiments/research_status.json`, appends cycle
notes to `docs/research-log.md`, and stores command logs under `runs/research/`.

Trace and plot selected rollouts:

```bash
PYTHONPATH=src python -m autodrift.rollout \
  --policy checkpoint \
  --checkpoint runs/<run>/checkpoint.pt \
  --seeds 7 37 \
  --out-dir runs/<rollout_dir>
```

## Deferred Infrastructure

Add these only when the project reaches the relevant milestone:

- External training framework adapter, if the in-repo PPO trainer becomes the
  bottleneck after M2 experiments.
- Scenario corpus versioning once obstacle tasks exist.
- Report generation once metrics stabilize.
- Hyperparameter sweep tooling once a first policy learns reliably.
- NMPC/SQP benchmark harness once model-based baselines are ready.
- Simulator adapter layer when moving beyond the built-in single-track model.
- CI/container packaging when the command set stabilizes.
