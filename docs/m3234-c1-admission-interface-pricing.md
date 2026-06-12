# M3234: C1 Admission-interface Pricing

Status: completed. This is a read-only pricing pass over existing C1 artifacts.
It performs no rollout, no training, writes no checkpoint/dataset, does not
mutate the incumbent, and makes no driver-performance, validation, promotion,
high-fidelity sufficiency, paper, repair-success, robustness-result,
feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3234-c1-admission-interface-pricing.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_admission_interface_pricing_prereg.json`
- Pricing JSON: `experiments/feasibility_audit/c5prime_c1_admission_interface_pricing.json`
- Harness log: `runs/research/m3234-c1-admission-interface-pricing_20260612T064954Z/command.log`

## Measured

M3234 compared the failed direct-MLP/action-MSE floor against a structured
tail-family interface candidate.

Direct floor:

| source | validation action MSE |
|---|---:|
| M3228 full direct MLP | 0.234184 |
| M3232 v2 quick direct MLP | 0.291470 |

Tail failure and interface anchor:

| readout | value |
|---|---:|
| M3229 direct-MLP validation prefix MSE | 0.026446 |
| M3229 direct-MLP validation tail MSE | 0.369957 |
| structured tail-family oracle MSE | 0.000000 |
| priced tail-MSE reduction | 0.369957 |
| threshold | 0.150000 |

Family support:

| panel | held-out family train coverage | missing held-out train support |
|---|---:|---|
| M3228 | 0.428571 | brake_steer_+0.7, brake_steer_-1.0, coast_steer_+0.7, coast_steer_-0.7 |
| M3232 v2 prereg | 1.000000 | none |

The structured library supports every v2 held-out family. The M3232 v2 quick
rows were 63.05% tail frames, so the priced interface targets the region that
actually dominated the failed gate.

## Inferred

The positive price is for an admission interface, not for a trained policy.
It says the next C1 unit should test a tail-family structured interface in a
separate no-PPO quick smoke rather than continuing direct continuous MLP action
regression.

The candidate interface decomposes the target as:

- prefix: continuous action or existing reflex-prefix head before `reveal_step`;
- tail: discrete structured oracle family plus reveal-relative phase, decoded
  through the frozen structured action library.

## Decision

Verdict: `interface_pricing_positive`.

C1 remains open. C2 and C3 remain blocked. The next branch is
`c5prime_track_c_c1_tail_family_interface_smoke`. M3234 admits only a separate
quick-smoke registration with frozen family-coverage and tail-reconstruction
gates; it does not admit full C1 training, C2, PPO, validation ranking, or any
driver-performance claim.
