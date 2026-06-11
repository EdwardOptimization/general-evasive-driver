"""Value-of-Information (VoI) measurement for the CURRENT task family.

Hypothesis under test: ~1500 null self-ID milestones are explained by the task
design never making the hidden parameter worth knowing (VoI ~ 0), rather than
by self-ID being impossible.

Definition (per scenario skeleton s):
    VoI(s) = E_theta[per-theta oracle best outcome]
             - max_{fixed plan p} E_theta[outcome of p]
where theta = the post-friction-step hidden friction mu, the fixed-plan
expectation is uniform over the theta grid, and "outcome" is reported both as
episode return (sum of env rewards) and success (outcome_bucket ==
success_obstacle_pass).

Task faces (representative of what the ~1500 milestones actually trained on):
  - g1_clean:      runs/feasibility_audit/selfid_g1_ignition_gate/configs/
                   clean_seed710001.json env block (M3214 G1 ignition gate env;
                   observation_degradation is 0/0 there and is dropped because
                   all plans here are open-loop).
  - m3012 specs 0001 / 0010 / 0011: the friction-step-enabled members of the
                   16 M3012 executable source specs (mu_nominal|mu_drop,
                   late_brake_low|late_brake_high, mu_recover|mu_low).
  Faces whose hidden mu is episode-constant AND friction-limits the sampled
  initial speed (specs 0002-0007, 0009, 0012, 0013, 0015, 0016) are excluded:
  there the initial state itself depends on mu, so a "same skeleton, different
  theta" intervention does not exist (documented limitation).

Skeleton construction / theta intervention:
  Arms differ ONLY in friction_step.mu_range = (theta, theta). Because every
  rng draw consumes the same stream positions regardless of the uniform bounds,
  reset(seed) produces bit-identical vehicle params (incl. pre-step mu),
  speed_ref, beta_target, initial pose, obstacle geometry and friction_step_at
  across arms; the single divergence is the mid-episode mu switch value.
  This is asserted at runtime for every skeleton.

Oracle / fixed-plan machinery (reused from oracle_certification.py):
  - per-arm oracle: structured open-loop candidates + CEM over
    piecewise-constant action segments, maximizing return.
  - fixed plans: each arm's best open-loop sequence replayed on the other arms
    (hold-last-action), 3 structured robust archetypes x 2 steer directions,
    plus a robust-CEM plan optimized for MEAN return across the 4 arms.
  - dominance closure: each arm's oracle is finally max'ed over every fixed
    plan evaluated on that arm, so VoI >= 0 numerically by construction.

Pure CPU / numpy, deterministic seeds, no policy training.
Run:  PYTHONPATH=src python scripts/feasibility_audit/voi_current_task_family.py
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.config import build_env_config, merge_env_config
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import outcome_bucket_from_info

REPO = Path(__file__).resolve().parents[2]

G1_CONFIG_PATH = REPO / "runs/feasibility_audit/selfid_g1_ignition_gate/configs/clean_seed710001.json"
M3012_SPECS_PATH = REPO / (
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_env_materialization_preflight/executable_source_specs.json"
)

THETA_GRID = (0.30, 0.55, 0.80, 1.05)
BASE_SEED = 20260611
N_SEGMENTS = 18

FACES = (
    {"face_id": "g1_ignition_gate_clean", "kind": "g1", "n_skeletons": 12, "seed_start": 910001},
    {"face_id": "m3012_spec0001_mu_nominal_drop", "kind": "m3012", "spec_index": 0, "n_skeletons": 4, "seed_start": 920001},
    {"face_id": "m3012_spec0010_late_brake", "kind": "m3012", "spec_index": 9, "n_skeletons": 4, "seed_start": 930001},
    {"face_id": "m3012_spec0011_mu_recover", "kind": "m3012", "spec_index": 10, "n_skeletons": 4, "seed_start": 940001},
)


# --------------------------------------------------------------------------- env


def load_face_env_dicts() -> list[dict[str, Any]]:
    faces = []
    g1_env = json.loads(G1_CONFIG_PATH.read_text())["env"]
    degradation = g1_env.pop("observation_degradation", None)
    specs = json.loads(M3012_SPECS_PATH.read_text())["executable_source_specs"]
    for face in FACES:
        face = dict(face)
        if face["kind"] == "g1":
            face["env_dict"] = g1_env
            face["env_source"] = str(G1_CONFIG_PATH.relative_to(REPO)) + "#env"
            face["note"] = f"observation_degradation dropped (was {degradation}; open-loop plans ignore observations)"
        else:
            spec = specs[face["spec_index"]]
            face["env_dict"] = spec["env_config"]
            face["env_source"] = (
                str(M3012_SPECS_PATH.relative_to(REPO)) + f"#{spec['executable_source_spec_id']}"
            )
            face["capability_pair"] = spec["capability_pair"]
        faces.append(face)
    return faces


def build_arm_env(env_dict: dict[str, Any], theta: float) -> AutoDriftEnv:
    merged = merge_env_config(env_dict, {"friction_step": {"mu_range": [theta, theta]}})
    return AutoDriftEnv(build_env_config(merged))


# ----------------------------------------------------------------------- rollout


def rollout_plan(env: AutoDriftEnv, seed: int, actions: np.ndarray) -> dict[str, Any]:
    """Open-loop rollout; hold last action after the sequence ends."""
    _obs, info = env.reset(seed=seed)
    total_reward = 0.0
    terminated = truncated = False
    t = 0
    applied: list[np.ndarray] = []
    n = len(actions)
    while not (terminated or truncated):
        action = actions[t] if t < n else actions[n - 1]
        applied.append(np.asarray(action, dtype=np.float64))
        _obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)
        t += 1
    bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
    return {
        "return": total_reward,
        "success": 1.0 if bucket == "success_obstacle_pass" else 0.0,
        "outcome_bucket": bucket,
        "steps": int(info.get("step", t)),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "mu_post": float(info.get("mu", float("nan"))),
        "applied_actions": applied,
    }


# ------------------------------------------------------------------- candidates


def segments_to_actions(segments: np.ndarray, seg_len: int) -> np.ndarray:
    return np.repeat(np.clip(segments, -1.0, 1.0), seg_len, axis=0)


def actions_to_segments(actions: np.ndarray, n_segments: int, seg_len: int) -> np.ndarray:
    segments = np.zeros((n_segments, 3), dtype=np.float64)
    fallback = actions[-1] if len(actions) else np.array([0.0, -1.0, 1.0])
    for k in range(n_segments):
        chunk = actions[k * seg_len : (k + 1) * seg_len]
        segments[k] = np.mean(chunk, axis=0) if len(chunk) else fallback
    return np.clip(segments, -1.0, 1.0)


def robust_archetype_plans(tto_steps: int, horizon: int) -> list[tuple[str, np.ndarray]]:
    """3 structured robust archetypes x 2 steer directions (theta-independent)."""
    plans = []
    for direction in (1.0, -1.0):
        tag = "left" if direction > 0 else "right"
        # conservative low speed: full brake, gentle swerve, recenter
        n1 = max(6, int(1.2 * tto_steps))
        cons = np.tile([direction * 0.4, -1.0, 1.0], (horizon, 1))
        cons[n1:] = [0.0, -1.0, 1.0]
        plans.append((f"robust_conservative_{tag}", cons))
        # moderate: half brake, firmer swerve, counter-steer, recenter
        n2 = max(5, int(0.8 * tto_steps))
        mod = np.tile([direction * 0.55, -1.0, 0.0], (horizon, 1))
        mod[n2 : n2 + 10] = [-direction * 0.3, -1.0, 0.0]
        mod[n2 + 10 :] = [0.0, -1.0, 0.5]
        plans.append((f"robust_moderate_{tag}", mod))
        # aggressive: keep speed, sharp swerve, counter-steer, recenter
        n3 = max(4, int(0.6 * tto_steps))
        agg = np.tile([direction * 0.85, 0.0, -1.0], (horizon, 1))
        agg[n3 : n3 + 12] = [-direction * 0.5, 0.0, -1.0]
        agg[n3 + 12 :] = [0.0, -0.5, -1.0]
        plans.append((f"robust_aggressive_{tag}", agg))
    return plans


def structured_candidates(tto_steps: int, horizon: int) -> list[tuple[str, np.ndarray]]:
    candidates: list[tuple[str, np.ndarray]] = []

    def const(action: list[float]) -> np.ndarray:
        return np.tile(np.asarray(action, dtype=np.float64), (horizon, 1))

    candidates.append(("full_brake_straight", const([0.0, -1.0, 1.0])))
    for s in (0.2, 0.5, 0.9, -0.2, -0.5, -0.9):
        candidates.append((f"brake_steer_{s:+.1f}", const([s, -1.0, 1.0])))
    for s in (0.3, 0.7, -0.3, -0.7):
        candidates.append((f"coast_steer_{s:+.1f}", const([s, -1.0, -1.0])))
    for s in (0.05, 0.12):
        candidates.append((f"throttle_track_{s:+.2f}", const([s, 0.0, -1.0])))
    for s in (0.6, 1.0, -0.6, -1.0):
        for frac in (0.5, 0.9):
            n = max(4, int(frac * tto_steps))
            seq = const([s, -1.0, 1.0])
            seq[n:] = [0.0, -1.0, 1.0]
            candidates.append((f"swerve_recenter_{s:+.1f}_f{frac}", seq))
    candidates.extend(robust_archetype_plans(tto_steps, horizon))
    return candidates


# ------------------------------------------------------------------------ search


def cem_search(
    score_fn,
    init_mean: np.ndarray,
    rng: np.random.Generator,
    population: int,
    elites: int,
    iterations: int,
) -> tuple[np.ndarray, list[dict[str, float]]]:
    """Generic CEM over [-1,1]^(n_segments x 3); score_fn(segments) -> float."""
    mean = init_mean.copy()
    std = np.full_like(mean, 0.5)
    history = []
    for iteration in range(iterations):
        samples = np.clip(
            rng.normal(loc=mean[None], scale=std[None], size=(population, *mean.shape)), -1.0, 1.0
        )
        scores = np.array([score_fn(samples[i]) for i in range(population)])
        order = np.argsort(-scores)
        elite = samples[order[:elites]]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), 0.05)
        history.append(
            {"iteration": iteration, "best_score": float(scores[order[0]]),
             "elite_mean_score": float(scores[order[:elites]].mean())}
        )
    return mean, history


def summarize_rollout(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "return": round(result["return"], 4),
        "success": result["success"],
        "outcome_bucket": result["outcome_bucket"],
        "steps": result["steps"],
        "min_clearance_margin": round(result["min_clearance_margin"], 4)
        if math.isfinite(result["min_clearance_margin"]) else None,
    }


def process_skeleton(job: dict[str, Any]) -> dict[str, Any]:
    """Full per-skeleton pipeline: 4 per-theta oracles + fixed-plan baseline."""
    env_dict = job["env_dict"]
    seed = job["seed"]
    budget = job["budget"]
    started = time.time()

    envs = {theta: build_arm_env(env_dict, theta) for theta in THETA_GRID}

    # ---- skeleton descriptor + cross-arm invariance assertion
    descriptors = {}
    for theta, env in envs.items():
        _obs, info = env.reset(seed=seed)
        descriptors[theta] = {
            "mu_pre": float(info["mu"]),
            "speed_ref": float(info["speed_ref"]),
            "beta_target": float(info["beta_target"]),
            "friction_step_at": int(info["friction_step_at"]),
            "obstacle_distance": float(info["obstacle_distance"]),
            "obstacle_half_width": float(env.obstacle_scenario.obstacle_half_width),
            "obstacle_label_at_mu_pre": str(info["obstacle_label"]),
            "obstacle_position": [float(v) for v in env.obstacle_position],
        }
    ref = descriptors[THETA_GRID[0]]
    for theta in THETA_GRID[1:]:
        d = descriptors[theta]
        for key in ("mu_pre", "speed_ref", "beta_target", "obstacle_distance", "obstacle_half_width"):
            assert abs(d[key] - ref[key]) < 1e-12, (job["skeleton_id"], theta, key)
        assert d["friction_step_at"] == ref["friction_step_at"], (job["skeleton_id"], theta)
        assert d["obstacle_label_at_mu_pre"] == ref["obstacle_label_at_mu_pre"]

    dt = float(envs[THETA_GRID[0]].config.dt)
    tto_steps = max(4, int(round(ref["obstacle_distance"] / max(ref["speed_ref"], 1e-6) / dt)))
    seg_len = max(6, int(math.ceil((tto_steps + 50) / N_SEGMENTS)))
    horizon = N_SEGMENTS * seg_len
    reveal_step = int(envs[THETA_GRID[0]].config.obstacle.perception_reveal_step)

    rollout_counter = {"n": 0}

    def run(theta: float, actions: np.ndarray) -> dict[str, Any]:
        rollout_counter["n"] += 1
        return rollout_plan(envs[theta], seed, np.asarray(actions, dtype=np.float64))

    # ---- per-theta oracle search (structured + CEM, maximize return)
    arm_best: dict[float, dict[str, Any]] = {}
    arm_success_found: dict[float, bool] = {}
    structured = structured_candidates(tto_steps, horizon)
    for arm_index, theta in enumerate(THETA_GRID):
        best = None
        success_found = False
        best_structured_segments = None
        best_structured_score = -np.inf
        for name, actions in structured:
            result = run(theta, actions)
            success_found = success_found or result["success"] > 0
            if best is None or result["return"] > best["return"]:
                best = {**result, "kind": f"structured:{name}"}
            segs = actions_to_segments(actions, N_SEGMENTS, seg_len)
            if result["return"] > best_structured_score:
                best_structured_score = result["return"]
                best_structured_segments = segs

        rng = np.random.default_rng(BASE_SEED + 1000 * job["skeleton_index"] + arm_index)

        def score_fn(segments: np.ndarray) -> float:
            nonlocal best, success_found
            result = run(theta, segments_to_actions(segments, seg_len))
            success_found = success_found or result["success"] > 0
            if result["return"] > best["return"]:
                best = {**result, "kind": "cem"}
            return result["return"]

        _mean, cem_history = cem_search(
            score_fn, best_structured_segments, rng,
            budget["cem_population"], budget["cem_elites"], budget["cem_iterations"],
        )
        best["cem_history_first_last"] = [cem_history[0], cem_history[-1]] if cem_history else []
        arm_best[theta] = best
        arm_success_found[theta] = success_found

    # ---- fixed plan set
    plans: list[tuple[str, np.ndarray]] = []
    for theta in THETA_GRID:
        plans.append((f"oracle_replay_theta_{theta:.2f}",
                      np.asarray(arm_best[theta]["applied_actions"], dtype=np.float64)))
    plans.extend(robust_archetype_plans(tto_steps, horizon))

    # robust CEM: maximize MEAN return across the 4 arms
    plan_matrix_partial = {}
    for name, actions in plans:
        plan_matrix_partial[name] = [run(theta, actions) for theta in THETA_GRID]
    best_seed_plan = max(plan_matrix_partial, key=lambda n: np.mean([r["return"] for r in plan_matrix_partial[n]]))
    seed_actions = dict(plans)[best_seed_plan]
    robust_init = actions_to_segments(np.asarray(seed_actions, dtype=np.float64), N_SEGMENTS, seg_len)
    robust_rng = np.random.default_rng(BASE_SEED + 1000 * job["skeleton_index"] + 777)
    robust_best = {"mean_return": -np.inf, "segments": robust_init}

    def robust_score(segments: np.ndarray) -> float:
        actions = segments_to_actions(segments, seg_len)
        mean_return = float(np.mean([run(theta, actions)["return"] for theta in THETA_GRID]))
        if mean_return > robust_best["mean_return"]:
            robust_best["mean_return"] = mean_return
            robust_best["segments"] = segments.copy()
        return mean_return

    _mean, robust_history = cem_search(
        robust_score, robust_init, robust_rng,
        budget["robust_population"], budget["robust_elites"], budget["robust_iterations"],
    )
    plans.append(("robust_cem_mean_return", segments_to_actions(robust_best["segments"], seg_len)))

    # ---- evaluate every plan on every arm
    plan_rows = []
    plan_eval: dict[str, list[dict[str, Any]]] = {}
    for name, actions in plans:
        results = plan_matrix_partial.get(name) or [run(theta, actions) for theta in THETA_GRID]
        plan_eval[name] = results
        plan_rows.append(
            {
                "plan": name,
                "mean_return": float(np.mean([r["return"] for r in results])),
                "mean_success": float(np.mean([r["success"] for r in results])),
                "per_theta": {f"{theta:.2f}": summarize_rollout(r) for theta, r in zip(THETA_GRID, results)},
            }
        )

    # ---- oracle dominance closure over the fixed plan set
    oracle_return = {}
    oracle_success = {}
    for i, theta in enumerate(THETA_GRID):
        best_plan_return = max(plan_eval[name][i]["return"] for name in plan_eval)
        any_plan_success = any(plan_eval[name][i]["success"] > 0 for name in plan_eval)
        oracle_return[theta] = max(arm_best[theta]["return"], best_plan_return)
        oracle_success[theta] = 1.0 if (arm_success_found[theta] or any_plan_success) else 0.0

    best_fixed_return = max(row["mean_return"] for row in plan_rows)
    best_fixed_return_plan = max(plan_rows, key=lambda r: r["mean_return"])["plan"]
    best_fixed_success = max(row["mean_success"] for row in plan_rows)
    best_fixed_success_plan = max(plan_rows, key=lambda r: (r["mean_success"], r["mean_return"]))["plan"]

    oracle_mean_return = float(np.mean(list(oracle_return.values())))
    oracle_mean_success = float(np.mean(list(oracle_success.values())))

    for env in envs.values():
        env.close()

    return {
        "skeleton_id": job["skeleton_id"],
        "face_id": job["face_id"],
        "seed": seed,
        "skeleton": {
            **ref,
            "tto_steps": tto_steps,
            "reveal_step": reveal_step,
            "steps_between_mu_switch_and_obstacle": tto_steps - ref["friction_step_at"],
            "segment_length_steps": seg_len,
            "searched_horizon_steps": horizon,
        },
        "theta_grid": list(THETA_GRID),
        "oracle_per_theta": {
            f"{theta:.2f}": {
                **summarize_rollout(arm_best[theta]),
                "kind": arm_best[theta]["kind"],
                "closed_return": round(oracle_return[theta], 4),
                "closed_success": oracle_success[theta],
            }
            for theta in THETA_GRID
        },
        "plans": plan_rows,
        "best_fixed_plan": {
            "by_return": {"plan": best_fixed_return_plan, "mean_return": round(best_fixed_return, 4)},
            "by_success": {"plan": best_fixed_success_plan, "mean_success": round(best_fixed_success, 4)},
        },
        "oracle_mean_return": round(oracle_mean_return, 4),
        "oracle_mean_success": round(oracle_mean_success, 4),
        "voi_return": round(oracle_mean_return - best_fixed_return, 4),
        "voi_success": round(oracle_mean_success - best_fixed_success, 4),
        "robust_cem_history_first_last": [robust_history[0], robust_history[-1]] if robust_history else [],
        "rollouts": rollout_counter["n"],
        "elapsed_s": round(time.time() - started, 1),
    }


# ------------------------------------------------------------------------ main


def aggregate(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = np.array([row[key] for row in rows], dtype=np.float64)
    return {
        "mean": round(float(values.mean()), 4),
        "median": round(float(np.median(values)), 4),
        "min": round(float(values.min()), 4),
        "max": round(float(values.max()), 4),
        "p90": round(float(np.percentile(values, 90)), 4),
        "values": [round(float(v), 4) for v in values],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="smoke run: 1 skeleton/face, tiny budgets")
    parser.add_argument("--processes", type=int, default=min(24, mp.cpu_count()))
    parser.add_argument("--cem-population", type=int, default=28)
    parser.add_argument("--cem-elites", type=int, default=7)
    parser.add_argument("--cem-iterations", type=int, default=18)
    parser.add_argument("--robust-population", type=int, default=20)
    parser.add_argument("--robust-elites", type=int, default=5)
    parser.add_argument("--robust-iterations", type=int, default=12)
    parser.add_argument(
        "--results-json", type=Path,
        default=REPO / "experiments/feasibility_audit/voi_current_task_family.json",
    )
    parser.add_argument(
        "--details-json", type=Path,
        default=REPO / "runs/feasibility_audit/voi_current_task_family/skeleton_details.json",
    )
    args = parser.parse_args()
    if args.quick:
        args.cem_population, args.cem_elites, args.cem_iterations = 8, 3, 4
        args.robust_population, args.robust_elites, args.robust_iterations = 8, 3, 3

    budget = {
        "cem_population": args.cem_population,
        "cem_elites": args.cem_elites,
        "cem_iterations": args.cem_iterations,
        "robust_population": args.robust_population,
        "robust_elites": args.robust_elites,
        "robust_iterations": args.robust_iterations,
    }

    started = time.time()
    faces = load_face_env_dicts()
    jobs = []
    skeleton_index = 0
    for face in faces:
        n = 1 if args.quick else face["n_skeletons"]
        for k in range(n):
            jobs.append(
                {
                    "skeleton_id": f"{face['face_id']}-skeleton-{k:02d}",
                    "skeleton_index": skeleton_index,
                    "face_id": face["face_id"],
                    "env_dict": face["env_dict"],
                    "seed": face["seed_start"] + k,
                    "budget": budget,
                }
            )
            skeleton_index += 1

    if args.processes > 1:
        with mp.Pool(processes=min(args.processes, len(jobs))) as pool:
            rows = pool.map(process_skeleton, jobs)
    else:
        rows = [process_skeleton(job) for job in jobs]

    # ------------------------------------------------------------- aggregates
    per_face = {}
    for face in faces:
        face_rows = [r for r in rows if r["face_id"] == face["face_id"]]
        if not face_rows:
            continue
        per_face[face["face_id"]] = {
            "env_source": face["env_source"],
            "capability_pair": face.get("capability_pair"),
            "n_skeletons": len(face_rows),
            "voi_return": aggregate(face_rows, "voi_return"),
            "voi_success": aggregate(face_rows, "voi_success"),
            "oracle_mean_return": aggregate(face_rows, "oracle_mean_return"),
            "oracle_mean_success": aggregate(face_rows, "oracle_mean_success"),
        }

    overall = {
        "n_skeletons": len(rows),
        "voi_return": aggregate(rows, "voi_return"),
        "voi_success": aggregate(rows, "voi_success"),
        "oracle_mean_return": aggregate(rows, "oracle_mean_return"),
        "oracle_mean_success": aggregate(rows, "oracle_mean_success"),
        "best_fixed_mean_return": aggregate(
            [{"v": r["oracle_mean_return"] - r["voi_return"]} for r in rows], "v"
        ),
        "best_fixed_mean_success": aggregate(
            [{"v": r["oracle_mean_success"] - r["voi_success"]} for r in rows], "v"
        ),
        "skeletons_with_voi_success_gt_0": int(sum(1 for r in rows if r["voi_success"] > 1e-9)),
        "skeletons_with_voi_return_gt_1": int(sum(1 for r in rows if r["voi_return"] > 1.0)),
    }

    skeleton_summaries = [
        {k: r[k] for k in (
            "skeleton_id", "face_id", "seed", "skeleton", "oracle_per_theta",
            "best_fixed_plan", "oracle_mean_return", "oracle_mean_success",
            "voi_return", "voi_success", "rollouts", "elapsed_s",
        )}
        for r in rows
    ]

    payload = {
        "protocol": "feasibility_audit_voi_current_task_family",
        "generated_by": "scripts/feasibility_audit/voi_current_task_family.py",
        "claim_scope": (
            "Measures VoI(skeleton) = E_theta[per-theta open-loop oracle outcome] - "
            "max_fixed_plan E_theta[outcome] on representative faces of the current task "
            "family, with theta = post-friction-step mu on a fixed 4-point grid and a "
            "uniform prior. Oracle and fixed-plan baselines are search lower bounds "
            "(structured + CEM); the fixed-plan baseline includes per-theta oracle "
            "replays, 6 robust archetypes and a robust-CEM plan, and the oracle is "
            "closed over all fixed plans so VoI >= 0 by construction. No claim is made "
            "about closed-loop controllers or learned policies."
        ),
        "hypothesis": (
            "If the ~1500 null self-ID milestones are explained by task design (hidden "
            "theta not worth knowing), VoI should be ~0 on these faces."
        ),
        "theta_grid": list(THETA_GRID),
        "theta_semantics": "friction_step.mu_range collapsed to (theta, theta): mu after the mid-episode friction step",
        "skeleton_invariance": (
            "asserted per skeleton: mu_pre, speed_ref, beta_target, friction_step_at, "
            "obstacle geometry identical across the 4 theta arms (same reset seed, "
            "identical rng stream consumption)"
        ),
        "excluded_faces_note": (
            "m3012 specs without friction_step (0002-0007, 0009, 0012, 0013, 0015, 0016) "
            "are excluded: episode-constant mu there friction-limits the sampled initial "
            "speed (friction_limited_speed=true), so a fixed-skeleton theta intervention "
            "does not exist for them."
        ),
        "budget": budget,
        "quick": bool(args.quick),
        "elapsed_s": round(time.time() - started, 1),
        "total_rollouts": int(sum(r["rollouts"] for r in rows)),
        "faces": per_face,
        "overall": overall,
        "skeletons": skeleton_summaries,
    }

    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    details = {
        "protocol": "feasibility_audit_voi_current_task_family_details",
        "note": "full per-skeleton plan matrices (per-theta outcome of every fixed plan)",
        "rows": [
            {k: r[k] for k in ("skeleton_id", "face_id", "seed", "plans", "robust_cem_history_first_last")}
            for r in rows
        ],
    }
    args.details_json.parent.mkdir(parents=True, exist_ok=True)
    args.details_json.write_text(json.dumps(details, indent=2), encoding="utf-8")
    print(f"results -> {args.results_json}")
    print(f"details -> {args.details_json}")
    print(
        f"overall VoI(return) mean={overall['voi_return']['mean']} "
        f"VoI(success) mean={overall['voi_success']['mean']} "
        f"({payload['total_rollouts']} rollouts, {payload['elapsed_s']}s)"
    )


if __name__ == "__main__":
    main()
