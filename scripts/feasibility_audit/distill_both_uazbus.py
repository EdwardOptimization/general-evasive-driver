"""CROSS-VEHICLE proof: a UAZBUS gated do-both driver (drift + avoid) by replicating
the PROVEN Sedan distill->DAgger recipe on UAZBUS.

WHY (docs/north-star-2026-06.md "(2) cross-vehicle DE-RISKED"): both teachers already
generalize to UAZBUS (2858 kg RWD/4WD high-CG, genuine contrast to the FWD Sedan) --
the de-risk PASSED: UAZBUS drifts sustain 90/90 at the re-tuned mu0.25/v6 cell with the
``uaz_ol_steer0p50`` DriftFeedbackPolicy spec, and the avoid oracle scores 1.0 on UAZBUS
even un-modified. So the do-both build is mostly PLUMBING (thread the UAZBUS variant +
params + the re-tuned drift cell through the distill/DAgger scenario construction) + the
proven distill->DAgger recipe.

WHAT this does (NEW FILE ONLY; imports the recipe machinery -- distill_both.py,
dagger_avoid.py/_v2.py -- VERBATIM; no protected module is modified):
  1. THREAD the UAZBUS variant + measured mass (2858) + the re-tuned mu0.25/v6 drift cell
     through the F2 scenario builders by monkeypatching the module-level scenario hooks
     (f2._avoidance_scenario, f2._drift_scenario, f2._drift_cell) and the drift demo
     teacher (the GPU drift EXPERT is replaced by the UAZBUS DriftFeedbackPolicy that the
     de-risk proved sustains 90/90). EVERY scenario the recipe constructs then carries
     chrono_vehicle_variant="uazbus_tmeasy" + params.mass=2858 (verified at runtime).
  2. DRIFT teacher = the UAZBUS DriftFeedbackPolicy (spec uaz_ol_steer0p50, the de-risk
     winner) on the mu0.25/v6 cell -- NOT the Sedan GPU expert. This tests whether the
     FEEDBACK teacher alone is enough to distill (UNLIKE the Sedan where the GPU expert
     was needed).
  3. AVOID teacher = make_avoidance_teacher (the un-modified Sedan-fitted oracle, which
     the de-risk showed scores 1.0 on UAZBUS) -- used as-is.
  4. Collect UAZBUS drift demos + UAZBUS avoid demos on Chrono -> BC-distill a FRESH gated
     AsymmetricActorCritic (distill_both.distill VERBATIM) -> multi-seed sweep + Chrono
     task-score selection (distill_both._chrono_select_eval VERBATIM) on a UAZBUS select
     namespace -> save distill_uazbus_policy.pt.
  5. Optional --dagger-rounds: DAgger continuation on the hard avoid cells (dagger_avoid
     machinery VERBATIM, on UAZBUS scenarios via the same patches) to close any imitation
     gap, with multi-seed Chrono-select and drift-held verification each round.

Then validate with a5_chrono_validate_uazbus.py (the UAZBUS A5: same frozen grid, UAZBUS
variant + the mu0.25 drift cell + the avoid grid).

Usage (base env has torch; ChronoWorkerClient spawns the chrono env itself):
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_uazbus.py \
        --workers 16 --drift-seeds 8 --avoid-seeds-per-cell 2 --epochs 4000 \
        --seed-sweep 4 --dagger-rounds 2 \
        --out runs/feasibility_audit/phase4_f2/distill_uazbus_policy.pt
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import phase4_f2_train as f2  # noqa: E402
import phase4_e4_drift_regime_pricing as e4  # noqa: E402  (DriftFeedbackPolicy/Spec, read-only)
import distill_both as db  # noqa: E402  (recipe machinery, imported VERBATIM)
import dagger_avoid as dag  # noqa: E402  (DAgger machinery, imported VERBATIM)
import cross_vehicle_uazbus_drift_derisk as uazdr  # noqa: E402  (the de-risked UAZBUS drift cell/scenario/spec)
from chrono_worker_client import ChronoWorkerClient, ChronoWorkerError  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"


# =====================================================================================
# Resilient Chrono client: the chrono worker subprocess occasionally dies on a hard solve
# (a known flakiness the de-risk scripts handle with their own _RestartingRunner). The
# recipe's parallel eval/rollout helpers (db._chrono_select_eval -> f2._eval_success_parallel,
# dag.collect_dagger) call client.reset/.step directly with NO restart, so one dead worker
# kills the whole run with a BrokenPipeError. This drop-in proxy presents the SAME
# reset/step/close interface but transparently respawns the underlying worker and retries
# on a broken pipe / worker error, so a single bad solve no longer aborts the build.
# =====================================================================================


class ResilientChronoClient:
    def __init__(self, *, stderr_log: Path | None = None, read_timeout_s: float = 600.0,
                 max_retries: int = 3):
        self._stderr_log = stderr_log
        self._read_timeout_s = read_timeout_s
        self._max_retries = int(max_retries)
        self._client = ChronoWorkerClient(stderr_log=stderr_log, read_timeout_s=read_timeout_s)
        self.backend_id = self._client.backend_id
        self._last_scenario = None
        self._last_episode_id = ""
        self._last_seed = None

    def _respawn(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
        self._client = ChronoWorkerClient(stderr_log=self._stderr_log, read_timeout_s=self._read_timeout_s)
        self.backend_id = self._client.backend_id

    def reset(self, scenario, *, episode_id: str = "", seed=None):
        self._last_scenario, self._last_episode_id, self._last_seed = scenario, episode_id, seed
        last_exc = None
        for _ in range(self._max_retries):
            try:
                return self._client.reset(scenario, episode_id=episode_id, seed=seed)
            except (BrokenPipeError, ChronoWorkerError, OSError) as exc:
                last_exc = exc
                self._respawn()
        raise last_exc

    def step(self, action):
        """On a mid-episode worker death we cannot faithfully resume the episode (the
        physics state is gone), so we respawn + re-reset and replay from t=0 is not
        possible cheaply; instead we raise so the caller's episode is counted as it
        stands. In practice reset is where the hard solves die, so this rarely fires."""
        try:
            return self._client.step(action)
        except (BrokenPipeError, ChronoWorkerError, OSError):
            # respawn so the NEXT episode on this client works; surface a terminal step
            # for the current one (finite zero obs -> the eval loop ends this episode).
            self._respawn()
            if self._last_scenario is not None:
                try:
                    self._client.reset(self._last_scenario, episode_id=self._last_episode_id, seed=self._last_seed)
                except Exception:
                    pass
            import numpy as _np
            return (_np.zeros(72, dtype=_np.float32), True, False, "worker_respawn",
                    {"termination_reason": "worker_respawn"})

    def step_many(self, actions):
        return self._client.step_many(actions)

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
DEFAULT_OUT = RUN_DIR / "distill_uazbus_policy.pt"

# --- the de-risked UAZBUS specifics (from cross_vehicle_uazbus_*_derisk.py) ------------------
VARIANT = uazdr.VARIANT  # "uazbus_tmeasy"
UAZBUS_MASS = uazdr.UAZBUS_MASS  # 2858.0 (backend overrides chassis mass from scenario params)

# The de-risked controllable-drift cell: mu0.25 / v6 / beta0.22 / yaw1.2 / r70 (sustain 90/90).
UAZBUS_DRIFT_CELL = {
    "cell_id": "uaz_mu0.25_v6_b0.22_y1.2_r70",
    "mu": 0.25,
    "speed_mps": 6.0,
    "initial_beta_rad": 0.22,
    "heading_error_rad": -0.10,
    "yaw_rate_scale": 1.20,
    "track_radius": 70.0,
    "track_width": uazdr.TRACK_WIDTH,
}

# The de-risk WINNER DriftFeedbackPolicy spec (uaz_ol_steer0p50): sustained controlled
# drift 90/90 on UAZBUS at the cell above (beta_max ~0.54). This is the drift TEACHER.
UAZBUS_DRIFT_SPEC = e4.DriftFeedbackSpec(
    name="uaz_ol_steer0p50",
    target_beta=0.45, beta_gain=0.30, yaw_gain=0.08, steer_ff=0.50,
    speed_target=18.0, throttle_gain=0.42, brake_gain=0.0,
)


# =====================================================================================
# PLUMBING: thread the UAZBUS variant + params + re-tuned drift cell through the recipe
# by replacing the F2 / distill_both module-level scenario+teacher hooks. The recipe
# machinery (distill_both, dagger_avoid) then constructs UAZBUS scenarios transparently.
# =====================================================================================

# Stash the original Sedan hooks (so we can verify the swap is real, not a no-op).
_ORIG_AVOID_SCENARIO = f2._avoidance_scenario
_ORIG_DRIFT_SCENARIO = f2._drift_scenario
_ORIG_DRIFT_CELL = f2._drift_cell
_ORIG_DB_DRIFT_SPECS = db._drift_specs
_ORIG_DB_LOAD_EXPERT = db.load_drift_expert


def _uaz_avoidance_scenario(seed: int, *, max_steps: int, reveal: float, mu: float) -> dict[str, Any]:
    """UAZBUS avoidance scenario: the EXACT F2 cross-vehicle scenario with the UAZBUS
    variant + measured mass threaded in (what the cross-vehicle build does). Mirrors the
    de-risk's _uaz_scenario (cross_vehicle_uazbus_avoid_derisk._uaz_scenario)."""
    reg, mod_b, interp = f2.f1._e2_context()
    import phase4_e2_chrono_two_regime_smoke as e2_smoke
    scenario = e2_smoke._make_scenario(reg, mod_b, interp, reveal=float(reveal), mu=float(mu),
                                       seed=int(seed), variant=VARIANT)
    scenario["params"]["mass"] = UAZBUS_MASS  # thread the real UAZBUS mass (default 1450 is NOT UAZBUS)
    scenario["scenario_id"] = f"uaz-avoidance-r{reveal:g}-mu{mu:.4f}-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


def _uaz_drift_scenario(seed: int, *, max_steps: int, difficulty: str = "hard") -> dict[str, Any]:
    """UAZBUS drift scenario on the de-risked mu0.25/v6 cell. Difficulty scales the entry
    beta exactly like F2's curriculum (DRIFT_DIFFICULTY_BETA_SCALE), so the demo set still
    covers easy/medium/hard entries. Reuses the de-risk's _scenario_for_uaz_cell (which is
    e4.scenario_for_cell with the UAZBUS variant + mass swapped in)."""
    cell = dict(UAZBUS_DRIFT_CELL)
    cell["initial_beta_rad"] = float(cell["initial_beta_rad"]) * float(
        f2.DRIFT_DIFFICULTY_BETA_SCALE.get(difficulty, 1.0))
    scenario = uazdr._scenario_for_uaz_cell(cell, seed=int(seed))
    scenario["scenario_id"] = f"uaz-drift-{difficulty}-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


def _uaz_drift_cell() -> dict[str, Any]:
    """The UAZBUS drift cell (the mu the recipe reads for drift-demo/select scenarios)."""
    return dict(UAZBUS_DRIFT_CELL)


def _uaz_drift_specs(n_seeds: int) -> list[dict]:
    """Drift demo scenarios on the UAZBUS cell across difficulties (disjoint 'distill' seed
    namespace), mirroring distill_both._drift_specs but on the UAZBUS mu/cell."""
    mu = float(UAZBUS_DRIFT_CELL["mu"])
    specs = []
    for diff in db.DRIFT_DIFFICULTIES:
        for i in range(n_seeds):
            seed = int(f2._seed_for("distill", "drift", diff, i))
            specs.append({
                "regime": "drift", "difficulty": diff, "seed": seed, "mu": mu, "reveal": 0.0,
                "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty=diff),
            })
    return specs


class _UazDriftExpert:
    """A drop-in for the GPU drift expert that distill_both.collect_demos drives on DRIFT
    specs (it calls ``expert.act(obs)`` once per step). Here .act() delegates to the UAZBUS
    DriftFeedbackPolicy -- the de-risked sustain-90 feedback teacher. A fresh policy per
    episode is NOT needed (DriftFeedbackPolicy is stateless given side), but we key on side
    from the cell's initial beta to mirror make_drift_teacher exactly."""

    def __init__(self) -> None:
        side = float(UAZBUS_DRIFT_CELL["initial_beta_rad"])
        self._policy = e4.DriftFeedbackPolicy(UAZBUS_DRIFT_SPEC, side=side)

    def act(self, obs: np.ndarray) -> np.ndarray:
        # collect_demos calls expert.act(obs) (no step index); DriftFeedbackPolicy ignores step.
        return np.asarray(self._policy(0, np.asarray(obs, dtype=np.float64)), dtype=np.float32)

    def eval(self):
        return self


def _load_uaz_drift_expert() -> _UazDriftExpert:
    print(f"DRIFT teacher = UAZBUS DriftFeedbackPolicy spec '{UAZBUS_DRIFT_SPEC.name}' "
          f"on cell {UAZBUS_DRIFT_CELL['cell_id']} (de-risk: sustain 90/90, beta_max ~0.54). "
          f"NOT the Sedan GPU expert.", flush=True)
    return _UazDriftExpert()


def _install_uazbus_patches() -> None:
    """Replace the Sedan scenario/teacher hooks with the UAZBUS ones, in BOTH f2 and db
    (distill_both binds some names at call time via f2.*, others via db.*)."""
    f2._avoidance_scenario = _uaz_avoidance_scenario
    f2._drift_scenario = _uaz_drift_scenario
    f2._drift_cell = _uaz_drift_cell
    db._drift_specs = _uaz_drift_specs
    db.load_drift_expert = _load_uaz_drift_expert


# =====================================================================================
# verification: confirm the scenarios actually carry the UAZBUS variant (not silently Sedan)
# =====================================================================================


def _verify_uazbus_scenarios(clients: list[ChronoWorkerClient]) -> dict[str, Any]:
    """Reset one drift + one avoid UAZBUS scenario on the REAL Chrono backend and confirm
    the backend reports chrono_vehicle_variant=uazbus_tmeasy + the UAZBUS total mass. This
    is the scoping's secondary risk ("verify the scenarios actually carry the UAZBUS variant
    else it silently runs the Sedan")."""
    client = clients[0]
    out: dict[str, Any] = {}
    # drift
    dr_scn = f2._drift_scenario(12345, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")
    _obs, reply = client.reset(dr_scn, episode_id="verify-drift", seed=1)
    bi = dict(reply.get("backend_info", {}))
    out["drift_scenario_variant_field"] = dr_scn.get("chrono_vehicle_variant")
    out["drift_scenario_mass_param"] = dr_scn.get("params", {}).get("mass")
    out["drift_backend_variant"] = bi.get("chrono_vehicle_variant")
    out["drift_backend_total_mass"] = bi.get("vehicle_total_mass")
    out["drift_cell_mu"] = dr_scn.get("params", {}).get("mu")
    # avoid
    av_scn = f2._avoidance_scenario(12345, max_steps=db.AVOID_MAX_STEPS, reveal=16.0, mu=0.5875)
    _obs, reply = client.reset(av_scn, episode_id="verify-avoid", seed=1)
    bi = dict(reply.get("backend_info", {}))
    out["avoid_scenario_variant_field"] = av_scn.get("chrono_vehicle_variant")
    out["avoid_scenario_mass_param"] = av_scn.get("params", {}).get("mass")
    out["avoid_backend_variant"] = bi.get("chrono_vehicle_variant")
    out["avoid_backend_total_mass"] = bi.get("vehicle_total_mass")
    out["all_uazbus"] = bool(
        out["drift_backend_variant"] == VARIANT and out["avoid_backend_variant"] == VARIANT)
    print("\n=== SCENARIO VARIANT VERIFICATION (real Chrono backend) ===", flush=True)
    print(f"  DRIFT: scenario.variant={out['drift_scenario_variant_field']} "
          f"params.mass={out['drift_scenario_mass_param']} mu={out['drift_cell_mu']} -> "
          f"backend variant={out['drift_backend_variant']} total_mass={out['drift_backend_total_mass']}",
          flush=True)
    print(f"  AVOID: scenario.variant={out['avoid_scenario_variant_field']} "
          f"params.mass={out['avoid_scenario_mass_param']} -> "
          f"backend variant={out['avoid_backend_variant']} total_mass={out['avoid_backend_total_mass']}",
          flush=True)
    print(f"  ALL scenarios carry UAZBUS variant (not silently Sedan): "
          f"{'YES' if out['all_uazbus'] else 'NO -- ABORT'}", flush=True)
    return out


# =====================================================================================
# main: collect -> distill (seed sweep + Chrono select) -> optional DAgger -> save
# =====================================================================================


def main() -> None:
    ap = argparse.ArgumentParser(description="UAZBUS cross-vehicle do-both driver (distill+DAgger recipe).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds", type=int, default=8, help="drift demo seeds PER difficulty (x3)")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="avoid demo seeds per reveal x mu cell (x20)")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=4)
    ap.add_argument("--select-avoid-units", type=int, default=16)
    ap.add_argument("--select-drift-units", type=int, default=8)
    # DAgger continuation (optional; close any avoid imitation gap on the hard cells)
    ap.add_argument("--dagger-rounds", type=int, default=0, help="0 = distill-only; >0 = DAgger continuation rounds")
    ap.add_argument("--dagger-seeds-per-cell", type=int, default=3)
    ap.add_argument("--dagger-hard-extra", type=int, default=5)
    ap.add_argument("--dagger-epochs", type=int, default=6000)
    ap.add_argument("--dagger-seed-sweep", type=int, default=6)
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    _install_uazbus_patches()
    print(f"[uaz-distill] variant={VARIANT} mass={UAZBUS_MASS} | "
          f"drift cell={UAZBUS_DRIFT_CELL['cell_id']} (mu{UAZBUS_DRIFT_CELL['mu']} v{UAZBUS_DRIFT_CELL['speed_mps']:g}) "
          f"spec={UAZBUS_DRIFT_SPEC.name}", flush=True)

    expert = _load_uaz_drift_expert()
    drift_specs = db._drift_specs(args.drift_seeds)
    avoid_specs = db._avoid_specs(args.avoid_seeds_per_cell)
    print(f"collecting demos on Chrono: {len(drift_specs)} drift + {len(avoid_specs)} avoid episodes, "
          f"{args.workers} workers", flush=True)

    clients = [ResilientChronoClient(stderr_log=RUN_DIR / f"uaz_distill_w{w}_stderr.log")
               for w in range(args.workers)]
    report: dict[str, Any] = {"variant": VARIANT, "mass": UAZBUS_MASS,
                              "drift_cell": UAZBUS_DRIFT_CELL, "drift_spec": UAZBUS_DRIFT_SPEC.__dict__}
    drift_demo = avoid_demo = None
    best = None  # (score, state_dict, stats, seed, sel)
    t0 = time.time()
    try:
        verify = _verify_uazbus_scenarios(clients)
        report["scenario_verification"] = verify
        if not verify["all_uazbus"]:
            raise SystemExit("FATAL: scenarios are NOT carrying the UAZBUS variant; aborting (would silently run Sedan).")

        drift_demo = db.collect_demos(clients, drift_specs, expert, label="DRIFT(uaz feedback)")
        avoid_demo = db.collect_demos(clients, avoid_specs, expert, label="AVOID(oracle)")
        if drift_demo["obs"].shape[0] == 0 or avoid_demo["obs"].shape[0] == 0:
            raise SystemExit("FATAL: a regime collected 0 demo frames; cannot distill.")
        report["drift_demo"] = {"frames": int(drift_demo["obs"].shape[0]),
                                "episodes": int(drift_demo["n_episodes"]),
                                "teacher_success": int(drift_demo["n_success"])}
        report["avoid_demo"] = {"frames": int(avoid_demo["obs"].shape[0]),
                                "episodes": int(avoid_demo["n_episodes"]),
                                "teacher_success": int(avoid_demo["n_success"])}

        # --- distill N seeds from the SAME demos; select by Chrono task score (recipe VERBATIM) ---
        per_seed = []
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- UAZBUS distill seed {s} ---", flush=True)
            m, st = db.distill(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                               holdout_frac=args.holdout_frac, seed=s)
            sel = db._chrono_select_eval(clients, m, n_avoid=int(args.select_avoid_units),
                                         n_drift=int(args.select_drift_units))
            av, dr = float(sel.get("avoidance", 0.0)), float(sel.get("drift", 0.0))
            print(f"  seed {s} CHRONO SELECT: avoid={av:.3f} drift={dr:.3f}", flush=True)
            st["select_avoid"] = av; st["select_drift"] = dr; st["distill_seed"] = s
            per_seed.append({"seed": s, "select_avoid": av, "select_drift": dr,
                             "drift_holdout_mse": st["drift_holdout_mse"], "avoid_holdout_mse": st["avoid_holdout_mse"]})
            score = (av, dr)
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
        report["distill_per_seed"] = per_seed

        model = f2.AsymmetricActorCritic(gated=True)
        model.load_state_dict(best[1])
        stats = best[2]
        print(f"\nSELECTED distilled seed {best[3]} "
              f"(Chrono select avoid={best[2]['select_avoid']:.3f} drift={best[2]['select_drift']:.3f})", flush=True)
        report["distill_selected"] = {"seed": int(best[3]), "select_avoid": float(best[2]["select_avoid"]),
                                      "select_drift": float(best[2]["select_drift"])}

        # --- optional DAgger continuation on the hard avoid cells (recipe VERBATIM on UAZBUS) ---
        dagger_history: list[dict] = []
        if int(args.dagger_rounds) > 0:
            print(f"\n######### DAgger continuation: {args.dagger_rounds} rounds (avoid head; drift frozen) #########",
                  flush=True)
            student = f2.AsymmetricActorCritic(gated=True)
            student.load_state_dict(best[1])
            student.eval()
            avoid_obs = avoid_demo["obs"].copy()
            avoid_act = avoid_demo["act"].copy()
            base_n = int(avoid_obs.shape[0])
            best_overall = (best[0], best[1], best[2], best[3])  # ((av,dr), state, stats, seed)
            for r in range(int(args.dagger_rounds)):
                print(f"\n========================= UAZBUS DAgger ROUND {r} =========================", flush=True)
                specs = dag._dagger_specs(args.dagger_seeds_per_cell, args.dagger_hard_extra, r)
                dagout = dag.collect_dagger(clients, specs, student)
                if dagout["obs"].shape[0] > 0:
                    avoid_obs = np.concatenate([avoid_obs, dagout["obs"]], 0)
                    avoid_act = np.concatenate([avoid_act, dagout["act"]], 0)
                aug_avoid = {"obs": avoid_obs, "act": avoid_act,
                             "n_episodes": avoid_demo["n_episodes"], "n_success": avoid_demo["n_success"]}
                print(f"  AUGMENTED avoid pool: {avoid_obs.shape[0]} frames "
                      f"(base {base_n} + DAgger {avoid_obs.shape[0]-base_n})", flush=True)
                rd_best, rd_per_seed = dag._redistill_select(
                    clients, drift_demo, aug_avoid, epochs=args.dagger_epochs, lr=args.lr, batch=args.batch,
                    holdout_frac=args.holdout_frac, seed0=args.seed, seed_sweep=args.dagger_seed_sweep,
                    select_avoid_units=args.select_avoid_units, select_drift_units=args.select_drift_units)
                (av, dr), state, rstats, win_seed = rd_best
                drift_regressed = [ps for ps in rd_per_seed if ps["select_drift"] < 0.999]
                if drift_regressed:
                    print(f"  !! drift < 1.000 on seeds {[(ps['seed'], ps['select_drift']) for ps in drift_regressed]}",
                          flush=True)
                print(f"\n  ROUND {r} SELECTED seed {win_seed}: select avoid={av:.3f} drift={dr:.3f}", flush=True)
                student = f2.AsymmetricActorCritic(gated=True)
                student.load_state_dict(state)
                student.eval()
                dagger_history.append({
                    "round": r, "select_avoid": av, "select_drift": dr, "win_seed": int(win_seed),
                    "aug_avoid_frames": int(avoid_obs.shape[0]), "dagger_round_labels": int(dagout["obs"].shape[0]),
                    "rollout_success": int(dagout["n_success"]), "rollout_offtrack": int(dagout["n_offtrack"]),
                    "rollout_collision": int(dagout["n_collision"]), "rollout_episodes": int(dagout["n_episodes"]),
                    "fail_cells": dagout["fail_cells"], "per_seed": rd_per_seed,
                    "drift_all_seeds_1000": bool(not drift_regressed),
                })
                if (av, dr) > best_overall[0]:
                    best_overall = ((av, dr), {k: v.clone() for k, v in state.items()}, rstats, win_seed)
            # adopt the best across distill + all DAgger rounds
            model = f2.AsymmetricActorCritic(gated=True)
            model.load_state_dict(best_overall[1])
            stats = best_overall[2]
            stats["select_avoid"] = float(best_overall[0][0]); stats["select_drift"] = float(best_overall[0][1])
            stats["distill_seed"] = int(best_overall[3])
            report["dagger_history"] = dagger_history
            report["final_selected"] = {"select_avoid": float(best_overall[0][0]),
                                        "select_drift": float(best_overall[0][1]), "seed": int(best_overall[3])}
            print(f"\nFINAL SELECTED (distill+DAgger): avoid={best_overall[0][0]:.3f} drift={best_overall[0][1]:.3f}",
                  flush=True)
    finally:
        for c in clients:
            c.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(), "gated": True,
        "label": "distill_both_uazbus", "variant": VARIANT, "mass": UAZBUS_MASS,
        "drift_teacher": f"uazbus_DriftFeedbackPolicy_{UAZBUS_DRIFT_SPEC.name}",
        "avoid_teacher": "make_avoidance_teacher_oracle",
        "drift_cell": UAZBUS_DRIFT_CELL, "drift_spec": UAZBUS_DRIFT_SPEC.__dict__,
        "drift_demo_frames": int(drift_demo["obs"].shape[0]),
        "avoid_demo_frames": int(avoid_demo["obs"].shape[0]),
        "scenario_verification": report.get("scenario_verification"),
        "dagger_rounds": int(args.dagger_rounds),
        **stats,
    }, out)
    report["elapsed_s"] = round(time.time() - t0, 1)
    report_path = RUN_DIR / "distill_uazbus_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nsaved UAZBUS distilled student -> {out}", flush=True)
    print(f"saved report -> {report_path}", flush=True)

    print("\n=== UAZBUS DISTILLATION REPORT ===", flush=True)
    print(f"  variant={VARIANT} mass={UAZBUS_MASS} verified={report.get('scenario_verification',{}).get('all_uazbus')}",
          flush=True)
    print(f"  DRIFT demos: {drift_demo['obs'].shape[0]} frames ({drift_demo['n_success']}/{drift_demo['n_episodes']} teacher-success)",
          flush=True)
    print(f"  AVOID demos: {avoid_demo['obs'].shape[0]} frames ({avoid_demo['n_success']}/{avoid_demo['n_episodes']} teacher-success)",
          flush=True)
    print(f"  drift holdout MSE = {stats['drift_holdout_mse']:.3e} | avoid holdout MSE = {stats['avoid_holdout_mse']:.3e}",
          flush=True)
    print(f"  SELECTED Chrono-select: avoid={stats['select_avoid']:.3f} drift={stats['select_drift']:.3f}", flush=True)
    print(f"\nNext (UAZBUS A5): PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate_uazbus.py "
          f"--policy {out} --avoid-units 40 --drift-units 20 --workers 16", flush=True)


if __name__ == "__main__":
    main()
