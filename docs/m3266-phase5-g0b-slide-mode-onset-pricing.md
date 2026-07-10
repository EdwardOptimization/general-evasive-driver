# M3266 Phase-5 G0b Slide-Mode Expressibility and Onset Pricing

Date: 2026-07-10

## Decision

**Completed / protocol gates passed.** The same planar and Chrono plants can
enter the frozen high-sideslip mode from a straight pre-slip state. The final
reachable-set adjudication may now be designed, but M3266 itself makes no
reachable-set, collision-avoidance, paper, promotion, or self-ID claim.

## Artifacts

- Preregistration:
  `experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing_prereg.json`
- Quick:
  `experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing_quick.json`
- Full:
  `experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json`
- Raw rows:
  `runs/feasibility_audit/phase5_g0b_slide_mode_onset_pricing/full/`

## Measured planar onset pricing

The obstacle was disabled during mode generation. The `obstacle_x` column is a
reference distance inherited from M3265; it was not a collision boundary in
this experiment.

| cell | first 4-frame onset | onset x | reference obstacle x | max beta | max dwell |
|---|---:|---:|---:|---:|---:|
| mu0p35_v12 | 0.72 s | 9.872 m | 11.4 m | 1.563 | 84 |
| mu0p60_v14 | 0.56 s | 9.277 m | 11.2 m | 1.552 | 65 |
| mu0p90_v16 | 0.46 s | 8.951 m | 11.2 m | 1.556 | 61 |

The optimizer intentionally maximized entry/dwell and the planar trajectories
later developed into spins. These rows prove high-sideslip onset expressibility
and provide a best-found onset scale only. They do not represent controlled
drift or a useful avoidance trajectory.

## Measured Chrono onset pricing

The `beta=0.24` classifier positive control passed with 120/120 axle-specific
tire-telemetry frames. From `beta=0`, direct CEM produced:

- first four-frame high-sideslip onset: **0.50 s**;
- maximum body sideslip: **0.484 rad**;
- maximum rear tire slip angle: **0.541 rad**;
- maximum front tire slip angle: **0.886 rad**;
- high-sideslip dwell: **72 frames**;
- best-action replay: exact within the frozen 1e-9 tolerance.

This closes M3265's method-level concern that the matched Chrono plant or
search parameterization could not generate the slide arm.

## Gate table

| gate | result |
|---|---|
| M3265 literature positive control retained | PASS |
| all planar same-plant entry cells valid | PASS |
| planar onset rows complete | PASS |
| Chrono beta=0.24 classifier positive control | PASS |
| Chrono beta=0 same-plant entry | PASS |
| axle-specific rear-slip requirement | PASS |
| exact best-action replay | PASS |
| all protocol gates | PASS |

## Contact-deadline correction for the final experiment

M3266's preregistered `pre_obstacle_mode_valid` field compares slide onset with
the obstacle **center**. That is adequate for persisting an onset reference but
is not the physical latest-start condition for an OBB collision. For a
lane-aligned obstacle the first nominal contact plane is approximately

`x_contact = D - obstacle_half_depth - vehicle_front_projection`.

Using the M3265 dimensions, the contact line is about 2.85 m before the obstacle
center. All three best planar onset locations above are therefore after the
corresponding nominal first-contact line. This does not fail M3266's frozen
mode-generation question because the obstacle was disabled, but it prevents
reusing `pre_obstacle_mode_valid` as collision-avoidance evidence.

## Requirements carried into final adjudication

The next experiment must:

1. evaluate the actual OBB first-contact plane, not obstacle center;
2. choose validation distances from M3266 onset pricing so the required-slide
   arm is physically expressible before contact in at least one tier;
3. compare matched `grip`, `required_slide`, and unconstrained `free` oracles;
4. require controlled slide, including a beta upper bound, speed floor, road
   containment, and no spin;
5. optimize the minimum clearable obstacle distance `D*` and report
   `D*_slide - D*_grip`, with smaller `D*` meaning a larger feasible set;
6. retain the literature and detailed-plant positive controls;
7. separate finite-domain empirical support from the bounded theorem.
