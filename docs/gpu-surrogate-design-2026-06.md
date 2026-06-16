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
