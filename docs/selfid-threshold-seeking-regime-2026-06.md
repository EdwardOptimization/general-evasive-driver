# Measurement B: Ramp-Policy VoI Regime Map (2026-06-11)

## Status

- measurement: `ramp_policy_voi_regime` — reveal-window sweep x controller
  classes on the B2K2_final commitment family, continuous mu (12
  points/window), selection + validation seeds, 11,280 episodes, 842 s CPU.
- data: `experiments/feasibility_audit/ramp_policy_voi_regime.json`,
  `runs/feasibility_audit/ramp_policy_voi_regime/episode_rows.csv`.
- claim boundary: scripted-controller measurement only; no training-level,
  driver-performance, or high-fidelity claim.

## Headline

**VoI(belief) = 0.000 at every reveal window tested (9.5/12/16/22/30 m).**
A belief-free threshold-seeking controller — worst-case-floor start, maximal
ramp, embedded shortfall identification (measurement A detector), immediate
re-plan, reflex-style reaction — matches the per-mu oracle everywhere,
including the tightest window where blind-commitment analysis had put the
value of knowing mu at 0.39-0.44.

## Regime matrix (validated success)

| reveal | oracle | seeker (no belief) | prior-seeker (+/-0.2 bin) | best fixed speed | best fixed ramp | VoI(belief) | detection value |
|---|---|---|---|---|---|---|---|
| 9.5 m | 0.958 | **0.958** | 0.875 | 0.375 | 0.125 | 0.000 | **0.583** |
| 12 m | 1.000 | 1.000 | 1.000 | 0.750 | 0.333 | 0.000 | 0.250 |
| 16 m | 1.000 | 1.000 | 1.000 | 0.917 | 0.333 | 0.000 | 0.083 |
| 22 m | 1.000 | 1.000 | 1.000 | 0.917 | 0.333 | 0.000 | 0.083 |
| 30 m | 1.000 | 1.000 | 1.000 | 0.833 | 0.333 | 0.000 | 0.167 |

detection value = seeker − best fixed plan: the worth of *embedded
identification* (identify-while-acting), which is what blind-commitment
policy classes lack. It is large exactly where the earlier commitment-VoI
was large — i.e. the 0.39-0.44 measured against fixed plans was real, but it
is captured **entirely** by a reactive short-window faculty, leaving zero
residual for a persistent belief.

Notable details:

- At reveal 9.5 the oracle and the seeker fail the *same* knife-edge mu
  point (0.958 both): there is literally no gap between "solvable with
  perfect knowledge" and "solvable by embedded identification" for a prior
  to live in.
- The prior-seeker is *worse* than the plain seeker at 9.5 m (0.875): its
  +/-0.2 bin floor start makes it overconfident at the domain edge (fails
  the lowest-mu point outright). A wrong-ish prior is a liability; the
  belief-free worst-case floor is safer.
- on_time = 1.000 for seekers at all windows: the deadline cost of starting
  from the worst-case floor and identifying on the way is ~zero in this
  family.

## Speed-accuracy frontier

Bolder starts + faster ramps dominate: mean identification step falls from
~115 (timid: ramp 800 N/s, conservatism 0) to ~22 (bold) while success rises
0.25 -> 1.00 and collisions stay 0 — because overshoot inside the rescue
budget is cheap (measurement C). "Experience = daring to ride the edge"
shows up as a frontier shift, but the daring is licensed by detection +
rescue, not by a mu-belief.

## Fidelity caveats (from the JSON, honest limits)

1. `dynamics.py` clamps rear fx at the friction limit with no lockup mode:
   straight-line over-braking costs almost nothing in-env, so fast ramps are
   not intrinsically punished (measurement C covers injected instability
   separately).
2. The 6000 N brake actuator saturates below the tire limit for mu > ~0.89:
   brake-side identification is censored at high mu; seekers recover via
   drive-side shortfall on re-acceleration.
3. Observations are noiseless and undelayed. Detection latency (140-400 ms,
   measurement A) is the quantity that buys belief its irrelevance; **under
   degraded observations the latency grows and belief value may re-emerge** —
   this is the one open door, directly testable with the
   observation-degradation wrapper (M3214 infrastructure).

## Conclusion

In this simulator and task family, the expert-driver mechanism implemented
faithfully (worst-case floor -> maximal informative ramp -> embedded
shortfall identification -> immediate re-plan -> reflex rescue) is
**complete without any persistent capability belief**. The skill
decomposition lands as: detection speed and rescue bandwidth carry all the
measured value; the prior carries none and can hurt at domain edges. The
remaining testable condition for belief to matter is observation
degradation (slower detection), and window tightnesses inside the
identification distance — which the data shows border directly on physical
unavoidability.
