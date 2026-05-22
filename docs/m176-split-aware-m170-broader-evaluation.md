# M176 Split-Aware M170 Broader Evaluation

M175 admitted M170 to broader split-aware evaluation: it preserves robust
boundary replay rows and passes behavior/protected-key checks, but loses
knife-edge row `67`. M176 compares M168 and M170 more broadly without running
more PPO.

This is a dual-track result. M170 is a valid split-aware candidate branch, but
M168 remains the strict full-replay checkpoint.

## Fixed Objective

| Policy | Fixed loss |
| --- | ---: |
| m168_from_m167_5168 | 0.397971 |
| m170_stage2 | 0.397740 |

M170 has the better fixed objective.

## Replay Gates

Full M164 replay:

| Policy | Normal success | Wrong-history success | Success drops | Gate |
| --- | ---: | ---: | ---: | --- |
| m168_from_m167_5168 | 0.681818 | 0.500000 | 16 | pass |
| m170_stage2 | 0.681818 | 0.511364 | 15 | fail |

Margin-split replay:

| Policy | Robust lost | Watchlist lost | Knife-edge lost | Split gate |
| --- | --- | --- | --- | --- |
| m168_from_m167_5168 | `[]` | `[]` | `[]` | pass |
| m170_stage2 | `[]` | `[]` | `[67]` | pass |

Interpretation:

- M168 is still the strict full-replay checkpoint;
- M170 is a split-aware candidate with one documented knife-edge stress loss.

## Behavior Seeds

Previously evaluated:

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9503 | m168_from_m167_5168 | 0.8625 | 0.1375 | 1.846380 |
| 9503 | m170_stage2 | 0.8625 | 0.1375 | 1.846537 |
| 9504 | m168_from_m167_5168 | 0.8625 | 0.1375 | 1.853938 |
| 9504 | m170_stage2 | 0.8625 | 0.1375 | 1.854103 |

New M176 behavior seeds:

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m168_from_m167_5168 | 0.8625 | 0.1375 | 1.837837 |
| 9505 | m170_stage2 | 0.8625 | 0.1375 | 1.838009 |
| 9506 | m168_from_m167_5168 | 0.8625 | 0.1375 | 1.855585 |
| 9506 | m170_stage2 | 0.8625 | 0.1375 | 1.855754 |

Ablation pattern on seeds `9505` and `9506` remains unchanged:

| Policy family | Reset success | Zero-all success | No-action success |
| --- | ---: | ---: | ---: |
| m168_from_m167_5168 | 0.8500 | 0.8000 | 0.8625 |
| m170_stage2 | 0.8500 | 0.8000 | 0.8625 |

M170 does not introduce aggregate behavior regression across seeds `9503` to
`9506`.

## Protected Key

M170 protected key result:

```text
runs/m175_m170_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m163_a100_s20 | 1 / 1 | true |
| m170_stage2 | 1 / 1 | true |

## Decision

M176 is positive as a broader evaluation of the split-aware branch.

Decision:

- keep M168 as the strict full-replay checkpoint;
- keep M170 as a split-aware candidate branch with better fixed objective and no
  aggregate behavior regression;
- do not run more PPO yet;
- use both checkpoints in the next self-identification/proof-surface evaluation
  to avoid choosing solely by fixed objective or aggregate behavior.

This preserves the stricter evidence chain while still tracking the stronger
aggregate candidate.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9505
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9506
```

Evidence reused:

```text
runs/m168_fixed_batch_outcome_eval_seed37/summary.json
runs/m170_fixed_batch_outcome_eval_seed37/summary.json
runs/m168_from_m167_5168_boundary_outcome_replay_gate_seed9510/summary.json
runs/m170_boundary_outcome_replay_gate_seed9510/summary.json
runs/m175_m168_margin_split_guard_seed9510/summary.json
runs/m175_m170_margin_split_guard_seed9510/summary.json
runs/m175_m170_behavior_gate_seed9503/policy_summary.csv
runs/m175_m170_behavior_gate_seed9504/policy_summary.csv
runs/m175_m170_critical_key_seed9944/summary.json
```
