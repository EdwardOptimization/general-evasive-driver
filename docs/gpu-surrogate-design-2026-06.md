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
