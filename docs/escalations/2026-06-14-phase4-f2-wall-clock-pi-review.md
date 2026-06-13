# Escalation: Phase-4 F2/F3 Wall-Clock PI Review

- date: 2026-06-14
- blocked branch: phase4_track_f_f2_wall_clock_pi_checkpoint
- blocked milestones: m3262-phase4-f2-wall-clock-pi-review

## What is blocked

M3261 completed F1 training infrastructure after the post-E4 PI disposition:
preregistration and quick smoke preceded the full run, mixed avoidance/drift
Chrono worker rollout passed, obs72/action3 and finite torch-update gates
passed, and the run reported the F2 compute-cost evidence PI requested before
the 100M-step launch.

The measured F1 projection is expensive enough that the roadmap requires a
hard stop before F2:

- aggregate throughput: 2.1031 Chrono steps/s
- projected 100M-step wall-clock: 13207.81 h / 550.33 days
- CUDA update throughput on the measured batch: 0.00415x CPU

PI then requested an F1b optimization rather than treating the M3261 projection
as final. M3263 completed that optimization:

- Chrono workers: 30
- closed-loop one-step throughput: 1600.8440 steps/s
- batched action-sequence throughput: 1967.0045 steps/s
- projected 100M-step best wall-clock: 14.12 h / 0.59 days
- PI target: >=1000 steps/s, met

Therefore F2 asymmetric actor-critic / teacher-student training and F3 judging
remain blocked on PI review of the F1b throughput report and explicit go.
Codex must not launch F2/F3, create policy checkpoints, tune criteria, or
interpret M3261/M3263 as driver performance evidence.

## Resume condition

Resume only when PI records one of these dispositions:

- approve F2/F3 with the measured F1b wall-clock accepted;
- revise the F2 scale, worker topology, or compute plan as a concrete
  preregistered unit;
- reject or defer F2/F3.

If approved, the next executable queue row must be no broader than the F2
preregistration / managed-run setup described in the roadmap. The full 100M
training run must be launched only as a managed background process with
progress artifacts and resume support, never inside an agent session.

## Who can unlock it

PI owns the wall-clock/go decision. This file is the repository-side record
that Codex execution has reached the F1b stop and must not self-approve the
robotics-parity RL launch.
