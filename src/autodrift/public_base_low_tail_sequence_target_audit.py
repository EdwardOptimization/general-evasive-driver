"""No-training short-horizon sequence target audit for the M399 public base."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.public_base_controlled_fusion_surface_probe import _base_actions, _mean, _percentile
from autodrift.public_base_replay_constrained_target_feasibility import (
    DEFAULT_ACTIVE_ROW_IDS,
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_CONTRAST_ROWS,
    DEFAULT_ENV_CONFIG,
    DEFAULT_LOW_TAIL_ROWS,
    DEFAULT_M267_CORPUS,
    DEFAULT_M912_SUMMARY,
    DEFAULT_POSITIVE_ROWS,
    DEFAULT_SCENARIO_CONFIG,
    DEFAULT_TARGET_ROWS,
    _m267_target_preflight,
    _requests,
    _snapshot,
    _summarize_m267_preflight,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _read_csv_rows


DEFAULT_RUN_DIR = Path("runs/m956_v4_public_base_low_tail_sequence_target_audit")
DEFAULT_HORIZONS = (2, 4, 6)
DEFAULT_AMPLITUDES = (0.004, 0.006, 0.008)
DEFAULT_MAX_LOW_TAIL_ROWS = 64
PREFIX_MEAN_LIMITS = {2: 0.006, 4: 0.010, 6: 0.014}


def classify_sequence_target_audit(
    *,
    contract_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    sequence_family_count: int,
    first_action_retained_family_count: int,
    sequence_low_tail_candidate_count: int,
    m267_sequence_preflight_pass_count: int,
    joint_sequence_candidate_count: int,
) -> str:
    if bool(contract_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "low_tail_sequence_target_audit_contract_artifact"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "low_tail_sequence_target_audit_reconstruction_blocked"
    if int(sequence_family_count) <= 0:
        return "low_tail_sequence_target_audit_no_family"
    if int(joint_sequence_candidate_count) > 0:
        return "low_tail_sequence_target_audit_joint_candidate"
    if int(sequence_low_tail_candidate_count) > 0 and int(m267_sequence_preflight_pass_count) == 0:
        return "low_tail_sequence_target_audit_m267_preflight_failure"
    if int(first_action_retained_family_count) > 0 and int(sequence_low_tail_candidate_count) == 0:
        return "low_tail_sequence_target_audit_no_sequence_low_tail_candidate"
    return "low_tail_sequence_target_audit_no_candidate"


def _parse_int_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(item) for item in str(raw).split(",") if item.strip())


def _parse_float_tuple(raw: str) -> tuple[float, ...]:
    return tuple(float(item) for item in str(raw).split(",") if item.strip())


def _safe_margin(result: dict[str, Any]) -> float:
    value = float(result.get("min_clearance_margin", float("nan")))
    return value if np.isfinite(value) else float("nan")


def _unit_direction(normal_action: torch.Tensor, intervention_action: torch.Tensor) -> np.ndarray:
    delta = (normal_action - intervention_action).detach().cpu().numpy().astype(np.float64)
    norm = float(np.linalg.norm(delta))
    if not np.isfinite(norm) or norm < 1e-8:
        return np.zeros(3, dtype=np.float64)
    return delta / norm


def _schedule(horizon: int, amplitude: float) -> np.ndarray:
    values = np.zeros(int(horizon), dtype=np.float64)
    if int(horizon) <= 1:
        return values
    tail = np.linspace(0.5, 1.0, int(horizon) - 1, dtype=np.float64)
    values[1:] = float(amplitude) * tail
    return values


def _prefix_l2(actions: list[np.ndarray], reference_actions: list[np.ndarray], horizon: int) -> dict[str, float | int]:
    count = min(len(actions), len(reference_actions), int(horizon))
    if count <= 0:
        return {"prefix_l2_mean": float("nan"), "prefix_l2_p95": float("nan"), "prefix_l2_max": float("nan"), "prefix_compare_steps": 0}
    distances = np.asarray(
        [float(np.linalg.norm(np.asarray(actions[i], dtype=np.float64) - np.asarray(reference_actions[i], dtype=np.float64))) for i in range(count)],
        dtype=np.float64,
    )
    return {
        "prefix_l2_mean": _mean(distances),
        "prefix_l2_p95": _percentile(distances, 95),
        "prefix_l2_max": float(np.max(distances)) if distances.size else float("nan"),
        "prefix_compare_steps": int(count),
    }


def _replay_sequence_delta(
    *,
    model: ActorCritic,
    snapshot: OutcomeSnapshot,
    env_config: Any,
    hidden: torch.Tensor,
    direction: np.ndarray,
    schedule: np.ndarray,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    current_hidden = hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for step_index in range(max_steps):
        action, next_hidden = deterministic_action_from_hidden(model, obs, current_hidden, device)
        if step_index < len(schedule):
            action = np.clip(
                np.asarray(action, dtype=np.float64) + float(schedule[step_index]) * np.asarray(direction, dtype=np.float64),
                -1.0,
                1.0,
            ).astype(np.float32)
        actions.append(np.asarray(action, dtype=np.float32))
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        current_hidden = next_hidden
        if terminated or truncated:
            break
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    first = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    return {
        "steps": int(len(rewards)),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "terminal_reason": reason,
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first[0]),
        "first_throttle": float(first[1]),
        "first_brake": float(first[2]),
    }, actions


def _selected_low_tail_indices(low_tail_mask: torch.Tensor, max_rows: int) -> list[int]:
    indices = [int(index) for index in torch.nonzero(low_tail_mask.detach().cpu(), as_tuple=False).reshape(-1).tolist()]
    if int(max_rows) > 0:
        indices = indices[: int(max_rows)]
    return indices


def _sequence_rows(
    *,
    model: ActorCritic,
    meta_rows: list[dict[str, Any]],
    samples: dict[str, torch.Tensor],
    low_tail_indices: list[int],
    env_config: Any,
    horizons: tuple[int, ...],
    amplitudes: tuple[float, ...],
    max_continuation_steps: int,
    device: torch.device,
) -> list[dict[str, Any]]:
    requests: dict[int, set[int]] = {}
    for index in low_tail_indices:
        row = meta_rows[index]
        requests.setdefault(int(row["seed"]), set()).add(int(row["step"]))
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=requests,
        device=device,
    )
    rows: list[dict[str, Any]] = []
    for index in low_tail_indices:
        row = meta_rows[index]
        snapshot = _snapshot(snapshots, int(row["seed"]), int(row["step"]))
        direction = _unit_direction(samples["normal_actions"][index], samples["intervention_actions"][index])
        base, base_actions = _replay_sequence_delta(
            model=model,
            snapshot=snapshot,
            env_config=env_config,
            hidden=snapshot.hidden,
            direction=np.zeros(3, dtype=np.float64),
            schedule=np.zeros(1, dtype=np.float64),
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        base_margin = _safe_margin(base)
        for horizon in horizons:
            for amplitude in amplitudes:
                family = f"delayed_projection_h{int(horizon)}_amp_{float(amplitude):.4f}".replace(".", "_")
                schedule = _schedule(int(horizon), float(amplitude))
                result, actions = _replay_sequence_delta(
                    model=model,
                    snapshot=snapshot,
                    env_config=env_config,
                    hidden=snapshot.hidden,
                    direction=direction,
                    schedule=schedule,
                    max_continuation_steps=max_continuation_steps,
                    device=device,
                )
                margin = _safe_margin(result)
                prefix = _prefix_l2(actions, base_actions, int(horizon))
                first_delta = (
                    float(np.linalg.norm(np.asarray(actions[0], dtype=np.float64) - np.asarray(base_actions[0], dtype=np.float64)))
                    if actions and base_actions
                    else float("nan")
                )
                rows.append(
                    {
                        "family": family,
                        "horizon": int(horizon),
                        "amplitude": float(amplitude),
                        "contrast_group_id": str(row.get("contrast_group_id", "")),
                        "source_index": str(row.get("source_index", "")),
                        "seed": int(row["seed"]),
                        "step": int(row["step"]),
                        "variant": str(row.get("variant", "")),
                        "source_pool": str(row.get("source_pool", "")),
                        "base_success": bool(base["success"]),
                        "sequence_success": bool(result["success"]),
                        "base_collision": bool(base["collision"]),
                        "sequence_collision": bool(result["collision"]),
                        "base_margin": base_margin,
                        "sequence_margin": margin,
                        "terminal_margin_delta": margin - base_margin if np.isfinite(margin) and np.isfinite(base_margin) else float("nan"),
                        "first_action_l2": first_delta,
                        **prefix,
                    }
                )
    return rows


def _summarize_sequence_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    import pandas as pd

    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for family, group in frame.groupby("family", observed=True):
        horizon = int(group["horizon"].iloc[0])
        first_values = group["first_action_l2"].astype(float)
        prefix_values = group["prefix_l2_mean"].astype(float)
        margin_delta = group["terminal_margin_delta"].astype(float)
        first_action_retained = bool(_mean(first_values) <= 0.003 and _percentile(first_values, 95) <= 0.008)
        prefix_limit = float(PREFIX_MEAN_LIMITS.get(horizon, 0.014))
        prefix_retained = bool(_mean(prefix_values) <= prefix_limit)
        success_delta = float(group["sequence_success"].astype(bool).mean() - group["base_success"].astype(bool).mean())
        collision_delta = float(group["sequence_collision"].astype(bool).mean() - group["base_collision"].astype(bool).mean())
        margin_mean_delta = _mean(margin_delta)
        positive_margin_fraction = float(np.mean((margin_delta.to_numpy(dtype=np.float64) > 0.0).astype(np.float32)))
        sequence_low_tail_candidate = bool(
            first_action_retained
            and prefix_retained
            and margin_mean_delta >= 0.001
            and success_delta >= 0.0
            and collision_delta <= 0.0
            and positive_margin_fraction >= 0.55
        )
        summary_rows.append(
            {
                "family": str(family),
                "horizon": horizon,
                "rows": int(len(group)),
                "first_action_l2_mean": _mean(first_values),
                "first_action_l2_p95": _percentile(first_values, 95),
                "prefix_l2_mean": _mean(prefix_values),
                "prefix_l2_p95": _percentile(prefix_values, 95),
                "prefix_mean_limit": prefix_limit,
                "terminal_margin_mean_delta": margin_mean_delta,
                "terminal_margin_p10_delta": _percentile(margin_delta, 10),
                "positive_margin_fraction": positive_margin_fraction,
                "success_delta": success_delta,
                "collision_delta": collision_delta,
                "first_action_retained": first_action_retained,
                "prefix_retained": prefix_retained,
                "sequence_low_tail_candidate": sequence_low_tail_candidate,
            }
        )
    return summary_rows


def run_low_tail_sequence_target_audit(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    low_tail_rows_path: Path,
    m267_corpus_path: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str,
    horizons: tuple[int, ...],
    amplitudes: tuple[float, ...],
    active_row_ids: tuple[int, ...],
    max_low_tail_rows: int,
    max_continuation_steps: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    from autodrift.public_base_controlled_fusion_surface_probe import _load_trainable_samples

    samples, meta_rows, rejected_rows = _load_trainable_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    _target_mask, low_tail_mask, _target_actions, _target_weights, _weight_rows, missing_target_keys = target_weight_vector(
        meta_rows=meta_rows,
        target_rows=target_rows,
        low_tail_rows=low_tail_rows,
        normal_actions=samples["normal_actions"],
    )
    low_tail_indices = _selected_low_tail_indices(low_tail_mask, max_low_tail_rows)
    sequence_detail_rows = _sequence_rows(
        model=model,
        meta_rows=meta_rows,
        samples=samples,
        low_tail_indices=low_tail_indices,
        env_config=env_config,
        horizons=horizons,
        amplitudes=amplitudes,
        max_continuation_steps=max_continuation_steps,
        device=resolved_device,
    )
    sequence_summary_rows = _summarize_sequence_rows(sequence_detail_rows)
    sequence_families = [str(row["family"]) for row in sequence_summary_rows]
    m267_preflight_detail_rows = _m267_target_preflight(
        model=model,
        corpus_csv=m267_corpus_path,
        env_config_path=env_config_path,
        active_row_ids=active_row_ids,
        family_names=sequence_families,
        device=resolved_device,
        max_continuation_steps=max_continuation_steps,
    )
    m267_preflight_rows = _summarize_m267_preflight(m267_preflight_detail_rows)
    m267_by_family = {str(row["family"]): row for row in m267_preflight_rows}
    family_summary: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for row in sequence_summary_rows:
        m267 = m267_by_family.get(str(row["family"]), {})
        m267_pass = str(m267.get("gate_pass", False)).lower() == "true" if not isinstance(m267.get("gate_pass"), bool) else bool(m267.get("gate_pass"))
        sequence_pass = bool(row["sequence_low_tail_candidate"])
        joint = bool(sequence_pass and m267_pass)
        combined = {
            **row,
            "m267_sequence_preflight_pass": m267_pass,
            "m267_active_rows_pass": bool(m267.get("active_rows_pass", False)),
            "m267_failed_active_rows": str(m267.get("failed_active_rows", "")),
            "joint_sequence_candidate": joint,
        }
        family_summary.append(combined)
        if sequence_pass != m267_pass:
            conflicts.append(
                {
                    "family": str(row["family"]),
                    "sequence_low_tail_candidate": sequence_pass,
                    "m267_sequence_preflight_pass": m267_pass,
                    "conflict_type": "sequence_without_m267" if sequence_pass else "m267_without_sequence",
                    "m267_failed_active_rows": str(m267.get("failed_active_rows", "")),
                }
            )
    first_action_retained_count = sum(1 for row in family_summary if bool(row["first_action_retained"]))
    sequence_candidate_count = sum(1 for row in family_summary if bool(row["sequence_low_tail_candidate"]))
    m267_pass_count = sum(1 for row in family_summary if bool(row["m267_sequence_preflight_pass"]))
    joint_count = sum(1 for row in family_summary if bool(row["joint_sequence_candidate"]))
    terminal_margin_positive_count = sum(
        1 for row in family_summary if float(row.get("terminal_margin_mean_delta", 0.0)) > 0.0
    )
    result_class = classify_sequence_target_audit(
        contract_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        sequence_family_count=len(family_summary),
        first_action_retained_family_count=first_action_retained_count,
        sequence_low_tail_candidate_count=sequence_candidate_count,
        m267_sequence_preflight_pass_count=m267_pass_count,
        joint_sequence_candidate_count=joint_count,
    )
    if joint_count > 0:
        next_blocker = "sequence target export and actor-fit objective design"
    elif sequence_candidate_count > 0 and m267_pass_count == 0:
        next_blocker = "branch-separated sequence target refinement"
    elif sequence_candidate_count == 0 and first_action_retained_count > 0 and m267_pass_count > 0:
        next_blocker = "target-metric artifact audit"
    elif sequence_candidate_count == 0 and first_action_retained_count > 0:
        next_blocker = "exact threshold sensitivity audit"
    else:
        next_blocker = "sequence replay infrastructure audit"
    write_csv_rows(run_dir / "low_tail_sequence_metrics.csv", sequence_detail_rows)
    write_csv_rows(run_dir / "sequence_family_summary.csv", family_summary)
    write_csv_rows(run_dir / "m267_sequence_preflight.csv", m267_preflight_rows)
    write_csv_rows(run_dir / "m267_sequence_preflight_rows.csv", m267_preflight_detail_rows)
    write_csv_rows(run_dir / "sequence_row_conflicts.csv", conflicts)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "public_base_low_tail_sequence_target_audit",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "low_tail_rows": low_tail_rows_path,
        "m267_corpus": m267_corpus_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(low_tail_mask.detach().cpu().sum().item()),
        "evaluated_low_tail_rows": int(len(low_tail_indices)),
        "horizons": [int(value) for value in horizons],
        "amplitudes": [float(value) for value in amplitudes],
        "sequence_family_count": int(len(family_summary)),
        "first_action_retained_family_count": int(first_action_retained_count),
        "sequence_low_tail_candidate_count": int(sequence_candidate_count),
        "terminal_margin_positive_family_count": int(terminal_margin_positive_count),
        "m267_sequence_preflight_pass_count": int(m267_pass_count),
        "joint_sequence_candidate_count": int(joint_count),
        "joint_sequence_families": [row["family"] for row in family_summary if bool(row["joint_sequence_candidate"])],
        "sequence_row_conflict_count": int(len(conflicts)),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "actor_output_contract_changed": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "next_blocker": next_blocker,
        "summary_json": run_dir / "summary.json",
        "sequence_family_summary_csv": run_dir / "sequence_family_summary.csv",
        "low_tail_sequence_metrics_csv": run_dir / "low_tail_sequence_metrics.csv",
        "m267_sequence_preflight_csv": run_dir / "m267_sequence_preflight.csv",
        "sequence_row_conflicts_csv": run_dir / "sequence_row_conflicts.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training low-tail sequence target audit.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, default=DEFAULT_POSITIVE_ROWS)
    parser.add_argument("--contrast-rows", type=Path, default=DEFAULT_CONTRAST_ROWS)
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO_CONFIG)
    parser.add_argument("--target-rows", type=Path, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--low-tail-rows", type=Path, default=DEFAULT_LOW_TAIL_ROWS)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--horizons", type=_parse_int_tuple, default=DEFAULT_HORIZONS)
    parser.add_argument("--amplitudes", type=_parse_float_tuple, default=DEFAULT_AMPLITUDES)
    parser.add_argument("--active-row-ids", type=_parse_int_tuple, default=DEFAULT_ACTIVE_ROW_IDS)
    parser.add_argument("--max-low-tail-rows", type=int, default=DEFAULT_MAX_LOW_TAIL_ROWS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_low_tail_sequence_target_audit(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        low_tail_rows_path=args.low_tail_rows,
        m267_corpus_path=args.m267_corpus,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        horizons=args.horizons,
        amplitudes=args.amplitudes,
        active_row_ids=args.active_row_ids,
        max_low_tail_rows=args.max_low_tail_rows,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"joint_sequence_candidate_count={summary['joint_sequence_candidate_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
