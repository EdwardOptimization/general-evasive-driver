"""Export M418 radius-calibrated active-set trajectory anchors."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.critical_key_replay_guard import CheckpointPolicy, parse_checkpoint_policy
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.old_key_replay_failure_trajectory_anchor import export_old_key_replay_failure_trajectory_anchor
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, resolve_device


DEFAULT_SPILLOVER_CASE_IDS = (
    "9951|perturbed|35|32|10.000000|-1.200000|1.400000",
    "9939|perturbed|27|27|12.500000|-0.800000|1.400000",
)

BASE_SOURCE_RADIUS_KEYS = {
    0: "m267_rows_6_15",
    1: "m267_rows_6_15",
    2: "old_key_10004",
    3: "old_key_9998",
    4: "old_key_10023",
}

RADIUS_PROFILES = {
    "conservative": {
        "m267_rows_6_15": 0.00015,
        "old_key_10004": 0.00035,
        "old_key_9998": 0.00008,
        "old_key_10023": 0.00020,
        "old_key_spillover_guards": 0.00008,
    },
    "medium": {
        "m267_rows_6_15": 0.00030,
        "old_key_10004": 0.00050,
        "old_key_9998": 0.00012,
        "old_key_10023": 0.00035,
        "old_key_spillover_guards": 0.00015,
    },
    "loose": {
        "m267_rows_6_15": 0.00045,
        "old_key_10004": 0.00065,
        "old_key_9998": 0.00018,
        "old_key_10023": 0.00050,
        "old_key_spillover_guards": 0.00025,
    },
}

MIXED_RADIUS_PROFILES = {
    "mixed_a": {
        "m267_rows_6_15": RADIUS_PROFILES["medium"]["m267_rows_6_15"],
        "old_key_10004": RADIUS_PROFILES["medium"]["old_key_10004"],
        "old_key_9998": RADIUS_PROFILES["medium"]["old_key_9998"],
        "old_key_10023": RADIUS_PROFILES["conservative"]["old_key_10023"],
        "old_key_spillover_guards": RADIUS_PROFILES["medium"]["old_key_spillover_guards"],
    },
    "mixed_b": {
        "m267_rows_6_15": RADIUS_PROFILES["medium"]["m267_rows_6_15"],
        "old_key_10004": RADIUS_PROFILES["loose"]["old_key_10004"],
        "old_key_9998": RADIUS_PROFILES["medium"]["old_key_9998"],
        "old_key_10023": RADIUS_PROFILES["conservative"]["old_key_10023"],
        "old_key_spillover_guards": RADIUS_PROFILES["medium"]["old_key_spillover_guards"],
    },
    "mixed_c": {
        "m267_rows_6_15": RADIUS_PROFILES["loose"]["m267_rows_6_15"],
        "old_key_10004": RADIUS_PROFILES["loose"]["old_key_10004"],
        "old_key_9998": RADIUS_PROFILES["medium"]["old_key_9998"],
        "old_key_10023": RADIUS_PROFILES["conservative"]["old_key_10023"],
        "old_key_spillover_guards": RADIUS_PROFILES["medium"]["old_key_spillover_guards"],
    },
}

PROFILE_SETS = {
    "base": RADIUS_PROFILES,
    "mixed": MIXED_RADIUS_PROFILES,
    "all": {**RADIUS_PROFILES, **MIXED_RADIUS_PROFILES},
}

PROFILE_ORDERS = {
    "base": ["medium", "conservative", "loose"],
    "mixed": ["mixed_a", "mixed_b", "mixed_c"],
    "all": ["medium", "conservative", "loose", "mixed_a", "mixed_b", "mixed_c"],
}

_BOOL_TRUE = {"1", "true", "yes", "y"}


def parse_case_id_list(raw: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("case id list must contain at least one value")
    return values


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in _BOOL_TRUE


def old_key_case_id(row: pd.Series | dict[str, Any]) -> str:
    return (
        f"{row['key']}|"
        f"{float(row['target_obstacle_distance']):.6f}|"
        f"{float(row['relocated_obstacle_body_y']):.6f}|"
        f"{float(row['relocated_obstacle_half_width']):.6f}"
    )


def build_spillover_failed_rows(
    guard_results_csv: Path,
    *,
    candidate_policy: str,
    spillover_case_ids: tuple[str, ...],
) -> pd.DataFrame:
    frame = pd.read_csv(guard_results_csv)
    if "policy" not in frame or "accepted" not in frame:
        raise ValueError("guard results must contain policy and accepted columns")
    rows = frame[frame["policy"].astype(str).eq(str(candidate_policy))].copy()
    if rows.empty:
        raise ValueError(f"no guard rows found for candidate policy {candidate_policy!r}")
    rows["case_id"] = rows.apply(old_key_case_id, axis=1)
    wanted = set(str(case_id) for case_id in spillover_case_ids)
    rows = rows[rows["case_id"].isin(wanted)].copy()
    rows = rows[~rows["accepted"].map(_truthy)].copy()
    if rows.empty:
        raise ValueError("no failed spillover rows matched the requested case ids")
    missing = sorted(wanted.difference(set(rows["case_id"].astype(str).tolist())))
    if missing:
        raise ValueError(f"missing requested spillover failure rows: {missing}")
    rows["candidate_normal_success_regression"] = False
    rows["candidate_normal_success"] = rows["normal_success"].map(_truthy)
    rows["candidate_wrong_history_margin"] = rows["wrong_history_margin"].astype(float)
    return rows.reset_index(drop=True)


def _load_npz_arrays(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    required = {"observation", "hidden", "reference_action", "source_index", "step_index", "weight"}
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"trajectory anchor missing fields: {missing}")
    return {name: np.asarray(data[name]) for name in required}


def _radius_for_base_sources(source_index: np.ndarray, profile: dict[str, float]) -> np.ndarray:
    radius = np.zeros_like(source_index, dtype=np.float32)
    for source, key in BASE_SOURCE_RADIUS_KEYS.items():
        radius[source_index == int(source)] = float(profile[key])
    unknown = sorted(set(int(value) for value in source_index.tolist()).difference(BASE_SOURCE_RADIUS_KEYS))
    if unknown:
        raise ValueError(f"base active-set anchor has unknown source indices: {unknown}")
    return radius


def _save_profile_anchor(
    *,
    output_npz: Path,
    base_arrays: dict[str, np.ndarray],
    spillover_arrays: dict[str, np.ndarray],
    profile: dict[str, float],
) -> dict[str, Any]:
    base_source = np.asarray(base_arrays["source_index"], dtype=np.int64)
    spill_source = np.asarray(spillover_arrays["source_index"], dtype=np.int64)
    source_offset = int(base_source.max()) + 1
    arrays = {
        "observation": np.concatenate(
            [np.asarray(base_arrays["observation"], dtype=np.float32), np.asarray(spillover_arrays["observation"], dtype=np.float32)],
            axis=0,
        ).astype(np.float32),
        "hidden": np.concatenate(
            [np.asarray(base_arrays["hidden"], dtype=np.float32), np.asarray(spillover_arrays["hidden"], dtype=np.float32)],
            axis=0,
        ).astype(np.float32),
        "reference_action": np.concatenate(
            [
                np.asarray(base_arrays["reference_action"], dtype=np.float32),
                np.asarray(spillover_arrays["reference_action"], dtype=np.float32),
            ],
            axis=0,
        ).astype(np.float32),
        "source_index": np.concatenate([base_source, spill_source + source_offset], axis=0).astype(np.int64),
        "step_index": np.concatenate(
            [
                np.asarray(base_arrays["step_index"], dtype=np.int64),
                np.asarray(spillover_arrays["step_index"], dtype=np.int64),
            ],
            axis=0,
        ).astype(np.int64),
        "weight": np.concatenate(
            [np.asarray(base_arrays["weight"], dtype=np.float32), np.asarray(spillover_arrays["weight"], dtype=np.float32)],
            axis=0,
        ).astype(np.float32),
    }
    base_radius = _radius_for_base_sources(base_source, profile)
    spillover_radius = np.full_like(spill_source, float(profile["old_key_spillover_guards"]), dtype=np.float32)
    arrays["radius"] = np.concatenate([base_radius, spillover_radius], axis=0).astype(np.float32)
    if not np.all(np.isfinite(arrays["radius"])) or float(arrays["radius"].min()) < 0.0:
        raise ValueError("radius values must be finite and nonnegative")
    np.savez(output_npz, **arrays)
    return {
        "anchor_npz": output_npz,
        "rows": int(arrays["observation"].shape[0]),
        "base_rows": int(base_source.shape[0]),
        "spillover_rows": int(spill_source.shape[0]),
        "source_index_offset": source_offset,
        "radius_min": float(arrays["radius"].min()),
        "radius_max": float(arrays["radius"].max()),
    }


def _source_summary_rows(
    *,
    base_summary_csv: Path,
    spillover_csv: Path,
    profile_name: str,
    profile: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = pd.read_csv(base_summary_csv)
    for _, row in base.iterrows():
        source_index = int(row["source_index"])
        radius_key = BASE_SOURCE_RADIUS_KEYS[source_index]
        rows.append(
            {
                "profile": profile_name,
                "source_index": source_index,
                "source_label": str(row["source_label"]),
                "case_id": str(row["case_id"]),
                "role": str(row["role"]),
                "rows": int(row["rows"]),
                "radius": float(profile[radius_key]),
                "weight_mean": float(row["weight_mean"]),
            }
        )
    spillover = pd.read_csv(spillover_csv)
    if not spillover.empty:
        grouped = spillover.groupby(["source_index", "case_id", "branch"], dropna=False).agg(
            rows=("step_index", "size"), weight_mean=("weight", "mean")
        )
        offset = int(base["source_index"].astype(int).max()) + 1
        for _, group in grouped.reset_index().iterrows():
            rows.append(
                {
                    "profile": profile_name,
                    "source_index": int(group["source_index"]) + offset,
                    "source_label": "old_key",
                    "case_id": str(group["case_id"]),
                    "role": "spillover_guard",
                    "rows": int(group["rows"]),
                    "radius": float(profile["old_key_spillover_guards"]),
                    "weight_mean": float(group["weight_mean"]),
                    "branch": str(group["branch"]),
                }
            )
    return rows


def export_active_set_radius_anchors(
    *,
    checkpoint_policy: CheckpointPolicy,
    reference_manifest: Path,
    base_active_anchor_npz: Path,
    base_active_anchor_csv: Path,
    guard_results_csv: Path,
    candidate_policy: str,
    spillover_case_ids: tuple[str, ...],
    max_continuation_steps: int,
    wrong_history_weight: float,
    normal_weight: float,
    profile_set: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    spillover_rows = build_spillover_failed_rows(
        guard_results_csv,
        candidate_policy=candidate_policy,
        spillover_case_ids=spillover_case_ids,
    )
    spillover_rows_csv = run_dir / "spillover_failed_rows.csv"
    write_csv_rows(spillover_rows_csv, spillover_rows.to_dict(orient="records"))
    spillover_run_dir = run_dir / "spillover_anchor"
    spillover_summary = export_old_key_replay_failure_trajectory_anchor(
        checkpoint_policy=checkpoint_policy,
        reference_manifest=reference_manifest,
        failed_rows_csv=spillover_rows_csv,
        max_continuation_steps=max_continuation_steps,
        wrong_history_weight=wrong_history_weight,
        normal_weight=normal_weight,
        device=device,
        run_dir=spillover_run_dir,
    )

    base_arrays = _load_npz_arrays(base_active_anchor_npz)
    spillover_arrays = _load_npz_arrays(Path(spillover_summary["anchor_npz"]))
    if profile_set not in PROFILE_SETS:
        raise ValueError(f"profile_set must be one of {sorted(PROFILE_SETS)}, got {profile_set!r}")
    radius_profiles = PROFILE_SETS[profile_set]
    profile_summaries: dict[str, dict[str, Any]] = {}
    source_rows: list[dict[str, Any]] = []
    resolved_device = resolve_device(device)
    for profile_name, profile in radius_profiles.items():
        profile_npz = run_dir / f"{profile_name}_radius_anchor.npz"
        profile_summary = _save_profile_anchor(
            output_npz=profile_npz,
            base_arrays=base_arrays,
            spillover_arrays=spillover_arrays,
            profile=profile,
        )
        anchor = load_trajectory_action_anchor(
            profile_npz,
            device=resolved_device,
            obs_dim=HUMAN_VIEW_OBS_DIM,
            hidden_size=int(np.asarray(base_arrays["hidden"]).shape[1]),
            act_dim=int(np.asarray(base_arrays["reference_action"]).shape[1]),
        )
        profile_summary["loaded_rows"] = int(anchor.size)
        profile_summary["loaded_radius_min"] = float(anchor.radius.min().detach().cpu().item())
        profile_summary["loaded_radius_max"] = float(anchor.radius.max().detach().cpu().item())
        profile_summaries[profile_name] = profile_summary
        source_rows.extend(
            _source_summary_rows(
                base_summary_csv=base_active_anchor_csv,
                spillover_csv=Path(spillover_summary["anchor_csv"]),
                profile_name=profile_name,
                profile=profile,
            )
        )
    source_summary_csv = run_dir / "radius_anchor_sources.csv"
    write_csv_rows(source_summary_csv, source_rows)
    summary = {
        "run_type": "active_set_radius_anchor_export",
        "checkpoint": asdict(checkpoint_policy),
        "reference_manifest": reference_manifest,
        "base_active_anchor_npz": base_active_anchor_npz,
        "base_active_anchor_csv": base_active_anchor_csv,
        "guard_results_csv": guard_results_csv,
        "candidate_policy": candidate_policy,
        "spillover_case_ids": spillover_case_ids,
        "spillover_failed_rows_csv": spillover_rows_csv,
        "spillover_anchor_summary": spillover_summary,
        "source_summary_csv": source_summary_csv,
        "profile_set": profile_set,
        "profiles": profile_summaries,
        "profile_order_for_probe": PROFILE_ORDERS[profile_set],
        "forbidden_shortcuts_used": False,
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_policy, required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--base-active-anchor-npz", type=Path, required=True)
    parser.add_argument("--base-active-anchor-csv", type=Path, required=True)
    parser.add_argument("--guard-results-csv", type=Path, required=True)
    parser.add_argument("--candidate-policy", default="m417_hinge")
    parser.add_argument("--spillover-case-ids", type=parse_case_id_list, default=DEFAULT_SPILLOVER_CASE_IDS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--wrong-history-weight", type=float, default=75.0)
    parser.add_argument("--normal-weight", type=float, default=75.0)
    parser.add_argument("--profile-set", choices=sorted(PROFILE_SETS), default="base")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = export_active_set_radius_anchors(
        checkpoint_policy=args.checkpoint_policy,
        reference_manifest=args.reference_manifest,
        base_active_anchor_npz=args.base_active_anchor_npz,
        base_active_anchor_csv=args.base_active_anchor_csv,
        guard_results_csv=args.guard_results_csv,
        candidate_policy=args.candidate_policy,
        spillover_case_ids=tuple(args.spillover_case_ids),
        max_continuation_steps=args.max_continuation_steps,
        wrong_history_weight=args.wrong_history_weight,
        normal_weight=args.normal_weight,
        profile_set=args.profile_set,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
