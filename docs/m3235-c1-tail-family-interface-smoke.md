# M3235: C1 Tail-family Interface Smoke

Status: completed. This is a no-PPO C1 interface smoke over frozen v2
structured-oracle rows. It performs no behavior pretraining, writes no policy
checkpoint, does not mutate the incumbent, and makes no driver-performance,
validation, promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, C2-admission, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3235-c1-tail-family-interface-smoke.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_tail_family_interface_smoke_prereg.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_tail_family_interface_smoke.json`
- Interface targets: `runs/feasibility_audit/c5prime_c1_tail_family_interface_smoke/quick/interface_targets.npz`
- Harness log: `runs/research/m3235-c1-tail-family-interface-smoke_20260612T065819Z/command.log`

## Measured

M3235 replayed the frozen M3232 v2 structured-oracle quick rows and encoded a
prefix/tail interface target artifact.

| measurement | value |
|---|---:|
| selected rows | 11 |
| train / selection / validation rows | 6 / 2 / 3 |
| demo replay successes | 11 / 11 |
| total frames | 1318 |
| tail frames | 831 |
| tail-frame share | 0.630501 |
| held-out family train coverage | 1.000000 |
| unsupported structured families | 0 |
| tail reconstruction MSE | 0.000000 |
| tail max abs error | 0.000000 |
| policy checkpoints written | 0 |

Frozen gates:

| gate | result |
|---|---|
| M3234 interface pricing positive | pass |
| demo replay all success | pass |
| held-out family train coverage | pass |
| all structured families supported | pass |
| required validation probes present | pass |
| tail reconstruction MSE <= 1e-12 | pass |
| tail max abs error <= 1e-6 | pass |
| tail frames >= 200 | pass |
| interface target artifact exists | pass |
| no policy checkpoint written | pass |

## Inferred

The smoke verifies the target path for a structured tail-family interface: the
tail segment of the failed direct action-regression problem can be represented
exactly by a discrete oracle family plus reveal-relative phase for this frozen
quick panel.

This does not show that a trainable policy can learn the interface, does not
rank a driver, and does not admit C2. It only justifies registering a separate
tail-family interface pretrain design/quick milestone with its own frozen
criteria.

## Decision

Verdict: `tail_family_interface_smoke_passed`.

C1 remains open under
`c5prime_track_c_c1_tail_family_interface_pretrain_design`. C2 and C3 remain
blocked. The next admissible C1 work unit is a preregistered tail-family
interface pretrain design/quick milestone; no full C1 training or C2 execution
is admitted by M3235.
