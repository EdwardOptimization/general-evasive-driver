# The two-regime thesis: drift is non-essential BEFORE slip, and "save-the-car" is closed-loop steering AFTER slip

Synthesis of directions 3 -> 2 -> 1. The popular "drift to avoid" intuition is FALSE; the real, consistent
differentiator is CLOSED-LOOP CONTROL OF THE VEHICLE AT THE FRICTION LIMIT (with active steering authority). "Drift"
is a STATE (deep sideslip), not a special technique you choose.

## Regime A -- BEFORE slip (grip intact): drift is non-essential, indeed counterproductive (direction 3)
Five measurements (lateral-capacity/label, CG reachability, axis-aligned box-SAT, angled+extended box-SAT, faithful
Chrono multibody), adversarially verified: controlled drift gives NO obstacle-avoidance advantage; it is equal-or-worse
everywhere; load transfer + tail-swing make it strictly worse where they bite. With physically-grounded labels the
genuine "must-drift" fraction is ~2% (the original label's 20.5% came from a 2x-understated conventional-grip
assumption). => "drift to avoid" is debunked.

## What the avoidance driver's value actually is (direction 2): closed-loop limit control, not drift, not mu-knowledge
RL (realistic obs) avoids 0.965 of the corrected avoidable spectrum (collision 0.035); non-privileged fixed rules
get <=0.43 and SLIDE OUT (sideslip 0.51). Mechanism probe: giving the rule the TRUE mu (mu_aware_aes) does NOT help
(0.430 == honest_aes). So the differentiator is NOT a maneuver (drift) and NOT friction knowledge -- it is CLOSED-LOOP
control: the RL modulates on the vehicle response to ride the limit without spinning; a fixed feedforward rule cannot,
even with perfect mu.

## Regime B -- AFTER slip (deep slide): active closed-loop steering SAVES the car where brake-only ESC fails (direction 1)
Recovery reachability (scripts/audits/recovery_reachability.py): init at a developing slide (sideslip beta0 + matching
yaw), compare a BRAKE-ONLY ESC (no counter-steer, mirrors classic ESC = wheel braking + torque cut) vs a
STEERING-CAPABLE closed-loop controller. There is a genuine band where steering control recovers and brake-only ESC
spins out (3/15 cells): DEEP slides (beta0 ~0.8-1.1 rad, i.e. 46-63deg) on LOW-to-MID mu (0.4-0.6). Shallow slides:
both recover. Extreme+low-mu (beta0>=0.9, mu=0.4): neither (physically unrecoverable). High mu (0.9): both recover.
=> drift/slide MANAGEMENT has real value, but ONLY AFTER the slide has developed -- exactly the complement of regime A.

## Unified conclusion
- "Drift" is a red herring: a state, not a technique. It does NOT help you avoid while grip is intact (regime A).
- The real skill is CLOSED-LOOP CONTROL AT THE LIMIT WITH ACTIVE STEERING. It beats fixed feedforward rules at
  avoidance (regime A driver), and beats brake-only ESC at deep-slide recovery (regime B). RL learns it; rules don't.
- The two-regime law: BEFORE slip drift is unnecessary; AFTER slip, active-steering slide management is the rescue.

## Honest caveats
- Baselines: honest_aes / brake-only-ESC are fixed/limited; a slip-feedback or active-steering ESC would narrow both
  gaps -- but such a controller is CONVERGING toward closed-loop steering control = what the RL learns. The defensible
  claim is about closed-loop-steering vs feedforward/brake-only, not "RL beats every conceivable rule".
- The recovery "best closed-loop" is a small gain sweep, not an optimal controller, so the recoverable-set boundary is
  a lower bound; a better controller may recover a slightly larger band.
- Planar dynamics for the sweeps (Chrono confirmed regime A); regime B on faithful Chrono is the natural next check.

## Regime B CONFIRMED on faithful Chrono (scripts/audits/chrono_recovery.py)
Repeated the slide-recovery test on the real multibody backend (init the Chrono vehicle in a developing slide via
initial_state vx/vy/yaw_rate, honored by the solver). Two faithful-physics refinements of the planar result:
1. The faithful vehicle is FAR more self-stabilising: with NO control it self-recovers from sideslips up to ~63deg at
   moderate yaw (planar spun). So the "needs active steering" band is narrower -- it requires HIGH yaw (3.0-4.0 rad/s)
   at MID mu (~0.5); at low mu (0.35) or extreme yaw (>=4.5) the spin is unrecoverable by anything.
2. In that developing-spin band (mu=0.5, beta0 34-57deg, yaw 3.0-4.0), BRAKE-ONLY ESC FAILS 9/9 -- it SPINS the car
   out (6/9) or STOPS it sideways (3/9), NEVER recovering. ACTIVE COUNTER-STEER recovers 9/9 (uniquely in 6/9).
   => braking during a developing spin is actively CATASTROPHIC on the faithful vehicle (load shifts off the rear,
   the brake force eats the friction circle); active counter-steer (the skilled-driver / RL action) is the rescue.

Net: the two-regime thesis is now Chrono-confirmed on BOTH sides. Regime A -- before slip, drift gives no avoidance
advantage (drift worse on Chrono via load transfer). Regime B -- after slip, active-steering closed-loop control
recovers where classic brake-based ESC catastrophically fails. The unifying law: the right control is ACTIVE STEERING
AT THE LIMIT; brakes/feedforward rules are the wrong tool both for limit avoidance and for spin recovery, and RL
learns the active closed-loop steering that wins in both regimes.
