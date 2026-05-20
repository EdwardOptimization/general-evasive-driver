# AutoDrift Setup

Last updated: 2026-05-20

## Conda Environment

Create the GPU development environment:

```bash
make env-create
conda activate autodrift
```

Update it after dependency changes:

```bash
make env-update
```

The default environment installs PyTorch from the official CUDA 13.0 wheel index
(`cu130`), which matches the local RTX 5080 / CUDA 13.1 driver stack. The
Makefile then installs the project in editable mode with
`pip install --no-deps -e .`, so changes under `src/autodrift` are picked up
without reinstalling.

For a CPU-only fallback:

```bash
make env-create-cpu
```

To switch an existing environment between PyTorch builds:

```bash
make torch-gpu
make torch-cpu
```

## Development Commands

```bash
make test
make eval-heuristic
make train-smoke
make benchmark-smoke
```

Equivalent direct commands:

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m autodrift.evaluate --episodes 5 --policy heuristic
PYTHONPATH=src python -m autodrift.train_ppo --config configs/ppo_smoke.json
PYTHONPATH=src python -m autodrift.benchmark --episodes 2 --policies heuristic random
```

After `make env-create` or `make env-update`, the same commands are also
available as console scripts: `autodrift-train-ppo`, `autodrift-evaluate`, and
`autodrift-benchmark`.

Training and evaluation commands create timestamped directories under `runs/`
unless an explicit `--run-dir` is provided. A typical PPO run contains:

- `config.json`
- `checkpoint.pt`
- `train_metrics.csv`
- `eval_summary.json`
- `manifest.json`

Evaluate a saved PPO checkpoint with:

```bash
PYTHONPATH=src python -m autodrift.evaluate \
  --policy checkpoint \
  --checkpoint runs/<run>/checkpoint.pt \
  --episodes 10
```

Run a shared-seed comparison with:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --policies heuristic checkpoint \
  --checkpoint runs/<run>/checkpoint.pt \
  --episodes 20
```

## Git Notes

Downloaded paper PDFs are kept as a local literature cache under `docs/papers/`
and are ignored by git. The tracked source of truth is:

- `docs/source-log.md`
- `docs/references.bib`
- reading notes under `docs/*.md`

If the PDF corpus needs to be pushed later, configure Git LFS before adding PDF
files to the repository history.
