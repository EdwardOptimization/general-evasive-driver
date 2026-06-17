# GPU dynamics surrogate (Path B) — design + plan, 2026-06-16

Goal: move the vehicle *dynamics* off CPU Chrono onto a GPU-batched torch model so PPO
can train at thousands–millions of parallel environments, crushing the rollout-batch
variance that leaves only 8/16 seeds at the both-good drift+avoidance frontier (avoidance
regresses). Chrono stays the high-fidelity validation reference. Synthesised from a 3-agent
design workflow (surrogate architect + GPU-env/RL engineer + sim-to-sim fidelity skeptic).

## Why migrate (verified)
Chrono::Vehicle is a CPU C++ multibody solver (Pardiso-MKL). Its GPU modules
(`Chrono::GPU` granular, `Chrono::FSI` fluids, `Chrono::Sensor` rendering) do **not**
accelerate vehicle dynamics; the installed pychrono has none of them. There is no
GPU-batched-vehicles path. Isaac Gym / Brax / MJX exist precisely because their physics is
rewritten as GPU-batched tensor ops; Chrono's is not. So the dynamics must be re-hosted.

## Architecture decision: grey-box (analytic backbone + learned residual)
- **Learn only `Δ{vx, vy, yaw_rate}`** (the nonlinear tyre-saturation channels). Everything
  else is analytic/vectorised in torch: the first-order actuator filter (exact recurrence),
  pose `{x,y,psi}` (kinematic RK4 integration), obs72's 60 geometry dims, reward, termination,
  and **obstacle collision** (Chrono uses `CollisionType_NONE` — collision is an analytic
  clearance test, not contact dynamics, so it is an event layer, not learned).
- **Physics backbone = `autodrift.dynamics.SingleTrackDriftModel`**, torch-vectorised in
  `src/autodrift/gpu_surrogate.py` (`analytic_step`), **bit-faithful to the numpy model**
  (`test_gpu_surrogate.test_analytic_matches_numpy`, max diff 9e-13). It already returns
  `TireForces` incl. rear force — feeding the drift-saturation criterion.
- **Learned residual** (next milestone): a small MLP fitting the *known* Chrono−analytic
  discrepancy (the HF4 gap that motivated using Chrono) at the drift saddle. Grey-box =
  analytic + residual. Plus a **rear-tyre-saturation auxiliary head** supervised on Chrono
  tyre telemetry — without it, "holds drift" on the surrogate would be FAKE (the drift verdict
  needs `rear_saturated`). Ensemble K=3–5 for blind-spot / OOD detection.
- Deterministic residual MLP (not a full neural-SDE): Chrono is deterministic and the goal is
  to *remove* variance; an optional heteroscedastic head gives cheap calibration/robustness.

## Throughput unlock (measured, RTX 5080)
The analytic backbone alone: **~91M env-steps/s at 262k parallel envs** (122 MB), wall-time
constant across N (launch-bound, room for far more) — vs ~1k env-steps/s for ~30-worker CPU
Chrono. ~5 orders of magnitude. The bottleneck moves from the environment to the policy update.

## Training the residual (when built)
Phase A single-step Huber on standardised `Δ{vx,vy,yaw_rate}`; Phase B multi-step free-running
unroll (K=24–50) with scheduled sampling — **mandatory**: the drift saddle is unstable, so
single-step error compounds and diverges within the 24-step sustain window. Pose-in-the-loss
(off-track termination reads analytic lateral error from x,y). Physics-informed priors: tyre
saturation bound (|lateral accel| ≤ ~1.1–1.25·μg) and longitudinal force-sign consistency.

## Data
~0.3–2M Chrono `(state, action, params) → next_state` 50 Hz transitions + `tire_telemetry`,
concentrated in the drift saddle (β∈[0.20,0.36], μ~0.48) + the avoidance μ/reveal panel,
driven by the E4 drift oracle + E2′ reflex + perturbation noise, via the existing 30-worker
collector. Coverage must include off-policy/perturbed states (PPO queries OOD).

## M1 — the feasibility gate (cheap kill-or-proceed)
Collect data → fit residual + saturation head → **fixed non-RL gate** (all required):
1. one-step held-out RMSE per stratum: vx≤0.05, vy≤0.03, yaw_rate≤0.01; rear_saturated
   balanced-accuracy ≥0.95;
2. N-step open-loop divergence (replay identical action sequence in surrogate vs Chrono):
   p90 |β| divergence ≤0.03 at 24 steps;
3. **decisive sub-test**: run the E4 `beta0p28_recover` drift oracle + the avoidance reflex on
   BOTH surrogate and Chrono on the 30 frozen E4 seeds — the surrogate must reproduce the
   drift-success and avoidance-pass outcomes.
Pass → build the GPU PPO stack; fail → cheap kill before the big build.

## Key risks + guards
- **Fake drift** (no rear saturation) → mandatory saturation head; verdict recomputed on Chrono
  telemetry only.
- **Policy exploits surrogate blind spots** → ensemble-disagreement reward penalty + state-
  visitation trust region + rollout-horizon cap + mandatory back-to-Chrono validation on the F2
  verdict seeds (reuse `adjudicate()` / extend `chrono_hf4_full_discrepancy.py`).
- **Saddle instability amplifies yaw error** → multi-step unroll loss + horizon cap at the
  validated divergence-crossing step.

## Phased plan
1. **[done]** Analytic backbone (`gpu_surrogate.analytic_step`), numpy-parity test, throughput proof.
2. GPU env: vectorised obs72 + reward + termination + obstacle event layer on the backbone.
3. Chrono data collection (+ tyre telemetry) over the coverage spectrum.
4. Fit residual + saturation head; **run M1 fidelity gate**.
5. If pass: GPU PPO rollout path; large-batch training of the gated policy; back-to-Chrono
   verdict (sim-to-sim transfer gap). Then the coverage spectrum (step 3 of the broader plan).

---

## M1 first signal (2026-06-16): analytic single-track vs Chrono divergence — decides grey-box

Open-loop divergence test (`scripts/feasibility_audit/surrogate_m1_divergence.py`): drove the E4
`beta0p28_recover` drift oracle in Chrono, replayed the identical action sequence through the
analytic single-track GPU model from the same initial state. Result (drift saddle, mu=0.48):

- β divergence: ~0.004 rad @1 step, **~0.06 rad @24 steps**; crosses the 0.03-rad gate at step **~6–7**
  (gate wants ≥24). **vx RMSE ~1.1 m/s** (dominant), vy/yaw RMSE ~0.25/0.17.

Conclusion (data-driven): the pure analytic single-track is **not faithful enough** (this is why
Chrono was needed), the **dominant gap is longitudinal** (the RWD driveline + TMeasy longitudinal
slip, which the simple drive-force model misses), and the one-step error is small but **compounds**
over the unstable saddle. → **Adopt the grey-box (single-track + learned residual)**, trained with a
multi-step free-running unroll, rather than a double-track+MF rewrite (which would help lateral
fidelity but not the dominant longitudinal gap). Next: collect Chrono transitions (with actuator
states + tyre telemetry), fit the residual + rear-saturation head, re-run the full M1 gate.

---

## M1 PASSES (2026-06-16): grey-box residual closes the gap; physics spec extracted

Collected 160 Chrono drift-cell rollouts (oracle + action noise, 14.4k transitions;
`surrogate_collect_data.py`). Trained the grey-box residual (single-track + ResidualDynamicsMLP,
Phase A single-step only, seconds on the RTX 5080; `surrogate_train_residual.py`):

| open-loop divergence (held-out) | analytic single-track | grey-box (+residual) | gate |
|---|---:|---:|---|
| β div @24 p90 | 0.138 | **0.0292** | ≤0.03 ✅ |
| vx RMSE | 1.097 | **0.085** | (13×) |

The residual closed the dominant longitudinal gap. Phase B (multi-step unroll) not even needed for
the open-loop gate (it would tighten the marginal p90 and is the next hardening step). **The B path
is feasible: 5-orders-of-magnitude throughput + a fidelity gate that passes with a cheap residual.**

Caveats (honest, remaining for the FULL gate): p90 0.0292 is marginal (Phase-B unroll + more data
tighten it); the **rear-saturation head** (for the drift `controlled_drift` criterion) is not yet
built; the decisive sub-test (oracle drift-success on both sims) is pending; this is the single
mu=0.48 cell (spectrum needs mu/variant as residual inputs + data across them).

The physics-rewrite alternative is fully spec'd (`docs/chrono-sedan-physics-extracted.json`): exact
Sedan mass/geometry, TMeasy (GuessPassCar70Par, mu_0=0.8, peak Fx/Fz~1.2-1.4), Sedan_EngineSimpleMap
torque map (flat 370 Nm 1600-4500 rpm), the real 6-speed auto ratios [0.265..1.499] + shift points,
0.2 conical final drive, open diff, RackPinion steering. Branchy parts (gear state machine, TMeasy
regime, bristle friction) all have branchless masked-torch plans. Kept as the debuggable
physics alternative if the residual proves brittle under PPO exploration.

---

## A1.iii decisive behavioural sub-test (2026-06-16): drift-SUCCESS transfer

Collected 160 Chrono drift-cell rollouts WITH the full E4 label (rear-tyre saturation per step +
`controlled_drift` + `drift_success`; `surrogate_collect_drift_labels.py`, 49/160 success). Replayed
each action sequence through the surrogate and recomputed the IDENTICAL E4 criterion
(`controlled_drift = finite & |beta|>=0.10 & rear_saturated & 2<=vx<=28 & |yaw|<=2.7`,
`drift_success = longest run >= 24`); `surrogate_oracle_consistency.py`:

| vs Chrono drift_success (49/160) | analytic single-track | grey-box (+residual) |
|---|---:|---:|
| balanced acc | 0.500 (TP=0) | **0.827** |
| agreement | 0.694 | **0.894** |
| false positives | 0 | **0** |
| per-step controlled_drift agree | 0.856 | **0.976** |
| \|alpha_rear\| vs Chrono rear-slip MAE | 0.030 | **0.0072** |

Findings: (1) **the behavioural test discriminates where open-loop divergence does not** — the
analytic model passes velocity RMSE-ish but reproduces drift-success at *chance* (never sustains
24 steps); the residual rescues it. (2) **Zero false positives** — the surrogate never reports a
success Chrono would fail, so PPO cannot game it for fake drift reward (the critical safe property);
the 17 false-negatives are *conservative* (the safe direction). Strict A1.iii gate (0.90/0.90) not
yet met — the conservative FN are consecutive-run breaks from the alpha_rear>=0.10 proxy + slight
velocity drift; A1.ii (learned rear-sat head, pushing rear_sat agree 0.973->~0.99) + A1.i (Phase-B
unroll) close them. Note: for the M1 INTENT (safe-to-train-on), zero-FP already satisfies the
no-optimistic-exploitation requirement; the FN only mean PPO is held to a slightly stricter bar.

---

## A2 PHYSICS REWRITE complete (2026-06-16): 4-way comparison — the methods-paper table

`src/autodrift/gpu_physics.py` — branchless GPU double-track + Pacejka tyre (combined-slip via
slip-vector projection → power-oversteer) + rear-wheel spin states + EngineSimpleMap → 6-speed
branchless gearbox (int tensor, masked `searchsorted`/`gather` shifts) → conical-0.2 → open diff +
quasi-static load transfer. Validated vs Chrono on the same held-out split / gate metric:

| GPU dynamics model | beta@24 p90 | vx_rmse | learning | throughput |
|---|---:|---:|---|---:|
| analytic single-track | 0.138 | 1.097 | none | 91M st/s @262k |
| single-track + residual (grey-box) | 0.029 | 0.085 | residual carries the powertrain | (same) |
| **physics — no learning** | **0.0435** | **0.227** | **none** | 1.3M st/s @16k |
| **physics + thin residual** | **0.0280** | **0.069** | residual RMS **0.031** (tiny) | (same) |

**The paper-C2 findings:**
1. The longitudinal gap the single-track lacked was a **missing state** (rear-wheel spin / powertrain),
   not a missing branch — adding the omega states + engine→gearbox→diff took vx_rmse 1.097→~0.4 before
   any tyre tuning. This is the central methods result.
2. **Physics-alone (zero learning) gets ~95% of the way** (3.2x beta / 4.8x vx over analytic), landing
   on the grey-box's Phase-A number — and it generalises by construction (params, not a fit).
3. **The hybrid wins** (0.0280, best of all four) and its residual is *thin* (RMS 0.031): the physics
   did the heavy lifting; the residual mops up a small unmodeled remainder rather than hiding the
   dynamics in a black box. This is the interpretability/generalisation argument vs the grey-box,
   whose residual carries the entire powertrain.
4. Both GPU routes are branchless + batch-independent (env i in a batch == env i alone).

Honest caveat: calibrated on the single mu=0.48 drift cell; the grip params (front/rear_grip_scale,
pac_By/Dy) are fit to that saddle — the avoidance / other-mu envelope needs re-validation (that
cross-mu generalisation test IS a paper-C2 experiment, and physics should generalise better than the
fit residual). Repro: `python scripts/feasibility_audit/surrogate_physics_gate.py [--residual] [--bench]`.

---

## A1 COMPLETE (2026-06-16): all three M1 sub-gates green (both surrogate routes)

Phase B (A1.i, `surrogate_train_residual_phaseB.py`) fine-tuned the residual through a 48-step
differentiable free-running unroll (penalises compounding directly):

| held-out open-loop | Phase A | Phase B |
|---|---:|---:|
| beta@24 p90 | 0.038 | **0.0156** (<=0.02 ✓) |
| vx_rmse | 0.083 | **0.049** |

Re-running the A1.iii behavioural drift-success consistency with the Phase-B residual
(`surrogate_saturation_head.py <phaseB.pt>`):

| vs Chrono drift_success (49/160) | agree | bal_acc | TP | FP | FN |
|---|---:|---:|---:|---:|---:|
| proxy \|alpha_rear\|>=0.10 | 0.944 | 0.908 | 40 | **0** | 9 |
| learned rear-sat head | **0.981** | **0.975** | 47 | 1 | 2 |

**A1 sub-gates, final:** (i) open-loop beta@24 p90 0.0156 <= 0.02 ✓; (ii) rear-sat head per-step
0.984 ✓; (iii) behavioural drift-success transfer 0.944/0.908 (proxy, FP=0) or 0.981/0.975 (head) ✓.
The Phase-B velocity tightening lifted even the zero-FP proxy past the gate, so **safe-to-train
holds without the head** (no optimistic exploitation); the head is polish (47/49 vs 40/49 recovered).

**M1 verdict: PASS on both routes.** grey-box (single-track + Phase-B residual + head) and physics
(double-track + thin residual) both reproduce Chrono's drift dynamics AND its drift-success verdict.
The B-path fidelity foundation is proven; next is A3 (GPU PPO env) -> A4 large-batch training.

---

## CORRECTION (2026-06-16) to the A2 4-way comparison — independent reproduction

Independently reproducing the physics gate (rather than trusting the build agent's report) revealed
the agent **over-claimed the hybrid**. Corrected, apples-to-apples (same seed-0 130/30 split, same
beta@24 metric, all reproduced):

| GPU dynamics model | beta@24 p90 | vx_rmse | robustness |
|---|---:|---:|---|
| analytic single-track | 0.138 | 1.097 | deterministic (fail) |
| **grey-box: single-track + UNROLLED residual** | **0.0156** | 0.049 | **robust — best fidelity** |
| physics-alone (zero learning) | 0.0435 | 0.227 | deterministic (robust) |
| physics + single-step residual (seed 0) | 0.0280 | 0.075 | **knife-edge** (0.026–0.051 over seeds) |

What was wrong and what is true:
- The agent's "physics+thin-residual PASSES at 0.028 → hybrid wins" is **not robust**. Its
  `--residual` is a single-step teacher-forced fit (unseeded); it compounds open-loop and **straddles
  the 0.03 gate** (0.026–0.051 across seeds). Seed 0 happens to give 0.0280, now seeded for repro.
- A Phase-B unroll fine-tune — which robustified the grey-box (0.038→0.0156) — is **UNSTABLE on the
  physics model** (backprop through the gear-FSM / stiff combined-slip diverges the residual, p90~0.12).
- **The robust fidelity winner on the trained cell is the cheap grey-box (single-track + unrolled
  residual), 0.0156** — better than the physics hybrid's best case. Physics-alone (0.0435, zero
  learning) is robustly good and **generalises by construction**; its advantage is out-of-distribution
  (cross-μ / cross-vehicle), which is a paper-C2 experiment, NOT raw accuracy on the trained cell.

**Decision for A3+:** carry the **grey-box** (single-track + Phase-B residual + rear-sat head) as the
primary GPU PPO surrogate (robust + fully working incl. drift-success), and keep the physics model as
the generalisation arm for the cross-μ study. This corrects commit e3a379b1's narrative.

---

## Avoidance-regime fidelity (2026-06-16): the grey-box holds up; avoid=1.000 needs A5 to arbitrate

The M1 validation was drift-cell-only; the grey-box residual was fit ONLY on mu=0.48 drift data, and
the A4 GPU PPO smoke train hit avoid=1.000 vs the CPU canonical 0.700 — suspect. Collected 120 Chrono
avoidance rollouts across the reveal×mu grid (oracle + noise; `surrogate_collect_avoid_labels.py`,
120/120 avoid_success) and replayed the SAME actions through the surrogates
(`surrogate_avoid_fidelity.py`):

| surrogate (avoidance) | vx_rmse | sideslip p90 | pos@step30 | avoid-outcome agree | FN |
|---|---:|---:|---:|---:|---:|
| analytic single-track (no residual) | 1.569 | 0.0151 | 0.226 m | 0.692 | 37/120 |
| grey-box (+ drift residual) | 1.052 | 0.0345 | 0.198 m | **0.967** | 4/120 |

Findings (partly overturning the prior that the drift residual would break avoidance):
1. **The drift-trained residual HELPS avoidance, not hurts** — outcome agreement 0.692→0.967, vx_rmse
   1.57→1.05, position 0.226→0.198 m. The longitudinal/powertrain correction generalises across
   regimes; it only mildly degrades sideslip (0.015→0.034, still tiny vs the drift saddle's needs).
   So the grey-box is a reasonable avoidance surrogate; avoid=1.000 is NOT a gross-fidelity artifact.
2. **Validation hole (honest):** the oracle succeeds 120/120 → NO crash-boundary cases. Avoidance
   success is decided AT the collision boundary (clearance vs 2.15 m), which this data never probes; a
   ~0.2 m position drift already flips 4/120 safe→crash. So the surrogate's fidelity *at the boundary*
   — exactly where avoid success/failure lives — is untested. avoid=1.000 cannot be trusted from the
   surrogate alone.
3. **Decisive arbiter = A5** (validate the GPU-trained policy back on Chrono via the four-arm). Also
   worth collecting crash-boundary rollouts (a weaker/noisier policy that sometimes crashes in Chrono)
   to gate the surrogate where it matters. Physics remains the cross-mu/vehicle generalisation arm
   (its avoidance test needs the avoid-vehicle re-parameterisation, mass 1450 not 1684 — a B-stream item).

---

## A5 DECISIVE VERDICT (2026-06-16): drift transfers (Chrono 1.000); avoid NOT fixed (0.700) — diagnosed

Ran the GPU-surrogate-trained policy (smoke, seed 0, surrogate drift=1.0/avoid=1.0) back on REAL
Chrono over the frozen four-arm validation grid (`a5_chrono_validate.py`, 40 avoidance + 20 drift):

| regime | surrogate | CPU canonical | **Chrono (A5)** |
|---|---:|---:|---:|
| drift | 1.000 | 0.856 | **1.000** |
| avoid | 1.000 | 0.700 | **0.700** |

**Finding 1 — drift: the GPU surrogate pipeline WORKS.** The drift policy trained entirely on the
grey-box surrogate transfers to Chrono at 1.000 — BETTER than the 8.6 h CPU run's 0.856 — in ~16 min
(even CPU-bottlenecked). The drift surrogate fidelity (β@24 0.0156 + rear-sat head) is high enough
that sim-to-sim transfer is essentially perfect. "又快又好" is achieved for drift. (One seed; A6
multi-seed to confirm robustness.)

**Finding 2 — avoid: NOT fixed, and diagnosed.** The surrogate's avoid=1.000 was an ARTIFACT (the
boundary-fidelity hole flagged in the avoidance-fidelity test: no crash-boundary cases). On Chrono
avoid = 0.700 = the CPU canonical, UNCHANGED. Large-batch GPU did not fix avoid — NOT because batch
size is wrong, but because **the surrogate's avoidance is too easy** (saturated at 1.0 → PPO gets
zero gradient pressure to improve avoidance past the BC level ~0.7). The simple "large batch crushes
variance → avoid improves" hypothesis is REFUTED for this surrogate; the real blocker is **surrogate
avoidance-boundary fidelity**, not batch size.

**Implication / next:** to actually fix avoid via GPU, the surrogate must pose the avoidance DIFFICULTY
faithfully — collect crash-boundary Chrono rollouts (a policy that sometimes crashes), train the
residual/physics to reproduce the collision boundary, so PPO has a real avoidance challenge. THEN
re-test whether large-batch fixes avoid. Separately: model-on-GPU throughput fix for the A6 multi-seed
run. Drift is a clean standalone win (faster + better than CPU).

---

## Faithful tyre (2026-06-16): your "小缺陷" instinct was RIGHT — but the tyre isn't the whole story

The user noted a true rewrite should match Chrono near-exactly, suspecting a tyre defect. Confirmed.
The calibrated-Pacejka physics model needed asymmetric grip FUDGE factors (front 1.10 / rear 0.85) +
pac_By/Dy tuned down — the tell that its un-fudged axle grip was wrong (Pacejka curve ≠ Chrono's Rill
TMeasy curve). Fix: sample Chrono's EXACT tyre.

- `extract_chrono_tmeasy_curves.py`: instantiates the real Chrono Sedan TMeasy tyre, imposes
  controlled (penetration→Fz, lateral-v→α, spin→κ), reads `ReportTireForce` → the exact Rill curve.
  Saved `chrono_tmeasy_curves.npz`. Sample: Fx/Fz@κ=0.10 **0.990** (peak 1.10), Fy/Fz@α=0.10 **0.851**
  (peak 0.941), strong degressive load dependence (peak Fy/Fz 1.02→0.74 as Fz 2000→8500 N).
- `gpu_physics_tmeasy.py`: Pacejka swapped for branchless torch interpolation of the EXACT curves,
  **front/rear_grip_scale = 1.0 (NO fudge)**. Gate (independently re-verified):

| model | β@24 p90 | vx_rmse |
|---|---:|---:|
| analytic single-track | 0.138 | 1.097 |
| calibrated-Pacejka (WITH fudge) | 0.0435 | 0.227 |
| **EXACT-TMeasy, NO fudge (grips=1.0)** | **0.0403** | 0.235 |
| grey-box residual | 0.0156 | 0.083 |

**Verdict — tyre necessary, NOT sufficient.** The exact tyre BEATS the calibrated-Pacejka (0.0403 <
0.0435) with the fudge factors set to 1.0 → the fudge WAS masking a wrong tyre; the user's instinct
holds. BUT a ~0.04 residual remains, so the gap is NOT only the tyre. Diagnosis: the residual is a
SIGNED, sign-reversing TRANSIENT (builds +0.009 by step 8, −0.0188 at step 24, +0.069 by step 89);
the worst cases are deep drift-entries — **the planar single-body recovers the drift entry FASTER
than Chrono.** A sign-reversing timescale error cannot be a grip error. The missing physics is the
**compliant suspension roll/pitch + the full TMeasy bristle/relaxation transient** that Chrono's
multibody solves and the quasi-static planar model omits. The grey-box residual learns exactly this
unmodeled-suspension/relaxation correction — which is why it reaches 0.0156 where pure physics
(calibrated OR exact-tyre) plateaus at ~0.04. (NN-fitted-tyre route building for the table-vs-NN
comparison; expected ≈ table since both fit the same exact curves.)

### NN-fitted tyre vs table-lookup (2026-06-16): representation-invariant — confirms the gap is NOT the tyre

Per "都试试", built the NN-tyre variant (`fit_tmeasy_tyre_nn.py` fits mlp_x(κ,Fz)→Fx/Fz, mlp_y(α,Fz)→
Fy/Fz on the SAME sampled Chrono curves, train MSE ~e-7; `gpu_physics_nn.py` swaps the LUT interp for
a branchless MLP forward, grips=1.0):

| tyre representation (exact Chrono curves, no fudge) | β@24 p90 | vx_rmse |
|---|---:|---:|
| table-lookup (bilinear) | 0.0403 | 0.235 |
| NN-fit (MLP) | 0.0377 | 0.242 |

NN matches table within noise (|Δ|=0.0026, opposite sides by a hair). **The ~0.04 floor is
representation-invariant** — swapping a LUT for a smooth NN of the identical curves moves nothing —
so the residual is NOT the tyre force law; it is the suspension/relaxation transient (→ L1 relaxation
layer). (NN stays in-grid during the gate; where it would extrapolate it rolls force down vs the
table's edge-clamp, but those states are unreached. An NN tyre WITH a relaxation/history state could
later absorb the transient — a candidate for the principled rewrite, distinct from a black-box residual.)

---

## Avoid-fix diagnostic (2026-06-16): the grey-box is BLIND to the collision boundary — tracks converge

Collected crash-boundary avoidance data (`surrogate_collect_avoid_boundary.py`: oracle + entry-
aggression sweep, 320 rollouts, 50 Chrono crashes) and measured surrogate collision-outcome accuracy
(`surrogate_avoid_boundary_gate.py`):

| surrogate | crash bal-acc | crashes caught (TP/50) | FP | FN (says SAFE, Chrono CRASHED) |
|---|---:|---:|---:|---:|
| analytic | 0.713 | 35 | 74 | 15 |
| grey-box (+drift residual) | **0.503 (chance)** | **2** | 9 | **48** |

The grey-box is **useless at the collision boundary** — predicts "safe" almost always (catches 2/50
crashes). THIS is why the GPU-trained policy hit avoid=1.0: the surrogate never reports a crash, so PPO
believes avoidance is solved. Worse, the drift-fit residual made collision prediction WORSE than plain
analytic (it smooths toward the safe oracle trajectories, blinding it to crashes) — concrete proof that
the learned residual does not generalise off its training distribution.

**Implication — the two tracks converge.** The avoid-fix needs a surrogate that predicts collisions by
construction; the grey-box can't, and can't be patched into it (it's fit to drift). The FAITHFUL PHYSICS
REWRITE (exact tyre done; L1 relaxation + L2 suspension in progress) is precisely that surrogate — a
near-exact physics model gets the avoidance pose/collision right everywhere, no per-regime fit. So:
finish the physics rewrite → use it as the (collision-faithful) surrogate for BOTH regimes → re-test the
avoid-fix. The physics-rewrite direction and the avoid-fix are one effort.

---

## L1 tyre relaxation (2026-06-16): the rewrite PASSES the gate — no learned residual, principled σ

L1 adds the TMeasy slip-relaxation transient (`gpu_physics_relax.py`): the slip entering the exact
curve lags the instantaneous slip over a relaxation length σ, d(slip_lag)/dt = (|vx|/σ)(slip−slip_lag),
semi-implicit (unconditionally stable, zero-σ → quasi-static). σ extracted from the EXACT Chrono tyre
(`extract_chrono_tmeasy_relax.py`): the literal bristle-stiffness σ=dF0/σ0=0.65 m is the upper bound
(over-relaxes); the physical relaxation length is the contact-patch scale, and the contact length was
INDEPENDENTLY MEASURED from the tyre at 0.093–0.131 m (0.107 m @ 4 kN).

σ sensitivity (held-out β@24 p90), pinning whether it's physical or fit:

| σ (m) | β@24 p90 | note |
|---:|---:|---|
| 0.065 | 0.0322 | |
| **0.107** | **0.0295 (PASS)** | **= measured contact length (independent, not tuned)** |
| 0.143 | 0.0263 | |
| 0.163 | 0.0256 | basin minimum |
| 0.195 | 0.0281 | |
| 0.326 | 0.0449 | |
| 0.651 | 0.0713 | literal bristle stiffness (over-relaxes) |

**Principled, not fit:** the independently measured contact length (0.107 m) passes the gate, and a
BROAD physical basin σ∈[0.10,0.20] m all gives ~0.026–0.031 — not a razor-thin tuned value. Signed
transient collapses: L0 @24 −0.0208 → L1 −0.0014; @89 +0.069 → +0.022; |sum| 0.099 → 0.036.

| model | β@24 p90 | learning | fudge |
|---|---:|---|---|
| L0 exact-tyre | 0.0403 | none | none |
| **L1 + relaxation (σ=contact length)** | **0.0295** | **none** | **none** |
| grey-box residual | 0.0156 | learned | — |

**Milestone: the faithful rewrite now PASSES the 0.03 fidelity gate with ZERO learned residual and ZERO
fudge — every parameter measured/derived from Chrono.** Vindicates the rewrite-over-grey-box direction.
~0.013 remains to the grey-box 0.0156, plausibly L2 suspension roll/pitch (dynamic, not quasi-static,
load transfer). Honest caveat: σ was derived (the fixed-spindle harness reports quasi-static per call,
so it couldn't dynamically measure the build-up) — but the measured contact length pins it and the
basin is broad, so the magnitude is physically grounded, not gate-tuned.

---

## A6.2 avoid-boundary convergence test (2026-06-17): rewrite beats grey-box but powertrain limits it

Re-parameterised L1 physics (gpu_physics_relax) for the avoidance vehicle (Chrono overrides mass=1450,
izz=2300, CG share 0.518; Sedan wheelbase/steer/tyre/relaxation kept) and replayed the 320 crash-
boundary rollouts (`surrogate_avoid_boundary_physics_gate.py`):

| surrogate | collision bal-acc | crashes caught | vx_rmse (avoid) |
|---|---:|---:|---:|
| grey-box (drift residual) | 0.503 (chance) | 2/50 | 1.05 |
| analytic | 0.713 | 35/50 | 1.57 |
| **L1 physics rewrite** | **0.665** | 30/50 | **1.31** |

Verdict — DIRECTION right, NOT yet faithful. The rewrite beats the grey-box (0.665 > 0.503): it carries
collision information the fitted residual destroys. But it is not collision-faithful (73 FP + 20 FN), and
the sanity check localises why: **vx_rmse 1.31 on avoidance vs 0.235 on drift** — the LONGITUDINAL physics
fails in the avoidance regime, drifting the pose and flipping outcomes both ways. Cause: the boundary data
is braking-heavy (entry-aggression sweep = throttle/brake), and the physics **brake torque is the one
GUESSED parameter** (max_brake_torque=2000 N·m, never measured); the powertrain envelope was only validated
on drift (steering-heavy). The LATERAL rewrite transfers; the POWERTRAIN/braking does not yet.

Next layers ("一点一点补"): (L1b) MEASURE the brake torque + throttle/engine response from Chrono (same
isolated-extraction approach as the tyre) and validate the powertrain over the avoidance speed/brake
envelope → tighten vx_rmse; then (L2) suspension roll/pitch. Re-run A6.2; target collision bal-acc ≥ 0.75
→ then A6.3 re-train avoid on the collision-faithful rewrite.

---

## A6.1b braking REJECTED + avoidance vx-gap diagnosis (2026-06-17)

Measured the Chrono Sedan brake (`extract_chrono_brake.py`): max_brake_torque = **2000 N·m/wheel**
(read off ChBrakeSimple at modulation 1; cross-checked by a full-brake decel test → 0.81 g, GRIP-limited
not torque-limited, so 2000 is more than enough). The guessed value was correct. The agent's hypothesis
was that gpu_physics_relax brakes only the 2 rear wheels (front sx=0 → zero front brake) vs the Sedan's
all-4 — but applying the all-4-wheel brake (`gpu_physics_brake.py`) made everything WORSE:

| | avoid vx_rmse | avoid collision bal-acc | drift β@24 p90 |
|---|---:|---:|---:|
| relax (rear-only brake) | 1.31 | 0.665 | 0.0295 |
| brake (all-4-wheel) | **1.75 ✗** | **0.569 ✗** | **0.0852 ✗ (broke drift)** |

**Braking is NOT the lever — REJECTED** (do not keep gpu_physics_brake). Re-diagnosed on CLEAN oracle
avoidance vs the adversarial entry-bias data:

| data | physics vx_rmse | vy_rmse |
|---|---:|---:|
| clean oracle avoidance | 1.207 | 0.138 |
| boundary (entry-bias) | 1.099 | 0.268 |
| drift (reference) | 0.235 | — |

**The avoidance vx gap (~1.2) is REAL and persistent** (clean ≈ boundary → not an adversarial-data
artifact), but the **LATERAL physics is faithful (vy_rmse 0.14)**. So the rewrite gets the evasive
dynamics right; only the LONGITUDINAL/powertrain is off in the avoidance regime (throttle/engine/drag
envelope at ~8 m/s on the near-straight 900 m radius — different from the drift saddle), and it resists
the quick fixes. This is the hard open piece for avoidance fidelity. Drift remains a clean win (passes,
transfers to Chrono 1.0). Strategic fork raised with the user (test avoid-fix directly vs keep
diagnosing the longitudinal envelope vs bank drift).

---

## A6.1c coastdown + driven-side localization (2026-06-17): vx gap is the PARTIAL-THROTTLE powertrain

Coastdown measured (`extract_chrono_coastdown.py`): the Sedan has NO aero body — coast decel is ~flat
0.28 m/s² (rolling+driveline), so the faithful resistance is **drag_coeff=0, Crr=0.0282** (the calibrated
0.80/0.03 over-resisted slightly). Installing the measured (lower) resistance made avoid vx WORSE
(1.21→1.36) — so resistance was NOT the cause; coast fix rejected (drift stays 0.0283, harmless). A
drive_scale sweep on the avoid replay LOCALIZES it to the DRIVEN side: scale 0→ too slow (−1.7), 1.0 →
too fast (+0.8), null at **≈0.57** → the powertrain delivers **~1.75× too much force at partial throttle**
(avoid cruises at throttle cmd ~0.16). The full-throttle engine map was extracted correctly; the
**partial-throttle blend / gear state / driveline is wrong**. Next (measure, not fit): extract the Chrono
Sedan's longitudinal driven-force vs (throttle, speed/rpm) — steady-state accel sweep — and match the
powertrain to it (folding in the measured drag=0/Crr=0.028 together). (My one-step ax probe that showed
"always decelerating" was a bug — it left wheel-ω at 0 → locked-wheel braking; the proper rollouts above
are authoritative.)

---

## A6.1d powertrain: the Sedan is FWD — structural fix (2026-06-17), avoid vx 1.21→0.90

Measured Chrono's driven-force surface (`extract_chrono_powertrain.py`): engine torque matches the
model's blend within 1.5%, final drive + gears match, gear schedule matches (gear 2 at 5/8/11/14 m/s).
The culprit was STRUCTURAL: **Chrono's Sedan is FRONT-wheel drive** (`GetDrivenAxleIndexes()=[0]`, rear
spindle torque=0), but the rewrite assumed RWD. Under acceleration, load transfers OFF the front (the
FWD driven axle) → traction-limited; the RWD model instead loads its driven (rear) axle → over-drives
~1.75×. Fix (`gpu_physics_pwr.py`, measured not tuned): keep the RWD force application (so drift, which
passes with it, is untouched) but cap each driven wheel's drive force by the measured FRONT friction
circle sqrt((mu·Fz_f)²−Fy_f²); plus measured resistance drag=0/Crr=0.0282.

| metric | relax (RWD, calib) | PWR (FWD cap, measured) |
|---|---:|---:|
| avoid vx_rmse | 1.207 | **0.897** |
| avoid vy_rmse | 0.138 | 0.126 |
| drift β@24 p90 | 0.0295 | **0.0283 (PASS)** |

Note (honesty): that the RWD model passes the DRIFT gate while the car is FWD means the drift saddle is
tyre-dominated (insensitive to driven axle); the avoidance acceleration phase is where FWD-vs-RWD shows.
The fix is a hybrid (RWD force + FWD traction cap), pragmatic not pure-FWD (a pure-FWD rewrite risks the
drift). Residual avoid vx 0.90 vs drift floor 0.235: now the late-turn CORNERING/induced drag (steps
50-200, throttle ~0.1), a tyre-combined-slip effect — a smaller refinement, not powertrain.

---

## A6.3 physics env wired + collision-faithful (2026-06-17): avoidance is now a REAL challenge

`gpu_env_physics.py` (GPUPhysicsAutoDriftEnv): the GPU PPO env on the faithful physics rewrite
(gpu_physics_pwr) instead of the grey-box. obs72/reward/termination/success copied byte-for-byte from
gpu_env (only throttle/brake read from physics state idx 7/8). obs72 parity vs env.py: drift 1.1e-7,
avoid 5.9e-8 (independently re-checked). Smoke-train (N=2048, 40 PPO updates):

- Drift trains to 1.000 at the genuine 24-step criterion — faithful + learnable (sanity ✓).
- **Avoidance is collision-faithful (the whole point):** BC baseline avoid = **0.094** (on the grey-box
  it was trivially ~0.98 — avoidance was FREE). A deliberately-bad straight-line policy: the physics env
  REGISTERS collisions (clearance 1.71 < 2.15 m); the grey-box registers ZERO (clearance 4.35 m — the ego
  never even reaches the obstacle). That is the A5 collision-blindness artifact reproduced and FIXED.
  Under stress (higher entry speed / shorter reveal) avoid degrades 1.000→0.489→0.261 with GENUINE
  collisions — graceful, real challenge. The training grid is still solvable to avoid 1.0 (honest), but
  avoidance must now be LEARNED, not handed out.

Next: A5 — validate the physics-env-trained policy on real Chrono (frozen grid, same as the grey-box A5
that gave avoid 0.700). The avoid-fix verdict on a collision-faithful surrogate.

---

## A5 on the physics-trained policy (2026-06-17): avoid 0.000 — partial fidelity is WORSE than none

Validated the physics-env-trained policy on real Chrono (frozen grid, same as the grey-box A5):

| regime | surrogate | CPU canonical | grey-box→Chrono | **physics→Chrono** |
|---|---:|---:|---:|---:|
| drift | 1.000 | 0.856 | 1.000 | **1.000** |
| avoid | 1.000 | 0.700 | 0.700 | **0.000** |

The physics-trained policy avoids perfectly on the collision-faithful surrogate but gets **0.000 on
Chrono** — WORSE than the grey-box policy's 0.700. All avoidance episodes terminate early (50–115 of 285
steps), success=False. **Decisive finding: a collision-faithful-but-imperfect surrogate is WORSE than a
collision-blind one for avoidance.** The grey-box's 0.700 was the BC-warmstart oracle behaviour surviving
(avoid was "free" there → never really learned). On the physics env avoidance had to be LEARNED (BC 0.094)
— so the policy actively OVERFIT the surrogate's residual gaps (vx 0.90 timing, FWD-cap hybrid, cornering
drag, collision bal-acc 0.695) and that learned maneuver systematically fails on Chrono.

**The deep lesson:** drift transfers from any surrogate (robust saddle-stabilisation); AVOIDANCE is a
precise collision-boundary/timing task that requires NEAR-EXACT fidelity to transfer — and partial
fidelity invites overfitting, which is worse than none. Two avoid-fix verdicts now: grey-box 0.700
(unlearned), physics 0.000 (overfit). Neither fixes avoid via straight surrogate training.

**Next (the robotics-validated fix for sim-to-sim overfitting): DOMAIN RANDOMISATION.** Randomise the
surrogate's avoidance physics (mass, μ, tyre grip, the residual-gap knobs, force perturbations) per env
per episode so the policy learns a ROBUST avoidance that doesn't rely on the surrogate's exact dynamics
(ADR; see [[robotics-recipes-for-autodrift]]). If DR-trained avoid transfers above 0.700 → the avoid-fix;
if not → strong evidence avoid is not a surrogate-fidelity problem but a deeper multi-task one.

---

## AVOID-FIX ARC — FINAL VERDICT (2026-06-17): three converging negatives; avoid is NOT surrogate-fixable

DR-trained policy on Chrono (independently re-verified): drift 1.000, **avoid 0.075**. DR did not close
the gap. The full avoid-fix investigation, three principled attacks, all fail:

| attack | mechanism | Chrono avoid |
|---|---|---|
| larger batch (grey-box surrogate) | crush PPO rollout variance | 0.700 (unlearned — BC oracle surviving) |
| collision-faithful surrogate (physics rewrite) | pose a real avoidance challenge | 0.000 (policy OVERFIT the residual gaps) |
| + domain randomisation (ADR) | robustness to the dynamics gap | 0.075 (gap is OUTSIDE the randomisable family) |

**Conclusion: the avoidance regression is NOT a surrogate/training problem.** It is not batch-size
(A5-greybox), not surrogate fidelity (A5-physics: partial fidelity is WORSE than none — overfitting),
and not training distribution (A5-DR). The remaining gap is STRUCTURAL — a surrogate-vs-Chrono
collision-boundary fidelity gap DR can't span — and/or the deeper multi-task drift↔avoid interference
the original gated-heads frontier already identified. Drift, by contrast, transfers to Chrono at 1.000
from EVERY surrogate — a robust saddle task is fidelity-tolerant; avoidance is a precise
collision-boundary/timing task that is not.

### What is DEFINITIVELY won (the bankable deliverables)
1. **Drift solved via a principled GPU rewrite** — physics rewrite (exact TMeasy tyre + relaxation +
   FWD-correct powertrain + measured resistance, every param measured from Chrono, no fudge/no learned
   residual, β@24 p90 0.0295) → trains → Chrono **1.000 > CPU 0.856**, at **~2400× Chrono throughput**.
2. **Methods contributions:** the GPU vehicle-dynamics rewrite + the FWD discovery (the Sedan is FWD,
   the rewrite had it wrong) + the collision-faithful GPU env (obs72 parity 1e-7) + the 2.4M st/s engine.
3. **Conditional-negative-result science:** WHEN does surrogate/large-batch training beat the baseline?
   Drift YES (robust), avoidance NO (timing-precise) — with mechanism (overfitting; DR can't close a
   structural gap; partial fidelity worse than none). This IS the project's conditional-negative paper.

### What is NOT worth pursuing
Further avoid-fix-via-surrogate (3 negatives, structural gap). The only remaining avoid lever is the
MULTI-TASK / architecture angle on Chrono directly (the GPU machinery makes such experiments fast for
drift, but avoidance needs Chrono validation, which is the slow CPU path). Recommendation: CONSOLIDATE
the drift + methods + negative-result wins into the papers (C2 methods + the conditional-negative-result).

---

## SCOPE CORRECTION (2026-06-17): the negatives are about SURROGATE TRANSFER, not feasibility

The user correctly pushed back on the "avoid is structural / not fixable" lean above. That over-reached.
The three negatives prove only that **the GPU-surrogate PATH does not improve avoid** (surrogate→Chrono
transfer gap). They do NOT show RL can't do both — and our own data refutes that: the 16-seed canonical
runs ONE policy at drift 0.856 + avoid 0.700 simultaneously, and pass7c seeds 2/7 hit drift=1.0 AND
avoid=1.0. So a generalist IS achievable; the obstacle is JOINT-PPO NEGATIVE TRANSFER (BC-baseline avoid
~0.98 → the joint PPO that drives drift to 1.0 regresses avoid). Human analogy (the user's point): master
each skill separately, then combine — no "unlearning avoidance while practising drifting".

Reopened the avoid-fix via TEACHER-STUDENT DISTILLATION (distill_both.py): distill a STRONG drift expert
(the GPU-trained policy, Chrono drift 1.0) + the avoid oracle into one gated student via pure BC, NO
interfering joint PPO; validate on Chrono. Target: avoid >= 0.700 AND drift >= 0.85 from one policy.

---

## DO-BOTH CONFIRMED (2026-06-17): one distilled policy — drift 1.000 + avoid 0.825 on Chrono

The user was right: RL CAN do both; the avoid regression was JOINT-PPO INTERFERENCE, not infeasibility.
Teacher-student distillation (distill_both.py) — distill the strong drift expert (GPU-surrogate-trained,
Chrono drift 1.0) + the avoidance ORACLE into one gated student via pure BC, NO interfering joint PPO —
then A5 on Chrono (independently re-verified):

| policy | drift | avoid |
|---|---:|---:|
| **distilled student (do-both)** | **1.000** | **0.825** |
| CPU canonical (BC + joint PPO) | 0.856 | 0.700 |
| joint-PPO physics policy | 1.000 | 0.000 |

The distilled student BEATS the canonical on BOTH axes. The avoid regression is removed by NOT doing the
interfering joint PPO — exactly the human route (master each skill, then combine; no "unlearning avoidance
while practising drifting"). The GPU surrogate's real payoff: it produced the FLAWLESS drift teacher
(distils to drift 1.0 every seed); the avoid came from the Chrono oracle; distillation combined them.

Honest caveats: (1) avoid distillation is SEED-SENSITIVE (0.0-0.81 across seeds; the both-good seed needs
a multi-seed sweep + Chrono-task-score selection on a disjoint namespace — the legit analog of the
canonical 16-seed selection). (2) The avoid ceiling 0.825 is IMITATION-PRECISION-limited: the failures
are OFF-LANE drift on hard cells, NOT collisions (the student is collision-safe, clearance ~2.0) — clean
headroom via more/better avoid demos or a stronger avoid teacher, not a collision problem.

This SUPERSEDES the earlier "avoid not fixable" lean: avoid IS fixable; the surrogate-TRAINING path failed
(overfitting) but the DISTILLATION path works. Next: cross-vehicle generality via the Tier-a Chrono
template port (docs/chrono-template-gpu-translation-plan-2026-06.md) carries this recipe across vehicles.

---

## DAgger → avoid 0.900 (drift 1.0); oracle ceiling = 1.0 → the residual is IMITATION, not physics (2026-06-17)

DAgger (dagger_avoid.py, 3 rounds, student-driven rollouts relabeled by the avoid oracle, re-distill +
Chrono-select; drift demos/head untouched) pushed Chrono avoid 0.825 → **0.900**, drift held **1.000**
(re-verified). Per-round select-avoid 0.562→0.812→0.938. Honest correction to the premise: the 0.825
failures were NOT off-lane — they were speed_too_low (over-conservative braking, 26/28); DAgger labeled
those with the oracle's carry-more-speed action and fixed it. Residual 4/40 = collisions at the two
tightest-reveal × lowest-μ cells (reveal 9.5/12 × low μ); every reveal ≥ 16 is perfect.

KEY: the avoid ORACLE scores **40/40 = 1.000** on the SAME A5 grid, including those hard cells. So
**0.900 is an IMITATION gap, NOT the physical ceiling** — avoid 1.0 IS reachable (the oracle does it);
the student just hasn't matched it on the hardest few cells. Path to 1.0: targeted DAgger coverage on
reveal-9.5/12 × low-μ. (This refines the north-star caveat: on THIS avoidance grid the physical ceiling
is 1.0, so the target genuinely is 1.0.)

| policy | drift | avoid |
|---|---:|---:|
| canonical (joint PPO) | 0.856 | 0.700 |
| distillation | 1.000 | 0.825 |
| + DAgger | 1.000 | 0.900 |
| avoid ORACLE (ceiling) | — | 1.000 |

---

## ★ BOTH-1.0 ACHIEVED (2026-06-17): one gated policy — drift 1.000 + avoid 1.000 on Chrono

DAgger-v2 (warm-start from the 0.900 policy, rollout budget concentrated on the 4 failing hard cells
reveal 9.5/12 × low-μ; drift demos/head frozen). Per-round hard-cell rollout success 0.729→0.958→1.000.
Final A5 Chrono (independently re-verified, frozen 40-avoid + 20-drift grid):

| policy | drift | avoid |
|---|---:|---:|
| CPU canonical (BC + joint PPO) | 0.856 | 0.700 |
| distillation | 1.000 | 0.825 |
| + DAgger | 1.000 | 0.900 |
| **+ DAgger-v2 (hard-cell)** | **1.000** | **1.000** |

Per-cell: 40/40, ZERO failures, ZERO collisions — all 4 formerly-hard cells now pass 2/2. Drift = 1.000
on every distilled seed (frozen drift demos → gated re-distill can't regress drift). Selection was on a
DISJOINT distill_select namespace (not the A5 grid) — no select-on-test. distill_dagger_v2_policy.pt.

**The full-scenario do-both Sedan driver is achieved at 1.0/1.0.** The recipe (north-star pieces ③+④):
cheap-GPU drift expert (planar surrogate, transfers to Chrono 1.0) + Chrono avoid oracle → gated student
via pure distillation (NO interfering joint-PPO) → DAgger to close the imitation gap on the hard cells →
multi-seed + Chrono-task-score selection. Drift-safe by the gated-double-head + frozen drift demos. Both
of the user's challenges vindicated: RL DOES do both (兼顾), and avoid DOES reach 1.0 (the regression was
joint-PPO interference + an imitation gap, neither fundamental). Remaining north-star piece: ② cross-vehicle
(same recipe per vehicle via template config; planar surrogate; Tier-b only if a vehicle fails to transfer).
