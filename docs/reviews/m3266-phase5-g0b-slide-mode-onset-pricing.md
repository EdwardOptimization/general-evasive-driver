# Review: M3266 Phase-5 G0b Slide-Mode Expressibility and Onset Pricing

## Verdict

**PASS for pricing; final adjudication may be registered separately.**

## Findings

1. Same-plant mode expressibility is no longer a blocker. Planar and Chrono
   searches both entered the frozen beta>=0.20, four-frame mode from beta=0.
2. The Chrono result is the stronger positive control: onset 0.50 s, maximum
   beta 0.484 rad, rear slip 0.541 rad, 72-frame dwell, exact replay.
3. The planar objective rewards onset/dwell and produces later spin. Those
   trajectories are valid onset probes but invalid controlled-drift avoidance
   candidates.
4. The artifact's `pre_obstacle` label uses obstacle center. The final
   experiment must replace it with the OBB first-contact plane; otherwise a
   slide initiated after physical collision could be counted as timely.
5. M3266 provides no comparison between grip and slide collision-avoidance
   feasible sets. It only licenses that comparison methodologically.

## Final-experiment admission conditions

- controlled high-sideslip band with upper beta and speed/stability limits;
- matched grip/required-slide/free action and optimizer budgets;
- minimum clearable obstacle-distance boundary rather than a few hand-picked
  success cells;
- disjoint search and validation streams;
- positive-control sensitivity and free-oracle consistency gates;
- planar and Chrono results reported separately.
