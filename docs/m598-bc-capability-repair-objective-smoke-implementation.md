# M598 BC Capability Repair Objective Smoke Implementation

## Purpose

M598 implements and runs the frozen-actor, head-only capability objective smoke
designed in M597.

This milestone is objective-wiring only:

```text
actor frozen
CapabilityHead only trained
no PPO
no route evaluation
no checkpoint promotion
```

## Implementation

M598 adds:

```text
src/autodrift/bc_capability_repair_smoke.py
tests/test_bc_capability_repair_smoke.py
```

The runner:

1. loads M596 train and validation corpora;
2. trains `CapabilityHead` on `base_next_hidden_seq`;
3. optimizes capability regression and pair ranking losses;
4. recomputes action-anchor MSE from the frozen BC5660 actor;
5. verifies actor parameters are unchanged;
6. saves only `capability_head.pt`, metrics CSVs, and `summary.json`.

It does not save a modified actor checkpoint.

## Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_bc_capability_repair_smoke.py \
  tests/test_bc_capability_repair.py \
  tests/test_bc_capability_corpus.py
```

Result:

```text
9 passed
```

The tests verify:

- the head-only smoke reduces synthetic regression and ranking losses;
- recomputed action-anchor MSE is zero for matching actions;
- capability repair and corpus helpers remain valid.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_repair_smoke \
  --train-corpus runs/m596_bc_capability_corpus_train_smoke/capability_corpus.npz \
  --train-pairs runs/m596_bc_capability_corpus_train_smoke/pairs.csv \
  --val-corpus runs/m596_bc_capability_corpus_validation_smoke/capability_corpus.npz \
  --val-pairs runs/m596_bc_capability_corpus_validation_smoke/pairs.csv \
  --base-checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --epochs 200 \
  --learning-rate 0.003 \
  --rank-loss-weight 0.25 \
  --seed 5980 \
  --device cpu \
  --run-dir runs/m598_bc_capability_repair_head_only_smoke
```

## Artifacts

```text
runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt
runs/m598_bc_capability_repair_head_only_smoke/train_metrics.csv
runs/m598_bc_capability_repair_head_only_smoke/validation_metrics.csv
runs/m598_bc_capability_repair_head_only_smoke/summary.json
```

## Results

| metric | initial | final | relative change |
| --- | ---: | ---: | ---: |
| train regression loss | 0.764369 | 0.159261 | -0.791643 |
| validation regression loss | 1.265884 | 0.420221 | -0.668041 |
| train rank loss | 0.831669 | 0.563961 | -0.321892 |
| validation rank loss | 0.871387 | 0.726029 | -0.166812 |

Safety and contract checks:

| metric | value |
| --- | ---: |
| train action-anchor MSE | 0.0 |
| validation action-anchor MSE | 0.0 |
| actor parameters changed | false |
| labels enter actor input | false |
| PPO used | false |
| promoted | false |
| passed | true |

M598 passes every M597 threshold:

- train regression loss drop >= `30%`;
- validation regression loss drop >= `10%`;
- train rank loss drop >= `10%`;
- validation rank loss does not increase;
- action-anchor MSE is `0`;
- actor parameters are unchanged.

## Interpretation

M598 proves:

```text
the M596 capability corpus has learnable future-response signal in BC5660
base hidden states, and the objective/pair-ranking losses are wired.
```

M598 does not prove:

```text
the driver is improved;
the actor uses hidden for actions;
wrong-history intervention sensitivity is repaired;
route or OOD performance improves.
```

Those require a later milestone that updates selected recurrent/actor modules
under strict action/behavior retention gates.

## Decision

```text
bc_capability_repair_head_only_smoke_pass_admit_audit
```

M598 passes because the frozen-actor capability head learns train and
validation capability targets and pair rankings while leaving the actor
unchanged.

## Next

```text
M599: audit the head-only smoke and decide whether to design recurrent-hidden
fine-tuning or additional diagnostics.
```
