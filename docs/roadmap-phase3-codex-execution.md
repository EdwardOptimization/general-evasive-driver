# Phase-3/4 Execution Roadmap (Codex-ready, refreshed 2026-06-14)

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
  current forward path is Phase-4 Chrono re-pricing, not another current-sim
  Track-C repair. CP-1 conditionally opened C1, M3238 blocked the local
  selector/interface route, PI reopened C1 as C1-v3/C1-v4, and M3247 closed
  Track C after the final guarded-RL rung failed. M3231 satisfied the D1b
  direction-positive precondition for CP-2, but no C3 scale-up is admitted
  after the M3247 verdict. M3239/M3240 completed B1b and rejected
  the current moving-crosser formulation (0/4 cells qualified, all rows
  reflex-solvable). M3241/M3242 completed B2b and rejected the current
  high-speed formulation (0/6 cells qualified; two weak 0.125 pockets with
  CI lower bound 0; scale-aware fixed_star/v4_pertuned 46/48). M3243 recorded
  the temporary blocked-dependency stop, then PI reopened C1 as C1-v3:
  residual RL on the frozen v4 reflex base. M3244 completed the 1024-step
  C1-v3 residual smoke and passed all quick gates. M3245 completed the
  preregistered <=1 h stage-1 run and failed the frozen gate: 0/3 cells
  passed, with v4+residual below `v4_pertuned` in every qualified cell.
  M3246 passed C1-v4 Stage A, but M3247 failed Stage B with 0/3 pass cells
  and 0/3 movement cells. M3250 completed full E1 Chrono spread-revival
  pricing and rejected the spread-revival thesis by the frozen rule. M3251
  passed the E2 Chrono protocol smoke, and M3252 completed full E2 with a
  positive clean Sedan/TMeasy belief-value verdict. M3253 passed the E3 A/C
  protocol smoke but did not decide the full detection-latency table or
  recoverable-set budget. M3254 passed the E3 tire-truth telemetry connector
  smoke and confirmed four-wheel slip/force/normal-load diagnostics are
  available. M3255 completed the full frozen E3 Sedan/TMeasy measurement A/C
  panel: 24/24 detector-latency rows and 72/72 recovery-budget rows were
  written, all protocol gates passed, CP-3 evidence is ready, and Track F is
  still not admitted. M3256 recorded PI CP-3 as a blocked process gate, then
  PI recorded CP-3 disposition A: harden Track E before any GPU. M3257
  completed E3-fix detector-onset reconciliation: 24/24 case rows and 3426
  trace rows, original early-fire rate 0.5, reconciled early-fire rate 0.0,
  detector miss rate 0.1667, and E2' dependency ready. M3258 then confirmed
  the E2' clean flip on Sedan/TMeasy plus UAZBUS/TMeasy with 30 validation
  seeds per cell, and M3259 confirmed the structural gap in Chrono
  (native_oracle - pertuned +0.18) while spread revival stayed unsupported.
  The harden-first CP-3 disposition is satisfied and PI approved Track F at
  100M steps / no time limit in principle, but then DEFERRED Track F behind
  a new Track E4 (Chrono drift / beyond-saturation pricing): E1'/E2'
  confirmed prizes in the avoidance regime only, never the drift regime
  (toy-sim reflex 0/84, thesis-queued) which Chrono's TMeasy tires can now
  represent. E4 is now completed by M3260; PI reviewed it on 2026-06-14 and
  approved Track F at full-scenario scope. M3261 completed F1 infrastructure
  and measured 2.1 steps/s -> 550-day projection. PI 2026-06-14: this was a
  ~170x infra bottleneck (2 workers + per-step IPC to the separate-env
  Chrono worker), not a Chrono limit. M3263 completed F1b throughput
  optimization with 30 workers and batched stepping: closed-loop throughput
  1600.8440 steps/s, batched action-sequence throughput 1967.0045 steps/s,
  best 100M projection 14.12 h. STOP for PI before F2.

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

### A2. Obs-normalization audit [DONE: M3221; blocker found, later narrowed by B2]
- question: how far do the nominal-vehicle normalization constants (vx/20,
  ay/15, 80 m boundary lookahead) shift the obs distribution across the
  population envelope, and what rescaling keeps channels in-range?
- method: zero-rollout where possible — sample population instances, drive
  scripted profiles, record per-channel obs ranges/saturation rates vs the
  nominal car; propose (do not yet apply) a normalization scheme.
- acceptance: per-channel saturation/shift table + a frozen recommendation;
  coverage-map risk item 1 closed.
- result: `docs/m3221-a2-obs-normalization-audit.md` completed the audit.
  Verdict at M3221 time: population or high-speed training needed a follow-up
  normalization/preview implementation. Main failures: `road_y/20` saturated
  on curved far-boundary points; `vx/20`, `vy/12`, `ax/15`, and `ay/15`
  saturated in high-speed profiles; obstacle `rel_vy/12` saturated with
  ego-relative obstacle mode. B2 later closed the explicit 36 m/s env-contract
  blocker only; population-scale training still needs a separate
  normalization decision.

### A3. C5' target consolidation on C5-F1 [DONE: M3222; historical CP-1 gate]
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

## Track C — C5' RL program (m1087 staged; CLOSED after M3247)

### C1. Oracle demo generator + BC warm-start [CLOSED / superseded after M3238]
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
  over 831 tail frames, and no policy checkpoint was written. At that point
  C1 temporarily moved to a preregistered tail-family interface pretrain
  design/quick milestone; this historical route is now closed.
  `docs/m3236-c1-tail-family-interface-pretrain-quick.md` then tested that
  path on the full v2 split plus deterministic rare-tail train support.
  It replayed 43/43 demos and beat aggregate validation floors (0.766082 vs
  0.538012), but failed the frozen per-family gates: `coast_steer_-0.7`
  validation was 0/101 frames and predicted-family reconstruction MSE was
  0.276010 vs <=0.1. This forced the M3237 synthesis/repricing step before
  any further local interface pretraining or controlled rollout design.
  `docs/m3237-c1-tail-family-interface-synthesis-repricing.md` completed that
  adjudication: the target remains priced and the structured representation is
  exact if the family is known, but local frame-wise interface pretraining is
  closed because aggregate validation accuracy masked a complete rare-family
  collapse. That admitted only the read-only family-selector/separability
  repricing in M3238; no local interface pretraining, controlled rollout
  design, full C1 training, or C2 work was admitted before that repricing.
  `docs/m3238-c1-family-selector-repricing.md` then completed that repricing
  and rejected the local family-selector route. Best train-only row selector
  validation accuracy was 0.803119 over the 0.538012 majority floor, but
  predicted-family reconstruction MSE was 0.268415 vs <=0.1 and
  `structured:coast_steer_-0.7` stayed 0/101, predicted as
  `structured:brake_steer_-1.0`. C1 local selector/interface training was
  then blocked. PI reopened the problem through C1-v3/C1-v4 nonlocal routes;
  M3247 has now closed Track C. No controlled rollout design, full C1
  training, C2, C3, or Track-C repair work is admitted from the local selector
  artifacts.
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

## Phase-4 — decisive experiments move to Chrono (PI diagnosis 2026-06-13)

**Rationale (PI)**: the toy simulator's simplicity (3-DOF single-track,
tanh tires, NO load transfer — h_cg never enters the force computation —
no tire relaxation, deterministic, smooth) predetermined several headline
conclusions: it is classical control's home turf by construction. Lateral
capacity mu*g is mass-independent in the toy model, which is exactly why
vehicle spread priced to ~0; load transfer is the real physical carrier of
the SUV-vs-sports-car mechanism. Conclusions not yet re-measured in Chrono
remain **demoted to toy-sim-scoped** until their Track-E pricing unit
completes. E1 has now rejected the spread-revival thesis in Chrono, E2 has
flipped the clean two-regime-law readout positive on Sedan/TMeasy, and E3
has completed the full Sedan/TMeasy detector-latency/recovery-budget
measurement under M3255. CP-3 is the remaining hard stop before Track F.
Conclusions with Chrono direction
checks (7-row ceiling, HF4 249/256, D1b structural gap) keep their scope. The
C1-v4 finality clause barred another same-interface attempt without new
pricing evidence: Track E below IS the new pricing path, and Track F changes
interface class, budget scale, and simulator — a different experiment,
PI-sanctioned.

### Track E — Chrono re-pricing (stage 1; CPU, zero training)

E0. Expressibility audit [DONE: M3248]: what vehicle-spread axes are
controllable in the Chrono variants (payload mass/position -> cg height,
tire parameter sets, wheelbase across variants)? Result: all three
whitelisted variants (`sedan_tmeasy`, `bmw_e90_tmeasy`, `uazbus_tmeasy`)
reset/stepped with finite obs72 and matching backend_info; the frozen
spread-axis table admits E1 on selected vehicle fixtures with load-transfer
physics active, while blocking independent payload-position, h_cg,
tire-family, split-mu, and continuous lf/lr/Iz/cf/cr axes without new
connectors. Acceptance satisfied: frozen spread-axis table feeding E1.

E1. Spread-revival pricing [DONE: M3249 quick smoke + M3250 full negative]:
four-arm degradation curve
IN CHRONO with real load transfer — vehicle classes x T-limit cells
(ported via the HF4 same-scenario export). Arms: fixed reflex (one global
Chrono retune, fixed* convention) / RLS-retuned / per-instance-tuned /
per-instance Chrono-native oracle (M3230/M3231 machinery). Question: does
(per-tuned - fixed) open up, and does (per-tuned - RLS) leave a residual,
when mass/cg/tires actually couple into lateral capacity? This is the
original C5 spread thesis's second life on its true physical carrier.
Prereg first; paired CIs; either verdict rewrites the papers.
M3249 exercised the four-arm protocol on the M3248-admitted variants and
passed, but it was not a spread-revival verdict because the quick smoke used
one row to exercise plumbing. M3250 then ran the full frozen pricing panel:
0/3 variants qualified, pooled `v4_pertuned - fixed_star` was -0.0556 with
CI95 [-0.1667, 0.0], pooled `v4_pertuned - v4_rls` was 0.0000 with CI95
[-0.1667, 0.1667], and the attempt-limited native-oracle anchor was below
`v4_pertuned` in this panel. E1 did not admit Track F. E2 and E3 have since
completed under M3252 and M3255, leaving CP-3 as the required PI checkpoint
before any Track F work beyond smoke.

E2. Two-regime law, Chrono version [DONE: M3251 quick smoke + M3252 full positive]:
port the
threshold-seeker + shortfall detector to the Chrono backend (per-backend
tau re-calibration, as flagged in WP4 notes); measure clean-sensing
VoI(belief) on Chrono T-limit cells (+ a degraded spot cell). Registered
prediction (falsifiable): with TMeasy + load transfer the detector is no
longer near-perfect and clean VoI(belief) > 0 — which would flip a
headline conclusion. Either verdict is paper-grade.
M3251 passed the protocol smoke on the Sedan fixture: 18/18 expected rows
were written for oracle_ramp / threshold_seeker / fixed_ramp over clean
9.5/30 m reveal tiers plus a delay25 tight degraded spot; reset obs finite,
variant match, calibration, and non-verdict gates all passed. Quick readouts
were not an E2 verdict. M3252 then ran the full frozen Sedan/TMeasy E2 panel:
280/280 selection rows and 192/192 validation rows were written, all protocol
gates passed, and the frozen clean positive rule was satisfied at reveal 9.5 m
(oracle - best_floor +0.75, CI95 [0.375, 1.0]) and 12 m (+0.625, CI95
[0.25, 0.875]). The delay25_tight degraded spot is secondary and non-gating
(+0.125, CI95 [0.0, 0.375]). E2 did not admit Track F by itself; E3 has since
completed under M3255, and CP-3 is still required before any Track F run
beyond smoke.

E3. Measurements A/C, Chrono re-run [DONE: M3253/M3254 smokes + M3255 full]:
detection-latency table and reflex recoverable-set budget re-measured on
Chrono (complements E2 and feeds the Track F safety gating). M3253 passed the
protocol smoke: 4/4 expected Sedan/TMeasy quick rows, finite reset obs,
variant matches, A long/lat detector traces, C baseline_coast/v4_incumbent
recovery traces, and quick_mode_is_verdict=0. It is not the full E3 verdict.
M3254 then passed the tire-truth telemetry connector smoke: 8/8 samples and
32/32 wheel rows, finite obs72, finite tire slip/force/wheel-speed rows, and
positive normal loads. M3255 then ran the full frozen Sedan/TMeasy panel:
24/24 detector-latency rows and 72/72 recovery-budget rows were written, all
protocol gates passed, and CP-3 evidence is ready. Measured safety readouts:
detector miss rate 0.1667, p90 latency 1.346 s, early-fire rate 0.5, v4
recovery 1.0, baseline recovery 1.0, v4-baseline delta 0.0. Track F remains
blocked until PI CP-3 confirms targets and budget.

### Track E' — Track-E hardening (CP-3 disposition A; CPU, zero training; E2' DONE; E1' DONE)

**CP-3 disposition (PI, 2026-06-13): option A — harden Track E before any
GPU.** The E2 headline flip (clean VoI(belief) > 0 in Chrono, the opposite
of the toy-sim VoI=0) is the most consequential result of the program if it
holds, but every Track-E full run was smoke-scale in power (E2 n=8/cell,
E1 3-6/arm, E3 12-24/axis), Sedan/TMeasy only, with one detector anomaly
and an underpowered native oracle in E1. Price-before-train one more level:
confirm the flip at adequate power BEFORE spending GPU-days on Track F.

E3-fix. Detector-onset reconciliation [DONE: M3257]:
M3257 audited and reconciled the obs72 shortfall detector vs the Chrono
tire-slip onset definition. Full result: 24/24 case rows, 3426 trace rows,
all protocol gates passed, original early-fire rate 0.5, reconciled
early-fire rate 0.0, detector miss rate 0.1667, corroborated early-fire rate
0.5, uncorroborated detector-fire rate 0.0, and reconciled p90 latency
1.346 s. The reconciled rule is now frozen for E2': use the detector fire
step as actor-visible onset when it occurs before the M3255 tire-slip truth
onset and that tire truth later occurs within the preregistered 150-step
window; otherwise keep the M3255 tire-slip truth onset.

E2'. Two-regime law hardened [DONE: M3258; depends M3257]: M3258 re-ran E2
under the frozen hardened protocol with >= 30 validation seeds per cell,
Sedan/TMeasy plus UAZBUS/TMeasy, all five clean reveal tiers plus the
delay25_tight degraded spot, paired CIs, new seed streams, preregistration,
and managed full execution. Result: 560/560 selection rows and 5760/5760
validation rows were written, all protocol gates passed, all five clean reveal
tiers qualified on both variants, and the frozen flip-confirmation criterion
passed with 4 positive tight clean cells across 2 variants. Max clean
oracle-minus-floor was +0.7667. This confirms the Chrono clean flip for the
scoped scripted-controller panel; it did not admit Track F by itself. Track F
then required the later PI review sequence, now advanced through E4 and F1.

E1'. Spread-revival repricing [DONE: M3259; depends E0; parallel to E2']:
M3259 re-ran E1 with the preregistered selection-row oracle-adequacy gate and
24 validation units per variant on Sedan/TMeasy, BMW_E90/TMeasy, and
UAZBUS/TMeasy. Result: all protocol gates passed, the oracle-adequacy gate
passed on all three variants, and spread revival was not supported by the
frozen rule: 0/3 variants qualified. Pooled `v4_pertuned - fixed_star` was
-0.1389 with CI95 [-0.2222, -0.0556], pooled `v4_pertuned - v4_rls` was
-0.0833 with CI95 [-0.1806, 0.0139], and pooled `native_oracle -
v4_pertuned` was +0.1806 with CI95 [0.0972, 0.2778]. This resolves the M3250
underpowered-native-anchor critique as a real negative spread-revival result;
it does not admit Track F, training, driver-performance, high-fidelity
sufficiency, paper, feasibility-proof, repair-success, robustness-result, or
self-ID claims.

### Track E4 — Chrono drift / beyond-saturation pricing [DONE: M3260; E4 PI review resolved]

**PI re-ordering (2026-06-13): Track F is DEFERRED until the drift regime is
priced.** E1'/E2' confirmed their prizes in the handling-limit AVOIDANCE
regime only (entry-speed commitment + threshold-braking + obstacle reveal;
the controllers ride just inside the boundary, F1-line-tracking style). No
E-unit tested sustained drift / beyond-rear-saturation operation — the
regime where the toy-sim reflex scored 0/84 and which the thesis (Section
5.1) explicitly queued/de-scoped because the toy tanh tire cannot represent
a stable drift equilibrium. Chrono's TMeasy combined-slip tires CAN
represent large sideslip and beyond-saturation dynamics, so this is the
first place the drift-regime reflex-vs-learned question is measurable. The
avoidance-regime prizes (structural gap +0.18, belief value up to +0.77)
may be much larger in the drift regime, where RL's advantage should be
greatest — so price it BEFORE committing GPU, and let it inform Track F's
training target.

E4. Drift-regime pricing [DONE: M3260; CPU, zero training; depends E0 fixtures]:
construct Chrono scenarios that require sustained controlled operation
beyond rear-tire saturation (e.g. high-speed corner entry and/or low-mu
emergency steer that forces large sideslip), with sideslip/yaw/tire-
saturation telemetry recorded (absent from E1'/E2'). Four arms: v4 reflex
(one global retune, fixed*) / per-instance-tuned reflex / native Chrono
oracle (structured + CEM, allowed drift maneuvers) / drift-specialized
oracle. Prereg first, new SEED_BASE, >= 20 validation units/cell, paired
CIs, oracle-adequacy gate (as E1'). Acceptance: per-cell (oracle - fixed*)
and (oracle - per-tuned) with CIs, and a documented characterization of
WHERE/WHY the reflex fails in the drift regime (does it fail to enter, fail
to stabilize, or fail to recover?). Either verdict feeds Track F's target
choice and the papers. Stretch: re-run the toy-sim's 3 drift_required rows'
geometry in Chrono to see if they are now solvable by an oracle.

M3260 result: full E4 completed with 204 rows (44 selection, 160 validation),
all protocol gates passed, and 20 validation units per drift cell. The
`low_mu_power_oversteer` cell showed a priced oracle gap of +0.4000 versus
both fixed* and tuned reflex, CI95 [0.1797, 0.6203], with reflex failures
mostly fail-to-enter plus some fail-to-stabilize. The `lift_off_recovery`
cell was near-neutral at +0.0500, CI95 [-0.0480, 0.1480], with reflex
failures all fail-to-stabilize. This is pricing evidence only, not training
or driver-performance evidence; Track F admission came later through explicit
PI review, followed by the M3261 F1 wall-clock stop.
- **PI stop (2026-06-14): Codex completed E4 and STOPPED for PI review.**
- **PI E4 disposition (2026-06-14): Track F APPROVED, full-scenario target.**
  E4 confirmed the largest reflex gap in the project in the drift regime
  (+0.40, reflex 0/0/0 vs drift-specialized oracle 0.40, dominant failure
  fail_to_enter). PI decision: train ONE driver across the FULL scenario
  distribution — not a drift specialist. Track F target = avoidance cells
  (E2'/E1' regime: belief value up to +0.77, structural gap +0.18) PLUS
  drift cells (E4 low_mu_power_oversteer: +0.40). Teacher is per-regime:
  the avoidance oracle for avoidance cells AND the drift-specialized oracle
  for drift cells (the generic CEM found nothing in drift — 0.0 — so the
  drift teacher MUST be the specialized feedback oracle, not search).
  Curriculum spans both regimes. The F1 wall-clock stop still applies before
  the 100M launch.

### Track F — robotics-parity RL protocol (stage 2; APPROVED full-scenario; F1 wall-clock stop before 100M)

**CP-3 GPU-days disposition (PI, 2026-06-13): 100M env steps approved in
principle, no time limit — but DEFERRED behind E4, and STOP AFTER F1.**
E2'/E1' confirmed the prize,
so PI commits to the full robotics-parity scale (100M, the
literature-standard upper end). One refinement (PI, 2026-06-13): Codex runs
F1 only (infra + smoke + throughput benchmark + projected 100M wall-clock)
and STOPS for a PI go/scale confirmation, because Chrono is CPU physics and
100M steps may be days-to-weeks of wall-clock — PI wants the measured cost
in hand before launching the multi-day F2 run (the last price-before-train,
applied to compute cost). This is NOT a budget cut: 100M/no-time-limit
stands; F1 just makes the calendar cost real first.

F1. Training infrastructure [DONE: M3261; STOP for PI wall-clock review]:
vectorized parallel Chrono workers for training; end-to-end smoke (sane
gradients, obs72/action3 contract held, finite losses, deterministic seed
handling); throughput benchmark + GPU-vs-CPU feasibility re-check. Result:
prereg + quick + full run passed, 48 mixed-regime Chrono worker steps were
written (avoidance 24, drift 24), aggregate throughput was 2.1031 steps/s,
projected 100M-step wall-clock was 13207.81 h / 550.33 days, and CUDA update
throughput was 0.00415x CPU on the measured batch. M3262 records the
blocked-on-PI wall-clock review gate; do NOT launch F2.

**PI F1 disposition (2026-06-14): as-built 550 days is infeasible, but it is
a ~170x INFRASTRUCTURE bottleneck, not a Chrono limit — do F1b optimization
before F2.** Diagnosis: F1 used only 2 workers on a 32-core machine and pays
a per-step IPC round-trip to the separate-conda-env Chrono worker; the
historical in-process Chrono backend smoke ran ~3400 internal steps/s
(~170 control steps/s single-worker) vs F1's ~1 control step/s/worker.
F2 stays on CPU (CUDA confirmed 0.004x CPU for this small net).

F1b. Training-throughput optimization [DONE: M3263; STOP for PI]:
prereg + quick + full run passed. M3263 scaled to 30 Chrono workers and added
batched `step_many` IPC amortization while keeping obs72/action3, determinism,
and mixed avoidance+drift coverage. Full result: 1920 mixed-regime steps,
closed-loop one-step throughput 1600.8440 steps/s, batched action-sequence
throughput 1967.0045 steps/s, speedup 935.27x vs F1, projected 100M best
wall-clock 14.12 h / 0.59 days, target >=1000 steps/s met. **STOP and report
to PI**; keep F2 blocked-on-PI; do NOT launch F2.

F2. Asymmetric actor-critic + teacher-student [BLOCKED: M3262, on F1b throughput report + PI go]:
robotics-field-standard recipe — privileged critic/teacher (true mu +
vehicle params), obs72+short-history student distillation (RMA-style),
curriculum, **100M env steps**, >= 8 seeds. **Training distribution = the
FULL scenario set, ONE driver (PI 2026-06-14)**: avoidance cells (E2'/E1'
regime) + drift cells (E4 low_mu_power_oversteer beyond-saturation), with a
curriculum spanning both. **Per-regime teacher**: avoidance oracle for
avoidance cells, drift-specialized feedback oracle for drift cells (the
generic CEM oracle scored 0.0 in drift, so the drift teacher MUST be the
specialized controller — search demos will not teach drift entry). Launch
as a MANAGED background process (`scripts/run_managed.sh` + progress.jsonl
+ --resume) — a multi-day run must NEVER live in an agent session (the
agent-dies-measurement-dies rule). **Judging prereg frozen BEFORE the full
run launches** (both readings, fixing the C1-v4 tension): primary =
seed-robust criterion (paired, seed-clustered); secondary-but-preregistered
= validated-best-seed engineering criterion. No criteria loosening.

F3. Judging [part of F2 prereg]: four arms in Chrono on the frozen cells
(fixed* / RLS-retuned / per-instance-tuned / per-regime oracle), reported
**per regime AND pooled**; three confirmed prizes to beat — avoidance
structural-ceiling gap (E1' +0.18), clean-sensing belief value (E2' up to
+0.77), and the drift gap (E4 +0.40, the largest); plus an
all-regimes-competence readout (the one driver must not regress ordinary
avoidance while gaining drift). PASS thresholds frozen before any full run.

**F2 build status (2026-06-14): three build passes + three adversarial
reviews done** (`docs/phase4-f2-build-review-2026-06-14.md`). Pass-3 is real
PPO (clipped surrogate + bootstrapped GAE + policy gradient, teacher = m1087
warm-start), all of B1-B6 + M1-M7 fixed and independently verified, real
budget 48.25M env steps / ~8.4 h at the F1b 30-worker rate. One condition
remained: S7 (stop-rule) correctly blocks because F2's drift validation
scenarios do not match E4's, so the drift oracle scores 0/N (vs the 0.40 E4
measured).

**PI two-stage decision (2026-06-14): do both, stage 1 then stage 2.** The
E4 drift cells are a deliberately narrow probe (2 hand-constructed cells,
car pre-initialized into a ~13-16 deg sideslip, ~30 km/h, 1.8 s episodes,
0.48 s sustain) — real drift/handling-limit is far wider (full speed,
varied geometry, full/split mu, entry-to-exit maneuvers, drift-as-avoidance).

- **F4-align (stage 1, DONE)**: a 4th small F2 build pass aligning
  F2's drift validation cells to E4's frozen `low_mu_power_oversteer` cell
  (mu 0.48, speed 9, radius 70, initial_beta 0.22) + the `beta0p22_power`
  oracle, so the drift oracle reproduces ~0.40 and S7 passes. Re-smoke
  (confirm drift oracle ~0.40, S7 proceed), then freeze the prereg and
  launch F2 as the clean first RL-vs-reflex baseline on exactly the priced
  cells. Claim scoped to "narrow drift probe + avoidance spectrum".
- **E4-prime + F2-wide (stage 2, queued after stage-1 result)**: widen the
  drift task surface (speed/geometry/mu spectrum, entry-to-exit maneuvers,
  drift-as-avoidance), re-price it four-arm (E4-prime, CPU zero-training),
  then retrain F2 on the representative surface. This is the faithful
  RL-vs-reflex-in-drift experiment; stage 1's clean baseline de-risks it.

**CP-3 (PI checkpoint) [FULLY RESOLVED 2026-06-13]**: disposition A
(harden first) was satisfied — E3-fix (M3257), E2' flip-confirmation at
power (M3258), and E1' oracle-adequate spread repricing (M3259) all
completed. The follow-on GPU-days checkpoint is then resolved by PI **FULL
APPROVAL: 100M env steps, no time limit, no intermediate budget gate** (see
the Track F header), but PI then inserted the E4 drift-pricing checkpoint.
M3260 completed E4; PI reviewed it on 2026-06-14 and approved Track F at
full-scenario scope. M3261 completed F1, PI requested F1b, and M3263
completed the throughput optimization with the >=1000 steps/s target met.
F2/F3 remain blocked until PI reviews the F1b wall-clock report and gives go;
M3262 records that blocker in the queue/escalation ledger.
The escalation `docs/escalations/2026-06-13-phase4-cp3-track-f-pi-checkpoint.md`
records the earlier CP-3 disposition.

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
- C1: CLOSED under the current-sim Track-C interface. Imitation/interface
  chain closed (M3228-M3238); C1-v3 residual-RL stage-1 DONE NEGATIVE
  (M3245); C1-v4 distill-then-RL Stage A passed (M3246) but Stage B first
  rung DONE NEGATIVE (M3247; 0/3 pass cells, 0/3 movement cells). No C1
  scale-up, 4M extension, driver-performance, high-fidelity sufficiency,
  repair-success, feasibility-proof, or self-ID claim is admitted.
- C2: SUPERSEDED / no Track-C admission after C1 closure
- C3: CLOSED / not adjudicated (the pre-registered condition was never triggered; Track C closed absent new pricing evidence)
- D1: DONE (M3227; tail-replay proxy reversed in all three variants)
- D1b: DONE (M3231; native Chrono oracle direction-positive on Sedan/BMW_E90)

Execution order note: M3243 recorded the brief roadmap-exhausted stop after
B1b/B2b closed negative; PI then reopened C1 as C1-v3 and C1-v4. M3244
passed the 1024-step residual-RL smoke, M3245 failed the preregistered C1-v3
stage-1 gate, M3246 passed the C1-v4 Stage-A distillation gate, and M3247
failed the C1-v4 Stage-B guarded-RL first rung. Track C is closed under the
current-sim interface. Do not resume local imitation/interface repairs, C1-v3,
C1-v4, C2, C3, or any driver-performance claim from those smoke, distillation,
or negative RL results. Phase-4 reopens the question only through new Chrono
pricing evidence; E0 is complete, E1 is completed negative, and E2 is
completed positive on the Sedan/TMeasy fixture. E3 protocol and telemetry
smokes passed, full E3 completed under M3255, M3256 recorded CP-3, and PI
resolved CP-3 as disposition A. M3257 completed E3-fix, M3258 completed
E2' hardening, M3259 completed E1' spread-revival repricing negative, M3260
completed E4 drift-regime pricing, PI approved Track F full-scenario scope on
2026-06-14, M3261 completed F1 infrastructure, and M3263 completed F1b
throughput optimization. No F2/F3 work is admitted before PI reviews the F1b
wall-clock report.
- E0: DONE (M3248; frozen Chrono spread-axis table and E1 envelope)
- E1: DONE (M3249 quick protocol smoke passed; M3250 full pricing negative with 0/3 qualifying variants)
- E2: DONE (M3251 quick protocol smoke passed; M3252 full Sedan/TMeasy verdict positive with 2 clean reveals qualifying)
- E3: DONE (M3253 passed protocol smoke; M3254 confirmed tire-truth telemetry; M3255 full measurement A/C completed with 24/24 latency rows, 72/72 recovery rows, all protocol gates passed, CP-3 evidence ready, Track F not admitted)
- CP-3: RESOLVED (PI 2026-06-13) — harden-first satisfied; Track F approved at 100M steps/no-time-limit in principle but DEFERRED behind Track E4 (drift pricing) and re-ordered 2026-06-14
- E3-fix: DONE (M3257; detector-onset reconciliation completed, corrected early-fire rate 0.0, E2' dependency ready)
- E2': DONE (M3258; flip confirmed with >=30 seeds/cell on Sedan/TMeasy + UAZBUS/TMeasy; AVOIDANCE regime only)
- E1': DONE (M3259; oracle adequacy gate passed, spread revival not supported, structural gap +0.18 confirmed; AVOIDANCE regime only)
- E4: DONE (M3260; full Chrono drift / beyond-saturation pricing completed, with one positive low-mu power-oversteer cell and one near-neutral lift-off recovery cell; PI review completed 2026-06-14)
- E4 review: DONE (PI 2026-06-14) — Track F APPROVED at FULL-SCENARIO scope: ONE driver over avoidance + drift, per-regime teacher (drift teacher = specialized oracle, not CEM)
- F1: DONE (M3261; infra + smoke + throughput + projected 100M wall-clock completed: 48 steps, 2.1031 steps/s, 13207.81 h / 550.33 days projected for 100M; STOP for PI wall-clock review)
- F1b: DONE (M3263; 30 workers, closed-loop 1600.8440 steps/s, batched action-sequence 1967.0045 steps/s, projected 100M best wall-clock 14.12 h / 0.59 days; target >=1000 steps/s met; STOP for PI)
- F2 build: 3 passes + 3 adversarial reviews done (real PPO, B1-B6+M1-M7 fixed, verified); freeze blocked only on the drift-scenario alignment (S7)
- F4-align: DONE (stage 1, build pass) — aligned F2's drift VALIDATION cell + matched
  oracle + success criteria + S7 seeds to E4's frozen low_mu_power_oversteer. KEY
  CORRECTION: E4's +0.40 came from the per-cell SELECTED drift oracle, which the frozen
  E4 full artifact records as `beta0p28_recover` (8/20 = 0.40), NOT `beta0p22_power`
  (the old F2 binding, measured 0/20 ~0 on this cell — the true root cause of S7's
  恒-stop, on top of the short rollout horizon). Re-smoke (--quick) measured: drift
  oracle ceiling 0.40 on E4's 20 frozen seeds (drift floor 0.0 -> clears 0.0+0.40),
  S7 recommendation="proceed"/should_stop=False, gate s7_stop_loss_active_M4=True,
  both-branches honest (unreachable prize 1.0 -> stop). No regression: avoidance
  student/oracle 1.0, M3 BC frames 12, M1 parallel throughput, B1-B6/M1-M7 + all 45
  F2 tests green; incumbent untouched. prereg freeze_ready=true, frozen=false (PI
  freeze pending); claim_scope="stage-1 narrow drift probe (E4 low_mu_power_oversteer)
  + avoidance spectrum". Ignition-ready (S7 no longer blocks); PI freeze -> managed launch.
- E4-prime + F2-wide: QUEUED (stage 2 after stage-1 result: widen + re-price the drift surface, retrain F2 on the representative surface)
- Phase-5 G0 pre-slip reachable-set proof-route pricing: DONE / BLOCKED BY
  GATE (M3265). The known 0.20/0.26 rad/s positive control, search health,
  determinism, and Chrono tire telemetry passed, but deliberate-slide mode
  expressibility failed 0/3 full emergency cells (four-frame dwell 0/1/2).
  This is not a dominance result. Full dual-proof adjudication remains blocked
  until a separately preregistered mode-expressibility and slip-onset pricing
  unit passes without lowering the 0.12/0.20 rad ambiguous-band thresholds.
- Phase-5 G0b slide-mode expressibility + onset pricing: DONE / PASSED
  (M3266). Planar beta=0 entry passed 3/3; Chrono beta=0 direct entry reached
  four-frame onset at 0.50 s, max beta 0.484, rear slip 0.541, 72-frame dwell,
  and exact replay. This is pricing only. Final adjudication must use the OBB
  first-contact plane, controlled-slide constraints, and matched
  grip/required-slide/free minimum-clearable-distance oracles.
- Phase-5 G1 pre-slip reachable-set adjudication: DONE / INCONCLUSIVE AT QUICK
  (M3267); full was not run. Corrected Chrono quick passed local-frame and exact
  replay with all arms finite: grip/required-slide/free D* =
  18.8/21.7/16.1 m, and the free trajectory was grip-like. Planar grip/free
  were finite at 13.3/12.9 m, but required-slide D* was not found, so the
  frozen completeness gate blocked full and no M3267 dominance claim exists.
- Phase-5 G2 Chrono-only pre-slip boundary adjudication: DONE / INCONCLUSIVE AT
  QUICK (M3268); full was not run. Fresh grip/free D* were 18.6/16.2 m, but the
  required-slide seed missed the finite set. Frame/tire/replay passed, so this
  prices optimizer instability rather than physical emptiness.
- Phase-5 G3 exact-anchor Chrono adjudication: DONE / FULL INCONCLUSIVE (M3269);
  detailed-model optimizer branch CLOSED. Quick passed. Full finite cells
  favored pooled grip over required slide by 6.8 m at mu 0.60 and 3.9 m at
  mu 0.90, all best free trajectories were grip-like, and no counterexample
  appeared. But slide completeness was 0/2 at mu 0.35 and 1/2 at mu 0.90, so
  the frozen full gate failed. Do not register another local optimizer repair;
  retain the bounded theory theorem plus explicitly incomplete experiments.
- Phase-5 H0 fixed-library overlap certificate: DONE / PASSED (M3270). Frozen
  every unique best physical action sequence from M3267 corrected quick and
  M3269 full, including failed source searches, then exhaustively replay the
  20-sequence library on fresh seeds in the selected overlap cells. It
  completed 480/480 classification rows and 60/60 exact
  replays. All 24 fresh seeds were overlap-complete; grip beat required slide
  by 4.0-7.5 m and every free optimum was grip-like. This establishes only a
  finite-library/finite-cell numerical certificate alongside the bounded
  theorem; it does not reopen optimizer repair, overwrite M3269, or prove
  continuous Chrono control-set dominance. The separate corrected-semantics
  post-slip strict-recovery panel is now admissible.
- Phase-5 H1 post-slip nested-control recovery certificate: DONE / QUICK
  INCONCLUSIVE (M3271); full not run. Compared a six-policy zero-steer physical-pedal baseline with an
  expanded 30-policy set that contains it exactly and adds countersteer
  feedback. Old recovery audits are not admissible because normalized pedal
  zero was incorrectly treated as physical zero. Canonical quick must produce
  healthy strict witnesses on both mirrored states before the managed 18-cell,
  three-seed full panel. Uniform braking is not ESC, stopping sideways is not
  recovery, and any result remains finite-state/finite-policy only. Action,
  nesting, telemetry, weak-inclusion, and exact-replay gates passed, but direct
  body-state reset produced rear slip only 0.00136 rad despite beta 0.8. The
  injected state therefore failed the frozen initial-slide truth gate. One
  mirror side had no recovery while the other coasted to recovery in 0.54 s;
  neither was strict. Any follow-up must first price a common continuous slide-
  entry prefix and branch without resetting body/wheel/tire states.
- Phase-5 H2 dynamic-prefix nested recovery certificate: DONE / QUICK NO
  STRICT WITNESS (M3272); full not run.
  Replay the hash-frozen M3266 slide-entry action continuously, branch at five
  quick or twelve full times without resetting vehicle or tire state, and apply
  the unchanged M3271 nested recovery-policy sets. A branch is eligible only
  with four-frame beta dwell, rear slip >=0.15, four-wheel truth, and identical
  prefix/branch hashes across policies. Strictness requires baseline failure or
  at least 0.20 s earlier recovery with added steering. Quick must have 3/5
  eligible branches and one strict witness before managed full. Four of five
  quick branches were eligible and all action/hash/tire/replay health gates
  passed, but zero-steer throttle or braking matched the expanded optimum at
  every eligible branch; steering time advantage was 0.00 s. This is valid
  negative evidence: moderate real slide alone does not imply steering-based
  drift recovery is needed. No further local Chrono policy repair is admitted.
- Phase-5 H3 planar dynamic-prefix recovery certificate: DONE / QUICK NO
  STRICT WITNESS (M3273); full not run.
  Use all three M3266-priced compact-model slide-entry prefixes and the unchanged
  M3271 nested policy sets to test deeper complete-Markov-state branches. Quick
  has nine frozen branches and must yield at least six eligible plus two strict
  witnesses across two friction tiers. Any support is compact-model existence
  evidence only and must be reported beside, not instead of, M3272's valid
  Chrono negative. All 9/9 quick branches were eligible, but baseline and
  expanded recovery were both 0/9; 270/270 rows and 18/18 exact replays passed.
  Current-model post-slip strict work is closed. The supported final statement
  is only that pre-slip deliberate drift is unnecessary under the theorem and
  tested finite domain; post-slip added authority is potentially useful but
  neither automatic nor empirically strict in the current panels.
- WP6.2 guardrails: **MERGED** (commit 05607bcd — validator V7 live in the
  pre-commit hook, escalation protocol in docs/escalations/, managed-run
  helper scripts/run_managed.sh). Codex execution may begin.
