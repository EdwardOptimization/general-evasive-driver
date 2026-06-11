# Heterogeneous-Belief Decomposition: Vehicle Knowledge vs Surface Knowledge (2026-06-11)

## Status

- measurement: `belief_decomposition` — user-proposed (production-AD
  background) revision input for
  `docs/research-plan-phase2-capability-boundary-tracking.md` (v2). Two
  neglected information sources in real driving: (a) the vehicle-class prior
  ("看到车型"), (b) sub-limit familiarization ("开一段时间" identifies vehicle
  parameters but NOT mu, because the sub-limit tire response sits in the tanh
  linear region where capacity cancels).
- data: `experiments/feasibility_audit/belief_decomposition.json`,
  `runs/feasibility_audit/belief_decomposition/episode_rows.csv` (11,592
  regime episodes + pure-dynamics M1 rollouts). 496 s CPU, single run,
  managed background process.
- script: `scripts/feasibility_audit/belief_decomposition.py` (reuses the
  controller family / task surface / degradation machinery of
  `ramp_policy_voi_regime.py` and `degraded_regime_final.py`; belief
  injection and vehicle randomization are new).
- claim boundary: scripted-controller measurement only; no training-level,
  driver-performance, or high-fidelity claim. RLS = recursive least squares
  (not training).

## Physics reduction (derived, then exploited; stated up front)

In `src/autodrift/dynamics.py` this controller family consumes vehicle
knowledge ONLY through two mass-normalized authority ratios:

- kappa_b = brake_scale / mass_scale, kappa_d = drive_scale / mass_scale.
- Capacity deceleration mu·0.98·g·lf/wb is **mass-free**; mu_hat =
  realized_force/(0.98·Fzr_believed) is **invariant to a consistent mass
  belief** (mass cancels). Mass alone is longitudinally unidentifiable AND
  unneeded. "Knowing the vehicle" = knowing kappa_b, kappa_d.
- Stiffness and actuator-tau scales are randomized in the env but not
  consumed by the scripted controllers (declared limitation; cg shift and
  inertia held nominal).

Belief enters in exactly two places: (i) the shortfall detector's
applied-force reading (wrong kappa_b ⇒ a multiplicative shortfall **bias**
1−kappa_true/kappa_believed that **no time-averaging removes**), and (ii)
the brake/throttle command mapping (force realized off by
kappa_true/kappa_believed).

## M1 — Sub-limit mu-leakage curve (measured, pure dynamics.py)

Fixed open-loop command sequence (drive pulse / brake pulse / steer sine,
6 s, forces = u × anchor-mu capacity), mu swept. Gaussian observer with the
M3214 noise-0.05 model (sigma = [1.0 m/s vx, 0.6 vy, 0.125 rad/s yaw,
0.75 m/s² ax/ay] per 20 ms frame), full-sequence posterior over mu:

| utilization u | posterior std / prior std | posterior mean (true 0.7) | seq. discriminability d(0.7 vs 0.9) |
|---|---|---|---|
| 0.20 | 1.000 | 0.700 | 0.001 |
| 0.40 | 0.977 | 0.711 | 0.005 |
| 0.60 | 0.826 | 0.781 | 0.023 |
| 0.80 | 0.675 | 0.850 | 0.095 |
| 0.95 | 0.558 | 0.889 | 0.491 |

- **u ≤ 0.4 leaks nothing** (posterior = prior to 2%; trajectory divergence
  between mu 0.3 and 1.1 under identical commands: max Δay 0.000–0.002 m/s²).
- Even u = 0.95 with smooth open-loop inputs is weak: d ≈ 0.49 over a full
  6 s sequence (≈40% pairwise error for adjacent mu), because at sub-limit
  both cars deliver the demanded force and re-equilibrate to the same
  curvature; only transients and tanh curvature differ.
- **The leak is one-sided**: the posterior mean is biased UP (0.85–0.89 at
  true 0.7) — sub-limit driving can rule out lower mu (would have
  saturated) but never upper mu. Ordinary driving yields at best a lower
  bound on grip, never the value. mu identification requires touching the
  saturation edge — exactly the seeker's shortfall events.

Same data, vehicle-parameter identifiability (RLS on noisy observables,
median |error| over 6 vehicles × 3 mu):

| condition | kappa_b err | kappa_d err | stiffness-scale err | drive-tau err |
|---|---|---|---|---|
| u=0.2, clean | 0.006 | 0.008 | 0.001 | 0.0014 |
| u=0.95, clean | 0.002 | 0.002 | 0.098 | 0.0014 |
| u=0.2, noise 0.05 | 0.099 | 0.095 | 0.88 | (clean readout only) |
| u=0.95, noise 0.05 | 0.018 | 0.027 | 0.74 | (clean readout only) |

- kappa_b/kappa_d are identifiable at u = 0.2 (gentlest) with <1% error
  under clean sensing — while the same data leaves the mu posterior at the
  prior. **The orthogonality the user predicted is measured.**
- Vehicle estimates are mu-invariant (max kappa_b_hat spread across mu 0.4
  vs 1.0: 0.0084).
- Under noise 0.05 the naive RLS hits an **attenuation-bias floor ~0.1**
  (noisy regressors obs7/8), improving with excitation, not with time.
- Stiffness fit degrades at high u (linearity breaks, honest) and is
  swamped by vy/yaw noise at this gentleness (errors-in-variables
  attenuation, ~0.8 — reported, not repaired). Drive-tau fit was run on the
  un-noised actuator channel only (declared gap).

## M2 — Four-tier prize decomposition (measured, core)

Vehicle-randomized B2K2_final at reveal 9.5 m (per-episode scales: mass
0.85–1.20, brake/drive 0.80–1.15, stiffness 0.65–1.35, actuator-tau
0.75–1.75, keyed by rollout seed), M3214 degradation cells, **matched
anchor** (every tier on the same degraded stream, no dead-reckoning
credit). 12 mu × 10 validation seeds = 120 episodes/arm/cell; selection on
2 disjoint seeds; per-cell, per-belief-mode detector tau re-calibration.
Tiers: T0 = best belief-free arm (nominal-vehicle seeker family vs fixed
plans, max); T1 = + true kappa; T2 = + true mu (vehicle nominal, optional
in-episode RLS in selection); T3 = both.

| cell (9.5 m) | T0 | T1 | T2 | T3 | prize T3−T0 | vehicle T1−T0 [CI95] | surface T2−T0 [CI95] | interaction |
|---|---|---|---|---|---|---|---|---|
| clean        | 0.483 | 0.675 | 0.908 | 0.908 | **+0.425** | +0.192 [0.12, 0.28] | +0.425 [0.34, 0.52] | −0.192 |
| 100 ms delay | 0.400 | 0.550 | 0.917 | 0.933 | **+0.533** | +0.150 [0.02, 0.28] | +0.517 [0.43, 0.61] | −0.133 |
| 240 ms delay | 0.392 | 0.400 | 0.800 | 0.800 | **+0.408** | +0.008 [−0.14, 0.16] | +0.408 [0.28, 0.53] | −0.008 |
| noise 0.05   | 0.358 | 0.358 | 0.475 | 0.492 | **+0.133** | +0.000 [0, 0] | +0.117 [0.01, 0.23] | +0.017 |
| 100 ms + noise | 0.375 | 0.375 | 0.458 | 0.492 | **+0.117** | +0.000 [0, 0] | +0.083 [−0.02, 0.19] | +0.033 |

(Wilson CIs per tier in the JSON; bootstrap CIs are episode-paired,
n=120/cell. T0/T1 fell back to the fixed plan wherever the seeker lost,
recorded per cell.)

Findings (measured):

1. **The prize is surface-dominated everywhere.** The surface component
   equals or nearly equals the full prize in all 5 cells; the vehicle
   component is significant only at clean/100 ms (0.19/0.15) and dies at
   240 ms and in noise cells (exactly 0: T1's best seeker, 0.11–0.13, loses
   to the belief-free fixed plan, so knowing the vehicle changes nothing).
2. **Vehicle and surface knowledge are substitutes, not complements**
   (interaction ≈ −vehicle component; T3−T2 ≤ 0.033 everywhere). Vehicle
   knowledge pays only *instrumentally* — it repairs the mu-detector — and
   becomes worthless once mu itself is known.
3. **Mechanism, directly measured in calibration**: sub-limit shortfall
   noise floor with nominal vehicle belief = 0.243 vs 0.018 with true
   belief (clean cells) — vehicle uncertainty alone forces tau from 0.08 up
   to 0.29, blinding the seeker to low-mu onsets even with perfect sensing.
   Under noise 0.05, 25-frame averaging shrinks the *sensor* part
   (truth-belief floor 0.36–0.38) but **not the vehicle-bias part**
   (nominal-belief floor 0.52–0.53): bias survives averaging, as predicted.
4. With vehicle randomization ON, the noise-cell matched prize compresses
   to ~0.12–0.13 (CI lower edges 0.017 / −0.008): vehicle heterogeneity
   degrades the mu-knowing oracle's execution too (stiffness/tau/brake
   scales), shrinking what matched belief can buy there.

## M3 — Familiarization-period value curve (measured)

Sub-limit ordinary-driving prefix (speed hold + gentle brake/drive pulses +
weave; measured peak rear utilization < 0.5 truth-frame) on the same
vehicle + degradation cell, no hazard; vehicle RLS accumulates on the
degraded stream; kappa estimate frozen, fed to the cell's T1-configured
seeker; 120 validation episodes per point.

| cell | prefix | success | T0 → T1 refs | recapture of (T1−T0) | kappa_b err (median) |
|---|---|---|---|---|---|
| clean        | 5 s  | 0.683 | 0.483 → 0.675 | **104%** | 0.0025 |
| clean        | 15 s | 0.683 | — | 104% | 0.0027 |
| 100 ms delay | 5 s  | 0.567 | 0.400 → 0.550 | **111%** | 0.0025 |
| 240 ms delay | 5 s  | 0.400 | 0.392 → 0.400 | 100% (gap ~0) | 0.0025 |
| noise 0.05   | 5 s  | 0.133 | 0.358 → 0.358 | n/a (gap 0; seeker class < fixed) | 0.114 |
| noise 0.05   | 15 s | 0.083 | — | n/a | 0.112 |
| 100ms+noise  | 5/15 s | 0.117/0.092 | 0.375 → 0.375 | n/a | 0.109/0.112 |

- **Where a vehicle gap exists (clean/100 ms), 5 s of zero-risk sub-limit
  driving recaptures all of it** (kappa to 0.25% error); 15 s adds nothing
  (converged). The vehicle share of the prize is *free*.
- The vehicle RLS is **delay-robust by construction** (all ego channels are
  delayed identically, so the regression frames stay time-consistent —
  identification doesn't race a deadline the way slip detection does); it
  is **noise-fragile in bias, not variance**: the kappa error plateaus at
  ~0.11 from 5 s → 15 s (attenuation from noisy actuator-state regressors).
  Inferred fix, untested: instrument the regression with the UNDEGRADED
  previous-command channels (obs 9–11) — an errors-in-variables IV repair.
- In noise cells the prefix arm (forced seeker) sits below the fixed-plan
  floor — the binding constraint there is mu-detection under noise, which
  no amount of vehicle familiarization touches.

## Answers to the three questions

- **(a) 大头是车还是路?** Surface (mu). The surface component carries the
  entire prize in every cell; the vehicle component is a minority share
  (≤0.19) confined to clean/100 ms cells, and its value is instrumental
  (it repairs mu-detection), vanishing once mu is known (substitutes,
  negative interaction).
- **(b) 熟悉期能白捡多少?** All of the vehicle share, in ≤5 s, at zero risk
  and utilization <0.5 — in the cells where that share exists. It buys
  nothing in noise cells (no vehicle gap there) and cannot touch the
  surface share (M1: sub-limit driving leaves the mu posterior at the
  prior, with at best a one-sided lower bound).
- **(c) WP1 修订建议** (inferred from measured structure):
  1. **Two-timescale estimator, asymmetric by design**: a slow, delay-robust
     vehicle-RLS channel (converges ≤5 s sub-limit; needs an IV/EIV repair
     against sensor-noise attenuation bias) feeding a fast mu channel that
     alone needs the history-bearing belief machinery. The WP1 label should
     stay mu — vehicle parameters are not worth learning with the estimator;
     they are worth *calibrating* with RLS.
  2. **Familiarization prefix as a standard task component**: if WP0/WP1
     adopt vehicle randomization (recommended for realism), the belief-free
     floor MUST include a familiarization prefix + RLS, otherwise the
     measured prize over-counts what the learned estimator has to deliver
     by exactly the free vehicle share (+0.15–0.19 in clean/100 ms cells).
  3. The WP1 eligible-cell list (matched prize ≥ 0.15) is insensitive to
     this revision in delay cells; under vehicle randomization the
     noise-cell matched prizes compress to ~0.12 — re-freeze the eligible
     list after deciding whether family #2 randomizes the vehicle.

## Caveats

- Numbers are NOT comparable 1:1 with `selfid-degraded-regime-final-2026-06.md`:
  this family adds vehicle randomization (oracle ceilings drop, floors
  shift), uses a fresh seed stream (20260622), the matched anchor only, and
  a trimmed seeker grid.
- Tier values take a validated max over {tier seeker, fixed plans}
  (precedented optimism, same as the prior measurements); 120
  episodes/cell ⇒ ~0.09 Wilson half-width; single-cell decompositions have
  ~0.1 granularity — conclusions rest on the structure across 5 cells.
- The scripted controllers do not consume stiffness/actuator-tau; a richer
  (lateral-limit) controller class could earn more from vehicle knowledge
  than measured here. cg/inertia not randomized.
- M3 prefix arms reuse the cell's T1-selected seeker config and
  truth-calibrated tau (no separate selection for the prefix arm); the
  drive-tau identifiability readout is clean-channel only.
- All clean-run fidelity caveats apply (rear clamp without lockup, 6000 N
  brake actuator censoring high mu; the wrapper degrades only what the
  controller reads).

## Consequence for the thesis

The degraded-regime belief prize is **mu-shaped, not vehicle-shaped**: the
persistent capability belief that earns its keep as a sensing-degradation
hedge is specifically the *surface* belief. Vehicle self-knowledge is real
but cheap — a few seconds of ordinary driving buys all of it — and its only
route to value is through making the mu-detector trustworthy. This sharpens
the two-regime law: what feeling-degradation destroys, and what belief must
replace, is knowledge of the *boundary* (mu), which sub-limit experience
provably cannot supply (one-sided bound only).
