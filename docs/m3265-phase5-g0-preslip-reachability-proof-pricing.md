# M3265 Phase-5 G0 Pre-Slip Reachability Proof-Route Pricing

Date: 2026-07-10

## Decision

**Completed / BLOCK AND RE-PRICE.** The proof machinery recovered the known
larger-control-set positive control, preserved deterministic action semantics,
and exposed finite Chrono tire telemetry. It did not satisfy the frozen planar
deliberate-slide expressibility gate in any of the three full emergency cells.
M3266 full reachable-set adjudication is therefore not admitted.

This milestone makes no reachable-set-dominance, detailed-model theorem,
paper-readiness, promotion, production-ESC, or self-ID claim.

## Frozen protocol

- Preregistration:
  `experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing_prereg.json`
- Theory certificate:
  `docs/preslip-reachable-set-dual-proof-theory-2026-07.md`
- Quick artifact:
  `experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing_quick.json`
- Full artifact:
  `experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json`
- Full raw rows:
  `runs/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing/full/`

The grip arm required maximum body sideslip at or below 0.12 rad. The slide arm
required body sideslip at or above 0.20 rad for at least four control frames
before the obstacle center, together with rear lateral-force utilization of at
least 0.90. Both arms used the same plant, actuator limits, matched CEM budget,
and disjoint deterministic optimizer seeds.

## Measured results

### Known-counterexample positive control

The frozen Zhao et al. 2022 Dubins construction was reproduced:

| yaw-rate set | minimum clearance |
|---|---:|
| conventional, 0.20 rad/s | -0.541 m |
| beyond-limit, 0.26 rad/s | +0.351 m |

This gate passing shows that the protocol can detect a drift-only witness when
the beyond-limit arm is deliberately given a larger control set.

### Matched planar mode pricing

| cell | grip valid | grip success | slide max beta | slide dwell | slide valid |
|---|---:|---:|---:|---:|---:|
| mu0p35_v12_ttc0p95 | yes | no | 0.134 | 0 | no |
| mu0p60_v14_ttc0p80 | yes | no | 0.205 | 1 | no |
| mu0p90_v16_ttc0p70 | yes | no | 0.222 | 2 | no |

All best trajectories were on the collision boundary. Minimum signed OBB
separation for the grip arm was -0.0016/-0.0018/-0.0002 m; for the slide arm it
was -0.0006/-0.1837/-0.3316 m. These numbers are pricing diagnostics, not a
dominance result, because the slide arm failed its own mode-validity gate.

### Chrono connector

Both connector profiles returned finite obs72 and finite tire-slip telemetry.
The nominal `grip_probe` reached maximum body sideslip 0.0372 rad and maximum
reported tire slip angle 0.3233 rad. The nominal `slide_probe` reached only
0.0197 rad body sideslip despite a 0.6842 rad maximum reported tire slip angle;
neither produced a four-frame deep-body-slide dwell. The aggregate tire value
also does not identify which axle produced the maximum. The connector gate
passes, but Chrono deliberate-slide expressibility remains unproven.

## Gate table

| gate | result |
|---|---|
| known larger-control-set positive control | PASS |
| matched planar mode expressibility | **FAIL** |
| search-health history | PASS |
| exact same-seed determinism | PASS |
| Chrono obs72/tire-telemetry connector | PASS |
| all protocol gates | **FAIL** |

## Interpretation

The result distinguishes two hypotheses that the older constant-action audits
conflated:

1. deep slide may not be physically initiable before collision in these short
   windows; or
2. the current parameterization/objective may be too weak to find an initiable
   slide.

M3265 cannot distinguish them because collision terminates the rollout before
the required dwell can accumulate. Treating this failure as an empty slide
feasible set would be circular.

## Required re-pricing before adjudication

The next proof-route unit must:

1. establish same-plant slide expressibility in obstacle-disabled, longer-horizon
   positive-control cells;
2. optimize time-to-slide and maximum pre-obstacle slide dwell independently of
   collision clearance;
3. persist front- and rear-axle tire-slip/force truth separately on Chrono;
4. retain the 0.20/0.26 rad/s positive control and the 0.12/0.20 rad ambiguous
   band;
5. block full reachable-set adjudication again if the detailed-model slide
   positive control or onset-time measurement fails.

No threshold is relaxed by M3265.
