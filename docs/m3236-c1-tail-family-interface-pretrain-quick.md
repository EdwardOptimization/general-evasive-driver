# M3236: C1 Tail-family Interface Pretrain Quick

Status: failed. This is a supervised C1 tail-family interface pretrain quick
over frozen structured-oracle tail frames. It did not run PPO or guarded RL,
did not mutate the incumbent, did not rank a driver, and does not admit C2.

## Artifacts

- Manifest: `experiments/manifests/m3236-c1-tail-family-interface-pretrain-quick.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick_prereg.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick.json`
- Dataset: `runs/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick/quick/interface_pretrain_dataset.npz`
- Interface-head checkpoint: `runs/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick/quick/interface_head.pt`
- Harness log: `runs/research/m3236-c1-tail-family-interface-pretrain-quick_20260612T071553Z/command.log`

## Measured

M3236 used the full M3232 v2 row split, not the M3235 quick subset, and added
deterministic train-role rare-tail support rows for both required coast-steer
validation families.

| measurement | value |
|---|---:|
| rows | 43 |
| train / selection / validation rows | 28 / 8 / 7 |
| demo replay successes | 43 / 43 |
| tail frames | 2928 |
| train / selection / validation tail frames | 1851 / 564 / 513 |
| best selected epoch | 105 |
| train family accuracy | 0.994057 |
| selection family accuracy | 0.927305 |
| validation family accuracy | 0.766082 |
| validation train-majority floor | 0.538012 |
| validation centroid floor | 0.444444 |
| predicted-family validation reconstruction MSE | 0.276010 |
| true-family validation reconstruction MSE | 0.000000 |

Validation family breakdown:

| validation family | frames | accuracy | dominant prediction |
|---|---:|---:|---|
| `structured:brake_steer_+0.4` | 68 | 1.000000 | `structured:brake_steer_+0.4` |
| `structured:brake_steer_-0.4` | 276 | 0.934783 | `structured:brake_steer_-0.4` |
| `structured:coast_steer_+0.7` | 68 | 0.985294 | `structured:coast_steer_+0.7` |
| `structured:coast_steer_-0.7` | 101 | 0.000000 | `structured:brake_steer_-1.0` |

Frozen gates failed:

| gate | result |
|---|---|
| validation family minimum accuracy | fail |
| required rare validation family accuracy | fail |
| predicted-family reconstruction MSE <= 0.1 | fail |

All split, replay, dataset/checkpoint, aggregate selection, aggregate
validation, and true-family reconstruction gates passed.

## Inferred

The aggregate validation accuracy is misleading. A frame-wise supervised
tail-family head can learn the common brake-steer families and `coast_steer_+0.7`,
but it maps every `coast_steer_-0.7` validation frame to
`brake_steer_-1.0`, which changes the decoded action enough to fail the
reconstruction gate.

This means the M3234/M3235 structured interface is representationally valid
when the family is known, but the local frame-wise supervised classifier is not
a sufficient pretrain path. Continuing local interface pretraining without a
synthesis/repricing step would repeat the same rare-family failure mode.

## Decision

Verdict: `tail_family_interface_pretrain_quick_failed_rare_family`.

C1 remains open under `c5prime_track_c_c1_tail_family_interface_reprice`.
C2 and C3 remain blocked. The next admissible C1 work unit is a
synthesis/repricing step over M3234-M3236 before any further local interface
pretraining or controlled rollout design.
