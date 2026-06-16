# AutoDrift — Master Plan (2026-06)

A complete, goal-drivable plan for the remaining work. Each milestone has a **deliverable**,
a **gate** (verifiable success condition), rough **effort**, **deps**, and **risk**. The
**Suggested Goals** at the bottom are copy-pasteable terminal conditions for goal-mode.

> **Progress (2026-06-17): Workstream A done through A5; central hypothesis REFUTED + DIAGNOSED;
> pivoted to the faithful-rewrite path (see "Revised path" below).** A0✓ A1✓ A2✓ A3✓ A4✓ A5✓.
> - A1: β@24 p90 0.0156; drift-SUCCESS transfer 0.944/0.908 (FP=0) / 0.981/0.975 (head). A2 CORRECTED
>   (a1a408ee): grey-box (0.0156) is the robust fidelity winner; A2's "hybrid" was an over-claimed seed.
> - A3✓ (25325ec4): GPU env obs72 parity 1.1e-7, 0 reward/termination mismatches, ~2.3M st/s; fixed a
>   success() bug. A4✓ (33d02b2b): GPU PPO trains drift 0.293→1.0 (model-on-CPU throughput caveat).
> - **A5✓ (d004ee2f) — the verdict:** GPU-trained policy on REAL Chrono → drift **1.000** (>CPU 0.856,
>   the "又快又好" win for drift) but avoid **0.700 = CPU canonical, NOT fixed.** The plan's central
>   "large-batch crushes variance → avoid improves" hypothesis is **REFUTED**: the surrogate's avoidance
>   was too easy (saturated → no PPO signal). Diagnosed (95279234): the grey-box is **blind to the
>   collision boundary** (crash bal-acc 0.503, catches 2/50). So the avoid-fix needs a *collision-faithful*
>   surrogate — which the grey-box can't be (it's fit), but the **faithful physics rewrite is, by
>   construction.** The rewrite-vs-grey-box question is settled in favour of the rewrite ([[prefer-physics
>   -rewrite-over-greybox]]): L0 exact TMeasy tyre (0.0403, table≈NN, no fudge) + L1 relaxation (**0.0295,
>   PASSES the gate, zero learning, σ=measured contact length**) — see Revised path. C1 paper: arXiv-ready
>   pending author. Lesson banked: independently reproduce subagent numbers (caught 2 over-claims).
>   Commits 8cd1dc96…692f2ce2.

## Revised path within Workstream A (post-A5 pivot, 2026-06-17)
A5 replaced "A6 = batch fixes avoid" (refuted) with: **build a collision-faithful surrogate via the
incremental Chrono rewrite, then re-test the avoid-fix on it.** Layered, every param measured from Chrono:
- **A6.0 [DONE]** L0 planar + EXACT TMeasy tyre (sampled off Chrono, table 0.0403 ≈ NN 0.0377, grips=1.0).
- **A6.1 [DONE]** L1 tyre slip-relaxation (σ=measured contact length 0.107 m → β@24 p90 **0.0295 PASS**,
  broad physical basin → principled not fit; collapses the drift-entry transient). `692f2ce2`.
- **A6.2 [PARTIAL]** `0a59db66`. Validated the L1 rewrite on the avoidance crash-boundary (re-param for
  the avoid vehicle). Collision bal-acc **0.665** (beats grey-box 0.503 — direction right, carries the
  collision info the residual destroys) but NOT yet faithful: **vx_rmse 1.31 on avoidance** vs 0.235 on
  drift localises the failure to the LONGITUDINAL/powertrain physics in the braking-heavy avoidance regime
  (the brake torque is the one GUESSED param; the powertrain was only validated on drift).
- **A6.1b [DONE — REJECTED]** `a6e2ac3e`. Measured brake = 2000 N·m/wheel (correct; 0.81 g grip-limited);
  the all-4-wheel brake change made avoid AND drift WORSE → braking was NOT the lever. Re-diagnosed: the
  avoidance **vx gap (~1.2) is real + persistent** (clean ≈ boundary) but the **LATERAL is faithful**
  (vy_rmse 0.14). Step-0 error ~0 and GROWS under throttle → a longitudinal **resistance/force-balance**
  gap (drag/rolling calibrated on drift, too low for low-sideslip cruise). Strategic confirmation: the
  rewrite IS the right path — every gap localizes + measures away (vs the grey-box's blind fit).
- **A6.1c [NEXT]** MEASURE the Sedan coastdown (drag + rolling) from Chrono → apply (measured, not
  calibrated) → re-gate avoid vx_rmse (→ toward 0.235) + drift (stay ~0.0295). The localized vx-gap fix.
- **A6.2′** Re-run the avoid-boundary gate with the measured powertrain (+ L2 suspension if needed).
- **A6.3** When A6.2′ passes: re-train the GPU policy on the (collision-faithful) physics surrogate →
  re-run A5 on Chrono → the real avoid-fix verdict.
- **L2 / A6.4** suspension roll/pitch (close the last 0.013 drift gap, 0.0295→~0.0156); model-on-GPU
  throughput (A4 rollout CPU-bound 0.11M st/s) before the full multi-seed run.

## Where we are
- **F2 driver (canonical)**: gated dual-head obs72 policy, 16-seed. **drift 0.856** (seed-clustered
  CI [0.728,0.953]; beats reflex floor 0.0 + oracle 0.35); **avoid 0.700** (CI [-0.511,-0.089],
  significant regression); pooled 0.762. Committed (`e6f24f17`).
- **C5' paper v1**: drafted → 5-agent adversarial review → major revision (citations verified,
  stats fixed, bilingual abstract, 2 figures). `paper/c5prime/` (`8a622e2a`).
- **GPU surrogate (Path B)**: **M1 PASS** — analytic backbone (91M env-steps/s @262k envs, ~5
  orders over CPU Chrono) + learned residual closes the Chrono drift gap (β@24 p90 0.138→0.029,
  vx RMSE 1.10→0.085). Physics-rewrite alternative building (agent). (`8cd1dc96`).
- Skills installed (academic-research v3.12, nature-skills ×11, PaperBanana).

## The decision that gates everything: does large-batch GPU PPO fix avoid?
The avoidance regression is the central open problem. Hypothesis (from the per-seed frontier +
the robotics-batch-variance literature): the 30-env CPU rollout's gradient variance leaves only
8/16 seeds at the both-good frontier; **thousands–millions of GPU envs crush that variance →
more seeds reach both-good → avoid stops regressing**. The GPU surrogate (Workstream A) exists to
test this. It is a HYPOTHESIS, not a certainty — A6 is the experiment that confirms or refutes it.

---

## Workstream A — GPU surrogate → large-batch PPO → deep avoid fix
*The active big thrust. A makes B affordable and tests the avoid-fix hypothesis.*

- **A0 [DONE]** analytic backbone + residual M1 PASS. `8cd1dc96`.
- **A1 — harden the fidelity gate.** Add the multi-step free-running unroll (Phase B) to tighten
  the residual's marginal p90; add the **rear-tyre-saturation head** (the drift `controlled_drift`
  criterion needs `rear_saturated`); run the decisive sub-test (E4 drift oracle + avoidance reflex
  on surrogate vs Chrono → reproduces the drift-success / avoidance-pass outcomes).
  *Gate*: β@24 p90 ≤ 0.02 (comfortable) **and** rear-sat balanced-acc ≥ 0.95 **and** the oracle
  reproduces drift-success on both sims (within 1 seed). *Effort*: 0.5–1 day. *Risk*: med (the
  saturation head may need broader data). *Dep*: A0.
- **A2 — physics rewrite + comparison.** Finish `gpu_physics.py` (branchless TMeasy + powertrain +
  load transfer), validate vs Chrono, and build the **comparison table**: {single-track,
  single-track+residual, physics, physics+thin-residual} × {β@24 p90, vx RMSE, throughput,
  cross-μ generalization}. *Gate*: physics model beats single-track and the comparison table is
  committed. *Effort*: 1–3 days (agent in progress). *Risk*: med (physics-alone may need a thin
  residual). *Dep*: A0. *(Also the core of paper C2.)*
- **A3 — GPU PPO env.** Vectorise obs72 + reward + termination + the obstacle/collision event
  layer on top of the surrogate (a torch batched env mirroring AutoDriftEnv's reset/step). Feed
  the EXISTING gated AsymmetricActorCritic + PPO update + per-regime advantage norm.
  *Gate*: a batched env steps N≥4096 envs on GPU, emits obs72 byte-comparable to the CPU env on a
  fixed state set (RMSE < 1e-3 on the geometry dims), runs one PPO update finite. *Effort*: 2–3
  days. *Risk*: high (obs72 + reward port must match exactly). *Dep*: A1.
- **A4 — large-batch PPO training.** Train the gated policy on the GPU env at large batch
  (thousands of envs), BC-warmstart → PPO. *Gate*: trains to drift+avoid success on the surrogate
  comparable-or-better than the CPU run, in << the 8.6 h CPU wall-clock. *Effort*: 1–2 days.
  *Risk*: med (surrogate exploitation — use the ensemble-disagreement guard + horizon cap). *Dep*: A3.
- **A5 — back-to-Chrono validation.** Validate the surrogate-trained policy on Chrono via the
  frozen four-arm adjudication (reuse `adjudicate()` / extend `chrono_hf4_full_discrepancy.py`);
  measure the sim-to-sim transfer gap. *Gate*: the policy's Chrono four-arm drift/avoid is within a
  pre-declared transfer-gap band of its surrogate score; gates pass. *Effort*: 0.5–1 day. *Risk*:
  high (the gap is the whole point of the validation). *Dep*: A4.
- **A6 — THE avoid-fix experiment.** With large batch, run the (16- or 32-seed) confirmatory and
  ask: does avoid stop regressing / do >8/16 seeds reach both-good? *Gate*: a committed verdict —
  avoid CI no longer excludes 0 (fixed) OR an honest "still regresses, batch wasn't the cause"
  (refuted). Either is a real result. *Effort*: GPU-time (hours). *Risk*: the hypothesis may be
  wrong. *Dep*: A5.

## Workstream B — coverage spectrum → general active-safety driver
*Needs A (GPU) to be affordable. Design already in `docs/coverage-spectrum-design-2026-06.md`.*

- **B1 — feasibility pre-check.** Generalise `oracle_ceiling_precheck` over candidate drift cells
  (β×μ×sustain) → prune undriftable/trivial cells → frozen feasible-cell list. *Gate*: committed
  feasible-cell list + per-cell oracle ceiling. *Effort*: 1 day. *Dep*: A1 (surrogate) or Chrono.
- **B2 — pre-register the spectrum + machinery.** Freeze the cells + per-cell four-arm gates;
  generalise the surrogate (μ/variant as inputs) + the trainer to a cell SET (DR-style sampling).
  *Gate*: frozen prereg + the cell-set train/validate path runs. *Effort*: 2–4 days. *Dep*: B1, A3.
- **B3 — run the spectrum (GPU).** S1 drift spectrum → S2 vehicle variants → S3 sensing
  degradation, large-batch on GPU, validated on Chrono. *Gate*: per-cell four-arm results
  committed. *Effort*: GPU-time (days). *Dep*: B2, A5.
- **B4 — general-driver verdict.** Per-cell adjudication → "across N pre-registered cells, the
  gated obs72 driver beats reflex+oracle on drift with CIs excluding 0, while [holding/regressing]
  avoidance." *Gate*: committed verdict + the honest where-it-generalises/fails map. *Dep*: B3.

## Workstream C — papers
- **C1 — C5' science paper → arXiv.** Fill author/affiliation; add the two deferred items as
  EITHER new experiments (MPC/NMPC drift baseline arm; per-seed VALIDATION-set frontier) OR an
  honest "future work" framing; final review pass; compile; submit. *Gate*: arXiv-submitted (or a
  compiled PDF ready to submit) with the author's go. *Effort*: 1–2 days (+ optional experiments).
  *Risk*: low. *Dep*: none (can start now). *Note*: the avoid result strengthens if A6 lands first.
- **C2 — GPU-vehicle-sim methods paper.** *"GPU-batched high-fidelity vehicle dynamics for RL:
  learned residual vs physics rewrite."* Contribution: two GPU routes from one Chrono HF source,
  compared on fidelity (open-loop divergence + drift-success), throughput, cross-μ generalisation,
  and RL-exploitation robustness. *Gate*: draft → 5-agent review → arXiv-ready. *Effort*: 3–5 days.
  *Risk*: med (positioning vs GPUDrive/Waymax — our delta is at-the-limit + multibody-validated +
  the two-route comparison). *Dep*: A1, A2 (the comparison data).
- **C3 — backlog papers (Task #6).** Conditional-negative-result + autonomous-loop case study.
  Lower priority; revisit after C1/C2. *Dep*: none.

## Dependencies / sequencing
```
A0 ─┬─ A1 ─┬─ A3 ─ A4 ─ A5 ─ A6   (deep avoid fix)
    │       └─ B1 ─ B2 ─ B3 ─ B4   (general driver; needs A1/A3 + GPU)
    └─ A2 ───────────────┐
C1 (now, independent) ────┤
                          └─ C2 (methods paper; needs A1+A2)
```
A is the critical path (unlocks B + the avoid fix + feeds C2). C1 is independent and can run anytime.

## Honest risk register
- The **avoid-fix hypothesis (A6) may be refuted** — large batch may not be the cause; that's still
  a publishable finding (and redirects to architecture/multi-task levers).
- **Sim-to-sim gap (A5)** may be larger than the open-loop divergence suggests once PPO exploits the
  surrogate — guarded by ensemble-disagreement + horizon cap + mandatory Chrono validation.
- **Physics-rewrite (A2)** may not pass alone — the hybrid (physics + thin residual) is the fallback;
  the comparison is the deliverable either way.
- **obs72/reward port (A3)** is the highest-bug-risk piece — must byte-match the CPU env.

## Suggested goals (copy-pasteable terminal conditions for goal-mode)
- **Goal α (recommended next):** "Harden the GPU surrogate and finish the physics rewrite: full M1
  fidelity gate green (β@24 p90 ≤ 0.02 + rear-sat head + oracle-on-both-sims) AND the
  single-track/residual/physics comparison table committed." → A1 + A2.
- **Goal β (the payoff):** "GPU PPO trains the gated driver on the surrogate, validates back on
  Chrono via the four-arm adjudication, and delivers the avoid-fix verdict (does large batch make
  avoid stop regressing)." → A3 + A4 + A5 + A6.
- **Goal γ (general driver):** "Run the pre-registered coverage spectrum (drift β×μ×sustain +
  vehicle variants + sensing) on GPU, validated on Chrono, and deliver the per-cell general-driver
  verdict." → B1–B4.
- **Goal δ (papers):** "C5' science paper and the GPU-vehicle-sim methods paper both arXiv-ready
  (compiled, reviewed, author-filled)." → C1 + C2.
