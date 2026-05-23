"""Export active-boundary v2 trajectory-window residual corpora."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.active_boundary_residual import (
    ACTIVE_BOUNDARY_REQUIRED_COLUMNS,
    VIOLATION_GAP_EROSION,
    VIOLATION_NAMES,
    VIOLATION_NORMAL_COLLISION,
    VIOLATION_WRONG_SAFE,
    _action,
    _finite_float,
    _truthy,
    parse_profile_path,
)
from autodrift.active_set_radius_anchor import old_key_case_id
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.critical_key_replay_guard import CheckpointPolicy, parse_checkpoint_policy
from autodrift.evaluate import load_env_config
from autodrift.old_key_neighborhood_targeted_replay import (
    _probe_config,
    _randomization,
    _require_columns,
    _snapshot,
    _tuple_range,
    collect_targeted_probe_snapshots,
)
from autodrift.outcome_sensitive_corpus import obstacle_override_config, relocate_obstacle_snapshot
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import resolve_device


DEFAULT_ACTIVE_KEYS = (
    "10004|perturbed|31|31",
    "10023|perturbed|12|12",
    "9998|perturbed|25|25",
)
DEFAULT_WINDOW_OFFSETS = (-6, -4, -2, 0)
WEIGHT_CAP = 0.002


def parse_offsets(raw: str) -> tuple[int, ...]:
    offsets = tuple(int(part.strip()) for part in str(raw).split(",") if part.strip())
    if not offsets:
        raise argparse.ArgumentTypeError("window offsets must contain at least one integer")
    return offsets


def _clip_weight(value: float) -> float:
    return min(WEIGHT_CAP, max(0.0, float(value)))


def _normal_margin_floor(key: str) -> float:
    return 0.0100 if str(key).startswith("10023|") else 0.0015


def _violation_type_for_key(row: pd.Series | dict[str, Any]) -> int:
    if not _truthy(row.get("normal_success", False)):
        return VIOLATION_NORMAL_COLLISION
    key = str(row["key"])
    if key.startswith("10023|"):
        return VIOLATION_GAP_EROSION
    return VIOLATION_WRONG_SAFE


def _row_family_weights(row: pd.Series | dict[str, Any], violation_type: int) -> tuple[float, float, float]:
    wrong_margin = _finite_float(row["wrong_history_margin"])
    gap_deficit = _finite_float(row["reference_margin_gap"]) - _finite_float(row["margin_gap"])
    normal_margin = _finite_float(row["normal_margin"])
    normal_deficit = _normal_margin_floor(str(row["key"])) - normal_margin

    wrong_weight = 0.0
    gap_weight = 0.0
    normal_weight = _clip_weight(normal_deficit)
    if violation_type == VIOLATION_WRONG_SAFE:
        wrong_weight = _clip_weight(max(1e-4, wrong_margin + 1e-4))
    elif violation_type == VIOLATION_GAP_EROSION:
        gap_weight = _clip_weight(max(1e-4, gap_deficit))
    elif violation_type == VIOLATION_NORMAL_COLLISION:
        normal_weight = _clip_weight(max(1e-4, -normal_margin))
        if str(row["key"]).startswith("10023|"):
            gap_weight = _clip_weight(max(1e-4, gap_deficit))
        else:
            wrong_weight = _clip_weight(max(1e-4, wrong_margin + 1e-4))
    return wrong_weight, gap_weight, normal_weight


def _active_rows_for_profile(path: Path, profile: str, active_keys: set[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    _require_columns(frame, ACTIVE_BOUNDARY_REQUIRED_COLUMNS, label=f"active-boundary-v2 guard results {path}")
    selected = frame[frame["policy"].astype(str).eq(str(profile))].copy()
    if selected.empty:
        raise ValueError(f"guard results {path} contain no rows for policy {profile!r}")
    active = selected[selected["key"].astype(str).isin(active_keys)].copy()
    if active.empty:
        raise ValueError(f"guard results {path} contain no active keys for policy {profile!r}")
    active["case_id"] = active.apply(old_key_case_id, axis=1)
    active["source_profile"] = str(profile)
    active["violation_type"] = active.apply(_violation_type_for_key, axis=1)
    active["violation_name"] = active["violation_type"].map(VIOLATION_NAMES)
    weights = active.apply(
        lambda row: _row_family_weights(row, int(row["violation_type"])),
        axis=1,
    )
    active["wrong_safety_weight"] = [float(value[0]) for value in weights]
    active["gap_weight"] = [float(value[1]) for value in weights]
    active["normal_safety_weight"] = [float(value[2]) for value in weights]
    positive = (
        active["wrong_safety_weight"].astype(float)
        + active["gap_weight"].astype(float)
        + active["normal_safety_weight"].astype(float)
    ) > 0.0
    return active[positive].reset_index(drop=True)


def _expand_window_rows(rows: pd.DataFrame, offsets: tuple[int, ...]) -> pd.DataFrame:
    expanded: list[dict[str, Any]] = []
    for _, row in rows.iterrows():
        source_step = int(row["source_step"])
        paired_step = int(row["paired_step"])
        for offset in offsets:
            source_window_step = max(0, source_step + int(offset))
            paired_window_step = max(0, paired_step + int(offset))
            item = dict(row)
            item["window_offset"] = int(offset)
            item["window_source_step"] = int(source_window_step)
            item["window_paired_step"] = int(paired_window_step)
            item["source_step"] = int(source_window_step)
            item["paired_step"] = int(paired_window_step)
            item["terminal_source_step"] = int(source_step)
            item["terminal_paired_step"] = int(paired_step)
            expanded.append(item)
    if not expanded:
        raise ValueError("active-boundary-v2 expansion produced no rows")
    return pd.DataFrame(expanded)


def _requests_by_condition_window(rows: pd.DataFrame) -> dict[str, dict[int, set[int]]]:
    requests: dict[str, dict[int, set[int]]] = {"nominal": {}, "perturbed": {}}
    for _, row in rows.iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        if source not in requests:
            raise ValueError(f"unexpected source_condition {source!r}")
        paired = "perturbed" if source == "nominal" else "nominal"
        requests[source].setdefault(seed, set()).add(int(row["window_source_step"]))
        requests[paired].setdefault(seed, set()).add(int(row["window_paired_step"]))
    return requests


def export_active_boundary_v2_corpus(
    *,
    proof_policy: CheckpointPolicy,
    candidate_policies: dict[str, Path],
    guard_results_csvs: dict[str, Path],
    reference_manifest: Path,
    active_keys: set[str],
    window_offsets: tuple[int, ...],
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    profile_frames = [_active_rows_for_profile(path, profile, active_keys) for profile, path in guard_results_csvs.items()]
    active = pd.concat([frame for frame in profile_frames if not frame.empty], ignore_index=True)
    if active.empty:
        raise ValueError("active-boundary-v2 export requires at least one active row")
    missing_profiles = sorted(set(active["source_profile"].astype(str)) - set(candidate_policies))
    if missing_profiles:
        raise ValueError(f"missing candidate checkpoint(s) for profiles: {missing_profiles}")
    expanded = _expand_window_rows(active, window_offsets)

    resolved_device = resolve_device(device)
    proof_model, _ = load_actor_critic_checkpoint(proof_policy.path, device=str(resolved_device))
    proof_model.eval()
    candidate_models = {
        profile: load_actor_critic_checkpoint(path, device=str(resolved_device))[0].eval()
        for profile, path in candidate_policies.items()
    }
    manifest = read_json(reference_manifest)
    base_config = obstacle_override_config(
        load_env_config(Path(manifest["env_config"])),
        distance_range=None,
        half_width_range=None,
        perception_reveal_step=manifest.get("obstacle_perception_reveal_step"),
        perception_reveal_distance=manifest.get("obstacle_perception_reveal_distance"),
    )
    configs = {
        "nominal": condition_config(
            base_config,
            _tuple_range(manifest["nominal_friction_mu_range"]),
            _randomization(manifest.get("nominal_randomization")),
        ),
        "perturbed": condition_config(
            base_config,
            _tuple_range(manifest["perturbed_friction_mu_range"]),
            _randomization(manifest.get("perturbed_randomization")),
        ),
    }
    probe = _probe_config(manifest.get("probe", {}))
    requests = _requests_by_condition_window(expanded)
    snapshots: dict[str, dict[int, dict[int, Any]]] = {"nominal": {}, "perturbed": {}}
    for condition, seed_requests in requests.items():
        for seed, steps in seed_requests.items():
            snapshots[condition][int(seed)] = collect_targeted_probe_snapshots(
                model=proof_model,
                env_config=configs[condition],
                condition=condition,
                seed=int(seed),
                requested_steps=set(int(step) for step in steps),
                max_probe_steps=int(manifest["max_probe_steps"]),
                probe_config=probe,
            )

    profile_to_index = {profile: index for index, profile in enumerate(sorted(candidate_policies))}
    arrays: dict[str, list[Any]] = {
        "observation": [],
        "normal_hidden": [],
        "wrong_hidden": [],
        "proof_normal_action": [],
        "proof_wrong_action": [],
        "candidate_normal_action": [],
        "candidate_wrong_action": [],
        "normal_margin": [],
        "wrong_history_margin": [],
        "margin_gap": [],
        "reference_wrong_history_margin": [],
        "reference_margin_gap": [],
        "wrong_safety_weight": [],
        "gap_weight": [],
        "normal_safety_weight": [],
        "violation_type": [],
        "row_id": [],
        "profile_index": [],
        "window_offset": [],
    }
    metadata_rows: list[dict[str, Any]] = []

    for row_id, row in expanded.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        paired = "perturbed" if source == "nominal" else "nominal"
        source_snapshot = _snapshot(snapshots, source, seed, int(row["window_source_step"]))
        paired_snapshot = _snapshot(snapshots, paired, seed, int(row["window_paired_step"]))
        if source_snapshot is None or paired_snapshot is None:
            raise ValueError(f"missing active-boundary-v2 snapshot for row {row_id}")
        relocated = relocate_obstacle_snapshot(
            source_snapshot,
            body_longitudinal=float(row["target_obstacle_distance"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        if relocated.hidden is None or paired_snapshot.hidden is None:
            raise ValueError("active-boundary-v2 snapshots require normal and wrong hidden states")
        profile = str(row["source_profile"])
        candidate_model = candidate_models[profile]
        obs = np.asarray(relocated.observation, dtype=np.float32)
        normal_h = relocated.hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)
        wrong_h = paired_snapshot.hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)

        arrays["observation"].append(obs)
        arrays["normal_hidden"].append(normal_h)
        arrays["wrong_hidden"].append(wrong_h)
        arrays["proof_normal_action"].append(_action(proof_model, obs, relocated.hidden, resolved_device))
        arrays["proof_wrong_action"].append(_action(proof_model, obs, paired_snapshot.hidden, resolved_device))
        arrays["candidate_normal_action"].append(_action(candidate_model, obs, relocated.hidden, resolved_device))
        arrays["candidate_wrong_action"].append(_action(candidate_model, obs, paired_snapshot.hidden, resolved_device))
        for name in (
            "normal_margin",
            "wrong_history_margin",
            "margin_gap",
            "reference_wrong_history_margin",
            "reference_margin_gap",
            "wrong_safety_weight",
            "gap_weight",
            "normal_safety_weight",
        ):
            arrays[name].append(_finite_float(row[name]))
        arrays["violation_type"].append(int(row["violation_type"]))
        arrays["row_id"].append(int(row_id))
        arrays["profile_index"].append(int(profile_to_index[profile]))
        arrays["window_offset"].append(int(row["window_offset"]))
        metadata_rows.append(
            {
                "row_id": int(row_id),
                "source_profile": profile,
                "profile_index": int(profile_to_index[profile]),
                "case_id": str(row["case_id"]),
                "key": str(row["key"]),
                "violation_type": int(row["violation_type"]),
                "violation_name": VIOLATION_NAMES[int(row["violation_type"])],
                "seed": seed,
                "source_condition": source,
                "terminal_source_step": int(row["terminal_source_step"]),
                "terminal_paired_step": int(row["terminal_paired_step"]),
                "window_source_step": int(row["window_source_step"]),
                "window_paired_step": int(row["window_paired_step"]),
                "window_offset": int(row["window_offset"]),
                "wrong_safety_weight": float(row["wrong_safety_weight"]),
                "gap_weight": float(row["gap_weight"]),
                "normal_safety_weight": float(row["normal_safety_weight"]),
                "normal_margin": float(row["normal_margin"]),
                "wrong_history_margin": float(row["wrong_history_margin"]),
                "margin_gap": float(row["margin_gap"]),
            }
        )

    npz_path = run_dir / "active_boundary_v2_corpus.npz"
    np.savez(
        npz_path,
        observation=np.asarray(arrays["observation"], dtype=np.float32),
        normal_hidden=np.asarray(arrays["normal_hidden"], dtype=np.float32),
        wrong_hidden=np.asarray(arrays["wrong_hidden"], dtype=np.float32),
        proof_normal_action=np.asarray(arrays["proof_normal_action"], dtype=np.float32),
        proof_wrong_action=np.asarray(arrays["proof_wrong_action"], dtype=np.float32),
        candidate_normal_action=np.asarray(arrays["candidate_normal_action"], dtype=np.float32),
        candidate_wrong_action=np.asarray(arrays["candidate_wrong_action"], dtype=np.float32),
        normal_margin=np.asarray(arrays["normal_margin"], dtype=np.float32),
        wrong_history_margin=np.asarray(arrays["wrong_history_margin"], dtype=np.float32),
        margin_gap=np.asarray(arrays["margin_gap"], dtype=np.float32),
        reference_wrong_history_margin=np.asarray(arrays["reference_wrong_history_margin"], dtype=np.float32),
        reference_margin_gap=np.asarray(arrays["reference_margin_gap"], dtype=np.float32),
        wrong_safety_weight=np.asarray(arrays["wrong_safety_weight"], dtype=np.float32),
        gap_weight=np.asarray(arrays["gap_weight"], dtype=np.float32),
        normal_safety_weight=np.asarray(arrays["normal_safety_weight"], dtype=np.float32),
        violation_type=np.asarray(arrays["violation_type"], dtype=np.int64),
        row_id=np.asarray(arrays["row_id"], dtype=np.int64),
        profile_index=np.asarray(arrays["profile_index"], dtype=np.int64),
        window_offset=np.asarray(arrays["window_offset"], dtype=np.int64),
    )
    rows_csv = run_dir / "active_boundary_v2_rows.csv"
    write_csv_rows(rows_csv, metadata_rows)
    counts = pd.DataFrame(metadata_rows)["violation_name"].value_counts().to_dict()
    cases = sorted(str(value) for value in active["case_id"].unique().tolist())
    summary = {
        "run_type": "active_boundary_v2_corpus_export",
        "proof_policy": asdict(proof_policy),
        "candidate_policies": {profile: str(path) for profile, path in sorted(candidate_policies.items())},
        "guard_results_csvs": {profile: str(path) for profile, path in sorted(guard_results_csvs.items())},
        "reference_manifest": reference_manifest,
        "corpus_npz": npz_path,
        "rows_csv": rows_csv,
        "rows": int(len(metadata_rows)),
        "base_active_rows": int(len(active)),
        "cases": cases,
        "window_offsets": list(window_offsets),
        "violation_counts": {str(key): int(value) for key, value in counts.items()},
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-policy", type=parse_checkpoint_policy, required=True)
    parser.add_argument("--candidate-policy", type=parse_profile_path, action="append", required=True)
    parser.add_argument("--guard-results-csv", type=parse_profile_path, action="append", required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--active-key", action="append", default=list(DEFAULT_ACTIVE_KEYS))
    parser.add_argument("--window-offsets", type=parse_offsets, default=DEFAULT_WINDOW_OFFSETS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = export_active_boundary_v2_corpus(
        proof_policy=args.proof_policy,
        candidate_policies=dict(args.candidate_policy),
        guard_results_csvs=dict(args.guard_results_csv),
        reference_manifest=args.reference_manifest,
        active_keys=set(str(key) for key in args.active_key),
        window_offsets=tuple(int(value) for value in args.window_offsets),
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"rows={summary['rows']}")
    print(f"cases={','.join(summary['cases'])}")


if __name__ == "__main__":
    main()
