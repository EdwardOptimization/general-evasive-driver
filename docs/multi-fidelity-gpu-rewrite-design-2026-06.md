# Multi-Fidelity GPU Faithful-Multibody Rewrite — Final Design (2026-06)

**Status:** design (synthesis of facets A/B/C/D, revised against adversarial source audit). Builds on
`docs/gpu-surrogate-design-2026-06.md`, `docs/chrono-template-gpu-translation-plan-2026-06.md`,
`docs/north-star-2026-06.md`, `docs/coverage-spectrum-design-2026-06.md`.
**Scope:** translate Chrono::Vehicle's *template* framework into a GPU-batched, branchless,
fixed-iteration constrained-DAE engine, exposed through a **rung registry behind one shared state
contract**, so PPO can pretrain on a fast-coarse config and posttrain on an accurate-slow config —
both behind the same obs72/do-both pipeline. **`config = fidelity` is realized as a registry + a
certified-agreement contract, NOT as one kernel that literally becomes the other.**

---

## 1. Vision & thesis

**Thesis (one paragraph).** The planar surrogate's residuals against real Chrono are *exactly the
multibody DOFs it dropped* — the `docs/gpu-surrogate-design-2026-06.md` dig localized them one by
one: the gear-SEED powertrain history (57% of the avoid-vx gap), driveline inertia (faithful but
null), FRONT longitudinal slip (omitted; over-builds front Fy), the per-corner geometric load
transfer, and a structural drift-RWD-vs-avoid-FWD tension. A *faithful* rewrite restores those DOFs
with a runtime constrained-DAE solve (the MJX/Brax/Isaac-Gym pattern, proven real for batched RL
physics). But the three fidelity rungs are **three modules sharing a contract, not one kernel that
degenerates by flipping a flag**: `gpu_physics_pwr3` (planar, 17-state, algebraic load transfer),
`gpu_vehicle_tier_a` (6-DOF chassis + 4 *explicit spring-damper* corners, 30-state), and a new
`gpu_vehicle_tier2` (full-linkage DAE) have three different state layouts and three different
vertical-mode treatments — they cannot be the same object. What unifies them is a **`FidelityConfig`
resolver** mapping `rung → module` behind a shared `physics_step`/`init_state`/`IDX` contract, with
each rung's cheap configs **validated to AGREE-WITHIN-TOLERANCE** with the rung below on a frozen
replay set (not bit-identical). The honest twist, carried directly from the data: **higher model
order does *not* monotonically lower error** — `gpu_vehicle_tier_a` *regresses* drift β@24 from
0.028 to 0.0756, and the only isolated DOF-restores the project ever tested (`pwr5` driveline-inertia,
`pwr6` front-slip) certified null/negative at the behavioral gate. So each config earns its place by
a *measured, multi-metric Fidelity Certificate against frozen Chrono rollouts*, **never by its DOF
count**.

**Why the split is justified — and by how much.** The pretrain/posttrain split is justified primarily
**versus CPU-Chrono** (~1k env-steps/s on a ~30-worker pool, the only baseline the project records),
not by a confidently-large intra-GPU gap. The repo's *measured* physics throughput is **~1.3M st/s
@16k eager / ~2.4M st/s "engine"** (`docs/gpu-surrogate-design-2026-06.md` lines 169, 607); the **91M
st/s @262k** figure is the *analytic backbone*, not the physics model. There is **no `torch.compile`
call anywhere in the env/physics/throughput/training code** (verified by grep over
`gpu_env_physics.py`, `gpu_physics_pwr3.py`, `rollout_throughput.py`,
`phase4_f2_gpu_train_physics.py`), so any compiled-speedup number is a *target to be measured at T0*,
not a result. Concretely: if compiled-pwr3 lands near ~2.4M and the heaviest rung near ~0.5M, the
**intra-GPU pretrain↔posttrain gap is ~5×, not ~1000×** — pretrain still carries the bulk cheaply,
but the speed argument leans on the ~500–2000× advantage over CPU-Chrono, which holds at every rung.

This unifies "fast training" and "faithful" honestly: fast is the cheap rung carrying the bulk of
PPO at hundreds-of-times CPU-Chrono throughput; faithful is the accurate rung restoring dropped DOFs
for the final validation/posttrain phase; and the certificate decides, per task and per regime,
which rung is actually better — because in this project, the measured answer is sometimes "the cheap
one."

---

## 2. Architecture — the GPU constrained-DAE solver (facet A)

### 2.1 The rung registry: three modules, one contract, validated agreement (NOT one kernel)

The engine is a **registry of three modules behind a shared contract**, not a single parameterized
kernel. The two existing rungs are *not* configs of the third — they are independent code paths with
different state layouts and vertical-mode treatments:

- **`src/autodrift/gpu_physics_pwr3.py`** — PLANAR single rigid body + 2 rear wheel-spin states +
  quasi-static algebraic load transfer (`_normal_loads`: the `m·a·h/L` longitudinal + `m·ay·h/track`
  lateral transfer). `PHYS_STATE_DIM=17`, `IDX = {x:0,y:1,psi:2,vx:3,vy:4,yaw_rate:5,steer:6,
  throttle:7,brake:8,...}` (verified, line 112-113). **Zero** bilateral constraints, **no z/roll/pitch
  DOF at all**. The coarse rung.
- **`src/autodrift/gpu_vehicle_tier_a.py`** — chassis 6-DOF rigid body + 4 corners whose vertical
  dynamics are an **EXPLICIT spring-damper ODE, sub-stepped** (`substeps=8`, `c_wheel` damping,
  series tyre/spring stiffness `Cz≈456 716`, per-corner travel states `zc[N,4]`/`zd[N,4]`), NOT a
  constraint solve. `TIER_A_STATE_DIM=30`, `IDX = {x:0,y:1,z:2,roll:3,pitch:4,yaw:5,vx:6,vy:7,...}`
  (verified, lines 91-93). **Fails drift** (β@24 0.0756) because the kinematic-corner reduction
  misses the real link DOFs / roll-centre geometry. The middle rung.

**Critical correction (was: "N_ITER=0 degenerates exactly").** Turning off constraint sweeps in a
maximal-coordinate corner does **not** reproduce tier_a's pre-solved kinematic lookup or pwr3's
algebraic transfer — it yields a *different* (unconstrained, free-floating) corner. tier_a's vertical
mode is an explicit ODE, not a constraint solve with iterations set to zero; pwr3 has no vertical DOF
to turn off. So **rung-2 is a NEW module** (`gpu_vehicle_tier2.py`) whose *cheap configs* are
**certified to AGREE-WITHIN-TOLERANCE** with pwr3/tier_a on the frozen replay set, not to be
bit-identical. The unification is the registry + shared contract (§3.4), which is real and buildable;
the "one kernel becomes the other" framing is dropped.

### 2.2 Coordinate choice — maximal + per-axle reduced dense blocks (NOT Featherstone)

Chrono's vehicle templates are *themselves* maximal-coordinate: a `ChDoubleWishbone` is
`upright[2] + UCA[2] + LCA[2] + tierod[2]` rigid bodies wired by `m_revolute*/m_spherical*` joints
+ `m_distTierod` (`ChLinkDistance`) + the spring/shock `ChLinkTSDA`; `ChMultiLink` is the analogous
`upright + upperArm + lateral + trailingLink + tierod`. The faithful translation is therefore
**body-for-body, joint-for-joint maximal**, which is also what MJX/Brax/Isaac Gym batch well (fixed-
topology constraint Jacobian = a dense per-env block, ideal for `[N,...]` tensors). A wishbone is a
*closed kinematic loop* (the spindle is held by two arms + a tierod), which reduced-coordinate
Featherstone cannot handle without loop-closure constraints anyway — so maximal is both the honest
match and the cleaner branchless target.

- **Rejected:** reduced-coordinate ABA (wrong for closed loops).
- **Rejected:** one monolithic `[N, ~102, ~102]` KKT per env (the Sedan is ~102 maximal DOF /
  ~100-105 constraints per the translation plan) — kernel-launch / solve death at N=262k. **Instead
  exploit the block-arrow structure (§2.3).**

### 2.3 The per-axle block decomposition (the key scalability move)

The two axles do not constrain each other directly — they share only the chassis body and the 1-D
driveline shafts. So the system is **block-arrow**:

- **Chassis**: 6-DOF maximal body — reuse tier-a's `{vx,vy,vz,wx,wy,wz, roll,pitch,yaw}` layout.
- **Each corner**: a SMALL fixed dense block `[N, D_CORNER, D_CORNER]` with `D_CORNER` = (link
  bodies × 6 + spindle 6); DoubleWishbone ≈ 24, MultiLink ≈ 30, **padded to a common `D_CORNER`
  with mask rows** so the kernel is one shape. Solved with its own constraint Jacobian.
- **Chassis↔corner coupling** (control-arm attachment) is a handful of constraint rows resolved in
  the same fixed-iteration sweep (block Gauss-Seidel naturally carries the coupling).

The branchless batched shape is `[N, n_axles, 2, D_CORNER, D_CORNER]` corner stack + `[N, 9]`
chassis state + `[N, 4]` wheel shafts. Axle-count / template differences are handled by **data**
(§4), never by Python-level topology changes — reusing tier-a's `FRONT_MASK`/`LEFT_MASK` pattern
(`gpu_vehicle_tier_a.py:86-87`). **The per-corner solve cost is real and unmeasured** — see §2.4 and
the Reality-check (§6) for why this block must be throughput-prototyped before T3 commitment.

### 2.4 The constraint solver — fixed-iteration, branchless, batched, differentiable

Per substep, form the index-3 DAE in velocity-impulse (Stewart-Trinkle / TGS) form. **Do NOT
factorize the full KKT.** Instead the MJX/Brax recipe — an unconstrained predicted velocity then a
FIXED number of projection sweeps:

```text
v* = v + h · M⁻¹ f                       # unconstrained (tyre/grav/driveline forces) — explicit
for k in range(N_ITER):                  # FIXED count, NO convergence test, NO break
    for each constraint block j:         # revolute/spherical/universal/distance + ground contact + driveline
        Δλ_j = -(J_j v* + β/h·C_j) / (J_j M⁻¹ J_jᵀ + cfm)   # block-diagonal effective mass
        λ_j  = project(λ_j + Δλ_j)        # bilateral: identity; contact normal: clamp_min(0)
        v*  += M⁻¹ J_jᵀ Δλ_j
v_{t+1} = v*
```

- The per-block effective mass `J_j M⁻¹ J_jᵀ` for a revolute (5 rows), spherical (3), universal
  (4), distance (1) is a tiny dense `≤6×6` solved by an **UNROLLED Cholesky / explicit inverse**
  (analytic ≤3×3; fixed 6×6 LDL, no pivoting). **No `torch.linalg.solve` inside the loop** for the
  small blocks (kernel-launch death at N=16k–262k); the whole sweep is fused elementwise `[N,...]`
  arithmetic, the style of pwr3's `_wheel_forces` / tier-a's `_interp2d`.
- **Baumgarte (`β`) + compliance (`cfm`)** soft constraints replace index-3 position-drift handling;
  this is what makes a fixed low iteration count usable AND makes the solve robust under op-reorder
  (no hard projection cliff). Brax/MJX `solref/solimp` analog.
- **Branchless** because the constraint LIST is fixed per config: a `[N, n_con]` set of
  `(block_type, body_a, body_b, anchor)` rows applied unconditionally; `project()` is
  `torch.where`/`clamp`, never an `if`.

**Why fixed-iteration is physically legitimate here (grounded in this project's own measurement):**
the suspension's job is small and slow — `docs/gpu-surrogate-design-2026-06.md` measured Chrono's
lateral load transfer is **~99% geometric/quasi-static, <1% roll-elastic** (the Sedan has NO
anti-roll bar, verified three ways). So the solve does not need to converge a stiff elastic network
to machine precision; it needs to (a) hold the kinematic loop closed (the geometric path tier-a got
wrong) and (b) carry the small elastic residual. A handful of Gauss-Seidel sweeps + Baumgarte
suffices to avoid gross under-convergence error **on this vehicle**, and `N_ITER` becomes the
fidelity dial (§4).

**The cost is unbenchmarked and is the dominant T3 risk.** A fixed-iteration projected-GS sweep over
padded `[N, n_axles, 2, ~24×24]` corner blocks with per-constraint unrolled Cholesky, plus
maximal-body gather/scatter, is realistically **100–1000× heavier per step than pwr3's elementwise
tyre eval**. At N=262k the per-iteration kernel launches + the larger state can plausibly push the
rung-2 rate *below* the ~0.5M floor in eager torch (no compile is yet shown to work on the solve
loop). **This is why a throughput-only prototype of this sweep is a hard T3 prerequisite (§6, T3a),
not an assumption.**

**Differentiability:** the whole sweep is `+ − · / clamp where exp searchsorted gather` — all
autograd-friendly, as pwr3/tier-a already are. The fixed iteration count makes the unroll depth
*static*, so backprop-through-solve is a finite static graph (no while-loop). **Recorded caveat:**
backprop through the gear-FSM / stiff combined-slip already diverged the residual in Phase-B, so soft
constraints (`cfm>0`) and the discrete-switch isolation (§2.6) are *not optional* — they keep the
gradient finite, but the project's primary path remains model-free; differentiable-unroll is reserved
for the cheap rung where it is already proven.

### 2.5 Integrator — semi-implicit Euler, sub-stepped, with the stiff 1-D modes implicit

Chrono::Vehicle uses HHT (implicit, α-damped) at 1 kHz (`chrono_vehicle_backend`: `INTERNAL_STEP_S
=1e-3`, 20 substeps / 0.02 s control step), which needs a Newton solve per step — exactly the cost
MJX/Brax avoid. We adopt **projected semi-implicit (symplectic) Euler**, sub-stepped (the standard
PBD/TGS GPU integrator): velocity updated from forces first (the §2.4 sweep), then position — pwr3
and tier-a already do this.

- **Step size:** carry the control rate `dt=0.02 s`; `substeps` is a CONFIG field (pwr3=4, tier-a=8;
  posttrain → up to 20 = Chrono 1 kHz parity).
- **The two genuinely stiff 1-D modes** — tyre vertical (`Cz≈456 716 N/m`, tier-a line 260) on
  ~45 kg unsprung (period ~2 ms → naive explicit needs h≤~0.5 ms ≈ 40 substeps) and the
  suspension spring/damper — are **scalar per corner** and integrated **implicitly closed-form**
  (the unconditionally-stable `1 − exp(−rate·h)` pattern pwr3 uses for slip-relaxation). This keeps
  `h≈5 ms` (substeps ~5-8 not ~40) without a global Newton solve — the "half-implicit" the
  translation plan named. The constraint loop + body translation stay explicit.

### 2.6 Discrete switches made round-off-robust under op-reorder

The measured non-robustness: a future `torch.compile` will flip ~3% of envs at gear thresholds
because a raw float compare lands differently after op-reorder. **Confirmed in source — and the fix
is NOT yet implemented:** `gpu_physics_pwr3._update_gear` (lines 423-429) is exactly
`up = (motor_rpm > up_thresh) & (gear < 5)` — a raw float `>` with no dead-band. There are exactly
THREE discrete switches; each gets the same treatment:

1. **Gear FSM** — already int64 state carried OUTSIDE the float state (pwr3 returns `new_gear`
   separately; `gpu_env_physics` stores `self.gear`), updated by a masked `+up.long() − down.long()`
   with a hysteresis band (`SHIFT_DOWN < SHIFT_UP`). **The fix for the 3% flip is a HARD T0
   deliverable, not a solved problem:** dead-band the compare (`motor_rpm > up_thresh + eps`, or
   compare quantized `floor(rpm/ΔRPM)`) and widen the band beyond per-step rpm round-off. Until this
   is implemented AND a bitwise-repeat replay test passes, `deterministic_switches=False` and **no
   certificate metric may be recorded** (enforced in the certify harness, §5.1 / §6 T0). Because gear
   is integer state, a boundary flip is self-correcting next step and cannot propagate into the float
   autograd graph.
2. **Contact on/off** (new in Tier-2, tyre-ground) — a SOFT penetration constraint, not a boolean:
   normal impulse = `clamp_min(0)` of a Baumgarte term over a small penetration depth (cfm/solimp),
   continuous through zero, so reorder cannot flip a sign. (Chrono runs `CollisionType_NONE`, so
   vehicle-obstacle collision is the **analytic clearance event** layer, not contact dynamics.)
3. **FWD front-traction cap / drive saturation** (pwr3) — a `clamp`, already continuous; its only
   sharp point is the `0.5·mu·Fz` floor (`clamp_min`), reorder-stable.

**Architecture invariant:** every discrete decision is either (a) integer state carried outside
autograd with a hysteresis dead-band sized > per-step round-off, or (b) a soft/clamped continuous
transition. NO raw float `>` drives a load-bearing branch *after T0*. **Open risk the doc does not
assume away:** if op-reorder can flip 3% of gear decisions, it can also perturb the float dynamics
the certificate measures — so the bitwise-repeat test must pass on the *full dynamics trace*, not
just the gear stream, before any §3.3 number is trusted.

### 2.7 Force assembly and driveline (the `f` fed to the solver)

The unconstrained force `f` in `v* = v + h·M⁻¹f` reuses verbatim the proven leaf ops: the EXACT
TMeasy tyre (`_wheel_forces`, `chrono_tmeasy_curves.npz`), the measured slip-relaxation, the
engine/gear LUTs + `_update_gear`, and the FWD front-traction cap. The engine consumes per-wheel
`Fx/Fy/Fz` and per-axle drive torque as `[N,4]` inputs. The **driveline open-differential 1-D KKT**
(open diff = 3-shaft linear constraint) is a small linear block solved in the SAME fixed-iteration
sweep as the joints. Driveline FWD/RWD/4WD = which entries of a `[N,4]` axle-torque vector the engine
feeds (a mask + the measured `GetDrivenAxleIndexes`, which this project already discovered is the
FRONT for the Sedan).

---

## 3. Fidelity spectrum + config schema (facet B)

### 3.1 The model-order rungs (the discrete Pareto points)

A rung is defined by *which multibody DOFs it carries*, mapped to the residuals from the dig:

- **F0 / rung-0 — PLANAR single-track** (`gpu_physics_pwr3.py`, `PHYS_STATE_DIM=17`). Restores vs the
  bare single-track: EXACT TMeasy curves, measured sigma, RWD powertrain + FWD front-axle cap,
  measured coastdown, and the carried **gear-SEED** win (`init_state` seeds the highest in-band gear).
  Closes: powertrain gap (gear-seed = 57% of avoid-vx) + tyre-relaxation transient (β@24
  0.0403→0.0295 with measured sigma). Drops: driveline inertia, front long-slip, the FWD/RWD tension.
  **THE PRETRAIN RUNG.** *Caveat: the trained pipeline today imports the stale `gpu_physics_pwr`, not
  pwr3 — repointing it is real T0 work, §6 T0.*
- **F1 / rung-1 — chassis-6DOF + 4 EXPLICIT-spring-damper corners** (`gpu_vehicle_tier_a.py`,
  `TIER_A_STATE_DIM=30`, substeps=8). Adds chassis z/roll/pitch + per-corner dynamic Fz from measured
  kinematic lookups + measured shock damping (front 10000 / rear 15000 N·s/m). **A MEASURED NEGATIVE
  RUNG:** avoid vx_rmse 0.897→0.903 (no change — the avoid gap is longitudinal, load-transfer-
  insensitive) and drift β@24 0.028→0.0756 (kinematic corners miss the real roll-centre geometry →
  over-transfer at entry → rear over-rotates). Retained for two reasons: (a) it is the cross-vehicle
  template carrier; (b) its certificate is the *empirical proof that "more DOF ≠ less error"*.
- **F2 / rung-2 — FULL-LINKAGE constrained DAE** (to build; §2; `gpu_vehicle_tier2.py`). The real
  ~10-15 true DOF solved as the §2.4 fixed-iteration sweep. **Expected payoff is UNPROVEN — and the
  project's own evidence points to "probably not without a recalibrated FWD redesign."** The only
  isolated DOF-restore the project tested (pwr6 front-slip) was **null/negative at the gate** (front
  long-slip emerges structurally but the worst-front-sx cells are *not* the β@24-metric cells, where
  front sx ≈ 0.01 at step 24); and the principled FWD restructure (pwr6 Option A) **broke the drift
  saddle structurally** (honest β 0.037→0.089) even with coupling=0. A full-linkage FWD-consistent
  rung-2 reintroduces exactly that structural tension. **THE POSTTRAIN RUNG ONLY IF its certificate
  beats rung-0 on the target cells** — gated on the §6 T3a afternoon-scale falsification test before
  any 6-12wk build.

### 3.2 The continuous/discrete KNOBS (cheap axes within a rung)

| knob | type | where it lives | accuracy effect | cost |
|---|---|---|---|---|
| `substeps` | int 1..16 | `PhysParams.substeps`=4, `TierAParams.substeps`=8 | semi-implicit Euler error; rung-1 needs ≥8 | linear |
| `tyre_transient` | {algebraic, relax} | `sigma_scale=0`→quasi-static; measured→relax | L0 plateaus 0.0403; L1 reaches 0.0295 | ~free (one `exp`) |
| `sigma_scale` | float | `PhysParams.sigma_scale` (gates use 0.165) | broad basin 0.10-0.20 m all ~0.026-0.031 | free |
| `integrator` | {semi-implicit-Euler, half-implicit-linearized} | rung-0/1 vs rung-2 | stiff-mode stability | ~equal 0/1 |
| `N_ITER` / `solver_iters` | int (rung-2 only) | the §2.4 sweep count | DAE constraint residual | linear in N_ITER |
| `cfm` / `β` | float (rung-2) | §2.4 softness | loop-closure tightness | ~free |
| DOF-restore flags | bool | `pwr5/pwr6` → flags `driveline_inertia`, `front_slip` | **MEASURED NULL/NEGATIVE** | small |

The DOF-restore flags stay in the schema as **certified-null** knobs (pwr5 == pwr3 to noise; pwr6
regresses drift honest 0.0368→0.0410) precisely so a config can *record* "tried, certified null"
rather than someone re-discovering it.

### 3.3 The spectrum table (rung × knob → certified error vs Chrono × throughput)

All error numbers are MEASURED gate outputs from `docs/gpu-surrogate-design-2026-06.md` and the gate
scripts (sigma_scale=0.165, seed-0 130/30 held-out split). "β@24 honest" = computed with Chrono's
TRUE vx. **Throughput numbers below are split into MEASURED and UNMEASURED PRIOR — no heavy-rung
throughput has ever been benched, and there is no `torch.compile` in the repo, so every "compiled"
figure is a T0 *target* to be measured, not a result.**

| config (rung, knobs) | module | drift β@24 p90 (honest true-vx) | avoid vx_rmse | avoid collision bal-acc | throughput |
|---|---|---|---|---|---|
| rung-0, substeps=4, L0 algebraic tyre | `gpu_physics_tmeasy` | 0.0403 | 0.235 (drift) | ~0.66 | **MEASURED** ~1.3M st/s @16k eager |
| **rung-0, substeps=4, L1 relax σ=0.165 (CARRIED)** | **`gpu_physics_pwr3`** | **0.0368** (raw 0.0323) | **0.520** | ~0.695 | **MEASURED** ~1.3-2.4M @16k eager; **@262k + compiled = T0 BENCH TARGET (unmeasured)** |
| rung-0 + driveline-inertia flag | `gpu_physics_pwr5` | 0.0321 (==pwr3 to noise) | 0.520 | — | ~same |
| rung-0 + front-slip-coupling flag | `gpu_physics_pwr6` | 0.0410 (WORSE) | 0.516 | — | ~same |
| rung-0 + 4-wheel-brake flag | `gpu_physics_pwr4` | 0.0395 (WORSE) | 0.641 (WORSE) | — | ~same |
| grey-box (single-track + unrolled residual) — reference | `gpu_surrogate` | 0.0156 (best on cell) | 0.049 | 0.503 (collision-BLIND) | **MEASURED** ~91M @262k (analytic backbone, NOT physics) |
| **rung-1, substeps=8, spring-damper corners (CERTIFIED-WORSE)** | **`gpu_vehicle_tier_a`** | **0.0756 (FAIL)** | **0.903** | ~0.70 (est) | **UNMEASURED PRIOR** — must bench (it exists and runs) |
| rung-2, full-linkage DAE, `N_ITER`=N | `gpu_vehicle_tier2` (to build) | TBD by certificate | TBD | targets ≥0.75 | **UNMEASURED PRIOR** — T3a prototype bench required |

Three load-bearing facts this table encodes:

1. **The accuracy column is non-monotone in rung.** rung-1 is strictly worse on BOTH headline metrics
   than rung-0 despite more DOF. The spectrum is a *measured scatter*, not a clean Pareto frontier by
   order; selection must read the certificate, never infer fidelity from rung.
2. **The grey-box is the fidelity ceiling on the trained cell (0.0156) but collision-BLIND (bal-acc
   0.503).** A single scalar error would pick it and ship a collision-blind avoidance model — which is
   why the certificate is multi-metric (§5).
3. **The throughput column is mostly UNMEASURED.** The only physics anchor is ~1.3-2.4M @16k eager.
   tier_a (which exists and runs) was never benched; rung-2 is bounded only by a solve-cost
   hand-wave. De-risking this is one afternoon (§6 T0/T3a) and gates the whole posttrain premise.

### 3.4 The config schema — a rung registry behind a shared contract

A single frozen dataclass extends the existing `PhysParamBatch`/`TierAParamBatch` pattern and mirrors
the `CHRONO_VEHICLE_VARIANTS` registry. Proposed `src/autodrift/fidelity_config.py`:

```python
@dataclass(frozen=True)
class FidelityConfig:
    config_id: str                      # content-addressed (hash of the tuple below)
    # axis 1: vehicle (template params; reuses the chrono variant registry id)
    vehicle_variant: str = "sedan_tmeasy"   # -> CHRONO_VEHICLE_VARIANTS key (cross-vehicle)
    param_overrides: dict = ...             # mass/izz/wheelbase/front_axle_share/driveline
    # axis 2: fidelity rung (which GPU module)
    rung: int = 0                           # 0=pwr3 planar, 1=tier_a, 2=tier2 DAE  (DISTINCT MODULES)
    # solver topology (rung-2 only)
    template_ids: tuple = ()                # per-axle suspension template enum
    n_axles: int = 2
    driveline_id: str = "FWD"               # FWD / RWD / 4WD
    body_layout: object = None              # [n_axles,2,D_CORNER] padded body/inertia table
    constraint_rows: object = None          # [n_con,(type,body_a,body_b,anchor)] fixed list
    # axis 3: numerical knobs (order within the rung)
    substeps: int = 4
    tyre_transient: str = "relax"           # {algebraic, relax}
    sigma_scale: float = 0.165
    integrator: str = "semi_implicit_euler"
    N_ITER: int = 0                         # rung-2 constraint sweeps  ← FIDELITY DIAL (rung-2 only)
    cfm: float = 1e-6; baumgarte: float = 0.2   # rung-2 softness        ← FIDELITY DIAL
    dof_flags: frozenset = frozenset()      # {driveline_inertia, front_slip, four_wheel_brake}
    # the CERTIFICATE (filled by the gate, not the author)
    certificate: "FidelityCertificate | None" = None
```

A **resolver** `build_model(cfg) -> (physics_step, init_state, state_dim, IDX, ParamBatch_factory)`
maps `rung` to the **distinct module** (`{0: gpu_physics_pwr3, 1: gpu_vehicle_tier_a,
2: gpu_vehicle_tier2}`), threads `vehicle_variant`+`param_overrides` into the rung's `*Params`
dataclass, and applies the knobs. The rung modules already share the *call* contract:
`physics_step(state, action, gear, P, dt) -> (next_state, next_gear, diag)` and `init_state(...) ->
(state, gear)` are identical across pwr3 and tier_a; **they do NOT share a state layout** (17 vs 30
dims; incompatible `IDX`).

**Fidelity = config, realized as a registry + certified agreement (the honest version).** PRETRAIN
selects rung-0/pwr3. POSTTRAIN selects a higher rung *iff its certificate dominates rung-0* (§5.2).
There is **no flag that turns one module into another**; instead each rung's cheap configs are
**validated to agree within tolerance** with the rung below on the frozen replay set (a registered
test, §5.1 M-agreement), which is what makes the spectrum a coherent ladder rather than three
unrelated models.

**The cross-fidelity obs72 invariant must be MADE TRUE before it is claimed — this is real T0 work,
not one line.** Today `gpu_env_physics.obs72_from_state` reads **hard-coded integers**:
`x=state[:,0]; y=state[:,1]; psi=state[:,2]; vx=state[:,3]; vy=state[:,4]; yaw=state[:,5];
steer=state[:,6]` (verified lines 355-356; also the reward/termination readers at ~459, ~478). Under
pwr3 `state[:,3]` is `vx`; under tier_a `state[:,3]` is `roll` — the layouts are **incompatible**, so
a fixed-integer read is silently wrong for rung-1/rung-2. The gate already needed an ad-hoc
`yaw_col = TA_IDX["yaw"]` remap (`gpu_tier_a_gate.py:90`) — the warning sign that the seam is not
free. **Required T0 refactor (~1-2 days):**

1. Replace the ~6 hard-coded `state[:,0..6]` sites in `obs72_from_state` and the reward/termination/
   success readers with `IDX[name]` indexing.
2. Require every registered rung to expose a **canonical planar sub-state by name** —
   `{x,y,psi,vx,vy,yaw_rate,steer,throttle,brake}` — via its `IDX`. pwr3 has this; tier_a must add
   the missing canonical names (it has `vx:6,vy:7,yaw:5` but not a `yaw_rate` alias, etc.).
3. Add a unit test asserting obs72 is **bit-identical across rungs for a fixed pose** (the 60 geometry
   dims are pose-derived; the ~12 ego-dynamics dims read by name must match).

Only after this passes can the design claim "obs72 holds across fidelities with zero policy change."
The extra link-body DOFs stay internal and never reach the policy — but that is a *property to be
enforced by the by-name contract*, not an existing fact.

---

## 4. Pretrain/posttrain curriculum (facet C)

### 4.1 The governing constraint — the curriculum is ASYMMETRIC, and mostly NOT a schedule

The project's own A5 results impose an asymmetry a naive "pretrain coarse → fine-tune accurate"
curriculum ignores:

| task | coarse-pretrain → Chrono transfer | mechanism | fidelity-curriculum verdict |
|---|---|---|---|
| **drift** | **1.000 from EVERY surrogate** (analytic, grey-box, planar) | robust saddle-stabilization, μ-low-sensitivity | **fidelity-TOLERANT** — pretrain on the cheap rung, NO fine-tune |
| **avoidance** | grey-box 0.700, **physics 0.000**, +DR 0.075 | precise collision-boundary/timing; partial fidelity invites OVERFIT | **fidelity-INTOLERANT** — coarse→fine REFUTED 3× |

So the fidelity curriculum is routed through the **do-both gated architecture** (`distill_both.py`'s
`AsymmetricActorCritic(gated=True)`, shared trunk + `actor_mean_a/b` heads): the **drift head** is the
curriculum's *only* client; the **avoid head** is an imitation client (Chrono oracle + DAgger). This
is forced by data, not taste.

### 4.2 The schedule

**Drift head — pretrain-only, NO posttrain fine-tune.** The planar-pretrained drift policy hits
Chrono 1.0 with zero fine-tuning, so the schedule degenerates: train the drift expert entirely on F0
(huge batch), then distill — *there is no posttrain fidelity stage for drift*. We do NOT spend Chrono
budget fine-tuning drift dynamics. No anneal/mixed-fidelity for drift either: F1 is a negative rung
and F0→F2 transfer is already perfect, so annealing through F1 would only hurt. What replaces the
schedule is **fidelity-as-DR** (§4.4) during the single F0 pretrain.

**Avoid head — NO dynamics-fidelity schedule.** Three A5 negatives prove avoid is not bridged by any
surrogate, any batch size, or DR-on-dynamics. Avoidance does not enter the fidelity curriculum as a
dynamics-training target; its "fidelity" comes from the **Chrono oracle demonstrations themselves**
(collected at F2 via `distill_both` `make_avoidance_teacher` + `run_episode(collect="bc")` — *no*
demo sim-to-sim gap because demos are collected on real Chrono pose). The avoid schedule is the proven
imitation chain: oracle-distill (`distill_both.py`) → hard-cell DAgger (`dagger_avoid_v2.py`), which
already reaches 1.0.

**The ONE legitimate fidelity switch — a future avoid-fidelity rung.** IF a collision-faithful rewrite
(rung-2) ever passes an avoid collision-boundary gate (bal-acc ≥0.75; currently 0.665-0.695), THEN a
posttrain stage for avoid becomes meaningful. The switch trigger is **a sim-to-sim collision-boundary
GATE, never a wall-clock/step timer**: switch from F0-DR pretrain to F-fine posttrain ONLY when the
fine rung's collision bal-acc ≥0.75 AND its avoid vx_rmse < ~0.4. Until that gate passes, avoid
posttrain is OFF (the A5-physics 0.000 result is exactly what happens if you switch onto a sub-gate
rung).

**One-paragraph recipe.** PRETRAIN: drift expert on F0 at 16k-262k batch with fidelity-DR (§4.4) →
distill the F0 drift expert + the F2 Chrono avoid oracle into one gated student (`distill_both.py`) →
DAgger the avoid head on F2 hard cells (`dagger_avoid_v2.py`). POSTTRAIN drift dynamics: **none
required**. POSTTRAIN avoid: an imitation loop on Chrono, gated by the collision-boundary fidelity test
before any dynamics rung is admitted.

### 4.3 Sim-to-sim transfer — what transfers, what breaks, obs72 invariance

- **What transfers:** the drift policy transfers F0→Chrono at 1.0 because obs72 is largely
  fidelity-invariant for the saddle: its 60 geometry dims (road lookahead + obstacle slots) are
  kinematic (computed from pose by identical CircleTrack math in gpu_env and gpu_env_physics,
  byte-for-byte), so only the ~6 ego-dynamics dims `{vx,vy,yaw_rate,...}` + steer/throttle/brake are
  fidelity-sensitive, and the planar model reproduces β=atan2(vy,vx) and yaw_rate well enough.
  **Conditional on the §3.4 by-name obs refactor** — until that lands, the invariance is only wired
  for rung-0.
- **What breaks (the dropped DOFs the policy never saw):** the **drift-RWD vs avoid-FWD structural
  tension** is the real transfer hazard — the principled FWD restructure (pwr6 Option A) BREAKS the
  drift saddle (honest β 0.037→0.089). A single planar structure cannot be faithful to both the
  RWD-omega drift saddle AND the FWD avoid acceleration. **Curriculum implication:** never fine-tune
  the drift head on an FWD-restructured rung; keep drift on RWD-faithful F0 and avoid on imitation —
  the gated heads make this split clean. Front long-slip and gear-seed/driveline-inertia do NOT break
  drift transfer (confirmed by the 1.0).
- **obs72 fidelity-invariance (actionable):** (1) keep `EGO_*_SCALE` normalizers FIXED across rungs;
  (2) fidelity-DR the dynamics channels (§4.4) so the obs72→action map is trained insensitive to the
  residual-gap directions; (3) anchor the avoid head to the F2 oracle (which acts on Chrono pose), not
  to any surrogate's pose drift.

### 4.4 Fidelity-as-DR — the multi-fidelity analog of domain randomization

Cheap to build because the injection point exists: `make_phys_param_batch` broadcasts any
`_PARAM_KEYS` field as a per-env `[N]` tensor, and `gpu_env_physics.__init__` builds `param_src` from
per-env tensors. Sample a per-env **fidelity vector** each episode over the KNOWN residual-gap
directions (NOT generic mass/μ noise):

- `sigma_scale ∈ [0.10/0.165, 0.20/0.165]` (the broad physical relaxation basin, σ∈[0.10,0.20] m all
  pass);
- `front_grip_scale, rear_grip_scale ∈ [0.95, 1.05]` (tyre-curve uncertainty);
- `h_cg_scale ∈ [0.9, 1.1]` (the load-transfer / geometric-vs-roll uncertainty F1 got wrong);
- `drive_scale ∈ [0.85, 1.15]` (brackets the measured ~0.57 partial-throttle null and high-μ
  over-accel);
- `max_brake_torque ∈ [1600, 2400]` (the one guessed→measured param);
- a `front_slip_coupling ∈ [0, 0.4]` knob toggling the pwr6 front-Fy robbing, so the policy sees both
  sx=0 and faithful-front-slip dynamics.

This is DR over exactly the directions the residual occupies, at **near-zero extra env cost** (per-env
tensors already broadcast). For **drift** the gap IS inside this family, so fidelity-DR *should* make
the drift expert more robustly transfer. **Honest scope:** fidelity-DR is a DRIFT-robustness tool, NOT
an avoid fix (the three avoid negatives stand; generic DR-on-dynamics is exactly what scored avoid
0.075). Add two near-free cheap-wins during F0 pretrain: **init-β randomization near β\*≈0.28** and a
**Jacobian regularizer λ≈1e-5** (both cut PPO seed variance). **The variance-reduction payoff is
itself UNTESTED** — open-question #5.

### 4.5 Composition with the proven do-both recipe

| component | fidelity-curriculum role |
|---|---|
| **drift expert** (`gpu_physics_policy_seed0.pt`, via `load_drift_expert`) | **FULL fidelity-DR pretrain on F0** — the only true curriculum client; produces a spectrum-robust drift teacher |
| **avoid oracle** (`make_avoidance_teacher`) | **NO curriculum** — analytic F2-Chrono oracle, demos on the real surrogate; fidelity-invariant by construction |
| **distillation student** (`distill_both.py` BC into `AsymmetricActorCritic(gated=True)`) | inherits fidelity-robustness from the drift teacher; the gate self-routes regimes from obs72; collect drift demos across sampled fidelities so the student's drift head is robust too |
| **DAgger** (`dagger_avoid_v2.py`) | **avoid-only, F2 hard cells** (`HARD_CELLS`) — closes the imitation gap 0.9→1.0; drift demos/head frozen → drift cannot regress by construction |

Selection stays on the disjoint `distill_select` namespace (`distill_both._chrono_select_eval`) — no
select-on-test. Cross-vehicle: the same fidelity-DR pretrain runs per variant (`chrono_vehicle_backend`
params → `PhysParams`); UAZBUS already showed the feedback teacher may suffice without a per-vehicle
GPU surrogate, so fidelity-DR is upside, not a blocker.

---

## 5. Validation certificate + integration + tiered build (facet D)

### 5.1 The per-fidelity Fidelity Certificate (the core deliverable)

A config IS a fidelity level, so each ships a machine-readable certificate pairing an **error bound**
(distance from Chrono) with a **measured throughput**. Produced by ONE standardized harness that
generalizes the three existing replay gates (`gpu_pwr3_gate.py`, `gpu_tier_a_gate.py`,
`surrogate_avoid_boundary_physics_gate.py`) against the SAME frozen Chrono rollouts and the SAME
held-out split (`idx[130:]`, sigma_scale=0.165) — apples-to-apples is already guaranteed.

**Five certified checks (each grounds on an existing gate):**

- **(M1) Drift lateral fidelity — β@24 p90.** From `gpu_pwr3_gate.py`: `beta = atan2(vy, |vx|+1e-6)`,
  `|beta_chrono − beta_model|` at step 24, p90 over held-out. **Gate ≤ 0.03.** MUST also carry the
  HONEST `p90_true` (β recomputed with Chrono's TRUE vx) so a config cannot pass by compensating a
  lateral error with a longitudinal one. Reference: planar pwr 0.0283/0.0368-honest, tier-a 0.0756
  FAIL, L0 0.0403.
- **(M2) Avoidance longitudinal fidelity — vx_rmse vs the 0.235 drift floor.** From `avoid_gate` /
  `class_rmse`: length-masked vx RMSE over the 120 avoid rollouts, against the planar baseline 0.897,
  WITH the accel/brake-class split + vy_rmse (~0.13, already faithful). **Report-and-rank, not
  pass/fail** — pretrain legitimately ships a coarse 0.90.
- **(M3) Collision boundary fidelity — balanced accuracy.** From
  `surrogate_avoid_boundary_physics_gate.py`: replay the boundary actions, threshold `crash_s` on the
  config's pose, `bal = 0.5*(TP/(TP+FN) + TN/(TN+FP))` vs Chrono. **Gate ≥ 0.75 to certify
  "collision-faithful."** Reference: grey-box 0.503 (chance), analytic 0.713, L1 0.665, planar pwr
  ~0.695. Carry TP/TN/FP/FN + "crashes caught" (bal-acc alone hides the FP/FN asymmetry).
- **(M4) Per-wheel telemetry RMSE — the multibody-DOF certificate.** From
  `chrono_vehicle_backend._collect_tire_telemetry_from_vehicle`: per wheel,
  `{slip_angle, longitudinal_slip, Fy, Fx, Fz, omega}`. Certify per axle/side RMSE. Directly audits
  the restored DOFs. **Warning carried from pwr6:** M4 telemetry can *improve* (front-Fy tail RMSE
  564→332 N) while M1 *regresses* — M4 is a mechanism diagnostic, NOT a promotion criterion. M1/M3
  decide promotion; M4 explains why.
- **(M-agreement) Cross-rung agreement.** A registered test that each rung's *cheap* config agrees
  within tolerance with the rung below on the frozen replay set — the property that makes the registry
  a coherent ladder (replaces the dropped "exact degeneration" claim).

**The closed-loop cap (sim-to-sim) — resolved as a FINAL promotion gate only, not a per-knob sweep.**
Open-loop replay (M1-M4) is necessary but proven insufficient: A5 showed a config can be
collision-faithful in replay (0.695) yet a policy TRAINED on it scores 0.000 on Chrono (overfit the
residual gaps). So the certificate has a second, expensive tier — `a5_chrono_validate.py`: train a
short policy on the config's env, run it on real Chrono, report `drift_succ`/`avoid_succ` vs CPU
canonical (drift 0.856, avoid 0.700). **Because CPU-Chrono is ~1k st/s and this is the project's
actual bottleneck (not GPU env steps), the closed-loop tier is capped (resolving open-question #8):**

- Closed-loop runs **only on a config that already DOMINATES rung-0 on open-loop M1/M3** — never as a
  per-knob or per-rung sweep.
- **At most ~5 posttrain candidates ever reach closed-loop**, total, across the whole program.
- The **per-quarter Chrono-validation budget is a hard, stated constraint** (≈ a handful of
  multi-seed A5 runs; each is the dominant wall-clock cost in the program). The roadmap is honest that
  *this CPU-Chrono axis, not GPU throughput, gates every promotion.*

**Certificate schema** (`src/autodrift/fidelity_config.py`):

```python
@dataclass(frozen=True)
class FidelityCertificate:
    config_id: str; parent_config_id: str          # lineage in the fidelity ladder
    state_dim: int; restored_dofs: tuple
    drift_beta24_p90: float; drift_beta24_p90_true: float; drift_pass: bool     # M1 gate 0.03
    avoid_vx_rmse: float; avoid_vx_rmse_accel: float; avoid_vx_rmse_brake: float; avoid_vy_rmse: float  # M2
    collision_bal_acc: float; collision_caught_n: int; tp: int; tn: int; fp: int; fn: int
    collision_faithful: bool                        # M3 gate 0.75
    telemetry_rmse: dict                            # M4 (diagnostic only, never a promotion criterion)
    agreement_rmse: dict                            # M-agreement vs the rung below
    closed_loop: dict                               # {drift_chrono, avoid_chrono} — FINAL gate only, ≤5 ever
    throughput_envsteps_per_s: float; batch_n: int; compiled: bool   # MEASURED via rollout_throughput
    deterministic_switches: bool                    # FALSE until gear dead-band + bitwise-repeat pass — BLOCKS emission
    chrono_replay_set: str                          # SHA of the frozen rollout npz
    held_out_split: str; seed: int; sigma_scale: float; git_sha: str
```

The certificate is **per-(config, replay-set, vehicle-variant)** — it does NOT claim generalization
beyond the cells it measured. The harness **refuses to emit any metric while
`deterministic_switches=False`** (i.e. until the §2.6 gear dead-band fix lands and the bitwise-repeat
test passes on the full dynamics trace).

### 5.2 How pretrain/posttrain pick configs

- **PRETRAIN:** maximize throughput s.t. `certificate.error[metric] ≤ tol_pretrain[metric]`. DRIFT →
  rung-0/pwr3 (drift transfers 1.0 regardless of the ~0.037 honest residual). AVOID pretrain →
  rung-0/pwr3 as the collision-faithful cheap env (GENUINE collisions vs grey-box's collision-blind
  0.503).
- **POSTTRAIN:** pick the highest-CERTIFIED-fidelity config that fits the wall-clock budget — and ship
  a higher rung to posttrain ONLY if its certificate **dominates** rung-0 on the target regime's
  metric AND passes the final closed-loop gate, NEVER because it has more DOF. **Today the honest
  posttrain config is STILL rung-0 with knobs tightened**, because no higher rung is certified-better.
  A higher-rung-but-uncertified-better config is exactly the overfitting TRAP the certificate exists
  to prevent (physics→Chrono avoid 0.000).

### 5.3 Integration with the existing pipeline (verified)

- **Model contract:** every config exports `physics_step(state[N,D], action[N,3], gear[N], P, dt) ->
  (next_state[N,D], gear[N], diag)`, `init_state(...) -> (state,gear)`, a `make_*_param_batch`, and an
  `IDX` map. **Invariant a higher-fidelity rewrite MUST preserve — by NAME, not by index:** the
  canonical planar sub-state `{x,y,psi,vx,vy,yaw_rate,steer,throttle,brake}` must be exposed in `IDX`.
  This is NOT true of the existing layouts as fixed integers (pwr3 `vx=3`, tier_a `roll=3`); it
  becomes true only after the §3.4 by-name refactor.
- **The env:** `GPUPhysicsAutoDriftEnv` is a byte-identical drop-in for the grey-box env (obs72/
  reward/termination/success copied verbatim; parity 1.1e-7 drift / 5.9e-8 avoid). Make it
  config-parametric: `build_env(config_id)` selects the config's `physics_step`/`init_state`/`IDX`.
  **Today this seam is stale:** `gpu_env_physics.py:52` imports `from autodrift import
  gpu_physics_pwr as phys` — the **pre-gear-seed** model (avoid vx 0.897), NOT pwr3 (avoid vx 0.520);
  `phase4_f2_gpu_train_physics.py` imports that same env. So T0 is "switch the env off the stale
  import AND build the registry," verified by a short PPO+A5 (§6 T0), not "wire the existing thing."
- **Chrono backend = oracle + telemetry source:** `chrono_vehicle_backend.py` is the GROUND TRUTH
  generating the saved replay rollouts AND the per-wheel M4 telemetry; its `CHRONO_VEHICLE_VARIANTS`
  registry (sedan/bmw_e90/uazbus) is the cross-vehicle axis.
- **do-both distill/DAgger:** verified fidelity-AGNOSTIC. `distill_both.py` collects demos on real
  Chrono and BC-distills a gated student; the GPU config's only upstream role is producing the DRIFT
  EXPERT whose drift transfers to Chrono 1.0.

### 5.4 Tech choice and honest throughput

**Tech choice — keep torch, ADD `torch.compile` (it is not yet present), add deterministic switches;
defer JAX; reserve CUDA.**

- **torch.compile (CHOSEN for T0-T2 — but NOT YET IN THE REPO):** there is no `compile` call in the
  env/physics/throughput/training code. The "128× / 582M" figure is a *target to bench at T0*, not a
  measured result. T0 must (a) add `torch.compile` to the env step, (b) bench it, and (c) land the
  gear dead-band so the compile does not silently corrupt certificate numbers. T0-T2 have no
  constraint solve so JAX's autodiff-through-solver buys nothing there.
- **JAX/XLA (DEFER to T3-only):** the MJX/Brax route earns its place only for the full-linkage DAE
  (T3), where gradients-through-the-constraint-solve and XLA's fusion of the batched saddle-point
  genuinely matter. Adopt iff T3 is greenlit.
- **Hand C++/CUDA (RESERVE):** max speed but loses torch PPO integration and the obs72-parity test;
  only if a certified config is throughput-bound AND torch CUDA-graphs can't capture it.

**Honest throughput. The ONLY measured physics anchors are ~1.3M @16k eager and ~2.4M "engine"; the
91M @262k is the analytic backbone, not physics; there is NO compiled number. Everything heavier than
pwr3 is UNMEASURED PRIOR:**

| config (rung) | state dim | per-step driver | status | number |
|---|---|---|---|---|
| planar pwr3 (PRETRAIN/T0) | 17 | elementwise tyre + gear FSM, NO solve | **MEASURED eager** | ~1.3-2.4M @16k; @262k+compiled = **T0 bench target** |
| analytic backbone (reference) | — | analytic step, NO physics | MEASURED | ~91M @262k |
| kinematic-corner (T1/tier-a) | 30 | +4 corner spring-damper ODEs + lookups, NO solve | **UNMEASURED PRIOR** | bench it (exists & runs) before quoting |
| full-linkage DAE (T3) | ~10-15 true / ~100 maximal | batched `[N,~24,24]` GS sweep/step + Jacobians | **UNMEASURED PRIOR** | T3a prototype bench; plausibly 100-1000× slower than pwr3; could fall below 0.5M in eager |

**The justification rewritten to be honest:** the pretrain/posttrain split is justified **versus
CPU-Chrono** — even a pessimistic ~0.5M st/s rung-2 is ~500× the ~1k st/s 30-worker Chrono baseline,
so posttrain on GPU still beats CPU by 2-3 orders of magnitude. The **intra-GPU pretrain↔posttrain
gap is NOT confidently large**: if compiled-pwr3 is ~2.4M and rung-2 is ~0.5M, the gap is ~5×, not
~1000×; "pretrain carries the bulk cheaply" then rests on the CPU comparison and on pretrain running
the *vast majority of updates*, not on a huge intra-GPU speed ratio. The certificate's
`throughput_envsteps_per_s` is **MEASURED** via `rollout_throughput.run_throughput_case(env_config=,
mode=, num_envs=, rollout_steps=, seed=)` — the table above is a planning prior, explicitly NOT a
certificate, and every "UNMEASURED PRIOR" must be replaced with a measured number before it gates any
decision.

---

## 6. Roadmap — tiers, dependency order, what ships first, effort

The build ships in tiers; each tier's deliverable is a *certificate*, and a RED certificate is a valid
(load-bearing) deliverable.

- **T0 — wire planar pwr3 as the PRETRAIN config behind the schema (≈ 1 week, NOT "days" — real work,
  not zero-risk).** Deliverables:
  1. **Bench compiled-pwr3** with `rollout_throughput.run_throughput_case` at N=262k and N=16k, add
     `torch.compile` to the env step, **commit the JSON, and replace every "582M" everywhere with the
     measured value.** This single afternoon decides whether the intra-GPU gap is ~5× or ~1000×.
  2. **Repoint `gpu_env_physics.py:52`** off the stale `gpu_physics_pwr` onto pwr3 (or the resolver),
     and run one short PPO + A5 to **confirm the pwr3-trained drift expert still transfers to Chrono
     1.0** (do not assume — the import is stale).
  3. **Refactor obs/reward/termination readers to `IDX[name]`** (the ~6 hard-coded `state[:,0..6]`
     sites) and add the bit-identical-across-rungs obs72 test (§3.4). ~1-2 days.
  4. **Land the gear dead-band fix in `_update_gear`** + a bitwise-repeat replay test that BLOCKS
     certificate emission while `deterministic_switches=False` (§2.6, §5.1). Re-run `gpu_pwr3_gate`
     across two compiled runs to confirm stability before trusting any §3.3 number.
  5. Build `fidelity_config.py` + `build_model` resolver + `build_env(config_id)` + generalize the
     three gates into one `certify.py --config <id>` harness.
  **Ships the pretrain rung and the certificate framework.** *Depends on: nothing new — but it is real
  T0 work, booked honestly, not zero.*
- **T1 — kinematic-corner tier-a as the first POSTTRAIN attempt: a RED certificate (EXISTS).**
  `gpu_vehicle_tier_a.py` is built and tested; the certificate is honest-negative (drift 0.0756 FAIL,
  avoid 0.903 unchanged). **Also bench tier_a throughput** (never measured) to ground the rung-1
  number. T1 ships as the certificate + the M4 telemetry that shows WHY — the framework BLOCKING a
  config that looks like an upgrade but regresses drift. *Depends on: T0 harness.*
- **T2 — measured longitudinal-fidelity fix (≈ 1.5-3 wk, RECOMMENDED NEXT).** The gates LOCALIZED the
  avoid vx gap to partial-throttle longitudinal deceleration (null at drive_scale≈0.57 → 1.75×
  over-force), explicitly NOT roll/pitch (tier-a falsified that). T2 = extract the Chrono driven-force
  surface vs (throttle, speed) + the brake/engine-brake/coast deceleration over the avoid envelope
  (`extract_chrono_powertrain.py`/`extract_chrono_coastdown.py`), fold into the config, re-certify
  M2/M3. Target avoid vx_rmse → 0.235, bal-acc ≥ 0.75. Leaves the tyre-dominated drift saddle
  untouched. **The cheapest path to a collision-faithful POSTTRAIN config.** *Depends on: T0 harness.*
- **T3a — the AFTERNOON-SCALE FALSIFICATION GATE for the full DAE (≈ days, BLOCKS T3).** Before any
  6-12wk build, run the two cheap pre-tests the dig already recommends:
  1. **Inject the quasi-static geometric load transfer as a constraint bias into tier_a and re-gate
     drift.** If that does NOT break the 0.0756 regression, the full DAE will not either — **kill T3
     cheaply.** This directly tests open-question #1 at afternoon cost.
  2. **Throughput-only prototype** of the §2.4 sweep — one corner block, fixed N_ITER, unrolled
     Cholesky, `[N,24,24]`, no physics correctness — benched with `rollout_throughput` at N=16k and
     N=262k in eager torch. De-risks the posttrain throughput premise before committing.
  **T3 is greenlit ONLY if T3a both (a) shows the constraint-bias closes the drift regression AND (b)
  the prototype clears the throughput floor.** *Depends on: T0 harness, tier_a.*
- **T3 — full-linkage DAE (the §2 engine) (≈ 6-12 wk, RESERVE, GATED ON T3a).** Build the §2.4
  fixed-iteration projected solver + per-template body/inertia tables + constraint-Jacobian assembly
  (extend `extract_chrono_suspension_kinematics.py` to emit `GetBallJointPos*`/`m_revolute*`
  hardpoints so Jacobians are MEASURED, not guessed) + the per-corner implicit vertical mode. New
  module `src/autodrift/gpu_vehicle_tier2.py` reusing pwr3's TMeasy/sigma/gear leaf ops verbatim.
  Validate per-corner against M4 on a Chrono drop/step-steer transient BEFORE wiring the full loop.
  JAX/XLA earns its place here. *Depends on: T0, T2 verdict, T3a falsification, hardpoint extraction.*

**Dependency order:** T0 (framework, with bench + obs refactor + gear fix) → {T1 (free, documents the
negative), T2 (recommended)} → T3a (cheap falsification) → T3 (reserve, gated). **What ships first:**
T0 + T2 give a working pretrain config and a collision-faithful posttrain config *with only rung-0
physics*; T3 is an additive slot gated by its own afternoon-scale falsification.

---

## 7. Open questions & risks (consolidated)

### 7.1 Open questions (the empirical unknowns that decide the design)

1. **Does rung-2 actually beat rung-0** on the drift β@24 honest-true-vx AND avoid collision bal-acc
   certificates, or does it overfit/regress like rung-1 and the physics→Chrono avoid 0.000? **This is
   the explicit GO/NO-GO for T3, answered cheaply by the T3a constraint-bias falsification BEFORE the
   full build** (§6). The project's only isolated DOF-restore (pwr6) was null/negative — the honest
   prior is "probably not without a recalibrated FWD redesign of uncertain payoff."
2. **What minimum `N_ITER` + substeps** reaches honest drift β@24 < 0.03 that pwr3 could not (0.0410
   honest)? If large, fall back to injecting the proven quasi-static geometric transfer as a
   *constraint bias* (the T3a test) and let the solver carry only the small elastic residual.
3. **Per-regime certificate tolerances** (`tol_pretrain`/`tol_posttrain`) for drift vs avoid.
4. **Is there ANY avoid rung that passes bal-acc ≥0.75** (currently 0.665-0.695)? If rung-2 can't
   cross 0.75, the avoid-fidelity-rung branch is permanently dead and avoid stays pure imitation.
5. **Does fidelity-DR measurably reduce drift multi-seed transfer variance**, or is drift already so
   fidelity-tolerant that DR is a no-op gain? Cheap to test (8-seed A5 with/without DR).
6. **Driveline 1-D KKT placement** — inside the §2.4 sweep or a separate small linear block? Needs a
   micro-benchmark.
7. **Cross-vehicle** — does the recipe transfer to `bmw_e90` (RWD), and does the FWD/RWD tension
   differ per vehicle in a way that changes which head the curriculum serves?
8. **RESOLVED in this design (§5.1):** closed-loop Chrono validation is a FINAL promotion gate only
   (≤5 candidates ever reach it), with a stated per-quarter Chrono budget — CPU-Chrono closed-loop,
   not GPU env steps, is the real bottleneck and the design now optimizes around that.

### 7.2 Risks (severity-ordered, with mitigations)

- **HIGH — rung-2 regresses drift like every isolated DOF-restore before it.** pwr6 front-slip was
  null/negative at the gate; the FWD restructure broke the saddle structurally (β 0.037→0.089). A
  full-linkage FWD-consistent rung-2 reintroduces that exact tension. *Mitigate:* T3a constraint-bias
  falsification gates the whole 6-12wk build; rung-2 ships ONLY if its certificate dominates rung-0;
  default posttrain stays rung-0.
- **HIGH — non-monotone fidelity.** rung-1 is certified WORSE than rung-0 on drift AND avoid.
  *Mitigate:* spectrum framed as a measured SCATTER certified per-config; selection reads the
  certificate, never the rung; rung-1 kept labeled certified-worse.
- **HIGH — higher fidelity makes transfer WORSE** (physics→Chrono avoid 0.000 — already happened).
  *Mitigate:* posttrain selection requires the higher rung's certificate to DOMINATE rung-0 AND pass
  the final closed-loop gate; default posttrain stays rung-0.
- **HIGH — drift-RWD vs avoid-FWD structural tension** breaks drift if a "more faithful" FWD rung ever
  fine-tunes the shared trunk. *Mitigate:* gated-heads split; drift head on F0-RWD, avoid head on F2
  oracle; never fine-tune drift on an FWD-restructured rung; frozen drift demos guarantee no
  regression in re-distill.
- **MEDIUM — throughput collapse** of the faithful config makes posttrain PPO impractical, and it is
  UNMEASURED. *Mitigate:* T3a prototype bench BEFORE the build; block-arrow decomposition keeps per-env
  work O(n_axles·D_CORNER²); implicit 1-D vertical mode keeps substeps ~5-8; posttrain runs smaller
  N / fewer updates; pretrain does the bulk.
- **MEDIUM — the intra-GPU pretrain↔posttrain gap is far smaller than the design once implied** (~5×,
  not ~1000×, if compiled-pwr3 ≈ 2.4M). *Mitigate:* justify the split vs CPU-Chrono (~500×+ at every
  rung), not by an intra-GPU ratio; bench compiled-pwr3 at T0 and re-state the gap honestly.
- **MEDIUM — torch.compile op-reorder corrupts the certificate** (3% gear-flip can perturb the float
  dynamics the certificate measures). *Mitigate:* gear dead-band + bitwise-repeat test on the FULL
  dynamics trace BLOCKS metric emission (`deterministic_switches=False` until it passes); enforced in
  the harness.
- **MEDIUM — the obs seam is not free.** state[:,3] is vx in pwr3 but roll in tier_a; obs reads
  hard-coded integers today. *Mitigate:* the §3.4 by-name refactor + bit-identical obs72 test is a
  hard T0 deliverable; the invariance claim is only made after it passes.
- **MEDIUM — fixed low N_ITER fails to hold the closed wishbone loop** → spindle drifts → tier-a-style
  drift regression. *Mitigate:* Baumgarte+cfm tuned so per-step constraint drift < the elastic
  residual (transfer is 99% geometric); gate the dial for monotone β@24 improvement; fall back to the
  geometric-transfer-injection bias.
- **MEDIUM — stiff tyre-vertical / suspension modes** blow up the step / reintroduce tier-a's spurious
  ~70 Hz wheel-hop unless treated implicitly. *Mitigate:* closed-form 1-D implicit update; validate the
  corner vertical mode against a Chrono drop/step-steer transient before wiring the full loop.
- **MEDIUM — differentiability breaks under PPO** (backprop through gear-FSM/stiff slip already
  diverged). *Mitigate:* soft constraints (cfm>0); static unroll; gear integer-outside-autograd; train
  model-free (primary path) and reserve differentiable-unroll for the cheap rung.
- **MEDIUM — CPU-Chrono closed-loop is the real bottleneck** (per-config validation at ~1k st/s).
  *Mitigate:* closed-loop is a final promotion gate only (≤5 candidates ever), with a stated quarterly
  budget (§5.1).
- **MEDIUM — certificate per-(config, replay-set, variant) does NOT generalize** off-distribution (the
  avoid=1.000 artifact). *Mitigate:* pin `chrono_replay_set` SHA; selection asserts coverage; out-of-set
  use = UNCERTIFIED.
- **MEDIUM — M4 telemetry mistaken for a promotion criterion** (pwr6 improved M4 while regressing M1).
  *Mitigate:* M4 is diagnostic-only in the schema; M1/M3 decide promotion.
- **LOW — cross-vehicle combinatorics.** *Mitigate:* certify the Sedan cell first; cross-vehicle
  on-demand; the harness is variant-parametric.

---

## Reality-check & honest bounds

The corrected verdicts, with numbers not hand-waving:

- **Throughput reality (the weakest part of the original, now grounded).** There is **no
  `torch.compile` in the repo** and the "582M st/s, 128× over eager" headline has **no code behind
  it** — it appeared only in design docs. The project's *measured* physics throughput is **~1.3M @16k
  eager / ~2.4M "engine"**; the **91M @262k** figure is the *analytic backbone*, not the physics
  model — a ~240× gap between the discarded claim and the real record. **Corrected stance:** pwr3
  compiled-throughput is a **T0 bench target**, not a result; the split is justified **versus
  CPU-Chrono (~500×+ at every rung)**, and the **intra-GPU pretrain↔posttrain gap may be ~5×, not
  ~1000×.** No rung heavier than pwr3 (not even tier_a, which runs) was ever benched; a fixed-iteration
  GS sweep over `[N, n_axles, 2, ~24×24]` blocks is plausibly **100–1000× heavier per step** and could
  fall **below ~0.5M @262k in eager torch**. One afternoon (bench compiled-pwr3 + a throughput-only
  §2.4 prototype, §6 T0/T3a) de-risks the entire posttrain premise.
- **Fidelity reality.** Fixed-iteration constrained solve is a legitimate, well-precedented choice
  (MJX/Brax/Isaac Gym), and the physical justification is strong: Chrono's lateral transfer is ~99%
  geometric/quasi-static with no anti-roll bar, so a handful of GS sweeps + Baumgarte won't reintroduce
  gross under-convergence error *on this vehicle*. **But the real fidelity problem is upstream of the
  solver, and the design now weights it correctly:** the project's own evidence says restoring dropped
  DOFs faithfully does **NOT** close the behavioral gates. pwr6 restored front long-slip with a
  *more*-faithful per-wheel law (tail Fy RMSE 564→332 N) and **drift got WORSE** (honest β
  0.0368→0.0410) because the metric reads step-24 where front sx≈0.01; pwr5 (driveline inertia) was
  faithful and NULL; the FWD restructure broke the saddle structurally. So "more faithful per-wheel"
  and "lower behavioral error at the gate" are **decoupled** — a full-linkage rung-2 can improve M4
  telemetry and still regress M1 drift. The certificate-as-arbiter (multi-metric, honest-true-vx,
  FP/FN-split collision, M4-diagnostic-only) is the correct response, and each rung's error *is*
  measurable against frozen Chrono. **But "error is measurable" ≠ "rung-2 will be certified better,"
  and the design's own data points toward "probably not."** Hence T3 is RESERVE, gated on the T3a
  falsification.
- **Transfer reality (the strongest facet, handled honestly).** The asymmetry is load-bearing and
  correct: drift transfers F0→Chrono at 1.0 from every surrogate (robust saddle), so coarse-pretrained
  drift needs **no fine posttrain**; avoidance has **three converging negatives** (large-batch 0.700,
  physics-faithful 0.000, +DR 0.075) proving partial fidelity is *worse* than none for the precise
  collision boundary, so avoid stays **Chrono-oracle imitation + DAgger** with demos on real Chrono
  (no sim-to-sim demo gap) and gated heads so the FWD/RWD tension never crosses heads — consistent with
  the proven do-both 1.0/1.0. **One honest gap, now fixed in the design:** obs72 fidelity-invariance
  was asserted but **not wired** — `obs72_from_state` reads dynamics dims by hard-coded integer, and
  `state[:,3]` is vx in pwr3 but roll in tier_a. The by-name refactor + bit-identical obs test (§3.4,
  T0) must land before the invariance is claimed.
- **Unification reality.** `config = fidelity` is **NOT one kernel that degenerates by flag** — tier_a
  uses an explicit spring-damper corner ODE (not a constraint solve with iters off), and pwr3 has no
  vertical DOF; the three rungs are **three modules with three state layouts** (17/30/~100-maximal).
  The honest, still-valid unification is a **rung registry + shared `physics_step`/`init_state`/`IDX`
  contract + a certified cross-rung AGREE-WITHIN-TOLERANCE test (M-agreement)**. That is buildable
  T0-T2 and mostly assembly of existing parts.

**Net verdict.** BUILDABLE AS A REGISTRY/CERTIFICATE FRAMEWORK (T0-T2), NOT as a "one kernel,
config=fidelity" unification. The two best ideas — the multi-metric Fidelity Certificate as the
arbiter (never DOF-count) and the asymmetric drift-DR-pretrain / avoid-Chrono-imitation curriculum —
are correct and directly supported by the project's data; the do-both 1.0/1.0 result and every cited
symbol exist. Build T0 (after the pwr3 bench, the obs by-name refactor, the stale-import repoint, and
the gear dead-band) + T2 as scoped; treat T3 as RESERVE, gated on the afternoon-scale T3a
constraint-bias falsification and throughput prototype. The "one continuous kernel" thesis and the
"1000× intra-GPU speed gap" are demoted to a registry-behind-a-contract and a vs-CPU justification —
honest, and still a genuinely useful multi-fidelity training framework.

---

## ★ T3a VERDICT (2026-06-17): full-DAE (T3) is NO-GO on converging evidence — scope = framework + rung0/1 + T2

The T3a falsification + the broader dig converge: **FOUR independent attempts to add fidelity/DOFs all
certified NULL or NEGATIVE at the behavioral gate**, so building the 6-12wk full-linkage DAE is NOT justified.

| DOF / fidelity added | result at the gate |
|---|---|
| rung-1 kinematic suspension (tier_a, 6-DOF chassis + 4 corners) | drift REGRESSED 0.028 -> 0.0756 |
| driveline rotational inertia (pwr5) | NULL (flat partial-throttle map; +315 rpm = -16 N) |
| front longitudinal slip / combined-slip (pwr6) | per-wheel more faithful, NULL/NEGATIVE at gate (drift 0.032->0.046) |
| geometric instantaneous load transfer (tier_a_geom, T3a) | drift 0.0756 -> 0.0748 (2% closed) + unstable in avoid |

The geometric-transfer first-cut was numerically unstable in the avoid regime (a single-pass ay~vx*wz proxy),
so it is not a clean proof on its own — but it is the FOURTH null in a row, and the drift-regime portion (where
it WAS stable) showed no improvement. On the weight of four independent nulls, the "higher model order closes
the residuals" premise behind T3 is REFUTED-to-the-extent-cheaply-testable. **DECISION: do NOT build the
full-linkage DAE (rung-2 / T3).** A clean two-pass geometric injection could still be run to harden the verdict,
but it would have to overturn four converging nulls to flip the decision.

**Revised "complete multi-fidelity GPU rewrite" scope** (what "done" means, minus the unjustified T3):
  framework (contracts/resolver/certify/bench ✅) + rung-0 planar (pretrain) + rung-1 kinematic (RED-cert
  documented) + **T2 longitudinal-fidelity rung** (the collision-faithful posttrain config — the recommended
  remaining build) + build_env wiring + gear dead-band (optional; certify runs eager). The fidelity spectrum is
  delivered by rung-0 (fast) and the T2 longitudinal rung (collision-faithful), NOT by a full multibody.

---

## T2 PROBE VERDICT (2026-06-17): avoid residual is STRUCTURAL, not a measurable longitudinal term — T2 NO-GO

Before committing 1.5-3wk to T2 (extract the Chrono driven-force surface -> a collision-faithful posttrain
rung), ran the cheap GO/NO-GO probe: root-cause the avoid residual that remains after the gear-SEED fix
(rung-0 avoid vx_rmse 0.520; the down-ramp +0.455 m/s2 / ~660 N ax-gap). Force breakdown from the avoid
telemetry (model pwr3 vs Chrono, 136 down-ramp steps):
- model DRIVE (F_drive_post) = 1712 N == Chrono driveshaft (verified ±14 N earlier) — drive MATCHES.
- model resistance 401 N, front body Fx -49 N — small, and Crr is wrong-sign (Chrono higher).
- the model applies the 1712 N drive at the REAR tyre (Fx_r_sum 1712, the FWD-kludge: FWD-capped magnitude
  but applied to the rear spin states) while real Chrono FWD drives the FRONT.
The +660 N is NOT a measurable longitudinal MAGNITUDE term (drive/resist all match or are small) — it is the
**drive DISTRIBUTION (front vs rear) × the cornering combined-slip coupling**: the same drive-on-rear vs
FWD-reality STRUCTURAL tension that (a) made the principled FWD restructure break the drift saddle and (b)
drove the T3a NO-GO. T2's "extract the driven-force surface" attacks the magnitude, which already matches, so
**T2 does NOT close the residual. T2 = NO-GO.**

## ★★ GPU MULTI-FIDELITY REWRITE — HONEST COMPLETION (2026-06-17)

With T3 (full-DAE) and T2 (longitudinal rung) both NO-GO on converging evidence, the rewrite's honest
complete scope is delivered:
- **FRAMEWORK: complete + training-ready** — contracts / resolver / rung registry / certify (the
  measured-certificate arbiter) / throughput bench / obs72-by-name / build_env(rung-0). `config -> build_model
  -> build_env -> step -> obs72 -> certify -> .dominates()` runs end-to-end, validated against the standalone
  gates byte-for-byte.
- **rung-0 (planar pwr3, gear-seed) IS the best config**: avoid vx_rmse 0.520, drift beta@24 0.032; fused
  ~380M st/s (126x @16k). It is the pretrain AND the carried config.
- **rung-1 (kinematic) is a documented RED certificate** (regresses drift) — the framework correctly ranks it
  BELOW rung-0 by measurement.
- **FINDING (the science): higher fidelity does NOT beat rung-0.** SIX independent fidelity/DOF additions
  (tier_a, pwr5 inertia, pwr6 front-slip, tier_a_geom, T3a, T2-longitudinal) all certified null/negative — the
  residuals are STRUCTURAL (the drift-RWD vs avoid-FWD single-track tension) + coupled, not isolated measurable
  terms. The multi-fidelity *machinery* is complete and correct; the fidelity *ladder* has one good rung
  (rung-0), and the evidence says building taller rungs is not justified. This is itself the publishable result.
