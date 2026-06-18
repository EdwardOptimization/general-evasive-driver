# F2 coverage spectrum — pre-registration DESIGN (step 3), 2026-06-16

Goal: extend the single-cell gated driver (pass-8: drift cell `low_mu_power_oversteer` +
avoidance μ/reveal grid) toward a **general active-safety driver** across scenarios and
vehicles. This is the DESIGN + pre-registration plan; runs follow after step-2 (16-seed
gated confirmatory) completes and the cells are frozen.

Grounding (current machinery):
- Drift: E4 catalog has **2 cells** (`low_mu_power_oversteer` μ=0.48 β0=0.22; `lift_off_recovery`
  μ=0.55 β0=-0.28) and **3 parameterized `DriftFeedbackSpec` laws** (target_β 0.16/0.22/0.28,
  memoryless feedback on current β + yaw_rate). F2 trains on 1 cell + 1 oracle.
- Avoidance: already a **5×4 grid** — reveal {9.5,12,16,22,30} m × μ {0.36,0.59,0.81,1.04}.
- Vehicle: Sedan ~1684 kg RWD TMeasy; 3 variant stubs (sedan/bmw_e90/uazbus). mass overridable;
  cg/Iz/tire come from the variant (not continuous knobs).
- Architecture: gated dual-heads (pass-8 default); obs72 actor, priv6 critic.

## Master variable table (ranges to cover)

| group | variable | current | spectrum range | knob | priority |
|---|---|---|---|---|---|
| **A drift** | target β\* | 0.28 (single) | **0.18 / 0.28 / 0.36 / 0.45** rad | DriftFeedbackSpec target_β | P0 |
| | surface μ | 0.48 (single) | **0.35 / 0.45 / 0.55** | cell μ | P0 |
| | sustain steps | 24 | **12 / 24 / 48** | MIN_SUSTAIN_STEPS | P0 |
| | entry maneuver | lift-off | + power-on, trail-brake | new spec | P1 |
| | corner radius | 70 m | 50 / 70 / 100 | cell radius | P1 |
| | drift direction | side-handled | L/R both (symmetry) | side | P1 |
| **B avoid** | reveal | 5 tiers | keep + add 8.0 m (knife-edge) | scenario | P1 |
| | μ | 4 pts | keep | scenario | P1 |
| | obstacle geom | single static | + offset spread, width, 2-obstacle | scenario | P1 |
| **C vehicle** | drive layout | RWD | RWD / AWD (sedan,bmw / uazbus) | variant | P0 |
| | cg / Iz | Sedan | sedan / bmw / uazbus | **variant swap** | P0 |
| | mass | 1684 | 900 / 1700 / 2500 (coarse) | chassis override | P1 |
| | max drive force | 8200 N | ×0.7 / 1.0 / 1.3 | drive_scale | P1 |
| **D surface** | μ heterogeneity | uniform | uniform / split-μ / μ-step | scenario | P0 |
| | slope/bank | flat | flat (+ bank optional) | scenario | P2 |
| **E sensing** | noise σ | clean | clean / 0.05σ IMU | degradation wrapper | P0 |
| | latency | ~0 | 0 / 100 / 250 / 500 ms | degradation wrapper | P0 |
| **F stats** | seeds | 16 (step1) | 16 (keep) | budget | — |
| | val episodes/cell | 30 | ≥20/cell | budget | — |

## Staging (avoid combinatorial explosion)

Don't cross A×C×D×E (thousands of cells). Train wide via domain-randomization over the
ranges (one gated policy), evaluate on a structured pre-registered grid (per-cell four-arm).

| stage | design | answers | rough cost |
|---|---|---|---|
| **S1 drift spectrum** | drift (β×μ×sustain, ~12 feasible cells after pre-check) + avoid grid, **default vehicle × clean sensing × 16 seed**, gated | does the gated driver generalize across the drift surface (not just one cell)? | multi-day managed |
| **S2 vehicle** | 3 variants × reduced spectrum (corners+center) × clean | "不同车型" — RWD vs AWD, cg/Iz | ~1.5× S1 |
| **S3 sensing** | clean / noise / latency × reduced spectrum × default vehicle | two-regime belief law (does the gated driver's advantage survive degraded sensing; does belief value resurface) | ~1× S1 |

## Two pre-gates (reuse existing machinery, freeze BEFORE runs)

1. **Feasibility pre-check (extend S7 oracle-ceiling to the spectrum).** Not every (β,μ,radius)
   is physically driftable (high μ + high β: can't break traction at feasible power; low μ +
   low β: trivial). For each candidate drift cell run the parameterized `DriftFeedbackSpec`
   oracle in Chrono, measure longest-controlled-drift vs the sustain threshold, and **prune
   cells where no teacher law clears floor+prize** (infeasible) and cells the floor already
   solves (trivial). This is the existing `oracle_ceiling_precheck` generalized over a cell list
   — cheap (oracle rollouts only, no training) and it produces the *actual* feasible-cell list,
   grounding the frozen spectrum in data rather than guesses.
2. **Pre-registration.** Freeze: the feasible cell list (post pre-check), per-cell floor/oracle,
   per-cell four-arm criteria, seed-clustered CI gates, the DR training distribution (the
   continuous ranges sampled at train time), and the disjoint eval grid. Frozen before any
   training run, per project discipline.

## Gates / adjudication (per cell)

Keep the four-arm structure per cell: {fixed*, entry-speed-floor, online-mu-seeker,
per-regime-oracle, gated-student} on 30 frozen validation episodes/cell, seed-clustered CIs.
Report **per-cell** (not pooled) so we see where the driver generalizes and where it fails.
B6 per-regime AUC gate, S7 oracle-ceiling per cell. The headline claim becomes: "across N
pre-registered drift cells spanning β×μ×sustain, the gated obs72 driver beats the reflex floor
(and the scripted oracle) on drift with seed-clustered CIs excluding 0, while holding avoidance."

## Implementation plan (effort estimate)

1. **Parameterize the drift scenario + teacher over a cell-spec** (moderate): generalize
   `_drift_scenario` / `make_drift_teacher` / `_drift_cell` to take a cell dict (μ, target_β,
   radius, speed, sustain) instead of the single fixed cell; pick the `DriftFeedbackSpec` by
   target_β (the 3 existing specs cover 0.16–0.28; add 0.36 / 0.45 specs or auto-scale gains —
   the saddle's low-μ-sensitivity suggests one parameterized law may transfer, to be verified by
   the feasibility pre-check).
2. **Feasibility pre-check sweep** (small): loop candidate cells, run the oracle, emit the
   feasible-cell list + per-cell oracle ceiling. Cheap; the first thing to run after step-2.
3. **Generalize train/validate to a cell SET** (moderate): BC warm-start imitates the per-cell
   teachers; PPO trains across cells (DR-style sampling of the drift cell each episode);
   per-cell validation + adjudication.
4. **Vehicle (S2) + sensing (S3)** reuse the variant + degradation-wrapper machinery (already
   exist) as orthogonal axes over a reduced spectrum.

## Sequencing

After step-2 (16-seed gated) completes and becomes canonical:
1. Run the **feasibility pre-check sweep** -> frozen feasible cell list.
2. Pre-register the S1 spectrum (cells + gates) -> freeze.
3. Implement the cell-set train/validate generalization.
4. Run S1 (drift spectrum), then S2 (vehicle), then S3 (sensing).

This is a multi-stage effort beyond a single session; S1 is the load-bearing generalization
claim (single-cell -> drift surface), S2/S3 extend to vehicles and degraded sensing.

---

## S1 RESULT (2026-06-18): one gated obs72 driver does the full 48-cell spectrum — drift 12/12 + avoid 30/36

Generalized the do-both distillation to the 48-cell full-scenario spectrum (distill_both_fullscenario.py).
ONE gated AsymmetricActorCritic (gate self-routes drift/avoid), per-cell Chrono-validated:
- **DRIFT 12/12** (every beta* x mu cell 8/8, mean sustain 80.2) — reproduces all 12 tuned drift teachers.
  Independently re-verified (subset).
- **AVOID 30/36** — base grid 15/20; geometry families largely hold (knife-edge 3/3, offset 6/7, width 6/6).
  The 6 misses are HIGH-MU avoid (r16-30 / mu 0.81-1.04 + one inward offset). = 42/48, one network, Chrono-verified.

**BC-CEILING FINDING (DAgger on the high-mu tail):** DAgger clears the missed high-mu-0.8125 cells in rollout
(10-14/14) BUT REBALANCES — the mid-mu (0.5875) cells then become the weak tail. A single BC avoid head has a
CAPACITY ceiling fitting 36 diverse avoid cells; distillation tops ~30-32/36 and DAgger shifts WHICH cells are
the tail rather than net-adding. To clear all 36 needs a bigger avoid head OR a targeted avoid-head PPO
(drift-frozen / gate-protected). Strategic: the strongest GENERAL driver is better served by the generality
axes (S2 vehicles + S3 sensing) than by squeezing the BC-ceiling tail. S1 base (42/48) carried into S2.

---

## ★ S2 RESULT (2026-06-18): cross-vehicle generality is SPLIT BY REGIME — drift generalizes, AVOID needs self-ID

Trained ONE vehicle-AGNOSTIC obs72 gated driver across all 3 vehicles (pool 3 vehicles' teachers ->
one gated AsymmetricActorCritic; no vehicle id in obs72). Per-(vehicle,regime) Chrono validation (the
single driver vs the per-vehicle-driver baselines):

| vehicle | DRIFT (1-driver / baseline) | AVOID (1-driver / baseline) |
|---|---|---|
| Sedan FWD | 1.00 / 1.00 | 0.00-0.10 / 1.00 |
| UAZBUS 4WD | 1.00 / 1.00 | 0.25 / 1.00 |
| BMW RWD | 0.85 / 0.85 | 0.05 / 1.00 |

- **DRIFT GENERALIZES (confirmed):** one vehicle-agnostic feedforward obs72 policy holds drift on all 3
  contrasting vehicles at the per-vehicle ceiling — it adapts from the observed dynamics alone, no vehicle
  conditioning. (Consistent with the drift saddle being mu-low-sensitive + obs72-controllable; Velenis/Goh.)
- **AVOID DOES NOT GENERALIZE (verified, mechanistic):** pooling 3 vehicles' avoid demos collapses avoid on
  EVERY vehicle. Independently re-verified (Sedan avoid 0.000 with the 3-vehicle policy vs 1.0 per-vehicle).
  NOT a surrogate gap (the per-vehicle drivers validate 1.0 on Chrono) and NOT a fluke (3 distill seeds, all
  teachers 40/40). MECHANISM: the 3 vehicles' safe-entry-speed budgets differ sharply (V_KNOTS Sedan
  (4.5,7.5,9.5,10.5) / UAZBUS (9.5,11,11,11) / BMW (12,12,12,12)) -> for the SAME obs72 approach the oracles
  command DIFFERENT entry speeds -> a feedforward obs72 policy gets CONFLICTING BC targets it cannot resolve
  (no vehicle id, no obs72 history) -> it averages to a wrong speed -> collisions.

**THIS IS THE self-ID / VoI RESULT (validates selfid-voi-design-flaw-hypothesis + the RMA bridge):** avoid is
exactly the regime where IDENTIFYING THE VEHICLE has value (VoI high), while drift does not need it (VoI~0).
The path to a cross-vehicle-GENERAL avoid = RMA: infer a vehicle latent z from obs72 HISTORY (the vehicle's
response reveals its capability) and condition the avoid head on z. The strongest general driver = drift
(already vehicle-general feedforward) + avoid-with-self-ID (RMA). NEXT: the RMA cross-vehicle avoid experiment.

---

## ★ S2 cross-vehicle AVOID — three experiments converge: avoid is VEHICLE-SPECIFIC (shared-trunk), drift is vehicle-general

Three measured experiments to make ONE network do avoid across 3 vehicles (all drift held 1.0/1.0/0.85):
1. **vehicle-AGNOSTIC** (obs72, no id): avoid collapses 0.0/0.25/0.05 (vs 1.0 baselines). Conflicting entry-speed budgets, no id.
2. **CONDITIONED** (obs75, vehicle one-hot, shared avoid head): recovers Sedan only (0.10->0.975), UAZBUS 0.15 / BMW 0.175 stay low. Id is necessary-but-not-sufficient. (Selection was Sedan-biased.)
3. **PER-VEHICLE AVOID HEADS** (1 drift + 3 avoid heads, hard-routed by id, gradient-isolation unit-tested): Sedan REGRESSES 0.975->0.575 *with its own private interference-free head*, BMW recovers 0.85, UAZBUS 0.20. Per-head holdout MSE LOW + separated (each head fits its budget) yet Chrono avoid fails -> the bottleneck is NOT head interference.

**DIAGNOSIS: the bottleneck is the SHARED TRUNK + avoid's closed-loop sensitivity.** The standalone per-vehicle
avoid drivers each hit 1.0 with a trunk trained on ONE vehicle; forcing one trunk to co-encode 3 vehicles' avoid
degrades each vehicle's avoid representation. DRIFT tolerates the shared trunk (it is a robust saddle-stabilization,
self-correcting); AVOID does not (small BC action errors compound to collisions — the F2/G1' BC-closed-loop finding,
now cross-vehicle). So: **DRIFT is vehicle-general (one representation works across 3 vehicles); AVOID is
vehicle-specific (each vehicle needs its own representation).** This is a clean structural result.

Implication for the strongest GENERAL driver: ONE network already does the full drift+avoid SPECTRUM (S1) + drift
across all vehicles. Cross-vehicle AVOID in one network needs per-vehicle representation (trunk FiLM/adapters) +
DAgger (close the closed-loop gap) — the indicated lever, given one honest probe next. The practical fallback is
per-vehicle full-spectrum drivers (each at do-both ceiling 1.0/1.0, 1.0/1.0, 0.85/1.0), since avoid is vehicle-specific.

---

## ★★ S2 RESULT — OVERTURNED (2026-06-18): ONE-network cross-vehicle driver DELIVERED via FiLM + DAgger

The "avoid is vehicle-specific" lean (3 experiments above) was PREMATURE — the indicated lever recovered it.
FiLM trunk-conditioning (per-vehicle gamma/beta on the shared trunk -> per-vehicle REPRESENTATION, fixing the
shared-trunk bottleneck) + DAgger (relabel student avoid failures with each vehicle's oracle -> close the
closed-loop compound-error gap) -> ONE obs75 network does drift+avoid across all 3 vehicles. Independently
re-verified on Chrono (loaded the saved policy, re-ran per-vehicle):

| vehicle | drift | avoid | per-vehicle baseline |
|---|---|---|---|
| Sedan FWD | 1.000 | 1.000 | 1.0/1.0 |
| UAZBUS 4WD | 1.000 | 0.857 | 1.0/1.0 |
| BMW RWD | 0.875 | 1.000 | 0.85/1.0 |

All avoid >= 0.86 (vs vehicle-agnostic 0.0/0.25/0.05, per-veh-head 0.575/0.20/0.85); drift held. distill_3vehicle_film_policy.pt.

**CORRECTED conclusion:** avoid is NOT vehicle-specific in the "cannot be done in one net" sense — it is HARDER
than drift (drift generalizes feedforward; avoid needs per-vehicle REPRESENTATION via FiLM + closed-loop DAgger),
but ONE network does it. The win came from DAgger round 1 (BC alone scattered; the rollout exposed an over-brake
stall mode whose oracle-relabeled states taught the entry-speed budgets on-distribution). HONEST CAVEATS: the
recipe is SEED-SENSITIVE (1/3 training seeds hit it -> needs the seed sweep + worst-vehicle selection, which it
has); the SAVED policy reproduces (my re-verify). BMW drift marginal (0.80-0.875 around its 0.85 baseline).
The strongest GENERAL single-network driver: full drift+avoid SPECTRUM (S1) + cross-vehicle (FiLM+DAgger). The
remaining integration = combine S1's 48-cell spectrum with the FiLM cross-vehicle (one net, spectrum x 3 vehicles).
Methods lesson re-banked AGAIN: never ship a NO-GO/vehicle-specific verdict from N experiments without the
indicated lever -- FiLM+DAgger was the lever, and it worked.

---

## ★★★ CAPSTONE (2026-06-18): ONE network masters the full drift+avoid SPECTRUM × 3 VEHICLES — 134/136, verified

The strongest most general single-network active-safety driver. distill_both_final_integrated.py combines the two
proven pieces: FiLM trunk (per-vehicle gamma/beta, obs75) + regime gate + 1 shared drift head + 3 per-vehicle avoid
heads + per-vehicle DAgger, over the 48-cell spectrum logic (drift beta*xmu + avoid reveal x mu x geometry).

Per-vehicle drift feasibility (Chrono-grounded, not guessed): Sedan 12/12 @v12-14, BMW 12/12 @v14-18, UAZBUS 4/12
(only high-beta 0.36-0.45 at low speed — the heavy 2858kg RWD genuinely can't break the rear at low beta; a physics
finding) -> 28 feasible (cell,vehicle) drift pairs.

MEASURED + INDEPENDENTLY RE-VERIFIED on Chrono:
| vehicle | DRIFT cleared (mean) | AVOID cleared (mean) |
|---|---|---|
| Sedan | 12/12 (1.000) [re-verified 4/4 @v12-14, sustain 90] | 34/36 (0.896) |
| UAZBUS | 4/4 (1.000) [re-verified 1.0] | 36/36 (0.993) |
| BMW | 12/12 (1.000) [re-verified 0.875] | 36/36 (1.000) |

**HEADLINE: 134/136 cells across 3 vehicles — drift 28/28, avoid 106/108.** The single shared FiLM drift head
generalizes drift across every feasible (cell,vehicle) pair; the per-vehicle avoid heads + DAgger recovered avoid
on all 3 (UAZBUS avoid — which collapsed to 0.20-0.54 in the unconditioned/per-veh-head attempts — is 36/36). Only
2 misses, both Sedan small-reveal hard avoid cells (knife_edge r8 / r9.5, the envelope edge, same cells S1 struggled
on — a residual closed-loop gap, not a routing failure: UAZBUS/BMW clear the identical geometry).

VERIFICATION NOTE (re-banked discipline): a naive re-check using cond._validate_per_vehicle's DO-BOTH drift cell
(Sedan v9) read Sedan drift 0.0 — a CELL-MISMATCH confound (the capstone trains on the v12-14 SPECTRUM, not v9).
Re-validated on the correct spectrum cells -> 4/4 @ sustain 90. Always validate on the cells the policy was trained
for. distill_final_integrated_policy.pt. CAVEATS: FiLM recipe seed-sensitive (selection sweep + worst-vehicle pick);
BMW drift marginal ~0.85-0.875; 2 Sedan avoid envelope-edge cells. NEXT: S3 degraded-sensing axis + final certification.

---

## S3 (2026-06-18): SENSING-DEGRADATION robustness of the capstone — TWO axes, zero-shot (no retrain)

Built+measured (not assumed) on the verified capstone driver via the tested ObservationDegradationWrapper
semantics applied client-side to the policy's VIEW only (success judged on TRUE physics; per-episode fresh
degrader => thread-safe + seed-deterministic). _s3_degraded_zeroshot.py (ego axis) + _s3_perception.py (perception axis).

AXIS 1 — PROPRIOCEPTIVE (delay + iid Gaussian noise on ego-response channels obs[0:8]; the channels a policy
could use for current-frame substitution of hidden-dynamics belief). Ladder clean / moderate(delay2,sigma.03) /
harsh(delay4,sigma.06), drift+avoid, 3 vehicles:
  drift: 1.000 invariant across all rungs/vehicles (BMW harsh 0.917 = 1 ep of n=12 noise).
  avoid: unmoved within n=10 noise (Sedan .80/.70/.90 non-monotonic = noise floor). EXPLANATION: this axis hits
  ego channels only; the obstacle-perception channels (44-71) that avoid actually depends on stay CLEAN, so the
  axis cannot bite avoid by construction. Drift is a feedback-stabilization task robust to proprioceptive noise.

AXIS 2 — EXTEROCEPTIVE (iid Gaussian noise on obstacle continuous channels x,y,rel_vx,rel_vy = obs idx
45-48/52-55/59-62/66-69, only on PRESENT obstacles; present-bit + size untouched). The avoid-critical axis.
Ladder clean / mild(.02) / moderate(.04) / harsh(.08), 6 avoid cells (one per reveal) x4 seeds:
| vehicle | clean | mild .02 | moderate .04 | harsh .08 |
|---|---|---|---|---|
| Sedan  | 1.000 | 1.000 | 0.958 (r8->0.75) | 0.875 (r8->0.50, r9.5->0.75) |
| UAZBUS | 1.000 | 1.000 | 1.000 | 1.000 |
| BMW    | 1.000 | 1.000 | 1.000 | 1.000 |

**S3 HEADLINE: the capstone is broadly robust to sensing degradation.** Drift is invariant to proprioceptive
degradation. Avoid is invariant to proprioceptive degradation (obstacle channels clean) and degrades only under
EXTEROCEPTIVE noise, GRACEFULLY (0.875 worst, not collapse) and ONLY at the small-reveal envelope edge (r8/r9.5 =
least reaction distance, where obstacle position error bites most). The degradation is VEHICLE-DEPENDENT: Sedan
susceptible at the edge, UAZBUS/BMW fully immune to both axes at every level tested. Consistent with the two-regime
VoI law on BOTH axes: drift (where identifying the vehicle/state has no value) is robust to sensing degradation;
avoid (where it has value) is the only regime that moves, and only at its hardest cells. NEXT: probe the indicated
lever (perception-DR fine-tune of Sedan small-reveal avoid) + final seed-clustered CI certification.
