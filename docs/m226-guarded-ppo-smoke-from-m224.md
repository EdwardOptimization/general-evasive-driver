# M226 Guarded PPO Smoke From M224

M226 runs exactly one tiny guarded PPO smoke from the best fixed-loss M224
actor-update checkpoint. It uses the M223 corpus and anchors rollout actions to
M224.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Config:

```text
configs/ppo_m226_guarded_from_m224_smoke.json
```

The config uses:

```text
outcome_intervention_snapshot_npz = runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
baseline_action_anchor_checkpoint = runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

## Training

Artifact:

```text
runs/ppo_m226_guarded_from_m224_seed5218/checkpoint.pt
```

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Built-in eval return | Built-in eval termination |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 66.29 | 0.962 | 10 | 68.114162 | 0.0000 |

Training reward is not used for promotion.

## Fixed M223 Eval

Artifact:

```text
runs/m226_fixed_batch_outcome_eval_seed37
```

| Policy | Fixed M223 loss |
| --- | ---: |
| m219_5216 | 0.210903 |
| m224_10063 | 0.209824 |
| m225_10065 | 0.210036 |
| m226_5218 | 0.209834 |

M226 is better than M219 and the M225 repeat seed shown here, but slightly worse
than M224. Fixed objective does not justify promotion.

## Replay Gates

Replay gates compare M226 against M224.

| Corpus | Rows | M226 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.000051 | 0.000101 | true |
| M183 M170 | 17 | 16 / 17 | -0.000059 | 0.000102 | false |
| M193 M189 | 14 | 14 / 14 | -0.000068 | 0.000203 | true |
| M212 M204 | 17 | 17 / 17 | -0.000079 | 0.000194 | true |
| M223 M219 | 17 | 17 / 17 | -0.000079 | 0.000194 | true |

M226 fails old M183 M170 replay by losing one normal-history success/drop row.
This is sufficient for rejection.

## Behavior Diagnostic

Artifacts:

- `runs/m226_behavior_gate_seed9505`
- `runs/m226_behavior_gate_seed9506`

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m226_5218 | 0.8625 | 0.1375 | 1.835295 |
| 9505 | m226_5218_reset | 0.8500 | 0.1500 | 1.833937 |
| 9505 | m226_5218_zero_all | 0.8000 | 0.2000 | 1.853221 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m226_5218 | 0.8625 | 0.1375 | 1.852807 |
| 9506 | m226_5218_reset | 0.8500 | 0.1500 | 1.850205 |
| 9506 | m226_5218_zero_all | 0.8000 | 0.2000 | 1.871129 |

Broad behavior remains stable. The failure is specific to proof-surface
retention, not broad obstacle-avoidance collapse.

## Protected Key Diagnostic

Artifact:

```text
runs/m226_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | true | 0.186385 | 0.086925 | 0.099460 |
| m226_5218 | 0 / 1 | false | 0.203847 | 0.104163 | 0.099684 |
| m220_5217 | 0 / 1 | false | 0.214602 | 0.119100 | 0.095502 |

M226 also fails the historical protected key by moving normal margin above the
`0.2` near-boundary window.

## Decision

M226 is negative:

- fixed M223 objective does not beat M224;
- M183 M170 replay fails with `16/17` retained drops;
- historical protected key fails with normal margin `0.203847`;
- broad behavior remains stable, so this is a proof-surface retention failure.

Current best remains M224.

Decision:

```text
reject_ppo_smoke_replay_and_protected_key_failure
```

Next step:

```text
m227-ppo-smoke-retention-failure-audit
```

Do not repeat M226 and do not run longer PPO. The next milestone must audit why
PPO lacks the snippet-level protection that made M224/M225 actor updates stable.
