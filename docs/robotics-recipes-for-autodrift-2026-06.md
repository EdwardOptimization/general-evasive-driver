# Robotics sim-to-real recipes → AutoDrift (obs72) — research synthesis, 2026-06-15

Two source-grounded literature passes (robotics adaptation + RL drifting/racing), mapped onto
AutoDrift's obs72/priv6 `AsymmetricActorCritic`, BC-warm-start→PPO, ~30-worker CPU Chrono.
Primary-source URLs at the bottom. "VERIFIED" = read from the paper; "UNCERTAIN" = secondary/unconfirmed.

## TL;DR
1. **The drift-RL literature directly diagnoses our two observed problems** (unstable-equilibrium
   hold + per-seed PPO collapse) and gives cheap, code-level fixes — and it **theoretically validates
   our obs72 design** (drift saddle has low sensitivity to μ → μ-free control is *expected* to work).
2. **RMA (latent system-ID)** is the bridge from the project's self-ID/belief thesis to a working
   recipe: it turns "does identification have value?" into a *measured* VoI of the estimated latent ẑ,
   and predicts our two-regime belief law (clean → ẑ uninformative; degraded → ẑ informative).
3. **Don't copy their scale** (2048–10⁶ parallel envs; we have ~30 CPU). Copy the qualitative tricks,
   keep our pre-registered structured eval (they don't pre-register / don't do four-arm adjudication).

---

## Part 1 — What the drift-RL literature does that we should adopt

### Already doing right (externally validated — don't change)
- **Small MLP actor.** Zhou 2025 uses (64,32,16); Cai 2020 ~256×2. Network size is not our problem.
- **In-env action smoothing.** We have `steer_tau=0.06`, `drive_tau=0.08`, `max_steer_rate=3.5 rad/s`
  first-order lag + rate limit in front of Chrono — equivalent to Cai's `a_t=0.9·a_{t-1}+0.1·a_net`
  steering low-pass and Djeumou's rate-limited action. `steer_rate_normalized` is exposed in obs72.
- **Sustain curriculum.** We ramp `DRIFT_SUSTAIN_START 6 → 24`; Cai uses easy→hard curriculum. Same idea.
- **β + yaw_rate in obs, no privileged μ.** THEORETICALLY SOUND: Velenis 2010 / Goh-Gerdes 2020 show
  drift equilibria are **saddle points with low sensitivity to friction & speed** — μ-free stabilization
  is *expected* to work. This is independent external support for both obs72 and the "clean sensing →
  identification has ≈0 value" finding.

### Cheap, high-payoff gaps (ordered by expected payoff)
| # | Fix | Source | Why it targets our problem | Our status |
|---|---|---|---|---|
| 1 | **Initial-state randomization around β\*** — start a fraction of drift rollouts already near β\*=0.28 (and some perturbed off it) | Zhou 2025 (+29% ablation) | Densely samples the saddle's stable/unstable manifolds → direct antidote to "occasionally collapses then can't recover" | **NOT done** — init β = N(0, 0.04), i.e. near-straight |
| 2 | **Jacobian regularization** `λ_jac·‖∂a_mean/∂o‖²` ≈ 1e-5 on the policy | Djeumou 2024 (TRI) | Penalizes sharp policy basins → less oscillation, lower seed-to-seed variance, noise-robust. Near-free PPO-loss addition | **NOT done** |
| 3 | **Bigger effective batch** — longer rollouts/update + target-KL early-stop to spend scarce data carefully | Zhou (10⁵–10⁶), Djeumou (2048) consensus | Our ~30-env rollout = high-variance gradient on a saddle reward → the oscillate/collapse we see. Confirms our suspicion | partial (30 workers; CPU-bound) |
| 4 | **Reward that rewards *being* in drift without a sharp β-setpoint** — tire-energy term `∝|(V sinβ+b·r)·F_yr|+|(Rω_r−V cosβ)·F_xr|`; OR Cai's reward going **negative past ±90°** divergence | Djeumou 2024; Cai 2020 | A sharp `−(β−0.28)²` quadratic punishes the natural wander around a saddle; tire-energy / banded reward is easier to hold | we use progressive drift reward + sustain |
| 5 | **Distributional critic** (quantile-regression value head) | GT Sophy 2022 (QR-SAC) | Stabilizes value targets in a high-variance at-the-limit regime; portable to our GAE critic | **NOT done** (scalar bootstrapped GAE) |
| 6 | **Error-derivative obs features** (ė_β etc.) — lets a memoryless law act PD not P | Cai 2020 | Our teacher is static feedback on current β+yaw_rate (P-like). Note obs72 already has yaw_rate + steer_rate, so payoff is smaller than for Cai — worth an ablation, not a sure win | yaw_rate ✓, explicit dβ/dt ✗ |

---

## Part 2 — RMA latent system-ID grafted onto obs72 (the belief-story bridge)

**RMA recipe (Kumar 2021, VERIFIED):** privileged factors e_t → encoder µ → latent z_t∈ℝ⁸ →
base policy π(x_t, a_{t-1}, z_t); a separate **adaptation module φ** consumes the last **k=50 steps
(0.5 s)** of (state,action) through a small 1-D CNN and **regresses to z_t (MSE), not to e_t**.
Training: **Phase 1** RL (PPO) trains π+µ on ground-truth z; **Phase 2** freezes them, trains φ by
supervised MSE(ẑ,z) on on-policy states (no RL); **Phase 3 (A-RMA, Kumar 2022)** re-fine-tunes π with
PPO while consuming φ's *imperfect* ẑ — "critical for reliable real-world performance."

**Graft onto AutoDrift:**
- Encoder µ: **priv6 → z** (z small, 2–4 dim — priv6 is only 6 channels).
- Base actor **π(obs72, z)** replaces `actor(obs72)`. Critic keeps obs72+priv6 (asymmetry for value).
- Adaptation **φ: obs72-history (k≈25–50 steps) → ẑ**, 1-D CNN, MSE to z.
- Phase 1 = our current BC→PPO with z=µ(priv6) inserted in the actor's privileged path.
  Phase 2 = cheap supervised regression (relax "on-policy" to a replay buffer to save sim steps).
  Phase 3 = brief A-RMA fine-tune warm-started from Phase-1 weights.
- **Deployable actor = π(obs72, φ(obs72-history))** — uses *only* obs72, preserving deployability.

**Why this is the right bridge for the self-ID VoI thesis:**
- It converts "does identification have value?" into **measured quantities**: mutual information
  `I(ẑ; μ)` and action-sensitivity `∂π/∂ẑ`.
- **Predicted, falsifiable:** CLEAN sensing → ẑ collapses to near-constant, `∂π/∂ẑ≈0` (RMA *confirms*
  our belief law). DEGRADED sensing (≈100 ms latency / 0.05σ IMU) → φ (a history denoiser, exactly
  Lee 2020's 2 s TCN structure) recovers an informative ẑ, `∂π/∂ẑ>0`, and the actor reclaims part of
  the +0.2 success. This is the VoI(ẑ) measurement the memory's self-ID hypothesis has been chasing.
- Regress φ to the **latent z, not raw priv6** (RMA's deliberate choice): z is the task-relevant
  compression; regressing raw priv6 wastes capacity recovering channels the policy doesn't use.

---

## Part 3 — Honest caveats
- **Scale is the real gap.** RMA: 1.2 B steps, batch 80k, ~24 h/GPU. Zhou: 10⁵–10⁶ GPU envs, ~11 min.
  Djeumou: 2048 envs. GT Sophy: ~10 days, A100 + a dozen PS4s. We are ~30 CPU envs — 2–3 orders down.
  Their *qualitative lessons* transfer; their *convergence speed* does not. A-RMA Phase 3 is a *second*
  full PPO phase — budget accordingly.
- **Don't adopt full ADR.** OpenAI's automatic domain randomization needs huge per-boundary sample
  volume to track a moving curriculum; at 30 envs its buffers fill too slowly. Take only the *idea*
  (widen a randomization range when success clears a threshold at its boundary) as a hand-tuned schedule.
- **Eval philosophy stays ours.** These papers report aggregate robustness + worst-case; they do not
  pre-register or do per-cell four-arm adjudication. For the scientific claim (where/why RL>reflex), keep
  the structured pre-registered eval grid; borrow only the *training* philosophy (domain randomization).
- **Sim-to-real maturity:** Cai & GT Sophy = sim-only. Real transfer exists only in Zhou (1/10 RC,
  domain randomization) and Djeumou (full-size Supra, uncertainty-aware neural-SDE replacing DR). If
  AutoDrift ever targets hardware, those two are the templates.
- **Unverified numbers:** ADR exact hyperparams (Table 15, paywalled appendix); GT Sophy obs dim/reward
  weights/network (Nature Extended Data, paywalled); Lee 2020 teacher latent dim; Cai hidden widths
  (read from a figure). Mechanisms verified; do not cite the specific numbers without the PDF.

## Primary sources
- RMA — https://arxiv.org/abs/2107.04034 · A-RMA — https://arxiv.org/abs/2205.15299 ·
  Walk-These-Ways — https://arxiv.org/abs/2212.03238
- Lee 2020 (ANYmal teacher-student) — https://arxiv.org/abs/2010.11251 ·
  ADR (Rubik's Cube) — https://arxiv.org/abs/1910.07113
- Cai 2020 (High-Speed Autonomous Drifting RL) — https://arxiv.org/abs/2001.01377 ·
  code https://github.com/caipeide/drift_drl
- GT Sophy (Wurman 2022, Nature) — https://www.nature.com/articles/s41586-021-04357-7
- Goh/Gerdes drift equilibria — https://asmedigitalcollection.asme.org/dynamicsystems/article/142/2/021004/1066044 ·
  Velenis 2010 — https://www.tandfonline.com/doi/abs/10.1080/00423111003746140
- Learning to Drift w/ IWD (Zhou 2025) — https://arxiv.org/abs/2507.23339 ·
  Reference-Free Formula Drift (Djeumou/TRI 2024) — https://arxiv.org/abs/2410.20990
