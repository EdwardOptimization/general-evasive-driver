# Direction 2: the honest avoidance driver -- differentiator is CLOSED-LOOP LIMIT CONTROL, not drift, not mu-knowledge

## Physically-corrected labels (conventional_lateral_mu_fraction 0.42->0.86, drift 0.85->0.90; measured AVERAGE capacity)
configs/m5_obstacle_corrected_avoidable_eval.json. With honest labels the "must-drift" bucket nearly vanishes:
drift_required = 1/200 (~0.5%) in the sampled distribution -- the avoidable spectrum is essentially aeb_feasible +
aes_feasible. (Original mislabel: drift_required 20.5%.)

## RL vs HONEST (non-privileged) baselines, corrected labels, 200 eps, per bucket
| bucket (n) | RL (realistic obs) | honest_aes (assumed mu) | mu_aware_aes (TRUE mu) | aeb |
|---|---|---|---|---|
| aeb_feasible (110) | 1.000 | 0.473 | -- | 0.164 |
| aes_feasible (89)  | 0.933 | 0.382 | -- | 0.180 |
| overall            | **0.965** | 0.430 | **0.430** | 0.170 |
| collision          | 0.035 | 0.370 | 0.370 | 0.795 |
| high_sideslip_frac | 0.153 | 0.509 (SLIDES) | 0.510 (SLIDES) | 0.127 |

## Mechanism (what is the RL's real differentiator?)
- It is NOT a special maneuver (drift): drift gives no avoidance advantage (direction 3, 5 measurements) and the RL's
  sideslip (0.15) is moderate, not a drift.
- It is NOT friction knowledge: mu_aware_aes (given the TRUE mu, no label) = honest_aes (assumed mu) = 0.430. Knowing
  mu does not rescue the fixed-gain rule -- it still SLIDES OUT (sideslip 0.51) and fails.
- It IS CLOSED-LOOP LIMIT CONTROL: the RL modulates steering/brake on the vehicle's RESPONSE to ride the friction
  limit without spinning out (sideslip 0.15, collision 0.035). A fixed feedforward rule cannot stay at the limit even
  with perfect mu -- it over- or under-commits and slides.

## Honest caveats (do NOT over-claim)
- These rule baselines are fixed-gain / open-loop; a SLIP-FEEDBACK (ESC-style) rule that reduces command when slip is
  detected would be a fairer "best rule" and likely beats honest_aes. But such a rule is closing the loop on the
  vehicle response -- i.e. converging toward exactly what the RL learns. The defensible claim is therefore: "operating
  at the friction limit for obstacle avoidance requires CLOSED-LOOP control of the vehicle's response; the RL learns
  it from realistic observations; fixed feedforward rules (even mu-aware) cannot." NOT "RL beats every possible rule."
- The avoidance task and the RL's 0.965 are real; the corrected labels make drift_required ~0 so there is no
  must-drift regime to claim.
