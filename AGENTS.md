# AGENTS.md — AutoDrift Phase-2 (manual-takeover era)

Full contract: `~/.agents/skills/autodrift-research-harness/SKILL.md`
(Phase-2 version, 2026-06-12). Read it before any work. Compact core:

1. **Read order**: `docs/current-status.md` (progress ledger, single source
   of truth) -> **`docs/roadmap-phase3-codex-execution.md` (the WHAT-NEXT
   queue: take the lowest-numbered OPEN unit, respect PI checkpoints)** ->
   `docs/research-plan-phase2-capability-boundary-tracking.md`
   -> `docs/capability-boundary-tracking-thesis-2026-06.md` ->
   `docs/data-coverage-map-2026-06.md` -> `scripts/feasibility_audit/README.md`.
2. **Feasibility-oracle-first**: no repair/improvement/training milestone
   without a pricing artifact proving the target is reachable and worth
   >= a pre-registered threshold. The 7 residual rows, the 3 drift_required
   rows (for the reflex family), and vehicle-spread reflex retuning are
   certified dead ends — auto-reject proposals targeting them.
3. **Pre-register before running** (`*_prereg.json`: criteria, honest
   floors = best belief-free/classical arm, matched-oracle anchors,
   disjoint seed streams); `--quick` smoke first.
4. **Long runs never live inside an agent session**: use
   `make research-run-next` or setsid/nohup + progress.jsonl + `--resume`.
5. **Stop rules**: 2x behavior-neutral on one target -> stop and re-price.
   Blocked dependency -> escalation note in `docs/escalations/` + queue row
   blocked; never bookkeeping loops.
6. **Milestone playbook** (M3215+): manifest with validator fields, queue
   row (csv lineterminator='\n'), `make research-validate` green in pending
   AND completed states, run via harness, doc + review + ledger update in
   `docs/current-status.md`. Strip trailing blank lines from
   `docs/research-log.md` before commit.
7. **Do not touch**: `ActiveSafetyReflexDriver` (v4 incumbent; v5 promotion
   deferred by PI). The autonomous loop stays paused until WP6.2 guardrails
   ship. RL/C5' work is judged engineering-only — no self-ID or
   history-attribution claims (thesis Section 10 explains why).
8. **Report format**: measured (with artifact paths) vs inferred, always
   separated; negatives at full fidelity.

Compute: CPU only (CUDA measured 2.6x slower for this model class);
parallelism = many single-thread processes (`OMP_NUM_THREADS=1`).
