# M139 M136 Key Action Anchor Objective

M139 tests whether direct retained-key action anchoring can repair the M137/M138
failure mode. M138 showed that fixed retained-snippet logprob can improve while
the same keys disappear from strict rollout selection. The M139 hypothesis was
that anchoring the M136 proof-surface action means to M132 might preserve the
rollout proof surface better than logprob retention.

## Implementation

`src/autodrift/outcome_intervention_optimize.py` now supports an optional
snippet-level action anchor:

```text
--snippet-action-anchor-checkpoint
--snippet-action-anchor-coef
--snippet-action-anchor-batch-size
--snippet-action-anchor-preferred-only
```

The anchor computes the reference squashed action mean from a checkpoint on the
same M136 snippet observations and recurrent hidden states. By default it
anchors both preferred and rejected hidden branches. This does not change actor
inputs and does not introduce hidden/oracle observations.

Focused validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_outcome_intervention_optimize.py
```

Result: `4 passed`.

## Objective Candidates

All candidates start from:

```text
runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt
```

All optimize actor-coupling parameters with frozen `log_std`, keep the existing
M137 rollout action anchor, and add snippet action anchoring to M132.

| candidate | steps | snippet coef | M136 loss | M136 improvement | action anchor MSE | snippet action MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M132 s60 | 0 | 0 | 0.106838 | 0.000000 | 0.000000 | 0.000000 |
| s40 snip100 | 40 | 100 | 0.105556 | 0.001283 | 0.000005717 | 0.000006005 |
| s40 snip500 | 40 | 500 | 0.106550 | 0.000289 | 0.000000672 | 0.000000349 |
| s20 snip1000 | 20 | 1000 | 0.106696 | 0.000142 | 0.000003242 | 0.000000219 |
| s10 snip2000 | 10 | 2000 | 0.106713 | 0.000125 | 0.000007837 | 0.000001068 |

M128 fixed outcome loss also stays near M132:

| candidate | M128 loss | delta vs M132 |
| --- | ---: | ---: |
| M132 s60 | 0.252310 | 0.000000 |
| s40 snip100 | 0.250220 | -0.002090 |
| s40 snip500 | 0.251822 | -0.000488 |
| s20 snip1000 | 0.251958 | -0.000352 |
| s10 snip2000 | 0.252344 | 0.000034 |

Artifacts:

```text
runs/m139_m136_retention_eval_seed0/policy_summary.csv
runs/m139_m128_outcome_eval_seed0/policy_summary.csv
runs/m139_m136_s40_env20_snip100_seed7140/summary.json
runs/m139_m136_s40_env20_snip500_seed7139/summary.json
runs/m139_m136_s20_env20_snip1000_seed7141/summary.json
runs/m139_m136_s10_env20_snip2000_seed7142/summary.json
```

## Behavior Gate

The most conservative useful candidate, `s20 snip1000`, keeps aggregate
behavior on seed `9503`.

| policy | success | termination | clearance mean |
| --- | ---: | ---: | ---: |
| M132 s60 | 0.8625 | 0.1375 | 1.841558 |
| s20 snip1000 | 0.8625 | 0.1375 | 1.841399 |
| reset hidden | 0.8500 | 0.1500 | 1.840128 |
| zero current response | 0.8000 | 0.2000 | 1.856083 |
| zero all response | 0.8000 | 0.2000 | 1.856083 |
| zero action history | 0.8625 | 0.1375 | 1.845555 |

Artifact:

```text
runs/m139_behavior_gate_seed9503/policy_summary.csv
```

Behavior is not the M139 blocker.

## Strict Proof-Surface Gate

M133 reference thresholds:

| policy | miner seed | selected pairs | selected seeds | snippets |
| --- | ---: | ---: | ---: | ---: |
| M132 s60 | 9900 | 10 | 8 | 17 |
| M132 s60 | 9920 | 9 | 8 | 14 |

M139 strict results:

| candidate | miner seed | selected pairs | selected seeds | snippets |
| --- | ---: | ---: | ---: | ---: |
| s40 snip100 | 9900 | 8 | 6 | 15 |
| s40 snip100 | 9920 | 7 | 6 | 12 |
| s40 snip500 | 9900 | 9 | 7 | 16 |
| s40 snip500 | 9920 | 8 | 7 | 14 |
| s20 snip1000 | 9900 | 9 | 7 | 16 |
| s20 snip1000 | 9920 | 8 | 7 | 13 |

Even `s20 snip1000`, with snippet action MSE only `2.19e-7`, loses one selected
pair and one selected seed on both strict miner seeds. The looser `s40 snip100`
candidate improves fixed losses more, but worsens strict diversity to `8/6` and
`7/6`.

Artifacts:

```text
runs/m139_s40_snip100_strict_60ep_seed9900/summary.json
runs/m139_s40_snip100_strict_60ep_seed9920/summary.json
runs/m139_s40_snip500_strict_60ep_seed9900/summary.json
runs/m139_s40_snip500_strict_60ep_seed9920/summary.json
runs/m139_s20_snip1000_strict_60ep_seed9900/summary.json
runs/m139_s20_snip1000_strict_60ep_seed9920/summary.json
```

## Decision

Reject M139 as a proof-surface repair.

M139 is a useful negative result:

- focused tests now cover the new optimizer path;
- fixed M136 and M128 losses can improve slightly;
- behavior retention and zero-response degradation remain visible;
- retained-key action drift can be made extremely small;
- strict rollout proof-surface diversity still falls below M133.

The key conclusion is that single-step retained-key action anchoring is still
not rollout-safe. The next repair should reason about rollout key survival or
strict proof-surface selection directly, not only about fixed snippet logprob or
fixed snippet action means.

## Next Step

M140 should audit key survival under the M139 candidates and prototype a
rollout-aware retention guard/objective. The objective should be tied to
selected-key survival or rollout margin surface, not just fixed snippet action
distance.
