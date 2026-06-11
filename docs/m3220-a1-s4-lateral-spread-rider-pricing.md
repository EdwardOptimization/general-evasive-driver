# M3220: A1 S4-Lateral Spread Rider Pricing

Status: completed. This is an auxiliary pricing measurement only. It does not
mutate the incumbent, run RL, admit Track C training, or make a driver
performance, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/c5_lateral_prereg.json`
- Full summary: `experiments/feasibility_audit/c5_lateral_spread_rider.json`
- Quick smoke: `experiments/feasibility_audit/c5_lateral_spread_rider_quick.json`
- Episode rows: `runs/feasibility_audit/c5_lateral_spread_rider/episode_rows.csv`
- Managed run log: `runs/managed/m3220-a1-s4-lateral-spread-rider_20260611T191239Z/run.log`

## Measurement

M3220 executed roadmap A1: the final cheap current-sim check of whether the
rejected C5 spread mechanism comes back when spread hits the lateral channel
instead of the mass/brake/drive/tau channel.

The S4L tier held mass, brake, drive, tire-stiffness scale, and actuator tau at
nominal, and sampled only:

- `cg_shift`: U[-0.42, +0.42] m, mapped through the existing `VehicleParams`
  `lf/lr` path.
- `inertia_scale`: U[0.6, 1.6], mapped to `Iz`.

The realized S4L envelope was:

| quantity | min | max | median |
|---|---:|---:|---:|
| cg_shift m | -0.3686 | 0.4051 | -0.0307 |
| lf m | 0.9814 | 1.7551 | 1.3193 |
| lr m | 1.0449 | 1.8186 | 1.4807 |
| inertia scale | 0.6403 | 1.5662 | 1.1797 |
| Iz | 1472.63 | 3602.21 | 2713.40 |

Runtime: 24 RLS prefixes, 7,776 selection episodes, 2,112 validation arm
episodes, 5,687 oracle rollouts, 345.6 s CPU. The fixed once-selected config
was unchanged from C5: `(brake=1.0, steer=1.45, relevance=1.0)`, with S0
selection success 132/144.

## Result

Pre-registered qualifying rule: a cell qualifies only if
`pertuned - fixed_star >= 0.15`, paired-bootstrap CI95 lower bound > 0, and
`pertuned - v4_rls >= 0.08`.

M3220 result: **0/4 cells qualify**. S4L lateral spread does not open a
measurable per-cell pricing gap in this current-sim rider.

| cell | oracle solved | fixed* | RLS | pertuned | prize | residual |
|---|---:|---:|---:|---:|---:|---:|
| S0/T-mid | 117/120 | 0.966 | 0.966 | 0.966 | +0.000 [0.000, 0.000] | +0.000 [0.000, 0.000] |
| S0/T-limit | 144/144 | 0.812 | 0.812 | 0.812 | +0.000 [0.000, 0.000] | +0.000 [0.000, 0.000] |
| S4L/T-mid | 117/120 | 0.966 | 0.966 | 0.957 | -0.009 [-0.026, 0.000] | -0.009 [-0.026, 0.000] |
| S4L/T-limit | 142/144 | 0.838 | 0.838 | 0.845 | +0.007 [-0.014, 0.028] | +0.007 [-0.014, 0.028] |

The grid arm selected the same fixed* config in 42/48
`(level, surface, instance)` cells. The six non-fixed selections did not
produce a validation gain at the pre-registered threshold.

## Interpretation

Measured: within this low-fidelity environment, the lateral cg/Iz channel also
fails to rescue the original C5 spread story. The fixed once-selected controller
is flat from S0 to S4L, and the best grid arm has no material advantage over the
fixed or kappa-RLS arms.

Inferred: this strengthens the current-sim conclusion that the actionable prize
is not population-specific calibration. The surviving prize remains the
T-limit structural ceiling gap measured by C5 (`oracle - pertuned` around
+0.16 to +0.21), not the spread mechanism.

Limits: M3220 still does not express load transfer, tire-curve shape changes,
wheel lockup, wheelbase classes, or high-fidelity Chrono vehicle-family
dynamics. The negative result therefore closes only the current-sim cg/Iz rider,
not real-world passenger-car variability.

## Decision

Accept M3220 as a completed A1 pricing rider. Update the roadmap status to
A1 DONE. The next lowest OPEN unit is A2, the observation-normalization audit,
unless the PI redirects.
