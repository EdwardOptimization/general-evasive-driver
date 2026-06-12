# M3239: B1b Moving-obstacle Pricing Smoke

Status: completed. This is a quick protocol smoke for the B1b
moving-obstacle pricing panel. It runs no training, writes no policy
checkpoint, does not mutate the incumbent, and makes no full B1b pricing,
driver-performance, validation, promotion, high-fidelity sufficiency, paper,
repair-success, robustness-result, feasibility-proof, C2-admission, or
self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3239-b1b-moving-obstacle-pricing-smoke.json`
- Preregistration: `experiments/feasibility_audit/moving_obstacle_pricing_prereg.json`
- Result JSON: `experiments/feasibility_audit/moving_obstacle_pricing_quick.json`
- Episode rows: `runs/feasibility_audit/moving_obstacle_pricing/episode_rows_quick.csv`
- Harness log: `runs/research/m3239-b1b-moving-obstacle-pricing-smoke_20260612T080032Z/command.log`

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
| oracle rollouts | 12 |
| elapsed seconds | 3.4 |

The quick panel exercised two preregistered moving-obstacle cells:
`slow_early_centering` and `fast_late_centering`.

Arm outcomes on the oracle-solved denominator:

| cell | oracle-solved rows | fixed_star | v4_rls | v4_pertuned | oracle - pertuned |
|---|---:|---:|---:|---:|---:|
| `slow_early_centering` | 4 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| `fast_late_centering` | 4 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

The selected `fixed_star` grid was the identity `(1.0, 1.0, 1.0)`, with
4/4 pooled selection successes. The identity grid also had 4/4 pooled
selection successes.

The `v4_rls` arm was intentionally inert on this panel:
`nominal_no_spread_inert_identical_to_fixed_star`. B1b varies moving-obstacle
timing and geometry, not vehicle population parameters, so there is no honest
vehicle-identification signal for an RLS retune here.

## Inferred

The protocol is now wired: disjoint selection and validation streams, fixed*
selection, per-cell reflex tuning, inert/no-spread RLS accounting, dynamic
crosser rows, and reveal-constrained oracle attempts all executed through the
harness.

The quick cells are too easy to support the B1b prize. Every reflex arm
already succeeds on every quick validation row, so the measured structural gap
is exactly zero in quick mode. This does not reject B1b because quick mode was
not powered or intended as pricing; it does mean the full pricing run should
not be sold as a foregone positive and should preserve or harden the
pre-registered full cells.

## Decision

Verdict: `b1b_pricing_protocol_smoke_passed`.

M3239 admits only a separate full B1b pricing run or a preregistered hardening
of that full panel. It does not admit moving-obstacle Track C training, C2, or
any driver-performance claim.
