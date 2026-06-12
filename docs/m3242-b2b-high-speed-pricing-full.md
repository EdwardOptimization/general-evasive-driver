# M3242: B2b High-speed Pricing Full

Status: completed. This is the full preregistered B2b high-speed pricing
panel admitted by M3241. It runs no training, writes no policy checkpoint,
does not mutate the incumbent, and makes no driver-performance, validation,
promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, C2-admission, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3242-b2b-high-speed-pricing-full.json`
- Preregistration: `experiments/feasibility_audit/high_speed_pricing_prereg.json`
- Result JSON: `experiments/feasibility_audit/high_speed_pricing.json`
- Episode rows: `runs/feasibility_audit/high_speed_pricing/episode_rows.csv`
- Harness log: `runs/research/m3242-b2b-high-speed-pricing-full_20260612T082644Z/command.log`

## Measured

Protocol gates:

| gate | value |
|---|---:|
| selection/validation seeds disjoint | true |
| validation rows | 48 |
| rows visible under fixed_star | 48 |
| oracle-attempted rows | 48 |
| structured/CEM-or-success coverage | true |

Compute budget:

| readout | value |
|---|---:|
| selection episodes | 648 |
| validation arm episodes | 192 |
| oracle rollouts | 197 |
| elapsed seconds | 11.5 |

The selected `fixed_star` grid was the identity `(1.0, 1.0, 1.0)`, with
21/24 pooled selection successes. The identity grid also had 21/24 pooled
selection successes. The inert `v4_rls` arm is intentionally identical to
`fixed_star` because this B2b panel has no vehicle-spread channel to identify;
it is retained to preserve the C5 pricing accounting convention.

Full-panel pricing on the oracle-solved denominator:

| cell | labels | oracle-solved rows | raw incumbent | fixed_star | v4_rls | v4_pertuned | oracle - pertuned | paired CI95 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `hs24_tight_mu055` | 8 drift_required | 8 | 0.8750 | 0.8750 | 0.8750 | 0.8750 | 0.1250 | [0.0000, 0.3750] |
| `hs30_mid_mu055` | 3 aes_feasible / 5 drift_required | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | [0.0000, 0.0000] |
| `hs30_tight_mu075` | 8 drift_required | 8 | 0.8750 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | [0.0000, 0.0000] |
| `hs36_mid_mu075` | 2 aes_feasible / 6 drift_required | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | [0.0000, 0.0000] |
| `hs36_tight_mu075` | 8 drift_required | 8 | 0.8750 | 0.8750 | 0.8750 | 0.8750 | 0.1250 | [0.0000, 0.3750] |
| `hs36_tight_mu095` | 8 drift_required | 8 | 0.6250 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | [0.0000, 0.0000] |

No cell qualified by the frozen B2b rule:
`qualifying_cells=[]`. The frozen rule required at least two full-panel cells
with `oracle - v4_pertuned >= 0.15` and paired bootstrap CI95 lower bound
above 0.

Row diagnostics:

| readout | value |
|---|---:|
| `drift_required` labels | 43/48 |
| `aes_feasible` labels | 5/48 |
| raw incumbent successes | 42/48 |
| fixed_star successes | 46/48 |
| v4_rls successes | 46/48 |
| v4_pertuned successes | 46/48 |
| oracle solvability | 48/48 |
| raw incumbent min clearance margin | -0.1768 m |
| fixed_star min clearance margin | -0.2734 m |
| v4_pertuned min clearance margin | -0.2734 m |
| reveal-step range | 3-10 |

Oracle successes were achieved by structured candidates in every row:
`structured:full_brake` on 21 rows, `structured:coast_steer_+0.65` on
16 rows, `structured:brake_steer_-0.35` on 6 rows,
`structured:brake_steer_+0.35` on 4 rows, and
`structured:coast_steer_-0.65` on 1 row.

Scale-aware classical control improved raw incumbent transfer in two cells:
`hs30_tight_mu075` had fixed_star minus raw incumbent +0.1250 with paired
CI95 `[0.0000, 0.3750]`, and `hs36_tight_mu095` had +0.3750 with paired
CI95 `[0.0000, 0.7500]`. These are reported diagnostics, not the primary
B2b prize criterion.

## Inferred

The B2b current high-speed formulation is negative by the preregistered rule.
The panel was not blocked by oracle feasibility or protocol coverage: every
validation row had a reveal step, every row was oracle-attempted, and oracle
solvability was 1.0. The negative verdict comes from the honest scale-aware
classical floor: `fixed_star` and `v4_pertuned` solved 46/48 validation rows,
leaving only two weak oracle-minus-pertuned pockets of 0.125 whose confidence
intervals include 0.

This is not as null as B1b. Most rows are labeled `drift_required`, the raw
incumbent transfer loses 6/48 rows, and the M3224 scale adapter matters in
the 30 m/s tight and 36 m/s high-mu tight cells. But the measured gap is
below the frozen +0.15 effect-size bar, not CI-positive, and not present in
the required two cells.

This rejects the current B2b high-speed type-(b) prize. It does not prove that
no high-speed task can ever create a gap; it says this six-cell M3224-profile
panel does not create a priced window-compression region beyond the best
scale-aware reflex-family baseline. Any later high-speed hardening,
degraded-sensing descriptive rider, or more adversarial task geometry must be
a new preregistered unit rather than a repair of M3242.

## Decision

Verdict: `b2b_high_speed_pricing_negative`.

B2b current formulation is done-negative. No high-speed Track C extension,
C2 admission, training, or driver-performance claim is admitted. With B1b and
B2b closed negative, the local autonomous roadmap has no lower-numbered OPEN
pricing unit unless PI reopens C1 or registers a new independent unit.
