# M3264 — Phase-4 F2 full managed launch (stage 1, 2026-06-14)

## Status

- F2 stage-1 full RL run LAUNCHED (PI authorization 2026-06-14, no time cap,
  bounded only by the step budget).
- managed run dir: `runs/managed/f2-full-stage1_20260614T100836Z/`
  (pid, command.txt, run.log, exit_code). Detached via setsid (survives the
  agent session, AGENTS.md rule 4).
- launch: `AUTODRIFT_F2_FULL_PI_AUTHORIZED=1 python
  scripts/feasibility_audit/phase4_f2_train.py --full --resume` via
  `scripts/run_managed.sh f2-full-stage1`.
- prereg frozen: `experiments/feasibility_audit/phase4_f2_prereg.json`
  (frozen=true, 2026-06-14); budget total_env_steps 48,250,880 (PPO 18.43M);
  no wall-clock cap.

## What it is

The decisive RL-vs-reflex experiment, stage 1 (narrow drift probe + avoidance
spectrum). Real asymmetric actor-critic: PPO clipped surrogate +
bootstrapped privileged GAE critic + policy gradient; per-regime teacher
(avoidance oracle reveal-post BC + E4 beta0p28_recover drift oracle) as
m1087 warm-start/annealed-auxiliary; 8 seeds, 30 Chrono workers, CPU.
Reached launch after 4 build passes + 3 adversarial reviews + the F4
drift-cell alignment; B1-B6 + M1-M7 all fixed and verified.

## Judging (F3, frozen)

Four arms (fixed* / RLS-retuned / per-instance-tuned / per-regime oracle) +
the trained student, per-regime AND pooled, dual readings (seed-robust
cross-training-seed paired t-CI + validated-best-seed); three prizes to beat
(avoidance +0.18, belief +0.77, drift +0.40) + all-regimes-no-regression;
B6 rank-biserial AUC>=0.9 hard gate; S7 stop-rule live.

## On completion

Poll `runs/managed/f2-full-stage1_20260614T100836Z/exit_code`; on exit 0 the
script writes the four-arm verdict. Then finalize M3264 + run F3 judging +
report the RL-vs-reflex result. Stage 2 (E4-prime + F2-wide) follows.

## Checkpoint / extension disposition (PI, 2026-06-14)

Crash-resume within the 48.25M budget is fully supported and active
(`--resume`; checkpoints save model + optimizer + RNG + update counter per
(seed,update); finished seeds marked DONE). Budget EXTENSION (48.25M ->
100M) is NOT wired as-is: it needs a small `--extend-to-updates` mode
(raise ppo_updates + continue past DONE seeds from their last checkpoint,
which already carry optimizer+RNG so continuation is seamless). PI decision
(option 2): do NOT pre-add the extension capability now. Wait for the 48.25M
verdict first; if RL clearly wins or loses, no extension is needed; if it is
"close but short", extension is reconsidered then AND, because that would be
deciding to train longer after seeing the result, it must be labelled a
post-hoc extension (or pre-declared) per the pre-registration discipline -
not a silent train-until-it-wins. Judging criteria stay frozen regardless.
