# Escalation: Phase-4 CP-3 Track-F PI Checkpoint

- date: 2026-06-13
- blocked branch: phase4_track_f_cp3_checkpoint
- blocked milestones: m3256-phase4-cp3-track-f-pi-checkpoint

## What is blocked

Track E is complete on the default Sedan/TMeasy Chrono fixture: M3250 closed
E1 negative, M3252 completed the full E2 verdict, and M3255 completed the
full E3 detector-latency/recovery-budget panel with CP-3 evidence ready.
The roadmap still forbids any Track F run beyond smoke until PI CP-3 confirms
the targets and GPU-days budget. Therefore F1 vectorized Chrono training
infrastructure, F2 asymmetric actor-critic/teacher-student training, and F3
judging preregistration are blocked on the missing PI CP-3 decision.

## Resume condition

Resume only when PI records a CP-3 disposition that either approves Track F
targets and budget, rejects Track F, or requests a concrete additional
preregistered pricing/measurement unit. If approved, the next queue row must
start no broader than F1 training infrastructure and must still obey
feasibility-oracle-first pricing, preregistration, CPU/compute discipline,
managed runs, and the no-self-ID claim boundary.

## Who can unlock it

PI owns CP-3. This file is the repository-side record that Codex execution has
finished Track E and must not self-approve robotics-parity RL or create
bookkeeping milestones while waiting for the CP-3 decision.

## Resolution (filled in when unblocked)

- date: 2026-06-13
- outcome: CP-3 disposition A (PI) — harden Track E before any GPU. The E2
  flip (clean VoI(belief) > 0 in Chrono) is the program's most consequential
  result but every Track-E full was smoke-scale in power. New OPEN units
  (Track E' in the roadmap): E3-fix (detector-onset reconciliation, first),
  then E2' (>= 30 seeds/cell, >= 2 vehicles, frozen flip-confirmation gate)
  and E1' (oracle-adequate spread repricing). Track F GPU budget is NOT
  approved; it is reconsidered only if E2' confirms the flip. Codex resumes
  on E3-fix.
- followup (GPU-days checkpoint): PI FULL APPROVAL 2026-06-13 — Track F at 100M env steps, no time limit, no intermediate budget gate. F1 builds infra + smoke + throughput (make-it-work, not a gate), then proceeds directly to the 100M managed run; judging prereg frozen before launch. Track F OPEN at F1.