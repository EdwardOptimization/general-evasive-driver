# M3241: B2b High-speed Pricing Smoke

Status: completed. This is a quick protocol smoke for the B2b high-speed
domain pricing panel. It runs no training, writes no policy checkpoint, does
not mutate the incumbent, and makes no full B2b pricing, driver-performance,
validation, promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, C2-admission, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3241-b2b-high-speed-pricing-smoke.json`
- Preregistration: `experiments/feasibility_audit/high_speed_pricing_prereg.json`
- Result JSON: `experiments/feasibility_audit/high_speed_pricing_quick.json`
- Episode rows: `runs/feasibility_audit/high_speed_pricing/episode_rows_quick.csv`
- Harness log: `runs/research/m3241-b2b-high-speed-pricing-smoke_20260612T082229Z/command.log`

## Measured

Protocol gates:

| gate | value |
|---|---:|
| accepted | true |
| selection/validation seeds disjoint | true |
| validation rows | 8 |
| rows visible under fixed_star | 8 |
| oracle-attempted rows | 8 |
| structured/CEM-or-success coverage | true |

Compute budget:

| readout | value |
|---|---:|
| selection episodes | 108 |
| validation arm episodes | 32 |
| oracle rollouts | 27 |
| elapsed seconds | 2.0 |

The quick panel exercised two high-speed cells: `hs24_tight_mu055` and
`hs30_tight_mu075`. Both had `drift_required` labels on all four validation
rows.

Arm outcomes on the oracle-solved denominator:

| cell | oracle-solved rows | raw incumbent | fixed_star | v4_rls | v4_pertuned | oracle - pertuned |
|---|---:|---:|---:|---:|---:|---:|
| `hs24_tight_mu055` | 4 | 1.0000 | 0.7500 | 0.7500 | 0.7500 | 0.2500 |
| `hs30_tight_mu075` | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

For `hs24_tight_mu055`, the paired bootstrap CI95 for
`oracle - v4_pertuned` was `[0.0000, 0.7500]`; this does not clear a
positive lower-bound gate. For `hs30_tight_mu075`, the gap was 0.

The selected `fixed_star` grid was the identity `(1.0, 1.0, 1.0)`, with
4/4 pooled selection successes. The identity grid also had 4/4 pooled
selection successes.

## Inferred

The B2b protocol is wired: M3224 high-speed profile rows, disjoint
selection/validation streams, raw incumbent transfer reporting, scale-aware
fixed*/pertuned classical floors, inert/no-spread RLS accounting, and
reveal-constrained oracle attempts all executed through the harness.

The quick smoke is directionally more interesting than B1b, but still not a
pricing result. One quick cell showed a 0.25 oracle-minus-pertuned gap, but
the CI lower bound was exactly 0 and the panel has only four validation rows
per cell. Full B2b pricing is still required.

## Decision

Verdict: `b2b_pricing_protocol_smoke_passed`.

M3241 admits only a separate full B2b pricing run. It does not admit
high-speed Track C training, C2, or any driver-performance claim.
