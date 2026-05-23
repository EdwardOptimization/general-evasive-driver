"""Export selective 10004 wrong-history trajectory-anchor profiles."""

from __future__ import annotations

import argparse
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json


TARGET_CASE_ID = "10004|perturbed|31|31|9.500000|-1.000000|0.800000"


@dataclass(frozen=True)
class Selective10004Profile:
    name: str
    radius: float
    tail_only: bool = False
    tail_fraction: float = 1.0 / 3.0


DEFAULT_PROFILES: tuple[Selective10004Profile, ...] = (
    Selective10004Profile("r0005", 0.0005),
    Selective10004Profile("r0010", 0.0010),
    Selective10004Profile("r0015", 0.0015),
    Selective10004Profile("r0020", 0.0020),
    Selective10004Profile("tail_r0005", 0.0005, tail_only=True),
    Selective10004Profile("tail_r0010", 0.0010, tail_only=True),
)


def _load_npz_arrays(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    required = {"observation", "hidden", "reference_action", "source_index", "step_index", "weight", "radius"}
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"anchor npz missing fields: {missing}")
    return {name: np.asarray(data[name]) for name in required}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _target_source_index(rows: list[dict[str, str]], target_case_id: str) -> int:
    matches = [
        int(row["source_index"])
        for row in rows
        if str(row.get("case_id", "")) == target_case_id and str(row.get("branch", "")) == "wrong_history"
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {target_case_id} wrong-history source, got {matches}")
    return matches[0]


def _tail_keep_indices(step_index: np.ndarray, target_mask: np.ndarray, tail_fraction: float) -> np.ndarray:
    target_indices = np.flatnonzero(target_mask)
    if target_indices.size < 1:
        raise ValueError("target source has no rows")
    if tail_fraction <= 0.0 or tail_fraction > 1.0:
        raise ValueError("tail_fraction must be in (0, 1]")
    target_sorted = target_indices[np.argsort(step_index[target_indices], kind="stable")]
    tail_count = max(1, int(math.ceil(float(target_sorted.size) * float(tail_fraction))))
    keep_target = set(int(value) for value in target_sorted[-tail_count:])
    return np.asarray([idx not in target_indices or idx in keep_target for idx in range(step_index.shape[0])], dtype=bool)


def _profile_arrays(
    arrays: dict[str, np.ndarray],
    *,
    target_source: int,
    profile: Selective10004Profile,
) -> tuple[dict[str, np.ndarray], int]:
    source_index = np.asarray(arrays["source_index"], dtype=np.int64)
    target_mask = source_index == int(target_source)
    if int(target_mask.sum()) < 1:
        raise ValueError(f"target source {target_source} has no rows")
    keep_mask = (
        _tail_keep_indices(np.asarray(arrays["step_index"], dtype=np.int64), target_mask, profile.tail_fraction)
        if profile.tail_only
        else np.ones(source_index.shape[0], dtype=bool)
    )
    result: dict[str, np.ndarray] = {}
    for name, value in arrays.items():
        filtered = np.asarray(value)[keep_mask]
        result[name] = filtered.copy()
    profile_target_mask = np.asarray(result["source_index"], dtype=np.int64) == int(target_source)
    if int(profile_target_mask.sum()) < 1:
        raise ValueError("profile removed all target rows")
    result["radius"] = np.asarray(result["radius"], dtype=np.float32)
    result["radius"][profile_target_mask] = float(profile.radius)
    return result, int(profile_target_mask.sum())


def _profile_source_rows(
    rows: list[dict[str, str]],
    *,
    target_source: int,
    profile: Selective10004Profile,
    target_rows: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        if int(copied["source_index"]) == int(target_source):
            copied["rows"] = int(target_rows)
            copied["radius"] = float(profile.radius)
            copied["role"] = "selective_10004_wrong_history_guard"
            copied["profile"] = profile.name
            copied["tail_only"] = bool(profile.tail_only)
        else:
            copied["profile"] = profile.name
            copied["tail_only"] = False
        output.append(copied)
    return output


def export_selective_10004_profiles(
    *,
    base_anchor_npz: Path,
    base_sources_csv: Path,
    run_dir: Path,
    target_case_id: str = TARGET_CASE_ID,
    profiles: tuple[Selective10004Profile, ...] = DEFAULT_PROFILES,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = _load_npz_arrays(base_anchor_npz)
    source_rows = _read_csv_rows(base_sources_csv)
    target_source = _target_source_index(source_rows, target_case_id)
    profile_summaries: list[dict[str, Any]] = []
    for profile in profiles:
        profile_dir = run_dir / profile.name
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_arrays, target_rows = _profile_arrays(arrays, target_source=target_source, profile=profile)
        anchor_path = profile_dir / "selective_anchor.npz"
        source_path = profile_dir / "selective_sources.csv"
        np.savez(anchor_path, **profile_arrays)
        write_csv_rows(
            source_path,
            _profile_source_rows(
                source_rows,
                target_source=target_source,
                profile=profile,
                target_rows=target_rows,
            ),
        )
        profile_summaries.append(
            {
                "name": profile.name,
                "anchor_npz": anchor_path,
                "source_summary_csv": source_path,
                "rows": int(profile_arrays["observation"].shape[0]),
                "target_source_index": int(target_source),
                "target_rows": int(target_rows),
                "target_radius": float(profile.radius),
                "tail_only": bool(profile.tail_only),
                "tail_fraction": float(profile.tail_fraction),
            }
        )
    summary = {
        "run_type": "selective_10004_anchor_export",
        "base_anchor_npz": base_anchor_npz,
        "base_sources_csv": base_sources_csv,
        "target_case_id": target_case_id,
        "target_source_index": int(target_source),
        "profiles": profile_summaries,
        "profile_count": int(len(profile_summaries)),
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-anchor-npz", type=Path, required=True)
    parser.add_argument("--base-sources-csv", type=Path, required=True)
    parser.add_argument("--target-case-id", default=TARGET_CASE_ID)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = export_selective_10004_profiles(
        base_anchor_npz=args.base_anchor_npz,
        base_sources_csv=args.base_sources_csv,
        target_case_id=str(args.target_case_id),
        run_dir=args.run_dir,
    )
    print(f"profiles={summary['profile_count']}")
    for profile in summary["profiles"]:
        print(f"{profile['name']}: rows={profile['rows']} target_rows={profile['target_rows']} radius={profile['target_radius']}")


if __name__ == "__main__":
    main()
