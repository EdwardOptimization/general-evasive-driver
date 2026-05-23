"""Export active-boundary old-key residual corpora."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.active_set_radius_anchor import old_key_case_id
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.critical_key_replay_guard import CheckpointPolicy, parse_checkpoint_policy
from autodrift.evaluate import load_env_config
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.old_key_neighborhood_targeted_replay import (
    _probe_config,
    _randomization,
    _requests_by_condition,
    _require_columns,
    _snapshot,
    _tuple_range,
    collect_targeted_probe_snapshots,
)
from autodrift.outcome_sensitive_corpus import obstacle_override_config, relocate_obstacle_snapshot
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import resolve_device


VIOLATION_WRONG_SAFE = 0
VIOLATION_GAP_EROSION = 1
VIOLATION_NORMAL_COLLISION = 2
VIOLATION_NAMES = {
    VIOLATION_WRONG_SAFE: "wrong_history_safe",
    VIOLATION_GAP_EROSION: "gap_erosion",
    VIOLATION_NORMAL_COLLISION: "normal_collision",
}

ACTIVE_BOUNDARY_REQUIRED_COLUMNS = {
    "policy",
    "key",
    "seed",
    "source_condition",
    "source_step",
    "paired_step",
    "target_obstacle_distance",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
    "reference_wrong_history_margin",
    "reference_margin_gap",
    "accepted",
    "normal_success",
    "normal_margin",
    "wrong_history_margin",
    "margin_gap",
}


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _finite_float(value: Any) -> float:
    parsed = float(value)
    if not np.isfinite(parsed):
        raise ValueError(f"expected finite float, got {value!r}")
    return parsed


def parse_profile_path(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("expected NAME=PATH")
    name, path = raw.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("profile name cannot be empty")
    return name, Path(path)


def classify_active_boundary_violation(row: pd.Series | dict[str, Any]) -> int:
    if not _truthy(row.get("normal_success", False)):
        return VIOLATION_NORMAL_COLLISION
    wrong_margin = _finite_float(row["wrong_history_margin"])
    reference_wrong_margin = _finite_float(row["reference_wrong_history_margin"])
    if wrong_margin > 0.0 and reference_wrong_margin < 0.0:
        return VIOLATION_WRONG_SAFE
    return VIOLATION_GAP_EROSION


def active_boundary_weight(row: pd.Series | dict[str, Any], violation_type: int) -> float:
    if violation_type == VIOLATION_NORMAL_COLLISION:
        return max(1e-4, -_finite_float(row["normal_margin"]))
    if violation_type == VIOLATION_WRONG_SAFE:
        return max(1e-4, _finite_float(row["wrong_history_margin"]) + 1e-4)
    gap_floor = _finite_float(row["reference_margin_gap"])
    margin_gap = _finite_float(row["margin_gap"])
    return max(1e-4, gap_floor - margin_gap)


def _failed_rows_for_profile(path: Path, profile: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    _require_columns(frame, ACTIVE_BOUNDARY_REQUIRED_COLUMNS, label=f"active-boundary guard results {path}")
    selected = frame[frame["policy"].astype(str).eq(str(profile))].copy()
    if selected.empty:
        raise ValueError(f"guard results {path} contain no rows for policy {profile!r}")
    failed = selected[~selected["accepted"].map(_truthy)].copy()
    if failed.empty:
        return failed
    failed["case_id"] = failed.apply(old_key_case_id, axis=1)
    failed["source_profile"] = str(profile)
    failed["violation_type"] = failed.apply(classify_active_boundary_violation, axis=1)
    failed["violation_name"] = failed["violation_type"].map(VIOLATION_NAMES)
    failed["weight"] = failed.apply(lambda row: active_boundary_weight(row, int(row["violation_type"])), axis=1)
    return failed.reset_index(drop=True)


def _action(
    model: Any,
    observation: np.ndarray,
    hidden: Any,
    device: Any,
) -> np.ndarray:
    if hidden is None:
        raise ValueError("active-boundary export requires recurrent hidden states")
    action, _ = deterministic_action_from_hidden(model, np.asarray(observation, dtype=np.float32), hidden, device)
    return np.asarray(action, dtype=np.float32)


def export_active_boundary_corpus(
    *,
    proof_policy: CheckpointPolicy,
    candidate_policies: dict[str, Path],
    guard_results_csvs: dict[str, Path],
    reference_manifest: Path,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    profile_frames = [_failed_rows_for_profile(path, profile) for profile, path in guard_results_csvs.items()]
    failed = pd.concat([frame for frame in profile_frames if not frame.empty], ignore_index=True)
    if failed.empty:
        raise ValueError("active-boundary export requires at least one failed row")
    missing_profiles = sorted(set(failed["source_profile"].astype(str)) - set(candidate_policies))
    if missing_profiles:
        raise ValueError(f"missing candidate checkpoint(s) for profiles: {missing_profiles}")

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
    requests = _requests_by_condition(failed)
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
    observations: list[np.ndarray] = []
    normal_hidden: list[np.ndarray] = []
    wrong_hidden: list[np.ndarray] = []
    proof_normal_action: list[np.ndarray] = []
    proof_wrong_action: list[np.ndarray] = []
    candidate_normal_action: list[np.ndarray] = []
    candidate_wrong_action: list[np.ndarray] = []
    normal_margin: list[float] = []
    wrong_history_margin: list[float] = []
    margin_gap: list[float] = []
    violation_type: list[int] = []
    weights: list[float] = []
    row_ids: list[int] = []
    profile_indices: list[int] = []
    metadata_rows: list[dict[str, Any]] = []

    for row_id, row in failed.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        paired = "perturbed" if source == "nominal" else "nominal"
        source_snapshot = _snapshot(snapshots, source, seed, int(row["source_step"]))
        paired_snapshot = _snapshot(snapshots, paired, seed, int(row["paired_step"]))
        if source_snapshot is None or paired_snapshot is None:
            raise ValueError(f"missing active-boundary snapshot for row {row_id}")
        relocated = relocate_obstacle_snapshot(
            source_snapshot,
            body_longitudinal=float(row["target_obstacle_distance"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        if relocated.hidden is None or paired_snapshot.hidden is None:
            raise ValueError("active-boundary snapshots require normal and wrong hidden states")
        profile = str(row["source_profile"])
        candidate_model = candidate_models[profile]
        obs = np.asarray(relocated.observation, dtype=np.float32)
        normal_h = relocated.hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)
        wrong_h = paired_snapshot.hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)
        proof_normal = _action(proof_model, obs, relocated.hidden, resolved_device)
        proof_wrong = _action(proof_model, obs, paired_snapshot.hidden, resolved_device)
        candidate_normal = _action(candidate_model, obs, relocated.hidden, resolved_device)
        candidate_wrong = _action(candidate_model, obs, paired_snapshot.hidden, resolved_device)

        observations.append(obs)
        normal_hidden.append(normal_h)
        wrong_hidden.append(wrong_h)
        proof_normal_action.append(proof_normal)
        proof_wrong_action.append(proof_wrong)
        candidate_normal_action.append(candidate_normal)
        candidate_wrong_action.append(candidate_wrong)
        normal_margin.append(_finite_float(row["normal_margin"]))
        wrong_history_margin.append(_finite_float(row["wrong_history_margin"]))
        margin_gap.append(_finite_float(row["margin_gap"]))
        violation = int(row["violation_type"])
        violation_type.append(violation)
        weights.append(float(row["weight"]))
        row_ids.append(int(row_id))
        profile_indices.append(int(profile_to_index[profile]))
        metadata_rows.append(
            {
                "row_id": int(row_id),
                "source_profile": profile,
                "profile_index": int(profile_to_index[profile]),
                "case_id": str(row["case_id"]),
                "key": str(row["key"]),
                "violation_type": violation,
                "violation_name": VIOLATION_NAMES[violation],
                "weight": float(row["weight"]),
                "seed": seed,
                "source_condition": source,
                "source_step": int(row["source_step"]),
                "paired_step": int(row["paired_step"]),
                "target_obstacle_distance": float(row["target_obstacle_distance"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "reference_wrong_history_margin": float(row["reference_wrong_history_margin"]),
                "reference_margin_gap": float(row["reference_margin_gap"]),
                "normal_margin": float(row["normal_margin"]),
                "wrong_history_margin": float(row["wrong_history_margin"]),
                "margin_gap": float(row["margin_gap"]),
            }
        )

    npz_path = run_dir / "active_boundary_corpus.npz"
    np.savez(
        npz_path,
        observation=np.asarray(observations, dtype=np.float32),
        normal_hidden=np.asarray(normal_hidden, dtype=np.float32),
        wrong_hidden=np.asarray(wrong_hidden, dtype=np.float32),
        proof_normal_action=np.asarray(proof_normal_action, dtype=np.float32),
        proof_wrong_action=np.asarray(proof_wrong_action, dtype=np.float32),
        candidate_normal_action=np.asarray(candidate_normal_action, dtype=np.float32),
        candidate_wrong_action=np.asarray(candidate_wrong_action, dtype=np.float32),
        normal_margin=np.asarray(normal_margin, dtype=np.float32),
        wrong_history_margin=np.asarray(wrong_history_margin, dtype=np.float32),
        margin_gap=np.asarray(margin_gap, dtype=np.float32),
        violation_type=np.asarray(violation_type, dtype=np.int64),
        weight=np.asarray(weights, dtype=np.float32),
        row_id=np.asarray(row_ids, dtype=np.int64),
        profile_index=np.asarray(profile_indices, dtype=np.int64),
    )
    metadata_csv = run_dir / "active_boundary_rows.csv"
    write_csv_rows(metadata_csv, metadata_rows)
    counts = failed["violation_name"].value_counts().to_dict()
    cases = sorted(str(value) for value in failed["case_id"].unique().tolist())
    summary = {
        "run_type": "active_boundary_corpus_export",
        "proof_policy": asdict(proof_policy),
        "candidate_policies": {profile: str(path) for profile, path in sorted(candidate_policies.items())},
        "guard_results_csvs": {profile: str(path) for profile, path in sorted(guard_results_csvs.items())},
        "reference_manifest": reference_manifest,
        "corpus_npz": npz_path,
        "rows_csv": metadata_csv,
        "rows": int(len(metadata_rows)),
        "cases": cases,
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
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    candidate_policies = dict(args.candidate_policy)
    guard_results_csvs = dict(args.guard_results_csv)
    summary = export_active_boundary_corpus(
        proof_policy=args.proof_policy,
        candidate_policies=candidate_policies,
        guard_results_csvs=guard_results_csvs,
        reference_manifest=args.reference_manifest,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"rows={summary['rows']}")
    print(f"cases={','.join(summary['cases'])}")


if __name__ == "__main__":
    main()
