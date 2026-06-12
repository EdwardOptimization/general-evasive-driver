# M3237: C1 Tail-family Interface Synthesis/Repricing

Status: completed. This is a read-only synthesis/repricing pass over
M3234-M3236 and the existing C5-prime pricing artifacts. It performs no
rollout, no training, writes no checkpoint/dataset, does not mutate the
incumbent, and makes no driver-performance, validation, promotion,
high-fidelity sufficiency, paper, repair-success, robustness-result,
feasibility-proof, C2-admission, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3237-c1-tail-family-interface-synthesis-repricing.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_tail_family_interface_synthesis_repricing_prereg.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_tail_family_interface_synthesis_repricing.json`
- Harness log: `runs/research/m3237-c1-tail-family-interface-synthesis-repricing_20260612T072433Z/command.log`

## Measured

The priced target remains alive:

| readout | value |
|---|---:|
| A3 target confirmed | true |
| A3 qualifying cells | S1/T-limit, S2/T-limit, S3/T-limit |
| D1b direction-positive all variants | true |
| M3234 interface pricing positive | true |
| M3234 priced tail-MSE reduction | 0.369957 |
| M3234 threshold | 0.150000 |

The representation remains valid if the oracle family is known:

| readout | value |
|---|---:|
| M3235 target-path smoke passed | true |
| M3235 tail reconstruction MSE | 0.000000 |
| M3236 true-family validation reconstruction MSE | 0.000000 |
| M3236 predicted-family validation reconstruction MSE | 0.276010 |

M3236 closed the local frame-wise pretraining path:

| readout | value |
|---|---:|
| selection accuracy | 0.927305 |
| validation accuracy | 0.766082 |
| best simple validation floor | 0.538012 |
| worst validation family | `structured:coast_steer_-0.7` |
| worst-family accuracy | 0.000000 |
| worst-family frames | 101 |
| worst-family dominant prediction | `structured:brake_steer_-1.0` |

The aggregate validation metric would have been misleading: it beat the best
simple floor by 0.228070 while a required rare family failed completely.

## Inferred

The structured decoder is not the failing component. M3235 and the M3236
true-family reconstruction show that the tail action can be represented
exactly when the family is known.

The failed component is the local frame-wise family selector. Continuing local
interface pretraining or moving to controlled rollout design from aggregate
accuracy would repeat the M3236 rare-family failure.

## Decision

Verdict: `pivot_to_family_selector_repricing`.

Closed branch:
`c5prime_track_c_c1_tail_family_interface_pretrain_design`.

Next branch:
`c5prime_track_c_c1_family_selector_repricing`.

C1 remains open. C2 and C3 remain blocked. The only admitted next work is a
read-only family-selector/separability repricing milestone. No further local
interface pretraining, controlled rollout design, full C1 training, or C2 work
is admitted by M3237.
