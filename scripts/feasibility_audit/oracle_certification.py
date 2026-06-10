"""Oracle certification of the 7 residual hard-safety failure rows (M3105 incumbent).

Converts the computed physical ceiling of the fixed 64-seed panel from inference to
measurement, via privileged search over control sequences:

- Tier A (full-preview oracle): searches the entire open-loop action sequence from
  step 0 -- "does ANY control sequence succeed on this episode?"
- Tier B (reveal-constrained oracle): forces the M3105 incumbent's closed-loop
  actions before the obstacle perception reveal step, searches only afterwards --
  "upper bound for any causal controller using actor-visible information only."

Environment reconstruction reuses the exact measurement-module code path
(m3088.env_config_for_executable_profile / wrap_env_with_profile_mask / AutoDriftEnv,
reset(seed=eval_seed)), and outcome semantics reuse autodrift.evaluate
.outcome_bucket_from_info (the same function used by run_episode_with_policy in all
full-fresh measurement preflights). No dynamics are re-implemented.

Deterministic: fixed numpy seeds, pure CPU / numpy. Re-runnable with
    PYTHONPATH=src python scripts/feasibility_audit/oracle_certification.py
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
from autodrift.artifacts import read_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    POLICY_ID as INCUMBENT_POLICY_ID,
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.evaluate import outcome_bucket_from_info, run_episode_with_policy

REPO = Path(__file__).resolve().parents[2]

M3084_DIR = REPO / (
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
M3105_DIR = REPO / (
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
M3012_DIR = REPO / (
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)

FAILURE_EPISODES = [
    "m3084-measurement-episode-0007",
    "m3084-measurement-episode-0010",
    "m3084-measurement-episode-0013",
    "m3084-measurement-episode-0024",
    "m3084-measurement-episode-0025",
    "m3084-measurement-episode-0026",
    "m3084-measurement-episode-0029",
]

# Physical-audit predictions from docs/feasibility-takeover-2026-06-route-decision.md
# (5 high-confidence unavoidable rows + 0024 medium-high + 0025 medium).
PHYSICAL_AUDIT_PREDICTIONS = {
    "m3084-measurement-episode-0007": {"prediction": "unavoidable", "confidence": "high"},
    "m3084-measurement-episode-0010": {"prediction": "unavoidable", "confidence": "high"},
    "m3084-measurement-episode-0013": {"prediction": "unavoidable", "confidence": "high"},
    "m3084-measurement-episode-0024": {"prediction": "unavoidable", "confidence": "medium_high"},
    "m3084-measurement-episode-0025": {"prediction": "unavoidable", "confidence": "medium"},
    "m3084-measurement-episode-0026": {"prediction": "unavoidable", "confidence": "high"},
    "m3084-measurement-episode-0029": {"prediction": "unavoidable", "confidence": "high"},
}

NO_HARD_FAIL_BUCKETS = {
    "success_obstacle_pass",
    "speed_too_low_noncollision_noncompletion",
    "max_steps_noncompletion",
}

BASE_SEED = 20260611


# --------------------------------------------------------------------------- env


def build_failure_contexts() -> list[dict[str, Any]]:
    """Join m3084 panel rows with m3012 workloads/specs for the 7 failure rows."""
    m3084_rows = {
        str(r["measurement_episode_id"]): r
        for r in read_csv_rows(M3084_DIR / "measurement_episode_rows.csv")
    }
    m3105_rows = {
        str(r["source_measurement_episode_id"]): r
        for r in read_csv_rows(M3105_DIR / "measurement_episode_rows.csv")
    }
    workloads = {
        str(r["executable_workload_id"]): r
        for r in read_csv_rows(M3012_DIR / "executable_workload_rows.csv")
    }
    spec_payload = read_json(M3012_DIR / "executable_source_specs.json")
    specs = {
        (str(r.get("task_source_id", "")), str(r.get("executable_source_spec_id", ""))): r
        for r in spec_payload["executable_source_specs"]
    }
    contexts = []
    for episode_id in FAILURE_EPISODES:
        row = m3084_rows[episode_id]
        workload = workloads[str(row["executable_workload_id"])]
        spec = specs[(str(row["task_source_id"]), str(row["executable_source_spec_id"]))]
        m3105_row = m3105_rows[episode_id]
        assert int(row["eval_seed"]) == int(m3105_row["eval_seed"]), episode_id
        contexts.append(
            {
                "episode_id": episode_id,
                "m3105_episode_id": str(m3105_row["runtime_smoke_episode_id"]),
                "eval_seed": int(row["eval_seed"]),
                "executable_source_spec_id": str(row["executable_source_spec_id"]),
                "executable_workload_id": str(row["executable_workload_id"]),
                "axis_id": str(m3105_row["axis_id"]),
                "profile_binding_name": str(workload["profile_binding_name"]),
                "config_path": str(workload["config_path"]),
                "spec": spec,
                "reveal_step": int(spec["env_config"]["obstacle"]["perception_reveal_step"]),
                "max_steps": int(spec["env_config"]["max_steps"]),
                "m3105_recorded": {
                    "outcome_bucket": str(m3105_row["outcome_bucket"]),
                    "termination_reason": str(m3105_row["termination_reason"]),
                    "steps": int(m3105_row["steps"]),
                    "min_clearance_margin": float(m3105_row["min_clearance_margin"]),
                },
            }
        )
    return contexts


def build_env(context: dict[str, Any]):
    profile_config = m3088.m3075.profile_config_for_runtime(
        read_json(context["config_path"]), profile_name=context["profile_binding_name"]
    )
    env_config = m3088.env_config_for_executable_profile(
        executable_spec=context["spec"], profile_config=profile_config
    )
    return m3088.wrap_env_with_profile_mask(m3088.AutoDriftEnv(env_config), profile_config)


# ----------------------------------------------------------------------- rollout


def incumbent_action(observation: np.ndarray) -> np.ndarray:
    return v4_v2_fallback_no_regression_hard_safety_direct_action(observation, V4_POLICY_CONFIG)


def rollout(env, controller: Callable[[int, np.ndarray], np.ndarray], seed: int) -> dict[str, Any]:
    """Light deterministic rollout; outcome classified by outcome_bucket_from_info
    (identical semantics to run_episode_with_policy in the measurement modules)."""
    obs, info = env.reset(seed=seed)
    track_width = float(env.config.track_width)
    tol = (
        float(env.config.soft_offtrack_tolerance_m)
        if bool(env.config.soft_offtrack_metric_enabled)
        else 0.0
    )
    boundary_margin_min = track_width + tol - abs(float(info.get("lateral_error", 0.0)))
    terminated = truncated = False
    t = 0
    actions: list[np.ndarray] = []
    while not (terminated or truncated):
        action = np.asarray(controller(t, obs), dtype=np.float64)
        actions.append(action)
        obs, _reward, terminated, truncated, info = env.step(action)
        boundary_margin_min = min(
            boundary_margin_min, track_width + tol - abs(float(info.get("lateral_error", 0.0)))
        )
        t += 1
    bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
    clearance = float(info.get("min_clearance_margin", float("nan")))
    combined = boundary_margin_min if not np.isfinite(clearance) else min(clearance, boundary_margin_min)
    return {
        "outcome_bucket": bucket,
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "steps": int(info.get("step", t)),
        "min_clearance_margin": clearance,
        "boundary_margin_min": float(boundary_margin_min),
        "combined_margin": float(combined),
        "actions": actions,
    }


def score_result(result: dict[str, Any], max_steps: int) -> float:
    margin = float(np.clip(result["combined_margin"], -2.0, 2.0))
    bucket = result["outcome_bucket"]
    if bucket == "success_obstacle_pass":
        return 3000.0 + 10.0 * margin
    if bucket in NO_HARD_FAIL_BUCKETS:
        return 1000.0 + 10.0 * margin
    # hard failure: later failure strictly better (secondary), then larger margin
    return -1000.0 + 100.0 * (result["steps"] / max(max_steps, 1)) + 50.0 * margin


# ------------------------------------------------------------------ controllers


def make_sequence_controller(
    segments: np.ndarray, seg_len: int, start_step: int, prefix: str
) -> Callable[[int, np.ndarray], np.ndarray]:
    """Piecewise-constant searched sequence from start_step; incumbent closed-loop
    before start_step (Tier B). Tier A uses start_step=0 (prefix unused)."""
    n_segments = segments.shape[0]

    def controller(t: int, obs: np.ndarray) -> np.ndarray:
        if t < start_step:
            return incumbent_action(obs)
        rel = t - start_step
        idx = min(rel // seg_len, n_segments - 1)
        return segments[idx]

    del prefix
    return controller


def make_steps_controller(
    steps: list[np.ndarray], start_step: int
) -> Callable[[int, np.ndarray], np.ndarray]:
    """Explicit per-step open-loop tail (used for incumbent replay candidate)."""

    def controller(t: int, obs: np.ndarray) -> np.ndarray:
        if t < start_step:
            return incumbent_action(obs)
        rel = t - start_step
        if rel < len(steps):
            return steps[rel]
        return steps[-1] if steps else np.array([0.0, -1.0, 1.0])

    return controller


# ------------------------------------------------------------------- candidates


def structured_candidate_set(incumbent_tail: list[np.ndarray]) -> list[tuple[str, list[np.ndarray]]]:
    """Each candidate is an explicit per-step action list (held at last action)."""
    horizon = 128
    candidates: list[tuple[str, list[np.ndarray]]] = []

    def const(action: list[float]) -> list[np.ndarray]:
        return [np.array(action, dtype=np.float64)] * horizon

    candidates.append(("incumbent_replay", [np.asarray(a, dtype=np.float64) for a in incumbent_tail]))
    candidates.append(("full_brake_straight", const([0.0, -1.0, 1.0])))
    steer_levels = [0.2, 0.5, 0.8, 1.0, -0.2, -0.5, -0.8, -1.0]
    for s in steer_levels:
        candidates.append((f"brake_steer_{s:+.1f}", const([s, -1.0, 1.0])))
    for s in steer_levels:
        candidates.append((f"coast_steer_{s:+.1f}", const([s, -1.0, -1.0])))
    for s in (0.5, 1.0, -0.5, -1.0):
        for n in (8, 16):
            seq = [np.array([s, -1.0, 1.0])] * n + [np.array([0.0, -1.0, 1.0])] * (horizon - n)
            candidates.append((f"swerve_recenter_{s:+.1f}_n{n}", seq))
    return candidates


def steps_to_segments(steps: list[np.ndarray], n_segments: int, seg_len: int) -> np.ndarray:
    """Encode a per-step candidate into the CEM segment parameterization."""
    segments = np.zeros((n_segments, 3), dtype=np.float64)
    fallback = steps[-1] if steps else np.array([0.0, -1.0, 1.0])
    for k in range(n_segments):
        chunk = steps[k * seg_len : (k + 1) * seg_len]
        segments[k] = np.mean(np.asarray(chunk), axis=0) if chunk else fallback
    return np.clip(segments, -1.0, 1.0)


# ------------------------------------------------------------------------ search


def certify_tier(
    env,
    context: dict[str, Any],
    *,
    tier: str,
    start_step: int,
    incumbent_actions: list[np.ndarray],
    rng: np.random.Generator,
    n_segments: int,
    seg_len: int,
    population: int,
    elites: int,
    iterations: int,
) -> dict[str, Any]:
    seed = context["eval_seed"]
    max_steps = context["max_steps"]
    rollout_count = 0

    def evaluate_controller(controller) -> tuple[dict[str, Any], float]:
        nonlocal rollout_count
        result = rollout(env, controller, seed)
        rollout_count += 1
        return result, score_result(result, max_steps)

    best: dict[str, Any] = {}
    best_success: dict[str, Any] = {}
    best_no_hard_fail: dict[str, Any] = {}
    latest_fail_step = -1

    def consider(kind: str, result: dict[str, Any], score: float, segments: np.ndarray | None):
        nonlocal best, best_success, best_no_hard_fail, latest_fail_step
        entry = {
            "kind": kind,
            "score": float(score),
            "outcome_bucket": result["outcome_bucket"],
            "termination_reason": result["termination_reason"],
            "steps": result["steps"],
            "min_clearance_margin": result["min_clearance_margin"],
            "boundary_margin_min": result["boundary_margin_min"],
            "combined_margin": result["combined_margin"],
            "segments": None if segments is None else np.round(segments, 6).tolist(),
            "applied_actions": [np.round(a, 6).tolist() for a in result["actions"]],
        }
        if not best or score > best["score"]:
            best = entry
        if result["outcome_bucket"] == "success_obstacle_pass" and (
            not best_success or score > best_success["score"]
        ):
            best_success = entry
        if result["outcome_bucket"] in NO_HARD_FAIL_BUCKETS and (
            not best_no_hard_fail or score > best_no_hard_fail["score"]
        ):
            best_no_hard_fail = entry
        if result["outcome_bucket"] not in NO_HARD_FAIL_BUCKETS:
            latest_fail_step = max(latest_fail_step, result["steps"])

    # 1) structured candidates --------------------------------------------------
    incumbent_tail = incumbent_actions[start_step:]
    structured_rows = []
    best_structured_segments = None
    best_structured_score = -np.inf
    for name, steps in structured_candidate_set(incumbent_tail):
        result, score = evaluate_controller(make_steps_controller(steps, start_step))
        structured_rows.append(
            {
                "name": name,
                "outcome_bucket": result["outcome_bucket"],
                "termination_reason": result["termination_reason"],
                "steps": result["steps"],
                "min_clearance_margin": result["min_clearance_margin"],
                "boundary_margin_min": result["boundary_margin_min"],
                "combined_margin": result["combined_margin"],
                "score": float(score),
            }
        )
        segments = steps_to_segments(steps, n_segments, seg_len)
        consider(f"structured:{name}", result, score, segments)
        if score > best_structured_score:
            best_structured_score = score
            best_structured_segments = segments

    # 2) CEM over piecewise-constant segments ------------------------------------
    mean = best_structured_segments.copy()
    std = np.full_like(mean, 0.5)
    cem_history = []
    for iteration in range(iterations):
        samples = np.clip(
            rng.normal(loc=mean[None], scale=std[None], size=(population, n_segments, 3)),
            -1.0,
            1.0,
        )
        scored: list[tuple[float, int]] = []
        for i in range(population):
            controller = make_sequence_controller(samples[i], seg_len, start_step, tier)
            result, score = evaluate_controller(controller)
            consider("cem", result, score, samples[i])
            scored.append((score, i))
        scored.sort(key=lambda item: (-item[0], item[1]))
        elite_idx = [i for _score, i in scored[:elites]]
        elite = samples[elite_idx]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), 0.05)
        cem_history.append(
            {
                "iteration": iteration,
                "best_score": float(scored[0][0]),
                "elite_mean_score": float(np.mean([s for s, _ in scored[:elites]])),
            }
        )

    return {
        "tier": tier,
        "search_start_step": start_step,
        "search_budget": {
            "structured_candidates": len(structured_rows),
            "cem_population": population,
            "cem_elites": elites,
            "cem_iterations": iterations,
            "total_rollouts": rollout_count,
            "segment_count": n_segments,
            "segment_length_steps": seg_len,
            "searched_horizon_steps": n_segments * seg_len,
        },
        "best": best,
        "best_success": best_success or None,
        "best_no_hard_fail": best_no_hard_fail or None,
        "success_found": bool(best_success),
        "no_hard_fail_found": bool(best_no_hard_fail),
        "latest_hard_fail_step_observed": latest_fail_step,
        "structured_results": structured_rows,
        "cem_history_first_last": [cem_history[0], cem_history[-1]] if cem_history else [],
    }


# ------------------------------------------------------------------------ main


def verify_with_measurement_module(env, context, entry: dict[str, Any], start_step: int) -> dict[str, Any]:
    """Re-run the best candidate through run_episode_with_policy (the exact
    measurement-module code path) to confirm identical outcome semantics."""

    steps = [np.asarray(a, dtype=np.float64) for a in entry["applied_actions"]]

    class ScriptedPolicy:
        def __init__(self):
            self.t = 0

        def reset(self):
            self.t = 0

        def act(self, observation, info):
            del info
            if self.t < len(steps):
                action = steps[self.t]
            else:
                action = steps[-1]
            self.t += 1
            return action

    del start_step
    row = run_episode_with_policy(env, ScriptedPolicy(), "oracle_certification_replay", context["eval_seed"])
    return {
        "outcome_bucket": str(row["outcome_bucket"]),
        "termination_reason": str(row["termination_reason"]),
        "steps": int(row["steps"]),
        "min_clearance_margin": float(row["min_clearance_margin"]),
        "matches_light_rollout": bool(
            str(row["outcome_bucket"]) == entry["outcome_bucket"]
            and int(row["steps"]) == entry["steps"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cpu", choices=["cpu"], help="cpu only; pure numpy")
    parser.add_argument("--population", type=int, default=64)
    parser.add_argument("--elites", type=int, default=8)
    parser.add_argument("--iterations", type=int, default=48)
    parser.add_argument("--segments", type=int, default=16)
    parser.add_argument("--segment-length", type=int, default=8)
    parser.add_argument("--quick", action="store_true", help="smoke run (small budget)")
    parser.add_argument(
        "--results-json",
        type=Path,
        default=REPO / "experiments/feasibility_audit/oracle_certification_results.json",
    )
    parser.add_argument(
        "--sequences-json",
        type=Path,
        default=REPO / "runs/feasibility_audit/oracle_certification_sequences.json",
    )
    parser.add_argument(
        "--progress-json",
        type=Path,
        default=REPO / "runs/feasibility_audit/oracle_certification_progress.json",
    )
    args = parser.parse_args()
    if args.quick:
        args.population, args.elites, args.iterations = 16, 4, 4

    started = time.time()
    contexts = build_failure_contexts()
    rows_out: list[dict[str, Any]] = []
    sequences_out: list[dict[str, Any]] = []

    for row_index, context in enumerate(contexts):
        env = build_env(context)
        try:
            # incumbent reproduction check (closed loop, light rollout)
            incumbent_result = rollout(env, lambda t, obs: incumbent_action(obs), context["eval_seed"])
            recorded = context["m3105_recorded"]
            reproduction_match = bool(
                incumbent_result["outcome_bucket"] == recorded["outcome_bucket"]
                and incumbent_result["steps"] == recorded["steps"]
                and abs(incumbent_result["min_clearance_margin"] - recorded["min_clearance_margin"]) < 1e-6
            )
            incumbent_actions = incumbent_result["actions"]

            tier_payload = {}
            for tier_index, (tier, start_step) in enumerate(
                [("tier_a_full_preview", 0), ("tier_b_reveal_constrained", context["reveal_step"])]
            ):
                rng = np.random.default_rng(BASE_SEED + 100 * row_index + tier_index)
                tier_result = certify_tier(
                    env,
                    context,
                    tier=tier,
                    start_step=start_step,
                    incumbent_actions=incumbent_actions,
                    rng=rng,
                    n_segments=args.segments,
                    seg_len=args.segment_length,
                    population=args.population,
                    elites=args.elites,
                    iterations=args.iterations,
                )
                # verification through the measurement-module episode runner
                for key in ("best", "best_success", "best_no_hard_fail"):
                    entry = tier_result.get(key)
                    if entry:
                        entry["measurement_module_verification"] = verify_with_measurement_module(
                            env, context, entry, start_step
                        )
                # move bulky per-step traces to the sequences artifact
                for key in ("best", "best_success", "best_no_hard_fail"):
                    entry = tier_result.get(key)
                    if entry:
                        sequences_out.append(
                            {
                                "episode_id": context["episode_id"],
                                "eval_seed": context["eval_seed"],
                                "tier": tier,
                                "slot": key,
                                "kind": entry["kind"],
                                "outcome_bucket": entry["outcome_bucket"],
                                "steps": entry["steps"],
                                "search_start_step": start_step,
                                "applied_actions_steer_throttle_brake": entry.pop("applied_actions"),
                                "segments": entry.get("segments"),
                            }
                        )
                tier_payload[tier] = tier_result

            rows_out.append(
                {
                    "episode_id": context["episode_id"],
                    "m3105_episode_id": context["m3105_episode_id"],
                    "eval_seed": context["eval_seed"],
                    "executable_source_spec_id": context["executable_source_spec_id"],
                    "executable_workload_id": context["executable_workload_id"],
                    "axis_id": context["axis_id"],
                    "profile_binding_name": context["profile_binding_name"],
                    "reveal_step": context["reveal_step"],
                    "max_steps": context["max_steps"],
                    "obstacle_label_reconstructed": None,  # filled below from env info
                    "physical_audit_prediction": PHYSICAL_AUDIT_PREDICTIONS[context["episode_id"]],
                    "m3105_recorded": recorded,
                    "incumbent_reproduction": {
                        "outcome_bucket": incumbent_result["outcome_bucket"],
                        "steps": incumbent_result["steps"],
                        "min_clearance_margin": incumbent_result["min_clearance_margin"],
                        "boundary_margin_min": incumbent_result["boundary_margin_min"],
                        "match": reproduction_match,
                    },
                    "tiers": tier_payload,
                }
            )
            # reconstruct the hidden generator label for reporting (privileged,
            # report-only -- never used by any controller)
            obs, info = env.reset(seed=context["eval_seed"])
            rows_out[-1]["obstacle_label_reconstructed"] = str(info.get("obstacle_label", ""))
        finally:
            env.close()

        args.progress_json.parent.mkdir(parents=True, exist_ok=True)
        args.progress_json.write_text(
            json.dumps(
                {
                    "completed_rows": len(rows_out),
                    "total_rows": len(contexts),
                    "elapsed_s": round(time.time() - started, 1),
                    "latest_episode": context["episode_id"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            f"[{len(rows_out)}/{len(contexts)}] {context['episode_id']} done "
            f"({time.time() - started:.1f}s)",
            flush=True,
        )

    payload = {
        "protocol": "feasibility_audit_oracle_certification",
        "generated_by": "scripts/feasibility_audit/oracle_certification.py",
        "claim_scope": (
            "Privileged oracle search over control sequences on the 7 residual hard-safety "
            "failure rows of the fixed M3084/M3105 64-seed panel. Tier A is a full-preview "
            "open-loop existence search; Tier B is reveal-constrained (incumbent closed-loop "
            "prefix before obstacle perception reveal). Oracle results bound what any "
            "controller could achieve on these rows; no driver-performance, validation, "
            "repair-success, or verdict claim is made for any deployable controller."
        ),
        "incumbent_policy_id": INCUMBENT_POLICY_ID,
        "outcome_semantics": "autodrift.evaluate.outcome_bucket_from_info (same as measurement modules)",
        "no_hard_fail_buckets": sorted(NO_HARD_FAIL_BUCKETS),
        "search_config": {
            "structured_candidates_per_tier": 26,
            "cem_population": args.population,
            "cem_elites": args.elites,
            "cem_iterations": args.iterations,
            "segments": args.segments,
            "segment_length_steps": args.segment_length,
            "base_seed": BASE_SEED,
            "rng": "numpy.random.default_rng(BASE_SEED + 100*row_index + tier_index)",
            "score_function": (
                "success: 3000 + 10*clip(combined_margin,-2,2); "
                "no-hard-fail: 1000 + 10*clip(combined_margin,-2,2); "
                "hard-fail: -1000 + 100*(fail_step/max_steps) + 50*clip(combined_margin,-2,2)"
            ),
            "combined_margin": "min(min_clearance_margin, track_width+tol-|lateral_error| per-step min)",
        },
        "seed_mapping": {c["episode_id"]: c["eval_seed"] for c in contexts},
        "spec_mapping": {c["episode_id"]: c["executable_source_spec_id"] for c in contexts},
        "elapsed_s": round(time.time() - started, 1),
        "rows": rows_out,
    }
    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.sequences_json.parent.mkdir(parents=True, exist_ok=True)
    args.sequences_json.write_text(
        json.dumps(
            {
                "protocol": "feasibility_audit_oracle_certification_sequences",
                "action_components": ["steer", "throttle", "brake"],
                "note": "raw env action space [-1,1]^3; throttle/brake mapped to [0,1] inside env",
                "sequences": sequences_out,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"results -> {args.results_json}")
    print(f"sequences -> {args.sequences_json}")
    print(f"total elapsed {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
