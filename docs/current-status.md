# Current Status

This file is the compact official state for the project. Milestone documents
and `docs/research-log.md` remain the detailed log of the autonomous-harness
era; the Phase-2 plan and thesis (pointer table below) define the active
program. Last full refresh: 2026-06-11 (WP6.3 of the Phase-2 plan; the
previous version was ~300 milestones stale and still pointed at the
abandoned paper route).

## Project Identity

- Repository: `general-evasive-driver`
- Python package: `autodrift`
- Working title: General Evasive Driver
- Core direction (Phase-2): capability-boundary tracking — when and how a
  driving policy at the handling limit needs a belief about its own
  capability envelope, on top of a certified reflex safety layer
  (the two-regime law).

## Project State: manual-takeover Phase-2

History in one paragraph: the autonomous harness loop ran 3214 numbered
milestones (M1–M3214; `experiments/research_status.json` records 3219
completed / 4 failed / 2 blocked task entries, `next_task: null`). On
2026-06-11 an independent feasibility audit showed the M3108–M3212
residual-repair branch was repairing physically unsolvable rows, and the
session was taken over manually (M3213 blocked;
`docs/feasibility-takeover-2026-06-route-decision.md`). The takeover route
then certified the reflex layer at the physical ceiling: oracle
certification measured all 7 residual hard-safety rows unrepairable by any
controller, causal or privileged (43,372 privileged rollouts, 7/7 hard-fail
in both tiers, `docs/feasibility-audit-oracle-certification-2026-06.md`);
feasible-row success is 55/55 on the fixed panel and 162/165 = 98.2% pooled
aeb_feasible with 0 collisions on all 172 feasible fresh-seed episodes
(`docs/feasibility-audit-stratified-panel-2026-06.md`); the HF4 dual-backend
measurement found 249/256 identical outcomes under Chrono::Vehicle with zero
new hard-safety failures
(`docs/feasibility-route-hf4-full-discrepancy-2026-06.md`). The ~1500-
milestone self-ID question was reformulated as capability-boundary tracking
(`docs/capability-boundary-tracking-thesis-2026-06.md`) and measured to the
**two-regime law**: under clean sensing, VoI(belief) = 0.000 at every reveal
window 9.5–30 m — a belief-free threshold-seeker matches the per-mu oracle;
under degraded sensing (delay/noise on the ego channels), belief value
revives to 0.17–0.88 in 12/14 cells (11/14 against the best belief-free
arm). Phase-2 (`docs/research-plan-phase2-capability-boundary-tracking.md`,
v2) started 2026-06-11 to test the law's generality (C1), belief
learnability (C2), FIR-vs-IIR (C3), and the deployable
belief→verifier→reflex stack (C4).

## Currently Running

- **WP0, week-1**: observation-degradation wrapper extension (AR(1)
  correlated noise, frame dropout, time-varying delay), family-#2 design
  freeze, clean-sensing acceptance; plus the week-1 governance items —
  WP6.0 (plan committed), WP6.1 (v5 promotion decision packet,
  `docs/v5-promotion-decision-packet-2026-06.md`), WP6.3 (this refresh and
  `scripts/feasibility_audit/README.md`).
- The autonomous milestone loop is **paused** and does not resume until the
  WP6.2 guardrails are implemented and smoke-tested.

## Pointer Table

| object | path |
|---|---|
| Governing thesis (two-regime law: Section 8) | `docs/capability-boundary-tracking-thesis-2026-06.md` |
| Phase-2 plan v2 (active program definition) | `docs/research-plan-phase2-capability-boundary-tracking.md` |
| Takeover decision (why M3213 was blocked) | `docs/feasibility-takeover-2026-06-route-decision.md` |
| Gate protocol v2 (anchors before informative actions; R²≤0.1 self-check) | `docs/selfid-gate-protocol-v2-2026-06.md` |
| Latest harness milestone (M3214: degradation pipeline + G1 ignition gate) | `docs/m3214-selfid-degradation-pipeline-integration-g1-ignition-gate.md` |
| Incumbent deployed driver (v4, untouched) | `src/autodrift/active_safety_reflex_driver.py`, `DRIVER_ID = active_safety_reflex_driver_m3105_incumbent_v4_no_regression` |
| v5 candidate (NOT promoted; decision pending with the PI) | `src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py` + `docs/v5-promotion-decision-packet-2026-06.md` |
| Measurement index (script → artifact → conclusion doc) | `scripts/feasibility_audit/README.md` |

## Hard Constraints (takeover discipline)

1. **The incumbent does not move.** `ActiveSafetyReflexDriver` (v4/M3105)
   stays the deployed driver; v5 remains a candidate until the promotion
   decision packet is adjudicated by the PI, and any merged controller must
   re-run the three pre-promotion panels (recovery / fixed feasible-row /
   fresh-seed) before WP2 consumes any recoverable-set surface.
2. **The autonomous loop stays paused** until the WP6.2 guardrails exist:
   pre-repair feasibility oracle gate, blocked-dependency escalation hook,
   managed-process rule for long measurements, and explicit paused/archived
   semantics for `experiments/research_queue.csv` /
   `experiments/research_status.json` / `experiments/scoreboard.csv`.
3. **Long measurements run as managed background processes only** (the
   agent-dies-measurement-dies failure occurred 3x and is a banned pattern).
4. **Acceptance criteria are pre-registered before any run**; selection /
   validation / training seed streams are mutually disjoint and frozen in
   pre-registration JSONs.
