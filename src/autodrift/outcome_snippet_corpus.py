"""Combine accepted outcome-intervention snippet artifacts."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_json


REQUIRED_ARRAY_KEYS = (
    "observation",
    "preferred_hidden",
    "rejected_hidden",
    "preferred_action",
    "weight",
)
REQUIRED_METADATA_COLUMNS = (
    "seed",
    "source_condition",
    "source_step",
    "paired_step",
    "normal_margin",
    "wrong_history_margin",
    "margin_gap",
    "weight",
)


def _load_input_manifest(run_dir: Path, *, require_accepted_only: bool) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        if require_accepted_only:
            raise ValueError(f"{run_dir}: missing manifest.json for accepted-only verification")
        return {}
    manifest = read_json(manifest_path)
    only_accepted = bool(manifest.get("outcome_export", {}).get("only_accepted_outcomes", False))
    if require_accepted_only and not only_accepted:
        raise ValueError(f"{run_dir}: outcome_export.only_accepted_outcomes must be true")
    return manifest


def _load_snippet_arrays(run_dir: Path) -> dict[str, np.ndarray]:
    npz_path = run_dir / "outcome_intervention_snippets.npz"
    if not npz_path.exists():
        raise ValueError(f"{run_dir}: missing outcome_intervention_snippets.npz")
    data = np.load(npz_path)
    missing = sorted(set(REQUIRED_ARRAY_KEYS).difference(data.files))
    if missing:
        raise ValueError(f"{run_dir}: snippet npz missing fields: {missing}")
    arrays = {key: np.asarray(data[key], dtype=np.float32) for key in REQUIRED_ARRAY_KEYS}
    rows = int(arrays["observation"].shape[0])
    if rows < 1:
        raise ValueError(f"{run_dir}: snippet npz must contain at least one row")
    for key, value in arrays.items():
        expected_rows = rows
        actual_rows = int(value.shape[0]) if value.ndim > 0 else 0
        if actual_rows != expected_rows:
            raise ValueError(f"{run_dir}: array {key!r} row count {actual_rows} does not match {expected_rows}")
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{run_dir}: array {key!r} contains non-finite values")
    if arrays["weight"].ndim != 1:
        raise ValueError(f"{run_dir}: weight must have shape (N,), got {arrays['weight'].shape}")
    if float(np.min(arrays["weight"])) <= 0.0:
        raise ValueError(f"{run_dir}: all outcome snippet weights must be positive")
    return arrays


def _load_snippet_metadata(run_dir: Path, *, rows: int, arrays: dict[str, np.ndarray]) -> pd.DataFrame:
    csv_path = run_dir / "outcome_intervention_snippets.csv"
    if not csv_path.exists():
        raise ValueError(f"{run_dir}: missing outcome_intervention_snippets.csv")
    metadata = pd.read_csv(csv_path)
    missing = sorted(set(REQUIRED_METADATA_COLUMNS).difference(metadata.columns))
    if missing:
        raise ValueError(f"{run_dir}: snippet metadata missing columns: {missing}")
    if len(metadata) != rows:
        raise ValueError(f"{run_dir}: metadata row count {len(metadata)} does not match npz rows {rows}")
    metadata_weight = metadata["weight"].astype(float).to_numpy(dtype=np.float32)
    if not np.allclose(metadata_weight, arrays["weight"], rtol=1e-5, atol=1e-7):
        raise ValueError(f"{run_dir}: metadata weights do not match npz weights")
    return metadata.reset_index(drop=True)


def _row_signature(arrays: dict[str, np.ndarray], row_index: int) -> str:
    digest = hashlib.sha256()
    for key in REQUIRED_ARRAY_KEYS:
        row = np.ascontiguousarray(arrays[key][row_index])
        digest.update(key.encode("utf-8"))
        digest.update(str(row.shape).encode("utf-8"))
        digest.update(str(row.dtype).encode("utf-8"))
        digest.update(row.tobytes())
    return digest.hexdigest()


def _row_arrays(arrays: dict[str, np.ndarray], row_index: int) -> dict[str, np.ndarray]:
    return {key: np.asarray(arrays[key][row_index], dtype=np.float32).copy() for key in REQUIRED_ARRAY_KEYS}


def _stack_rows(rows: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    if not rows:
        raise ValueError("combined outcome snippet corpus must contain at least one row")
    output: dict[str, np.ndarray] = {}
    for key in REQUIRED_ARRAY_KEYS:
        if key == "weight":
            output[key] = np.asarray([float(row[key]) for row in rows], dtype=np.float32)
        else:
            output[key] = np.stack([row[key] for row in rows]).astype(np.float32)
    return output


def _summarize(metadata: pd.DataFrame, *, input_rows: int, input_runs: list[Path], deduplicate: bool) -> dict[str, Any]:
    weights = metadata["weight"].astype(float)
    contributing_counts: dict[str, int] = {}
    for source_runs in metadata.get("source_runs", pd.Series(dtype=str)).astype(str):
        for source_run in source_runs.split("|"):
            contributing_counts[source_run] = contributing_counts.get(source_run, 0) + 1
    return {
        "input_runs": len(input_runs),
        "input_rows": int(input_rows),
        "output_rows": int(len(metadata)),
        "duplicate_rows_removed": int(input_rows - len(metadata)),
        "deduplicate": bool(deduplicate),
        "unique_seeds": int(metadata["seed"].nunique()) if "seed" in metadata else 0,
        "source_condition_counts": metadata["source_condition"].value_counts().sort_index().to_dict(),
        "primary_source_run_counts": metadata["source_run"].value_counts().sort_index().to_dict(),
        "source_run_counts": dict(sorted(contributing_counts.items())),
        "weight_sum": float(weights.sum()) if len(weights) else 0.0,
        "weight_min": float(weights.min()) if len(weights) else 0.0,
        "weight_max": float(weights.max()) if len(weights) else 0.0,
    }


def combine_outcome_snippet_runs(
    input_runs: list[Path | str],
    *,
    run_dir: Path | str,
    deduplicate: bool = False,
    require_accepted_only: bool = True,
) -> dict[str, Any]:
    """Combine accepted outcome-intervention snippet runs into one corpus."""

    run_paths = [Path(path) for path in input_runs]
    if not run_paths:
        raise ValueError("at least one input run is required")

    output_dir = Path(run_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_arrays: list[dict[str, np.ndarray]] = []
    selected_metadata: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    input_rows = 0

    for source_run in run_paths:
        _load_input_manifest(source_run, require_accepted_only=require_accepted_only)
        arrays = _load_snippet_arrays(source_run)
        row_count = int(arrays["observation"].shape[0])
        metadata = _load_snippet_metadata(source_run, rows=row_count, arrays=arrays)
        input_rows += row_count
        for row_index, row in metadata.iterrows():
            signature = _row_signature(arrays, int(row_index))
            source_run_text = str(source_run)
            if deduplicate and signature in seen:
                existing_index = seen[signature]
                existing = selected_metadata[existing_index]
                existing["source_runs"] = f"{existing['source_runs']}|{source_run_text}"
                existing["source_row_indices"] = f"{existing['source_row_indices']}|{int(row_index)}"
                existing["source_run_count"] = int(existing["source_run_count"]) + 1
                continue

            row_dict = row.to_dict()
            row_dict["source_run"] = source_run_text
            row_dict["source_row_index"] = int(row_index)
            row_dict["source_runs"] = source_run_text
            row_dict["source_row_indices"] = str(int(row_index))
            row_dict["source_run_count"] = 1
            row_dict["snippet_signature"] = signature
            seen[signature] = len(selected_metadata)
            selected_metadata.append(row_dict)
            selected_arrays.append(_row_arrays(arrays, int(row_index)))

    combined_arrays = _stack_rows(selected_arrays)
    combined_metadata = pd.DataFrame(selected_metadata)
    summary = _summarize(combined_metadata, input_rows=input_rows, input_runs=run_paths, deduplicate=deduplicate)

    npz_path = output_dir / "outcome_intervention_snippets.npz"
    metadata_csv = output_dir / "outcome_intervention_snippets.csv"
    summary_csv = output_dir / "summary.csv"
    np.savez_compressed(npz_path, **combined_arrays)
    combined_metadata.to_csv(metadata_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    manifest = {
        "run_type": "outcome_snippet_corpus",
        "input_runs": [str(path) for path in run_paths],
        "deduplicate": bool(deduplicate),
        "require_accepted_only": bool(require_accepted_only),
        "summary": summary,
        "artifacts": {
            "outcome_intervention_snippets_npz": npz_path,
            "outcome_intervention_snippets_csv": metadata_csv,
            "summary_csv": summary_csv,
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine accepted outcome-intervention snippet runs.")
    parser.add_argument("--input-run", action="append", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--deduplicate", action="store_true")
    parser.add_argument("--allow-unverified-accepted", action="store_true")
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="outcome_snippet_corpus")
    manifest = combine_outcome_snippet_runs(
        args.input_run,
        run_dir=run_dir,
        deduplicate=args.deduplicate,
        require_accepted_only=not args.allow_unverified_accepted,
    )
    print(pd.Series(manifest["summary"]).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
