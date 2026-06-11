# Final Measurement: VoI(belief) Under Observation Degradation (2026-06-11)

## Status

- measurement: `degraded_regime_final` — the thesis's "single remaining door"
  (docs/capability-boundary-tracking-thesis-2026-06.md Section 7): does belief
  value re-emerge when the ego-response observation channels are
  delayed/noisy? Two tightest reveal tiers (9.5 / 12 m) of the regime
  measurement x degradation matrix delay_steps {0,5,12,25} (0-0.5 s) x
  noise_std {0, 0.05} (ego channels 0-8, M3214 wrapper; geometry untouched).
- data: `experiments/feasibility_audit/degraded_regime_final.json`,
  `runs/feasibility_audit/degraded_regime_final/episode_rows.csv` (23,040
  regime episodes), `latency_rows.csv` (96 mechanism episodes). 839 s CPU.
- script: `scripts/feasibility_audit/degraded_regime_final.py` (reuses the
  controller family / task surface / evaluation pipeline of
  `ramp_policy_voi_regime.py` and the Measurement-A latency protocol of
  `slip_onset_detectability.py`).
- claim boundary: scripted-controller measurement only; no training-level,
  driver-performance, or high-fidelity claim.

## Headline

**VERDICT (pre-registered rule, threshold VoI >= 0.15 on validation seeds):
belief value RE-EMERGES under observation degradation.** 12 of 14 degraded
cells clear the threshold on the primary readout; at the tightest window
(9.5 m) **every** degraded cell clears it, including the mildest (100 ms
ego-response delay, no noise: VoI = +0.208). The clean cells reproduce the
original VoI = 0.000 bit-for-bit (replication anchor: identical seeds,
identical selected plan, oracle/seeker 0.958/0.958 at 9.5 m, 1.000/1.000 at
12 m).

The constructive null of `selfid-threshold-seeking-regime-2026-06.md` is
therefore **boundary-complete, not universal**: passive fast adaptation +
reflex is self-sufficient exactly while incipient-slip detection is fast and
reliable; degrade the felt response and the value of knowing the capability
envelope returns — and it returns as *precise* belief (per-mu oracle), not as
the coarse +/-0.2 prior.

## VoI definitions (two anchors, pre-declared)

- **voi_belief (PRIMARY, decision metric)** = clean-cell oracle success
  (degradation-FREE anchor, per the design spec: the oracle knows mu and
  needs no detection) minus the cell's best belief-free seeker. Justified in
  this deterministic simulator because the previous-command channels (9-11)
  are never degraded: a mu-knowing agent can dead-reckon its ego state from
  its own commands + known dynamics, so the clean oracle is an *attainable*
  ceiling for the belief-endowed class under any sensing degradation.
- **voi_belief_matched (SECONDARY)** = same-cell *degraded* oracle minus
  seeker: the value of knowing mu given identical sensing and no
  dead-reckoning credit. The two bracket belief value from above/below.

Episode geometry is identical across cells (jitter keyed by rollout seed
only), so all differences are caused by the degraded sensing alone.

## Regime matrix (validated success, 12 mu points x 2 val seeds per cell)

### reveal 9.5 m (tightest)

| delay (ms) | noise | oracle_clean | oracle_degraded | seeker | prior(+/-0.2) | best fixed | **VoI(belief)** | VoI matched | prior_adv | detect_value |
|---|---|---|---|---|---|---|---|---|---|---|
| 0   | 0    | 0.958 | 0.958 | 0.958 | 0.875 | 0.375 | **0.000** | 0.000 | -0.083 | +0.583 |
| 100 | 0    | 0.958 | 0.958 | 0.750 | 0.750 | 0.417 | **0.208** | 0.208 | 0.000 | +0.333 |
| 240 | 0    | 0.958 | 0.875 | 0.333 | 0.458 | 0.417 | **0.625** | 0.542 | +0.125 | -0.083 |
| 500 | 0    | 0.958 | 0.625 | 0.292 | 0.333 | 0.375 | **0.667** | 0.333 | +0.042 | -0.083 |
| 0   | 0.05 | 0.958 | 0.667 | 0.083 | 0.208 | 0.292 | **0.875** | 0.583 | +0.125 | -0.208 |
| 100 | 0.05 | 0.958 | 0.542 | 0.208 | 0.208 | 0.333 | **0.750** | 0.333 | 0.000 | -0.125 |
| 240 | 0.05 | 0.958 | 0.458 | 0.333 | 0.250 | 0.292 | **0.625** | 0.125 | -0.083 | +0.042 |
| 500 | 0.05 | 0.958 | 0.333 | 0.083 | 0.083 | 0.292 | **0.875** | 0.250 | 0.000 | -0.208 |

### reveal 12 m

| delay (ms) | noise | oracle_clean | oracle_degraded | seeker | prior(+/-0.2) | best fixed | **VoI(belief)** | VoI matched | prior_adv | detect_value |
|---|---|---|---|---|---|---|---|---|---|---|
| 0   | 0    | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | **0.000** | 0.000 | 0.000 | +0.250 |
| 100 | 0    | 1.000 | 1.000 | 1.000 | 1.000 | 0.792 | **0.000** | 0.000 | 0.000 | +0.208 |
| 240 | 0    | 1.000 | 1.000 | 1.000 | 1.000 | 0.833 | **0.000** | 0.000 | 0.000 | +0.167 |
| 500 | 0    | 1.000 | 0.542 | 0.667 | 0.625 | 0.917 | **0.333** | -0.125 | -0.042 | -0.250 |
| 0   | 0.05 | 1.000 | 0.875 | 0.792 | 0.750 | 0.750 | **0.208** | 0.083 | -0.042 | +0.042 |
| 100 | 0.05 | 1.000 | 0.875 | 0.792 | 0.917 | 0.750 | **0.208** | 0.083 | +0.125 | +0.042 |
| 240 | 0.05 | 1.000 | 0.792 | 0.833 | 0.792 | 0.792 | **0.167** | -0.042 | -0.042 | +0.042 |
| 500 | 0.05 | 1.000 | 0.500 | 0.417 | 0.458 | 0.833 | **0.583** | 0.083 | +0.042 | -0.417 |

(detect_value = seeker - best no-detection fixed plan; prior_adv = prior
seeker - plain seeker.)

## Mechanism evidence (measured)

1. **Detection latency grows with delay** (Measurement-A protocol re-run on
   degraded streams, per-cell re-calibrated tau, ground truth from
   undegraded env internals): median detection delay 7.0 -> 11.5 -> 27.5 ->
   32.0 steps (140 -> 230 -> 550 -> 640 ms) for obs delay 0/5/12/25 steps;
   command overshoot beyond the limit at detection 10% -> 25% -> 19% -> 47%;
   misses appear at delay 12 (2/6). False positives 0/4 in every cell.
2. **Noise 0.05 makes the single-frame protocol structurally blind**: the
   honestly re-calibrated threshold (3.6-4.3 m/s^2, = 1.5x the sub-limit
   noise floor) *exceeds the largest physically attainable true shortfall*
   (~2.7 m/s^2 = (6000 N - lowest-mu limit)/mass) -> miss rate 100% at all
   delays. Detection survives only via temporal averaging, which buys back
   threshold at the price of latency: the re-calibrated tau falls 1.20 ->
   ~1.20 -> ~0.50-0.60 -> ~0.26-0.37 for windows W = 1/5/12/25 frames, and
   the seeker selection chose **W = 25 (0.5 s of averaging) in every noise
   cell** — the noise->latency conversion observed directly in selection.
3. **Embedded identification degrades on the task itself** (best-seeker
   validation telemetry, reveal 9.5): identified fraction 1.00 (clean) ->
   0.25-0.67 (noise cells); mean identification step 26.7 -> 41.6-78.2;
   mu_hat error 0.0005 -> 0.02-0.19; episodes with rescue-depth overshoot
   8% -> 46-67%.
4. **Identification becomes a liability**: detection value, +0.583/+0.250 in
   the clean cells, turns *negative* in 7 of 14 degraded cells (to -0.417 at
   12 m / 500 ms / noise). Under delayed/noisy feedback the threshold-seeking
   act itself mistimes braking, and a blind fixed plan (0.917 at 12 m,
   500 ms delay) beats both the seeker (0.667) and the degraded oracle
   (0.542). The clean-regime hero faculty inverts sign.
5. **The coarse prior does not rescue**: prior_advantage is small and
   inconsistent (-0.083 .. +0.125). What re-emerges is the value of
   *precise* capability knowledge (the per-mu oracle), consistent with the
   conditional-VoI result that precision pays in tight windows; a +/-0.2 bin
   floor is both too conservative to exploit and equally detection-crippled.

## Honest-fairness measures (so the seeker cannot fake belief value)

- Per-cell tau re-calibration on sub-limit ramps (1.2x observed max
  shortfall, floor 0.08), separately for every averaging window; the
  calibrated variants compete in the per-cell selection grid (selection
  seeds), and only the selected seeker is validated.
- Smoothing windows W in {1, 5, 12, 25} offered in noise cells; W>1 enforces
  actuator-branch unanimity over the window (averaging across brake<->drive
  transitions produces fake shortfall ~ 1.0 — branch misclassification, not
  signal; excluded from both calibration and detection).
- The seeker grid keeps the clean run's winning rates/backoffs/dv offsets;
  prior seekers inherit the best seeker's selected detector variant, so the
  prior arm differs only by the granted bin.
- The clean cell of each tier uses the same wrapper construction path and
  reproduces the original regime numbers exactly.

## Interpretation: real sensor conditions (inferred, not measured)

noise_std 0.05 on the normalized ego channels corresponds to per-20 ms-frame
sigma of ~1.0 m/s on vx, ~0.75 m/s^2 on accelerations, ~0.125 rad/s on yaw
rate — an unfiltered consumer-grade IMU/odometry stack under vibration.
delay 5/12/25 steps = 100/240/500 ms ego-response latency — estimator +
bus latency (100 ms) up to heavy filtering or degraded state estimation
(500 ms; note 0.5 s is also what a 25-frame average costs, so "noisy sensor
+ honest filtering" lands in the same regime as "delayed sensor"). Under any
of these conditions, in reaction windows at or below ~12 m, a vehicle that
*already knows* its grip envelope keeps 0.17-0.88 success probability that a
purely reactive identify-while-acting controller forfeits. Where the prior
comes from is unconstrained by this measurement: memory, map data, weather
side channels — but it must be precise, not a +/-0.2 band.

## Caveats

- The PRIMARY VoI grants the belief agent dead-reckoning (legitimate here:
  deterministic dynamics, undegraded command channels; no process noise
  exists in this simulator). The matched SECONDARY readout is the
  no-dead-reckoning lower bound: it also clears the threshold in 6 cells
  (all at 9.5 m, up to +0.583), so the verdict does not hinge on the anchor
  choice — but at 12 m the matched VoI stays < 0.15 (max +0.083, two cells
  negative): at the looser window degradation mostly collapses *execution*
  for every sensing-bound controller, and only belief + model-based
  prediction (the clean anchor) recovers it.
- 12 mu points x 2 validation seeds per arm per cell (24 episodes/arm):
  single-cell VoI has ~0.1 granularity; the conclusion rests on the
  monotone structure across 14 cells, not on any single cell.
- All clean-run fidelity caveats apply (rear clamp without lockup, 6000 N
  brake actuator censoring mu > ~0.89). The wrapper degrades only what the
  controller reads; environment truth is untouched.
- Scripted controller family, zero training: this measures the value
  structure available to policy classes, not what a trained policy attains.

## Consequence for the thesis

The capability-boundary-tracking story closes with a two-regime law:

> **Belief is worthless exactly where the body can feel; it becomes
> decisive exactly where feeling is delayed or drowned.** Detection speed
> and rescue bandwidth carry all value under clean sensing (VoI(belief) = 0
> everywhere); 100 ms of ego-response delay at a 9.5 m window already
> re-opens a 0.21 gap, and realistic IMU noise re-opens 0.17-0.88 across
> both tight windows. The persistent capability belief earns its keep as a
> *sensing-degradation hedge* — and the measured failure mode it must hedge
> is precisely the clean paradigm's own embedded-identification act turning
> into a liability (detection value down to -0.417).

This is the affirmative closure of the one open door left by
`selfid-threshold-seeking-regime-2026-06.md`; the learnability gate for a
history-bearing policy (rate/regret terms) now has a measured target regime:
degraded-sensing cells of the tight-window family.
