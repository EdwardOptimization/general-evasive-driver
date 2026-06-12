# M3238: C1 Family-selector Repricing

Status: completed. This is a read-only selector/separability repricing pass
over the existing M3236 tail-family dataset and M3237 synthesis result. It
performs no rollout, no training, writes no checkpoint/dataset, does not
mutate the incumbent, and makes no driver-performance, validation, promotion,
high-fidelity sufficiency, paper, repair-success, robustness-result,
feasibility-proof, C2-admission, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3238-c1-family-selector-repricing.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_family_selector_repricing_prereg.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_family_selector_repricing.json`
- Source dataset: `runs/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick/quick/interface_pretrain_dataset.npz`
- Harness log: `runs/research/m3238-c1-family-selector-repricing_20260612T074049Z/command.log`

## Measured

Input support:

| readout | value |
|---|---:|
| tail rows | 43 |
| tail frames | 2928 |
| train rows / frames | 28 / 1851 |
| selection rows / frames | 8 / 564 |
| validation rows / frames | 7 / 513 |
| train-majority validation floor | 0.538012 |

Selector battery:

| selector | validation acc | over floor | validation reconstruction MSE | `coast_+0.7` acc | `coast_-0.7` acc | all gates |
|---|---:|---:|---:|---:|---:|---|
| `train_majority_floor` | 0.538012 | 0.000000 | 0.526894 | 0.000000 | 0.000000 | false |
| `frame_centroid_z` | 0.458090 | -0.079922 | 0.359428 | 1.000000 | 0.000000 | false |
| `row_centroid_mean_z` | 0.803119 | 0.265107 | 0.268415 | 1.000000 | 0.000000 | false |
| `row_1nn_mean_std_first_last_z` | 0.803119 | 0.265107 | 0.268415 | 1.000000 | 0.000000 | false |

Best selector by both validation accuracy and reconstruction MSE:
`row_centroid_mean_z`.

Its frozen gates:

| gate | result |
|---|---|
| validation accuracy over majority floor >= 0.15 | pass |
| each required rare family frame accuracy >= 0.5 | fail |
| required rare row accuracy = 1.0 with positive margin | fail |
| predicted-family validation reconstruction MSE <= 0.1 | fail |

The required positive coast family is separable:
`structured:coast_steer_+0.7` has 68/68 validation frames correct and a
positive row margin of 12.333416.

The required negative coast family is not separable under this interface:
`structured:coast_steer_-0.7` has 0/101 validation frames correct, is
predicted as `structured:brake_steer_-1.0` for all 101 frames, and has a
negative row margin of -138.088562 under the best selector.

No selector was admissible: `admissible_selectors=[]`.

## Inferred

The structured decoder is still not the failing component. M3235/M3236/M3237
already showed exact reconstruction when the family is known.

The failed component is the local family selector. Aggregate row-level
accuracy is again misleading: it clears the floor by 0.265107 while a required
rare family fails completely and the decoded predicted-family action remains
far above the 0.1 MSE gate.

This negative result rejects this local selector route. It does not reject the
C5-prime structural-ceiling target itself, which remains priced by A3/D1b and
alive if a correct nonlocal/interface route can be priced.

## Decision

Verdict: `family_selector_repricing_negative`.

Closed branch:
`c5prime_track_c_c1_family_selector_repricing`.

Next branch:
`c5prime_track_c_c1_pause_pending_pi_or_nonlocal_interface_reprice`.

C1 local selector/interface training is blocked pending PI or new
nonlocal-interface pricing. C2 and C3 remain blocked. No further local
selector/interface training, controlled rollout design, full C1 training, or
C2 work is admitted by M3238.
