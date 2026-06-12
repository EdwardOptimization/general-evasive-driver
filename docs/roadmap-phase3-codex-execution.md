# Phase-3 Execution Roadmap (Codex-ready, 2026-06-12)

## Status

- kind: ordered execution queue for autonomous/Codex sessions. The contract
  lives in `AGENTS.md` + `~/.agents/skills/autodrift-research-harness/SKILL.md`
  (Phase-2 version); criteria definitions live in
  `docs/research-plan-phase2-capability-boundary-tracking.md`; live progress
  in `docs/current-status.md`. This file is the WHAT-NEXT list.
- execution rule: take the lowest-numbered OPEN unit whose dependencies are
  met; register it as the next M-milestone per the playbook; never run two
  units that write the same files concurrently. Update the unit's status
  line here and the ledger in `docs/current-status.md` when done.
- PI checkpoints are hard stops: mark the unit blocked-on-PI and move to the
  next independent track; do not self-approve.
- default path note: the C5 spread formulation was rejected by pricing
  (`docs/c5-reflex-degradation-2026-06.md`), and the A1 S4-lateral rider was
  also negative (`docs/m3220-a1-s4-lateral-spread-rider-pricing.md`). The
  default forward path is therefore C5'-main (structural-ceiling prize).
  CP-1 conditionally opened C1, but M3238 has since blocked the local
  selector/interface route pending PI or new nonlocal-interface pricing.
  M3231 satisfied the D1b direction-positive precondition for CP-2, but C3
  remains blocked on C2 and PI CP-2. M3239/M3240 completed B1b and rejected
  the current moving-crosser formulation (0/4 cells qualified, all rows
  reflex-solvable). M3241/M3242 completed B2b and rejected the current
  high-speed formulation (0/6 cells qualified; two weak 0.125 pockets with
  CI lower bound 0; scale-aware fixed_star/v4_pertuned 46/48). M3243 recorded
  the temporary blocked-dependency stop, then PI reopened C1 as C1-v3:
  residual RL on the frozen v4 reflex base. M3244 completed the 1024-step
  C1-v3 residual smoke and passed all quick gates. M3245 completed the
  preregistered <=1 h stage-1 run and failed the frozen gate: 0/3 cells
  passed, with v4+residual below `v4_pertuned` in every qualified cell. C3
  scale-up is not admitted from this result; further C1-v3 work requires a
  synthesis or PI route decision. CP-2 remains budget-only in principle
  because D1b is already direction-positive, but there is no admitted >1 h
  run to approve from M3245.

## Track A — pricing/science completion (CPU only, zero training)

### A1. S4-lateral spread rider [DONE: M3220]
- question: can vehicle-population spread move the handling-limit feasible
  boundary when it hits the LATERAL channel (cg position lf/lr, inertia Iz)
  — the one channel the rejected mass/brake spread never touched?
- method: extend `scripts/feasibility_audit/c5_reflex_degradation.py` with a
  lateral-spread tier (direct VehicleParams construction: lf/lr shifts
  beyond +-0.12 m, Iz 0.6-1.6x, optionally wheelbase classes); same four
  arms, same frozen criteria pattern (prereg first; new SEED_BASE).
- acceptance: pre-registered: (per-tuned - fixed) and (per-tuned - RLS) per
  cell with paired CIs; either verdict feeds the papers.
- template: `experiments/feasibility_audit/c5_prereg.json` + the C5 doc.
- result: `docs/m3220-a1-s4-lateral-spread-rider-pricing.md` completed the
  cg/Iz rider. Verdict: 0/4 cells qualified; S4L/T-limit prize was +0.007
  with paired CI95 [-0.014, 0.028]. Current-sim lateral spread does not rescue
  the original C5 spread mechanism; this does not cover load transfer,
  tire-curve shape, wheelbase classes, or Chrono multi-vehicle dynamics.

### A2. Obs-normalization audit [DONE: M3221; blocker found]
- question: how far do the nominal-vehicle normalization constants (vx/20,
  ay/15, 80 m boundary lookahead) shift the obs distribution across the
  population envelope, and what rescaling keeps channels in-range?
- method: zero-rollout where possible — sample population instances, drive
  scripted profiles, record per-channel obs ranges/saturation rates vs the
  nominal car; propose (do not yet apply) a normalization scheme.
- acceptance: per-channel saturation/shift table + a frozen recommendation;
  coverage-map risk item 1 closed.
- result: `docs/m3221-a2-obs-normalization-audit.md` completed the audit.
  Verdict: population or high-speed training remains blocked on a follow-up
  normalization/preview implementation. Main failures: `road_y/20` saturated
  on curved far-boundary points; `vx/20`, `vy/12`, `ax/15`, and `ay/15`
  saturate in high-speed profiles; obstacle `rel_vy/12` saturates with
  ego-relative obstacle mode. No normalization was applied in M3221.

### A3. C5' target consolidation on C5-F1 [DONE: M3222; gates Track C]
- question: re-confirm the structural-ceiling gap (oracle - per-tuned,
  measured +0.16-0.21 at T-limit) on the curvature-compensated C5-F1 family
  with hardened seeds (>= 10 validation seeds/cell), and freeze the RL
  target cells + judging prereg (four arms, engineering-only).
- acceptance: gap CI excluding 0 in >= 3 T-limit cells on the re-measured
  panel; frozen `experiments/feasibility_audit/c5prime_prereg.json` naming
  target cells, floors, per-instance oracle protocol.
- result: `docs/m3222-a3-c5prime-target-consolidation.md` completed the
  fresh-seed A3 consolidation. Verdict: C5-prime target confirmed by the
  frozen rule, with 3/4 T-limit cells qualifying. S1/S2/S3 had oracle -
  pertuned gaps +0.1597/+0.2153/+0.1736 with paired CI95 lower bounds > 0;
  S0 was positive but below the +0.15 effect-size bar (+0.1389).
- **CP-1 (PI checkpoint)** after A3: PI confirms the C5' target before
  Track C training begins.
- **CP-1 disposition (PI, 2026-06-12): conditional approval, option 1.**
  C1 opens immediately (current-sim, per the frozen c5prime_prereg). In
  parallel, unit D1b (Chrono-native oracle pricing) must run; **CP-2 gains
  the precondition "D1b direction-positive"** on top of the budget
  confirmation. Rationale: A3 confirms the prize in current-sim; the D1
  tail-replay reversal leaves the prize's high-fidelity validity unpriced,
  and this program's standing rule is price-before-train.

## Track B — env engineering backlog (coverage-map priority order)

Specs: `docs/data-coverage-map-2026-06.md` (priority list + gap rows).
Each unit: implementation + loud-validation + tests + a smoke measurement
demonstrating the new axis, registered as a milestone. No training claims.

### B1. Moving obstacles [DONE: M3223]
- per-step obstacle kinematics (constant-velocity crosser first), collision
  geometry, feasibility-label re-derivation under dynamic geometry,
  observation-slot rel-v semantics un-zeroed BEHIND a config flag (legacy
  zero-rel-vel contracts untouched; grep list in the coverage map row).
- acceptance: deterministic replay; labels re-derived; legacy validators
  green; smoke panel with a scripted controller.
- result: `docs/m3223-b1-moving-obstacle-kinematics-smoke.md` completed the
  flagged constant-velocity crosser implementation. The default remains
  static; `obstacle_relative_velocity_mode="zero"` stayed exact-zero in all
  smoke frames; dynamic labels carry obstacle lateral velocity and predicted
  lateral offset at arrival; deterministic replay passed 4/4 seeds.

### B1b. Moving-obstacle pricing [DONE: M3239 smoke + M3240 full negative]
- question: does the constant-velocity crosser axis (built in B1/M3223)
  create type-(b) regions — per-instance oracle succeeds, best
  reflex-family arm fails — via the timing/prediction demand that
  single-frame reactive control cannot meet?
- method: scenario panel on the flagged moving-obstacle axis (crosser
  speed x reveal x geometry; C5-F1 placement discipline); four arms per
  the C5 pricing pattern — fixed reflex (one global retune allowed, the
  fixed* convention) / RLS-retuned / per-instance-tuned / per-instance
  oracle (CEM); feasibility labels re-derived under dynamic geometry (B1
  delivered this); oracle-infeasible rows excluded from the denominator.
  Prereg first, new SEED_BASE, managed run.
- acceptance: pre-registered (oracle - per-tuned) per cell with paired
  CIs; gap >= 0.15 CI-excluding-0 in >= 2 cells => a new priced prize
  (Track C extension candidate, post-CP-2); either verdict feeds papers.
- result: `docs/m3239-b1b-moving-obstacle-pricing-smoke.md` completed the
  quick protocol smoke. `docs/m3240-b1b-moving-obstacle-pricing-full.md`
  then completed the full panel and rejected the current B1b formulation:
  0/4 cells qualified, oracle-minus-pertuned gap was 0.0000 in every cell,
  oracle solvability was 1.0, and fixed_star/v4_rls/v4_pertuned all succeeded
  32/32. All rows were `aeb_feasible`; the moving-crosser axis as priced here
  does not create a type-(b) timing/prediction prize. Any later
  moving-obstacle hardening requires a new preregistration.

### B2. > 20 m/s speed domain [DONE: M3224]
- scenario configs to 36 m/s; preview/normalization per A2 recommendation;
  feasibility labels at high speed; smoke panel.
- result: `docs/m3224-b2-high-speed-domain-normalization-preview-smoke.md`
  completed the non-default high-speed observation/preview profile. The legacy
  fixture exposed the old blocker (`ego_vx` max abs 1.800, fixed preview
  1.111 s), while the scaled 36 m/s profile kept selected channels within
  max abs 0.900, held 2.500 s road preview, preserved obs72 shape, produced
  high-speed labels 592/592, and replayed deterministically 4/4. This closes
  the high-speed env-contract blocker only; it does not admit training or a
  controller-performance claim.

### B2b. High-speed domain pricing [DONE: M3241 smoke + M3242 full negative]
- question: does window compression at production speeds (24/30/36 m/s,
  on the M3224 high-speed observation/preview profile) open type-(b)
  gaps (the K2 effect amplified), and — secondary, reported not gated —
  does belief value revive at high speed under sensing degradation (the
  two-regime law at production speeds)?
- method: high-speed panel (speed tier x reveal tier x mu) on the M3224
  profile; same four arms with the fixed* one-global-retune convention
  (v4's absolute thresholds were never tuned for this domain — the
  retune IS part of the honest baseline); per-instance feasibility
  labels at speed (B2 delivered); optional degradation axis on the
  tightest cells. Prereg first, new SEED_BASE, managed run.
- acceptance: pre-registered gap table with paired CIs; secondary
  VoI(belief) table descriptive only.
- result: `docs/m3241-b2b-high-speed-pricing-smoke.md` completed the quick
  protocol smoke. `docs/m3242-b2b-high-speed-pricing-full.md` then completed
  the full panel and rejected the current B2b formulation by the frozen rule:
  0/6 cells qualified, oracle solvability was 1.0, oracle-minus-pertuned gap
  was 0.125 in `hs24_tight_mu055` and `hs36_tight_mu075` and 0.0000 in the
  other four cells, and all paired CI95 lower bounds were 0. Scale-aware
  `fixed_star`/`v4_pertuned` succeeded 46/48 versus raw incumbent 42/48, so
  the panel shows weak high-speed pockets and a real scale-adapter transfer
  effect but no priced type-(b) window-compression prize. Any later high-speed
  hardening or degraded-sensing descriptive rider requires a new
  preregistration; M3242 admits no Track C extension, C2, training, or
  driver-performance claim.

### B3. Geometry-channel degradation + split-mu [DONE: M3225]
- wrapper extension to obstacle/boundary channels (the only sensing axis
  never degraded) + left/right split-mu in dynamics if expressible without
  load transfer; declare honestly what is not expressible.
- result: `docs/m3225-b3-geometry-degradation-split-mu-expressibility-smoke.md`
  completed the config-gated geometry-channel degradation smoke and split-mu
  expressibility audit. Full smoke ran 16 paired episodes and 400 paired
  frames. Road boundary channels changed (max 0.159) and active obstacle
  continuous channels changed (max 0.132), while ego/commands,
  present/size fields, empty obstacle slots, termination, and obs72 shape were
  preserved; deterministic replay passed 4/4. Current-sim split-mu was
  declared not expressible on the `DriftObstacleEnv` single-track outcome path
  because that path has one scalar `mu`, aggregated front/rear tire forces, and
  no left/right contacts or per-side normal loads. Existing source-only
  four-wheel HF0 primitives are not integrated as this B3 obstacle-env outcome
  backend.

### B4. Minute-scale drive structure [DONE: M3226]
- episode chaining or long-episode support (the real L3.5 scale);
  familiarization carry-over semantics; smoke.
- result: `docs/m3226-b4-minute-scale-drive-structure-smoke.md` completed
  the minute-scale env-structure smoke. The env now records raw obstacle pass
  independently from `finish_on_pass` truncation, preserving the existing
  `finish_on_pass=True` completion behavior while allowing post-pass
  continuation when `finish_on_pass=False`. Full smoke ran 4 seeds for 3000
  steps / 60.0 s each with obs72 shape preserved; warmup gate passed at steps
  215-216, emergency obstacle appeared at step 250, raw obstacle pass occurred
  at steps 991-999, minimum post-pass continuation was 2001 steps, and
  deterministic replay passed 2/2. This is env engineering only, not a
  controller-performance claim.

## Track C — C5' RL program (m1087 staged; opens after CP-1)

### C1. Oracle demo generator + BC warm-start [BLOCKED after M3238; pending PI/new-interface pricing]
- per-instance oracle demos on the frozen C5' cells; BC with DAgger-lite +
  held-out epoch selection (the G1' lessons are mandatory); capacity and
  seed discipline per the WP1 pattern.
- result so far: `docs/m3228-c1-c5prime-oracle-demo-bc-warmstart.md` ran the
  first preregistered structured-oracle demo + MLP BC warm-start. Quick smoke
  passed, but full validation action MSE was 0.234184 against the frozen
  <=0.12 gate, so M3228 failed and does not admit C2. `docs/m3229-c1-bc-warmstart-failure-localization.md`
  localized the failure to a selection/validation tail-action generalization
  gap (validation prefix MSE 0.026446 vs tail MSE 0.369957).
  `docs/m3232-c1-v2-tail-balanced-warmstart-smoke.md` then quick-smoked a
  revised v2 preregistration with rare coast-steer train support and
  validation probes. It replayed demos and wrote checkpoint/dataset artifacts
  but failed the frozen quick validation action-MSE gate (0.291470 vs <=0.12).
  `docs/m3233-c1-synthesis-repricing.md` then completed the required
  synthesis/repricing: A3/D1b keep the C5-prime target priced, but the local
  direct-MLP/action-MSE warm-start branch pivots after two gate failures.
  `docs/m3234-c1-admission-interface-pricing.md` then priced the successor
  interface positive: a structured tail-family oracle anchor removes 0.369957
  validation tail MSE vs the 0.15 threshold, and v2 held-out family train
  coverage is 1.0. `docs/m3235-c1-tail-family-interface-smoke.md` then ran
  the no-PPO interface smoke: 11/11 frozen demo replays succeeded, held-out
  family train coverage was 1.0, tail reconstruction MSE/max error were 0
  over 831 tail frames, and no policy checkpoint was written. C1 remains open
  under `c5prime_track_c_c1_tail_family_interface_pretrain_design`; do not
  proceed to full v2, another local direct-MLP BC repair, full C1 training, or
  C2 from the failed artifacts. Next C1 unit is a preregistered tail-family
  interface pretrain design/quick milestone with frozen criteria.
  `docs/m3236-c1-tail-family-interface-pretrain-quick.md` then tested that
  path on the full v2 split plus deterministic rare-tail train support.
  It replayed 43/43 demos and beat aggregate validation floors (0.766082 vs
  0.538012), but failed the frozen per-family gates: `coast_steer_-0.7`
  validation was 0/101 frames and predicted-family reconstruction MSE was
  0.276010 vs <=0.1. C1 remains open under
  `c5prime_track_c_c1_tail_family_interface_reprice`; do not continue local
  interface pretraining or controlled rollout design until a synthesis/repricing
  unit adjudicates M3234-M3236.
  `docs/m3237-c1-tail-family-interface-synthesis-repricing.md` completed that
  adjudication: the target remains priced and the structured representation is
  exact if the family is known, but local frame-wise interface pretraining is
  closed because aggregate validation accuracy masked a complete rare-family
  collapse. C1 remains open under
  `c5prime_track_c_c1_family_selector_repricing`; the next C1 unit is
  read-only family-selector/separability repricing. No local interface
  pretraining, controlled rollout design, full C1 training, or C2 work is
  admitted before that repricing.
  `docs/m3238-c1-family-selector-repricing.md` then completed that repricing
  and rejected the local family-selector route. Best train-only row selector
  validation accuracy was 0.803119 over the 0.538012 majority floor, but
  predicted-family reconstruction MSE was 0.268415 vs <=0.1 and
  `structured:coast_steer_-0.7` stayed 0/101, predicted as
  `structured:brake_steer_-1.0`. C1 local selector/interface training is
  blocked pending PI or a new nonlocal-interface pricing route. C2 remains
  blocked; no controlled rollout design, full C1 training, or C2 work is
  admitted from the local selector artifacts.
### C1-v3. Residual RL on the reflex base (nonlocal route) [STAGE-1 DONE NEGATIVE: M3245]
- **PI route decision (resolves the M3243 escalation)**: the prize is real
  in both simulators (A3 +0.16-0.22 current-sim; D1b +0.11-0.22
  Chrono-native), and M3228-M3238 established WHY local imitation fails —
  per-instance CEM oracle solutions are heterogeneous ("rare family"
  collapse), so imitating a non-policy is the wrong interface. The
  nonlocal route stops imitating entirely: **learn a bounded residual on
  top of the frozen v4 reflex and let RL discover its own drift-grade
  solutions**.
- architecture: action = clip(v4(obs) + Delta_theta(obs), action bounds),
  v4 frozen; Delta bounded per channel (delta_max frozen in the prereg);
  optional recoverable-set gating of Delta per the thesis deployable-safety
  principle (measurement-C surface, conservative snap). No supervised
  dataset, hence no dataset leak gate; engineering-only judging — no
  history-attribution claims.
- training: guarded RL directly on the frozen c5prime cells (m1087: the BC
  stage is deliberately skipped — that is the route decision); 1024-step
  smoke first; reward recalibration 40/60 as measured (P1 residual cited);
  >= 8 training seeds; the G1 variance lessons (seed-clustered SE) apply
  to all readouts.
- judging (prereg frozen BEFORE any full run): four arms on frozen
  validation seeds — fixed v4 / v4_pertuned / v4+residual (candidate) /
  per-instance oracle ceiling. Primary = (v4+residual - v4_pertuned) per
  cell, paired CIs; PASS = recapture >= 50% of the A3 gap in >= 2 of the
  3 qualified T-limit cells. Stop rules: behavior-neutral x2 => stop and
  synthesize; no criteria loosening; verdict either way is accepted.
- budget ladder: smoke <= 10 min; stage-1 <= 1 h (no checkpoint needed);
  **CP-2 before anything > 1 h** — D1b precondition is MET (M3231), so
  CP-2 is now budget-only; proposed first full budget <= 6 h CPU.
- smoke result: `docs/m3244-c1-v3-residual-rl-smoke.md` completed the 1024-
  step residual-on-frozen-v4 PPO smoke. All quick gates passed: S1/S2/S3
  C5-prime structural-gap rows were exercised, residual and final actions
  stayed finite and bounded, the optimizer changed parameters, and checkpoint
  plus metrics artifacts were written. This admits only the stage-1
  preregistration step; it is not a performance, C2, C3, high-fidelity, or
  self-ID claim.
- stage-1 result: `docs/m3245-c1-v3-residual-rl-stage1.md` completed the
  preregistered eight-seed first run and failed the frozen PASS rule. 0/3
  cells passed; v4+residual minus `v4_pertuned` was
  -0.6276/-0.4262/-0.3299 on S1/S2/S3, with paired CI95 entirely negative in
  all cells. This rejects this residual-on-v4 stage-1 attempt and admits no
  scale-up, C2, C3, driver-performance, high-fidelity sufficiency,
  feasibility-proof, or self-ID claim.

### C1-v4. Distill-then-RL — THE FINAL ATTEMPT [DONE: STAGE B FAIL; TRACK C CLOSED]
- **Finality clause**: this is the last pre-registered attempt at the C5'
  prize via learning. Any verdict closes Track C: PASS => C5' positive;
  FAIL => the bound "the structural prize is real in two simulators but
  resisted four learning interfaces" is accepted and the program moves to
  papers. No fifth attempt without new pricing evidence.
- **Diagnosis it acts on** (M3245 + C5 pricing): the per-tuned arm's
  advantage over raw v4 is mostly ONE global recalibration, and the
  per-tuned family is a coherent low-dimensional parametric policy family
  — by construction learnable, unlike the heterogeneous oracle CEM
  solutions that killed M3228-M3238. Stage-1 PPO failed to find even that
  recalibration at 65k steps (the G1 variance floor).
- **Stage A — distill the per-tuned family** (supervised, minutes): train
  the residual Delta to reproduce (v4_pertuned(obs) - v4_fixed(obs)) on
  per-tuned rollouts over the frozen cells. Frozen gate A: distilled
  closed-loop success within 0.05 (paired) of v4_pertuned on held-out
  validation rows in all 3 cells. Includes a representation check: if the
  per-tuned delta does not fit within delta_max, report it and widen
  delta_max for an exploratory arm (primary keeps M3245 bounds for
  comparability). Gate-A failure => architecture insufficiency, stop
  before any RL.
- **Stage A result (M3246)**: PASS. Primary M3245-bounded student was within
  0.05 of `v4_pertuned` in all three frozen cells: +0.0139 (S1), -0.0208
  (S2), +0.0000 (S3). Representation check found primary delta overbound on
  17.18% of teacher frames, so the exploratory widened-delta arm was reported
  but is not the gate. This admitted Stage B, which M3247 then ran.
- **Stage B — guarded RL from the distilled warm start**: realistic
  budget — 1M steps/seed first rung (~20-30 min wall at measured
  throughput, 8 seeds), one extension to 4M steps/seed if the
  intermediate readout shows movement; entropy/log_std schedule frozen in
  the prereg; behavior-neutral x2 stop rule.
- **Stage B result (M3247)**: FAIL. First rung ran 8 seeds x 1M steps from
  the M3246 primary distiller. 0/3 cells passed and 0/3 cells met the frozen
  movement threshold for extension. `v4_stage_b - v4_pertuned` was -0.0651
  (S1), -0.0425 (S2), -0.0052 (S3); recapture fractions were all negative.
  No 4M extension is admitted.
- **Judging**: identical frozen criteria to C1-v3 (four arms, primary =
  v4+residual - v4_pertuned per cell, paired CIs, seed-clustered SE,
  PASS = recapture >= 50% of the A3 gap in >= 2 of 3 cells). No criteria
  loosening. **CP-2 budget approved by PI disposition: <= 6 h CPU total
  for this attempt** (D1b precondition met by M3231).
- **Disposition**: Track C is closed. The accepted bound is now: the C5-prime
  structural prize is priced in A3 and direction-positive under D1b Chrono
  native oracle search, Stage A can distill the `v4_pertuned` floor, but the
  final guarded-RL rung did not robustly convert the gap into a policy. No
  fifth attempt without new pricing evidence.

### C2. Capability pretrain + guarded RL smoke [SUPERSEDED by C1-v3 (the residual route trains directly); original BC-first chain closed by M3238]
- superseded unit: do not run the original BC/pretrain-first chain. Its
  runnable replacement is C1-v3 residual RL on the frozen v4 base.
### C3. Staged scale-up [CLOSED / NOT ADMITTED]
- **CP-2 (PI checkpoint)** before any run > 1 h compute: PI confirms budget
  AND unit D1b must have returned direction-positive (CP-1 disposition).
  D1b is direction-positive by M3231, but M3247 Stage B failed and did not
  trigger the extension rule. No C3 scale-up is admitted.
- verdict either way is accepted and recorded; no criteria loosening.

## Track D — high-fidelity / Chrono (continues M3218/M3219)

### D1. S4 multi-vehicle Chrono pricing [DONE: M3227]
- the variant selector is smoked (M3219: Sedan default + BMW_E90/UAZBUS);
  needed: frozen prereg + declared handling of unmapped lf/lr/iz/cf/cr
  (coverage-map fidelity row), then a small cross-vehicle pricing rollout
  (does the structural-ceiling gap direction hold across Chrono vehicles?).
- acceptance: direction-preservation verdict per vehicle; absolute numbers
  are not claims.
- result: `docs/m3227-d1-s4-hf-lite-chrono-pricing.md` completed the frozen
  D1 S4-HF-lite direction-pricing proxy. Full run: 108 Chrono episodes over
  Sedan/BMW_E90/UAZBUS, finite obs72 resets and variant matching passed.
  Verdict: direction **reversed** in all three variants. The A3 current-sim
  structured oracle-tail replay underperformed `v4_pertuned` by -0.0833
  (Sedan), -0.0833 (BMW_E90), and -0.5000 (UAZBUS). This is negative
  direction-pricing only; it does not refute A3 current-sim pricing and does
  not price a fresh high-fidelity oracle or continuous lf/lr/Iz/cf/cr mapping.

### D1b. Chrono-native oracle pricing [DONE: M3231; CP-2 precondition satisfied]
- question: does the structural-ceiling gap exist under Chrono dynamics
  when the oracle is searched NATIVELY in Chrono (closed-loop /
  CEM-in-backend), rather than tail-replayed from current-sim (the M3227
  proxy, which reversed as expected for an open-loop transplant)?
- method: per-instance oracle search executed in the Chrono backend
  (structured candidates + reduced-budget CEM over piecewise segments;
  machinery: `scripts/feasibility_audit/chrono_backend_worker.py` +
  the oracle_certification CEM pattern), on >= 3 instances per frozen
  T-limit cell x >= 2 vehicle variants (sedan_tmeasy + one non-sedan);
  compare against the best fixed/per-tuned arm evaluated in Chrono on the
  same instances. Declared handling of unmapped lf/lr/iz/cf/cr per
  M3219/M3227 notes. Managed run (hours-scale); prereg first with a
  direction criterion frozen (gap > 0 per variant, paired).
- acceptance: per-variant direction verdict; positive opens CP-2's
  precondition, negative scopes Track C claims to current-sim and CP-2
  re-evaluates.
- result: `docs/m3230-d1b-chrono-native-oracle-pricing-smoke.md`
  completed the protocol smoke, then
  `docs/m3231-d1b-chrono-native-oracle-pricing-full.md` completed the full
  frozen panel. Verdict: D1b direction-positive in both preregistered Chrono
  variants. Native Chrono oracle minus same-row `v4_pertuned` was +0.2222 on
  `sedan_tmeasy` (9/9 vs 7/9) and +0.1111 on `bmw_e90_tmeasy` (8/9 vs 7/9).
  This satisfies the CP-2 D1b direction-positive precondition, but remains
  high-fidelity direction-pricing only: no training, no incumbent mutation,
  no validation/ranking/promotion, no driver-performance claim, and no
  high-fidelity sufficiency claim.

## Out of scope for Codex sessions

- Papers (WP5): Claude + PI via the ARS pipeline.
- v5 promotion: deferred by PI until research completion.
- Anything touching `ActiveSafetyReflexDriver` or loosening a frozen
  criterion. Guardrails are merged in commit 05607bcd; autonomous/Codex
  sessions still follow this ordered roadmap and PI checkpoints.

## Status lines (update in place)

- A1: DONE (M3220; 0/4 cells qualified under cg/Iz S4L rider)
- A2: DONE (M3221; normalization/preview implementation blocker found)
- A3: DONE (M3222; C5-prime target confirmed 3/4 T-limit cells; CP-1 conditional approval recorded)
- B1: DONE (M3223; flagged constant-velocity crosser smoke passed)
- B2: DONE (M3224; explicit 36 m/s normalization/preview smoke passed)
- B3: DONE (M3225; geometry-channel degradation smoke passed; split-mu not expressible on the DriftObstacleEnv single-track path)
- B4: DONE (M3226; 60 s warmup-to-obstacle-to-post-pass continuation smoke passed)
- B1b: DONE (M3239 smoke + M3240 full negative; current moving-crosser formulation 0/4 cells qualified)
- B2b: DONE (M3241 smoke + M3242 full negative; current high-speed formulation 0/6 cells qualified)
- C1: imitation chain closed (M3228-M3238); C1-v3 stage-1 DONE NEGATIVE (M3245); **C1-v4 OPEN — THE FINAL ATTEMPT** (distill-then-RL; PI disposition 2026-06-12, CP-2 budget <= 6 h approved)
- C2: SUPERSEDED
- C3: BLOCKED on C1-v4 verdict (any verdict closes Track C)
- D1: DONE (M3227; tail-replay proxy reversed in all three variants)
- D1b: DONE (M3231; native Chrono oracle direction-positive on Sedan/BMW_E90)

Execution order note: M3243 recorded the brief roadmap-exhausted stop after
B1b/B2b closed negative; PI has since reopened C1 as C1-v3. M3244 passed the
1024-step residual-RL smoke, and M3245 failed the preregistered stage-1 gate.
There is currently no admitted C1-v3 scale-up or C3 run from this result; a
synthesis or PI route decision is required before another C1-v3 attempt. Do
not resume local imitation/interface repairs, C2, C3, or any
driver-performance claim from the smoke or negative stage-1.
- WP6.2 guardrails: **MERGED** (commit 05607bcd — validator V7 live in the
  pre-commit hook, escalation protocol in docs/escalations/, managed-run
  helper scripts/run_managed.sh). Codex execution may begin.
