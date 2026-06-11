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
  default forward path is therefore C5'-main (structural-ceiling prize),
  pending CP-1. PI may override at CP-1.

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

### C1. Oracle demo generator + BC warm-start [BLOCKED on CP-1]
- per-instance oracle demos on the frozen C5' cells; BC with DAgger-lite +
  held-out epoch selection (the G1' lessons are mandatory); capacity and
  seed discipline per the WP1 pattern.
### C2. Capability pretrain + guarded RL smoke [BLOCKED on C1]
- envelope-head pretrain; 1024-step guarded RL smoke first; reward
  recalibration 40/60 as measured; judging prereg frozen before any full
  run (engineering-only, four-arm, frozen validation seeds).
### C3. Staged scale-up [BLOCKED on C2]
- **CP-2 (PI checkpoint)** before any run > 1 h compute: PI confirms budget.
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

## Out of scope for Codex sessions

- Papers (WP5): Claude + PI via the ARS pipeline.
- v5 promotion: deferred by PI until research completion.
- Anything touching `ActiveSafetyReflexDriver` or loosening a frozen
  criterion. Guardrails are merged in commit 05607bcd; autonomous/Codex
  sessions still follow this ordered roadmap and PI checkpoints.

## Status lines (update in place)

- A1: DONE (M3220; 0/4 cells qualified under cg/Iz S4L rider)
- A2: DONE (M3221; normalization/preview implementation blocker found)
- A3: DONE (M3222; C5-prime target confirmed 3/4 T-limit cells; CP-1 still required)
- B1: DONE (M3223; flagged constant-velocity crosser smoke passed)
- B2: DONE (M3224; explicit 36 m/s normalization/preview smoke passed)
- B3: DONE (M3225; geometry-channel degradation smoke passed; split-mu not expressible on the DriftObstacleEnv single-track path)
- B4: DONE (M3226; 60 s warmup-to-obstacle-to-post-pass continuation smoke passed)
- C1-C3: BLOCKED on CP-1
- D1: DONE (M3227; Chrono multi-vehicle direction-pricing reversed in all three variants)
- WP6.2 guardrails: **MERGED** (commit 05607bcd — validator V7 live in the
  pre-commit hook, escalation protocol in docs/escalations/, managed-run
  helper scripts/run_managed.sh). Codex execution may begin.
