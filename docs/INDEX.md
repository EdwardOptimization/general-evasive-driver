# AutoDrift — navigation index

The repo is large because the autonomous research process emits a load-bearing artifact tree
(`docs/m####-*.md` milestone records + generated `src/autodrift/*.py` + `experiments/manifests/*.json`),
enforced on every commit by `python -m autodrift.research_validate`. This index points to the
human-meaningful deliverables and findings amid that scaffolding.

## Core simulation + RL code (`src/autodrift/`)
- `dynamics.py` — single-track RWD vehicle, nonlinear tire saturation (friction-circle capped), DR params.
- `env.py` — Gymnasium env (obs72, friction step, obstacle task + scenario labels), `ObstacleTaskConfig`.
- `scenarios.py` — obstacle feasibility labels (aeb/aes/drift_required/unavoidable). **NOTE: the default
  `conventional_lateral_mu_fraction=0.42` understates real grip ~2x — see the foundation audit.**
- `policies.py` — baselines: `aeb`, `aes_heuristic`, `envelope_aes` (PRIVILEGED, invalid baseline), `honest_aes`,
  `mu_aware_aes` (mechanism probe).
- `vector_env.py`, `config.py`, `train_ppo.py`, `benchmark.py`, `evaluate.py` — training/eval harness.
- `gpu_env*.py`, `gpu_physics_pwr*.py`, `gpu_sim/` — fast GPU surrogate (pwrBD = faithful longitudinal config).

## Trained drivers (checkpoints under `runs/feasibility_audit/phase4_f2/`)
- `distill_final_robustified_capstone.pt` — the certified one-hot FiLM driver (drift+avoid spectrum x 3 vehicles,
  132/136 seed-clustered CI). Needs a vehicle one-hot label.
- `selfid_fullscenario_best.pt` — LABEL-FREE self-ID driver (infers vehicle from history; drift 1.0 + avoid 0.956).
- `selfid_rma_round1.pt` — avoid-only RMA self-ID (0.970, A-comparable).
- `runs/ppo_fullspectrum/fullspectrum_avoid_driver.pt` — full-spectrum avoidance PPO driver.

## Key findings (docs/, 2026-06)
- `two-regime-thesis-drift-2026-06.md` — **the headline**: drift is non-essential/counterproductive for avoidance
  BEFORE slip; active-steering closed-loop control is the rescue AFTER slip. Unifies the three directions below.
- `foundation-audit-drift-required-label-2026-06.md` — the `drift_required` label is built on a 2x-wrong grip
  assumption; 5 measurements (planar + Chrono) + adversarial verification show drift gives no avoidance advantage.
- `honest-avoidance-driver-2026-06.md` — the RL avoidance driver's real differentiator is closed-loop limit control
  (not drift, not mu-knowledge); fixed rules slide out even with true mu.
- `selfid-rma-experiment-2026-06.md` — replacing the vehicle one-hot with history-inferred RMA self-ID; recovers
  avoid + generalises to unseen vehicles (leave-one-out 0.965).
- `coverage-spectrum-design-2026-06.md` — the S1/S2/S3 spectrum, cross-vehicle, certification, perception-DR.
- `multi-fidelity-gpu-rewrite-design-2026-06.md`, `m5-emergency-avoidance.md` — GPU rewrite + M5 obstacle taxonomy.

## Reproducible audits (`scripts/audits/`)
- `measure_env_lateral_capacity.py` — env's real conventional vs drift lateral force capacity.
- `drift_reachability.py` / `box_reachability.py` / `box_reachability_angled.py` — CG + oriented-box avoidance
  reachability (drift gives no edge, even angled/extended).
- `chrono_drift_reachability.py` — faithful-Chrono confirmation.
- `recovery_reachability.py` — direction-1 slide-recovery (steering vs brake-only ESC).

## Session experiment scripts (`scripts/feasibility_audit/`)
185 files — the F2/capstone/self-ID pipeline (e.g. `distill_both_final_integrated.py`, `distill_both_3vehicle_film.py`,
`phase4_f2_train.py`, `selfid_models.py`, `_selfid_*.py`, `_s3_*.py`). The `_`-prefixed ones are one-off
analysis/validation scripts for specific milestones.

## Process scaffolding (do not hand-edit)
- `docs/m####-*.md` (3263) + `experiments/manifests/*.json` (3183) + `experiments/research_queue.csv` — the
  autonomous research-process state, required by the `research_validate` commit hook. `scratch/` (gitignored) holds
  throwaway debug probes. `runs/` (gitignored, ~28GB) holds training/eval artifacts.
