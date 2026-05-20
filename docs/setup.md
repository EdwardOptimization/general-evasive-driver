# AutoDrift Setup

Last updated: 2026-05-20

## Conda Environment

Create the CPU development environment:

```bash
make env-create
conda activate autodrift
```

Update it after dependency changes:

```bash
make env-update
```

The environment installs PyTorch from the official CPU wheel index to avoid
accidentally pulling multi-GB CUDA packages into the default development
environment. The Makefile then installs the project in editable mode with
`pip install --no-deps -e .`, so changes under `src/autodrift` are picked up
without reinstalling.

## Development Commands

```bash
make test
make eval-heuristic
make train-smoke
```

Equivalent direct commands:

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m autodrift.evaluate --episodes 5 --policy heuristic
PYTHONPATH=src python -m autodrift.train_ppo --total-steps 512 --rollout-steps 128 --eval-episodes 1
```

## Git Notes

Downloaded paper PDFs are kept as a local literature cache under `docs/papers/`
and are ignored by git. The tracked source of truth is:

- `docs/source-log.md`
- `docs/references.bib`
- reading notes under `docs/*.md`

If the PDF corpus needs to be pushed later, configure Git LFS before adding PDF
files to the repository history.
