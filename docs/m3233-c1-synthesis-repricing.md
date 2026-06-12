# M3233: C1 Synthesis/Repricing

Status: completed. This is a process synthesis over existing C5-prime pricing
and C1 warm-start artifacts. It performs no rollout, no training, no criterion
relaxation, no incumbent mutation, and makes no driver-performance,
validation, promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3233-c1-synthesis-repricing.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_synthesis_repricing_prereg.json`
- Synthesis JSON: `experiments/feasibility_audit/c5prime_c1_synthesis_repricing.json`
- Harness log: `runs/research/m3233-c1-synthesis-repricing_20260612T064016Z/command.log`

## Measured

The target remains priced:

| source | readout |
|---|---|
| A3 current-sim | C5-prime target confirmed in 3/4 T-limit cells; qualified oracle - pertuned gaps S1 +0.1597, S2 +0.2153, S3 +0.1736 |
| D1b Chrono-native | direction-positive in both preregistered variants: Sedan +0.2222, BMW_E90 +0.1111 |

The direct MLP/action-MSE warm-start branch failed twice while artifact gates
were healthy:

| milestone | mode | validation action MSE | gate | zero baseline | rollout context |
|---|---|---:|---|---:|---:|
| M3228 | full | 0.234184 | fail (<= 0.12) | 0.501099 | 5/10 |
| M3232 | quick v2 | 0.291470 | fail (<= 0.12) | 0.559903 | 2/3 |

M3229's localization remains the failure diagnosis: validation tail MSE
0.369957 vs prefix MSE 0.026446 (13.99x), with brake-channel MSE 0.201318
as the largest action-channel component.

## Inferred

The C5-prime structural prize is not dead: both A3 and D1b keep it priced.
What is dead is another local repair of the same direct-MLP/action-MSE
warm-start branch. M3232 added rare-tail support but worsened validation MSE
relative to M3228 by 0.057286, while demo replay, checkpoint, and dataset
gates stayed healthy.

The rollout contexts are useful diagnostics, but they cannot override the
frozen action-MSE admission gate. No replacement gate was priced in M3233.

## Decision

Workflow synthesis decision: `pivot`.

C1 remains open under a new successor branch,
`c5prime_track_c_c1_admission_interface_pricing`. C2 and C3 remain blocked.
Do not run full v2, start C2, or perform another local direct-MLP BC repair
from M3228/M3232. The next C1 unit should price/design an admission interface
before any new warm-start training, using the direct MLP action-MSE path as the
failed floor rather than the default continuation.
