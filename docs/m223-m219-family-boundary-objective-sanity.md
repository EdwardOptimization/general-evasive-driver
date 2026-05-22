# M223 M219-Family Boundary Objective Sanity

M223 converts the M222 robustness-passing accepted wrong-history rows into
replay-aligned boundary-outcome corpora. No PPO or actor update is run in this
milestone.

## Inputs

Accepted rows:

```text
runs/m222_m219_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
```

Source checkpoints:

```text
m219_5216   runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt
m218_5214   runs/ppo_m218_guarded_from_m217_seed5214/checkpoint.pt
m217_10054  runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
```

Rejected M220 is not used as a source checkpoint.

## Objective Sanity

Artifacts:

- `runs/m223_m219_boundary_outcome_corpus_seed10060`
- `runs/m223_m218_boundary_outcome_corpus_seed10060`
- `runs/m223_m217_boundary_outcome_corpus_seed10060`

| Source | Rows | Physical groups | Targets | Seed passes | Objective pass | Mean combined improvement | Mean delta improvement | Pairwise accuracy after |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| m219_5216 | 17 | 13 | 2 | 3 / 3 | true | 2.281296 | 3.029568 | 1.0000 |
| m218_5214 | 17 | 13 | 2 | 3 / 3 | true | 2.281324 | 3.029691 | 1.0000 |
| m217_10054 | 17 | 13 | 2 | 3 / 3 | true | 2.273794 | 3.023828 | 1.0000 |

All three corpora are learnable under the objective sanity probe. The current
best M219 corpus is the primary source for any later update.

## Replay Sanity

Artifact:

```text
runs/m223_m219_boundary_replay_sanity_seed10060
```

The M219 corpus is replayed with M219 seed `5216` as baseline and M218 seed
`5214` as adjacent-family candidate.

| Metric | Value |
| --- | ---: |
| Rows | 17 |
| Baseline normal success | 1.0 |
| Candidate normal success | 1.0 |
| Baseline success drops | 17 |
| Candidate success drops | 17 |
| Normal margin delta | 0.000056 |
| Margin gap delta | 0.000002 |
| Gate pass | true |

Replay sanity preserves normal success and wrong-history success drops.

## Decision

M223 is positive.

What it proves:

- the M222 protected surface can be converted into compact, source-diverse
  boundary-outcome corpora;
- objective-only probes learn the target on all three retained family
  checkpoints;
- the current-best M219 corpus replays normal-success plus wrong-history drops.

What it does not prove:

- that actor updating is safe;
- that PPO can continue from M219;
- that the old single protected key can be ignored.

Decision:

```text
admit_guarded_actor_update_design
```

Next step:

```text
m224-m223-guarded-actor-update
```

M224 should run exactly one small preferred-only snippet-anchored actor update
from M219 seed `5216`, using the M223 M219 corpus. It must preserve old/current
replay, the new M223 replay surface, broad behavior, and the historical
protected key before any repeat or PPO.
