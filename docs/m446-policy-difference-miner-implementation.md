# M446 Policy-Difference Miner Implementation

M446 implements the reusable policy-difference miner designed in M445. It does
not train, run PPO, promote a checkpoint, lower proof thresholds, or change the
actor input/output contract.

## Implementation

New module:

```text
src/autodrift/policy_difference_miner.py
```

New focused tests:

```text
tests/test_policy_difference_miner.py
```

The miner reads benchmark/evaluation `episodes.csv` files, compares a baseline
policy to candidate policies on shared seeds, and exports accepted divergence
rows plus a compact diversity-capped corpus.

Accepted divergence types:

```text
success_flip
collision_flip
margin_sign_flip
near_boundary_margin_delta
large_margin_delta
return_delta
```

The miner uses hidden/environment fields only for mining and diversity
accounting. It does not change deployable actor inputs.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.policy_difference_miner \
  --episodes-csv runs/m444_proof_utility_generalization_seed9600/episodes.csv \
  --baseline-policy m399_base \
  --candidate-policy m434_r0010 \
  --candidate-policy m438_r0015 \
  --candidate-policy m427_high_utility \
  --candidate-policy m442_tail_v2 \
  --run-dir runs/m446_policy_difference_miner_smoke
```

Artifacts:

```text
runs/m446_policy_difference_miner_smoke/policy_difference_candidates.csv
runs/m446_policy_difference_miner_smoke/compact_policy_difference_corpus.csv
runs/m446_policy_difference_miner_smoke/policy_difference_summary.json
```

## Smoke Result

| Metric | Value |
| --- | ---: |
| comparison rows | `640` |
| accepted rows | `2` |
| selected rows | `1` |
| accepted policies | `m434_r0010`, `m438_r0015` |
| accepted divergence types | `return_delta: 2` |
| selected divergence types | `return_delta: 1` |

Accepted rows:

| Seed | Policy | Type | Delta return | Delta margin |
| ---: | --- | --- | ---: | ---: |
| `9706` | `m438_r0015` | `return_delta` | `1.482061` | `-0.001744` |
| `9706` | `m434_r0010` | `return_delta` | `1.471349` | `-0.001305` |

There are no accepted:

```text
success_flip
collision_flip
margin_sign_flip
near_boundary_margin_delta
large_margin_delta
```

So the M444 benchmark rows remain effectively indistinguishable at the
closed-loop outcome and safety-margin levels.

## Tests

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_policy_difference_miner.py
```

Result:

```text
3 passed
```

Compile check:

```bash
python -m compileall -q src tests
```

Result: passed.

## Interpretation

The tool is ready for a real fresh mining run.

The smoke result reinforces M444 rather than contradicting it: the recent
candidate family does not diverge meaningfully on the 160-seed broad benchmark.
Only two reward-level differences are found, both on the same seed and with no
success/collision/sign/margin-threshold difference.

The next step should run a larger fresh pool and use this miner to answer
whether meaningful policy-difference scenarios exist outside the old-key proof
surface.

## Decision

M446 passes its infrastructure gate:

- reusable miner CLI exists;
- focused tests pass;
- smoke artifacts are written;
- no checkpoint is promoted;
- no actor contract change is made.

Admit:

```text
m447-fresh-policy-difference-mining-run
```

M447 should run a larger fresh benchmark and mine policy differences from that
output. It remains diagnostic and non-promotion.
