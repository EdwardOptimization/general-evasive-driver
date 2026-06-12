"""Read-only C1 family-selector separability repricing after M3237.

This script performs no rollout and no training. It reads the M3236
tail-family dataset plus the M3237 synthesis result, evaluates a small
deterministic selector battery using train-only statistics, and decides
whether the family-selector route is priced well enough to justify another
training milestone.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5prime_c1_oracle_bc_warmstart as c1  # noqa: E402
from autodrift.artifacts import read_json, utc_timestamp, write_json  # noqa: E402


PREREG_JSON = (
    REPO
    / "experiments"
    / "feasibility_audit"
    / "c5prime_c1_family_selector_repricing_prereg.json"
)
OUTPUT_JSON = (
    REPO
    / "experiments"
    / "feasibility_audit"
    / "c5prime_c1_family_selector_repricing.json"
)
M3236_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_pretrain_quick.json"
M3237_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_synthesis_repricing.json"
DATASET_NPZ = (
    REPO
    / "runs"
    / "feasibility_audit"
    / "c5prime_c1_tail_family_interface_pretrain_quick"
    / "quick"
    / "interface_pretrain_dataset.npz"
)

ROLE_NAMES = {0: "train", 1: "selection", 2: "validation"}
ROLE_IDS = {name: role_id for role_id, name in ROLE_NAMES.items()}

CLAIM_BOUNDARY = (
    "M3238 C1 family-selector/separability repricing only: read-only "
    "analysis of the existing M3236 tail-family dataset and M3237 synthesis "
    "result. No rollout, no training, no checkpoint, no dataset write, no "
    "incumbent mutation, no validation ranking, no driver-performance claim, "
    "no high-fidelity sufficiency claim, no C2 admission, and no self-ID claim."
)


def _round(value: float | int | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _path_text(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _role_indices(role_id: np.ndarray, role_name: str) -> np.ndarray:
    return np.where(role_id == ROLE_IDS[role_name])[0]


def _stable_standardize(obs: np.ndarray, train_idx: np.ndarray) -> np.ndarray:
    mean = obs[train_idx].mean(axis=0)
    std = obs[train_idx].std(axis=0)
    std[std < 1e-6] = 1.0
    return (obs - mean) / std


def _decode_structured(family_ids: np.ndarray, phases: np.ndarray, family_names: list[str]) -> np.ndarray:
    return np.asarray(
        [
            c1.structured_tail_action(family_names[int(family_id)], int(phase))
            for family_id, phase in zip(family_ids, phases)
        ],
        dtype=np.float32,
    )


def load_dataset(result: dict[str, Any]) -> dict[str, Any]:
    with np.load(DATASET_NPZ, allow_pickle=True) as data:
        arrays = {
            "obs": np.asarray(data["obs"], dtype=np.float32),
            "oracle_actions": np.asarray(data["oracle_actions"], dtype=np.float32),
            "family_id": np.asarray(data["family_id"], dtype=np.int64),
            "tail_phase": np.asarray(data["tail_phase"], dtype=np.int64),
            "role_id": np.asarray(data["role_id"], dtype=np.int64),
            "row_id": np.asarray(data["row_id"], dtype=np.int64),
            "family_names": [str(item) for item in data["family_names"]],
        }
    rows = list(result["dataset"]["per_row"])
    if int(arrays["row_id"].max(initial=-1)) >= len(rows):
        raise ValueError("dataset row_id exceeds M3236 per_row metadata")
    return {"arrays": arrays, "rows": rows}


def role_family_counts(arrays: dict[str, np.ndarray | list[str]]) -> dict[str, dict[str, int]]:
    family_id = np.asarray(arrays["family_id"], dtype=np.int64)
    role_id = np.asarray(arrays["role_id"], dtype=np.int64)
    family_names = list(arrays["family_names"])
    out: dict[str, dict[str, int]] = {
        family: {"train": 0, "selection": 0, "validation": 0}
        for family in family_names
    }
    for family, role in zip(family_id, role_id):
        out[family_names[int(family)]][ROLE_NAMES[int(role)]] += 1
    return out


def frame_majority_predictions(family_id: np.ndarray, role_id: np.ndarray) -> np.ndarray:
    train_idx = _role_indices(role_id, "train")
    counts = Counter(int(family_id[idx]) for idx in train_idx)
    majority = counts.most_common(1)[0][0]
    return np.full_like(family_id, fill_value=majority, dtype=np.int64)


def frame_centroid_predictions(
    obs_z: np.ndarray,
    family_id: np.ndarray,
    role_id: np.ndarray,
    n_families: int,
) -> tuple[np.ndarray, np.ndarray]:
    train_idx = _role_indices(role_id, "train")
    centroids = []
    for family in range(n_families):
        idx = train_idx[family_id[train_idx] == family]
        centroids.append(obs_z[idx].mean(axis=0) if len(idx) else np.zeros((obs_z.shape[1],), dtype=np.float32))
    centroid_arr = np.asarray(centroids, dtype=np.float32)
    distances = np.sum(np.square(obs_z[:, None, :] - centroid_arr[None, :, :]), axis=2)
    return distances.argmin(axis=1).astype(np.int64), distances


def row_features(obs_z: np.ndarray, row_id: np.ndarray, rows: list[dict[str, Any]], mode: str) -> np.ndarray:
    features: list[np.ndarray] = []
    for row_index in range(len(rows)):
        idx = np.where(row_id == row_index)[0]
        if len(idx) == 0:
            raise ValueError(f"row {row_index} has no frames")
        row_obs = obs_z[idx]
        if mode == "mean_z":
            feature = row_obs.mean(axis=0)
        elif mode == "mean_std_first_last_z":
            feature = np.concatenate([row_obs.mean(axis=0), row_obs.std(axis=0), row_obs[0], row_obs[-1]])
        else:
            raise ValueError(f"unknown row feature mode: {mode}")
        features.append(feature.astype(np.float32))
    return np.vstack(features)


def row_labels(arrays: dict[str, np.ndarray | list[str]], rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    family_id = np.asarray(arrays["family_id"], dtype=np.int64)
    role_id = np.asarray(arrays["role_id"], dtype=np.int64)
    row_id = np.asarray(arrays["row_id"], dtype=np.int64)
    row_family = []
    row_role = []
    for row_index in range(len(rows)):
        idx = np.where(row_id == row_index)[0]
        if len(idx) == 0:
            raise ValueError(f"row {row_index} has no frames")
        row_family.append(int(family_id[idx[0]]))
        row_role.append(int(role_id[idx[0]]))
    return np.asarray(row_family, dtype=np.int64), np.asarray(row_role, dtype=np.int64)


def row_centroid_predictions(
    features: np.ndarray,
    row_family: np.ndarray,
    row_role: np.ndarray,
    n_families: int,
) -> tuple[np.ndarray, np.ndarray]:
    train_rows = np.where(row_role == ROLE_IDS["train"])[0]
    centroids = []
    for family in range(n_families):
        idx = train_rows[row_family[train_rows] == family]
        centroids.append(features[idx].mean(axis=0) if len(idx) else np.zeros((features.shape[1],), dtype=np.float32))
    centroid_arr = np.asarray(centroids, dtype=np.float32)
    distances = np.sum(np.square(features[:, None, :] - centroid_arr[None, :, :]), axis=2)
    return distances.argmin(axis=1).astype(np.int64), distances


def row_one_nn_predictions(
    features: np.ndarray,
    row_family: np.ndarray,
    row_role: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_rows = np.where(row_role == ROLE_IDS["train"])[0]
    distances = np.sum(np.square(features[:, None, :] - features[None, :, :]), axis=2)
    nearest_train_rows = np.asarray(
        [train_rows[int(np.argmin(distances[row_index, train_rows]))] for row_index in range(len(row_family))],
        dtype=np.int64,
    )
    predictions = row_family[nearest_train_rows].astype(np.int64)
    return predictions, distances, nearest_train_rows


def frame_predictions_from_rows(row_predictions: np.ndarray, row_id: np.ndarray) -> np.ndarray:
    return np.asarray([row_predictions[int(row_index)] for row_index in row_id], dtype=np.int64)


def _distance_margin(
    distance_row: np.ndarray,
    true_family: int,
    row_family: np.ndarray | None = None,
    train_rows: np.ndarray | None = None,
) -> tuple[float | None, int | None]:
    if row_family is None:
        true_distance = float(distance_row[true_family])
        masked = distance_row.copy()
        masked[true_family] = np.inf
        nearest_wrong = int(np.argmin(masked))
        return float(masked[nearest_wrong] - true_distance), nearest_wrong
    assert train_rows is not None
    true_rows = train_rows[row_family[train_rows] == true_family]
    wrong_rows = train_rows[row_family[train_rows] != true_family]
    if len(true_rows) == 0 or len(wrong_rows) == 0:
        return None, None
    true_distance = float(np.min(distance_row[true_rows]))
    nearest_wrong_row = int(wrong_rows[int(np.argmin(distance_row[wrong_rows]))])
    wrong_distance = float(distance_row[nearest_wrong_row])
    return wrong_distance - true_distance, int(row_family[nearest_wrong_row])


def summarize_selector(
    *,
    name: str,
    kind: str,
    frame_predictions: np.ndarray,
    arrays: dict[str, np.ndarray | list[str]],
    rows: list[dict[str, Any]],
    required_rare_families: list[str],
    row_predictions: np.ndarray | None = None,
    family_distances: np.ndarray | None = None,
    row_distances: np.ndarray | None = None,
    nearest_train_rows: np.ndarray | None = None,
) -> dict[str, Any]:
    family_id = np.asarray(arrays["family_id"], dtype=np.int64)
    role_id = np.asarray(arrays["role_id"], dtype=np.int64)
    row_id = np.asarray(arrays["row_id"], dtype=np.int64)
    phases = np.asarray(arrays["tail_phase"], dtype=np.int64)
    actions = np.asarray(arrays["oracle_actions"], dtype=np.float32)
    family_names = list(arrays["family_names"])
    row_family, row_role = row_labels(arrays, rows)
    role_accuracy = {}
    for role_name in ("train", "selection", "validation"):
        idx = _role_indices(role_id, role_name)
        role_accuracy[role_name] = _round(float(np.mean(frame_predictions[idx] == family_id[idx])) if len(idx) else 0.0)

    validation_idx = _role_indices(role_id, "validation")
    decoded = _decode_structured(frame_predictions[validation_idx], phases[validation_idx], family_names)
    validation_mse = float(np.mean(np.square(decoded - actions[validation_idx]))) if len(validation_idx) else 0.0
    family_metrics: dict[str, dict[str, Any]] = {}
    for family in sorted(set(int(item) for item in family_id[validation_idx])):
        idx = validation_idx[family_id[validation_idx] == family]
        counts = Counter(family_names[int(pred)] for pred in frame_predictions[idx])
        family_metrics[family_names[family]] = {
            "frames": int(len(idx)),
            "accuracy": _round(float(np.mean(frame_predictions[idx] == family_id[idx])) if len(idx) else 0.0),
            "predicted_counts": dict(sorted(counts.items())),
        }

    required: dict[str, dict[str, Any]] = {}
    validation_rows = np.where(row_role == ROLE_IDS["validation"])[0]
    train_rows = np.where(row_role == ROLE_IDS["train"])[0]
    for family in required_rare_families:
        if family not in family_names:
            required[family] = {"frames": 0, "frame_accuracy": None, "missing_from_dataset": True}
            continue
        family_index = family_names.index(family)
        frame_idx = validation_idx[family_id[validation_idx] == family_index]
        row_idx = [
            int(row_index)
            for row_index in validation_rows
            if int(row_family[row_index]) == family_index
        ]
        row_summary: dict[str, Any] = {}
        if row_predictions is not None:
            row_counts = Counter(family_names[int(row_predictions[row_index])] for row_index in row_idx)
            row_summary = {
                "rows": len(row_idx),
                "row_accuracy": _round(
                    float(np.mean([row_predictions[row_index] == row_family[row_index] for row_index in row_idx]))
                    if row_idx
                    else 0.0
                ),
                "row_predicted_counts": dict(sorted(row_counts.items())),
            }
            if nearest_train_rows is not None:
                row_summary["nearest_train_rows"] = [
                    {
                        "validation_row": str(rows[row_index]["row_id"]),
                        "nearest_train_row": str(rows[int(nearest_train_rows[row_index])]["row_id"]),
                        "nearest_train_family": family_names[int(row_family[int(nearest_train_rows[row_index])])],
                    }
                    for row_index in row_idx
                ]
        margins: list[float] = []
        nearest_wrong_counts: Counter[str] = Counter()
        if family_distances is not None:
            for frame in frame_idx:
                margin, nearest_wrong = _distance_margin(family_distances[int(frame)], family_index)
                if margin is not None:
                    margins.append(float(margin))
                if nearest_wrong is not None:
                    nearest_wrong_counts[family_names[int(nearest_wrong)]] += 1
        elif row_distances is not None:
            if kind == "row_1nn":
                for row_index in row_idx:
                    margin, nearest_wrong = _distance_margin(
                        row_distances[row_index],
                        family_index,
                        row_family=row_family,
                        train_rows=train_rows,
                    )
                    if margin is not None:
                        margins.append(float(margin))
                    if nearest_wrong is not None:
                        nearest_wrong_counts[family_names[int(nearest_wrong)]] += 1
            else:
                for row_index in row_idx:
                    margin, nearest_wrong = _distance_margin(row_distances[row_index], family_index)
                    if margin is not None:
                        margins.append(float(margin))
                    if nearest_wrong is not None:
                        nearest_wrong_counts[family_names[int(nearest_wrong)]] += 1
        required[family] = {
            "frames": int(len(frame_idx)),
            "frame_accuracy": _round(float(np.mean(frame_predictions[frame_idx] == family_id[frame_idx])) if len(frame_idx) else 0.0),
            "predicted_counts": dict(
                sorted(Counter(family_names[int(pred)] for pred in frame_predictions[frame_idx]).items())
            ),
            **row_summary,
            "margin_median": _round(float(np.median(margins)) if margins else None),
            "margin_min": _round(float(np.min(margins)) if margins else None),
            "positive_margin_rate": _round(float(np.mean(np.asarray(margins) > 0.0)) if margins else None),
            "nearest_wrong_counts": dict(sorted(nearest_wrong_counts.items())),
        }

    summary = {
        "kind": kind,
        "accuracy_by_role": role_accuracy,
        "validation_predicted_family_reconstruction_mse": _round(validation_mse),
        "validation_family_metrics": family_metrics,
        "required_rare_validation_families": required,
    }
    return {"name": name, **summary}


def add_gate_results(selector: dict[str, Any], floor_accuracy: float, thresholds: dict[str, Any]) -> dict[str, Any]:
    required = selector["required_rare_validation_families"]
    rare_frame_pass = all(
        family_summary.get("frame_accuracy") is not None
        and float(family_summary["frame_accuracy"]) >= float(thresholds["min_required_rare_validation_family_accuracy"])
        for family_summary in required.values()
    )
    rare_row_pass = True
    if selector["kind"].startswith("row"):
        rare_row_pass = all(
            float(family_summary.get("row_accuracy", 0.0)) >= float(thresholds["min_required_rare_row_accuracy"])
            and family_summary.get("margin_min") is not None
            and float(family_summary["margin_min"]) > float(thresholds["min_required_rare_margin"])
            for family_summary in required.values()
        )
    validation_accuracy = float(selector["accuracy_by_role"]["validation"])
    over_floor = validation_accuracy - floor_accuracy
    mse = float(selector["validation_predicted_family_reconstruction_mse"])
    gates = {
        "validation_accuracy_over_floor_gate_passed": over_floor
        >= float(thresholds["min_validation_accuracy_over_majority_floor"]),
        "required_rare_frame_accuracy_gate_passed": rare_frame_pass,
        "required_rare_row_gate_passed": rare_row_pass,
        "predicted_family_reconstruction_gate_passed": mse
        <= float(thresholds["max_predicted_family_validation_reconstruction_mse"]),
    }
    gates["all_passed"] = all(gates.values())
    enriched = dict(selector)
    enriched["validation_accuracy_over_majority_floor"] = _round(over_floor)
    enriched["gates"] = gates
    return enriched


def evaluate_selectors(dataset: dict[str, Any], prereg: dict[str, Any]) -> dict[str, Any]:
    arrays = dataset["arrays"]
    rows = dataset["rows"]
    obs = np.asarray(arrays["obs"], dtype=np.float32)
    family_id = np.asarray(arrays["family_id"], dtype=np.int64)
    role_id = np.asarray(arrays["role_id"], dtype=np.int64)
    row_id = np.asarray(arrays["row_id"], dtype=np.int64)
    family_names = list(arrays["family_names"])
    train_idx = _role_indices(role_id, "train")
    obs_z = _stable_standardize(obs, train_idx)
    row_family, row_role = row_labels(arrays, rows)
    required = list(prereg["required_rare_validation_families"])

    majority_pred = frame_majority_predictions(family_id, role_id)
    majority = summarize_selector(
        name="train_majority_floor",
        kind="frame_floor",
        frame_predictions=majority_pred,
        arrays=arrays,
        rows=rows,
        required_rare_families=required,
    )
    floor_accuracy = float(majority["accuracy_by_role"]["validation"])
    selector_summaries = [
        add_gate_results(majority, floor_accuracy, prereg["thresholds"]),
    ]

    centroid_pred, centroid_distances = frame_centroid_predictions(obs_z, family_id, role_id, len(family_names))
    selector_summaries.append(
        add_gate_results(
            summarize_selector(
                name="frame_centroid_z",
                kind="frame_centroid",
                frame_predictions=centroid_pred,
                arrays=arrays,
                rows=rows,
                required_rare_families=required,
                family_distances=centroid_distances,
            ),
            floor_accuracy,
            prereg["thresholds"],
        )
    )

    mean_features = row_features(obs_z, row_id, rows, mode="mean_z")
    row_centroid_pred, row_centroid_distances = row_centroid_predictions(
        mean_features,
        row_family,
        row_role,
        len(family_names),
    )
    selector_summaries.append(
        add_gate_results(
            summarize_selector(
                name="row_centroid_mean_z",
                kind="row_centroid",
                frame_predictions=frame_predictions_from_rows(row_centroid_pred, row_id),
                arrays=arrays,
                rows=rows,
                required_rare_families=required,
                row_predictions=row_centroid_pred,
                row_distances=row_centroid_distances,
            ),
            floor_accuracy,
            prereg["thresholds"],
        )
    )

    nn_features = row_features(obs_z, row_id, rows, mode="mean_std_first_last_z")
    row_nn_pred, row_nn_distances, nearest_train_rows = row_one_nn_predictions(nn_features, row_family, row_role)
    selector_summaries.append(
        add_gate_results(
            summarize_selector(
                name="row_1nn_mean_std_first_last_z",
                kind="row_1nn",
                frame_predictions=frame_predictions_from_rows(row_nn_pred, row_id),
                arrays=arrays,
                rows=rows,
                required_rare_families=required,
                row_predictions=row_nn_pred,
                row_distances=row_nn_distances,
                nearest_train_rows=nearest_train_rows,
            ),
            floor_accuracy,
            prereg["thresholds"],
        )
    )
    best_by_mse = min(
        selector_summaries,
        key=lambda selector: (
            float(selector["validation_predicted_family_reconstruction_mse"]),
            -float(selector["accuracy_by_role"]["validation"]),
        ),
    )
    best_by_accuracy = max(
        selector_summaries,
        key=lambda selector: (
            float(selector["accuracy_by_role"]["validation"]),
            -float(selector["validation_predicted_family_reconstruction_mse"]),
        ),
    )
    admissible = [selector for selector in selector_summaries if selector["gates"]["all_passed"]]
    return {
        "dataset": {
            "artifact": _path_text(DATASET_NPZ),
            "frames": int(len(family_id)),
            "rows": int(len(rows)),
            "role_frame_counts": {
                role_name: int(len(_role_indices(role_id, role_name)))
                for role_name in ("train", "selection", "validation")
            },
            "role_row_counts": {
                role_name: int(np.sum(row_role == role_index))
                for role_index, role_name in ROLE_NAMES.items()
            },
            "tail_frames_by_family_role": role_family_counts(arrays),
        },
        "selectors": {selector["name"]: selector for selector in selector_summaries},
        "floor": {
            "name": "train_majority_floor",
            "validation_accuracy": _round(floor_accuracy),
        },
        "best_by_validation_mse": {
            "name": best_by_mse["name"],
            "validation_accuracy": best_by_mse["accuracy_by_role"]["validation"],
            "validation_predicted_family_reconstruction_mse": best_by_mse[
                "validation_predicted_family_reconstruction_mse"
            ],
            "gates": best_by_mse["gates"],
            "required_rare_validation_families": best_by_mse["required_rare_validation_families"],
        },
        "best_by_validation_accuracy": {
            "name": best_by_accuracy["name"],
            "validation_accuracy": best_by_accuracy["accuracy_by_role"]["validation"],
            "validation_predicted_family_reconstruction_mse": best_by_accuracy[
                "validation_predicted_family_reconstruction_mse"
            ],
            "gates": best_by_accuracy["gates"],
            "required_rare_validation_families": best_by_accuracy["required_rare_validation_families"],
        },
        "admissible_selectors": [selector["name"] for selector in admissible],
    }


def synthesize_decision(prereg: dict[str, Any], m3237: dict[str, Any], evaluated: dict[str, Any]) -> dict[str, Any]:
    upstream = m3237["decision"]
    target_still_priced = bool(upstream["target_still_priced"])
    representation_alive = bool(upstream["representation_alive_if_family_known"])
    admissible_selectors = list(evaluated["admissible_selectors"])
    best_mse = evaluated["best_by_validation_mse"]
    negative = target_still_priced and representation_alive and not admissible_selectors
    if admissible_selectors:
        synthesis_decision = "admit_family_selector_training_design"
        c1_status = "open"
        next_branch = "c5prime_track_c_c1_family_selector_training_design"
        recommended_next = (
            "Register a separate selector-training design/quick milestone. C2 remains blocked "
            "until a C1 warm-start/control gate passes."
        )
        next_process_admitted = True
    elif negative:
        synthesis_decision = "family_selector_repricing_negative"
        c1_status = "blocked_pending_pi_or_new_interface_pricing"
        next_branch = "c5prime_track_c_c1_pause_pending_pi_or_nonlocal_interface_reprice"
        recommended_next = (
            "Do not run more local tail-family selector training. Escalate C1 for a PI/new-interface "
            "decision, or move to the next independent roadmap pricing unit if C1 is treated as paused."
        )
        next_process_admitted = False
    else:
        synthesis_decision = "stop_track_c_pending_target_or_representation_reprice"
        c1_status = "blocked_pending_target_or_representation_reprice"
        next_branch = "c5prime_track_c_target_or_interface_reprice"
        recommended_next = "Re-price the C5-prime target or the structured representation before any C1 work."
        next_process_admitted = False

    return {
        "synthesis_decision": synthesis_decision,
        "closed_branch": "c5prime_track_c_c1_family_selector_repricing" if negative else None,
        "next_branch": next_branch,
        "c1_status": c1_status,
        "c2_admitted": False,
        "c3_admitted": False,
        "target_still_priced": target_still_priced,
        "representation_alive_if_family_known": representation_alive,
        "selector_route_priced": bool(admissible_selectors),
        "admissible_selectors": admissible_selectors,
        "best_selector_by_validation_mse": best_mse["name"],
        "best_selector_validation_mse": best_mse["validation_predicted_family_reconstruction_mse"],
        "best_selector_validation_accuracy": best_mse["validation_accuracy"],
        "best_selector_gates": best_mse["gates"],
        "required_rare_failure_preserved": not bool(best_mse["gates"]["required_rare_frame_accuracy_gate_passed"]),
        "next_process_admitted": next_process_admitted,
        "next_training_admitted": False,
        "controlled_rollout_design_admitted": False,
        "more_local_interface_pretraining_admitted": False,
        "recommended_next": recommended_next,
        "reason": (
            "The target and representation remain alive, but the deterministic selector battery "
            "does not clear the frozen rare-family and reconstruction gates. The strongest simple "
            "row-level selector still maps the required structured:coast_steer_-0.7 validation row "
            "to structured:brake_steer_-1.0, preserving the M3236 failure mode."
            if negative
            else "Selector repricing did not hit the negative route."
        ),
    }


def run() -> dict[str, Any]:
    t0 = time.time()
    prereg = read_json(PREREG_JSON)
    for artifact in prereg["source_artifacts"].values():
        artifact_path = REPO / artifact if not Path(artifact).is_absolute() else Path(artifact)
        if not artifact_path.exists():
            raise FileNotFoundError(artifact_path)
    if not DATASET_NPZ.exists():
        raise FileNotFoundError(DATASET_NPZ)
    m3236 = read_json(M3236_JSON)
    m3237 = read_json(M3237_JSON)
    dataset = load_dataset(m3236)
    evaluated = evaluate_selectors(dataset, prereg)
    decision = synthesize_decision(prereg, m3237, evaluated)
    payload = {
        "protocol": "c5prime_c1_family_selector_repricing",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_family_selector_repricing.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": _path_text(PREREG_JSON),
        "source_artifacts": prereg["source_artifacts"],
        "measured": {
            "dataset": evaluated["dataset"],
            "selector_floor": evaluated["floor"],
            "selectors": evaluated["selectors"],
            "best_by_validation_mse": evaluated["best_by_validation_mse"],
            "best_by_validation_accuracy": evaluated["best_by_validation_accuracy"],
            "admissible_selectors": evaluated["admissible_selectors"],
            "upstream_m3237_decision": {
                "target_still_priced": bool(m3237["decision"]["target_still_priced"]),
                "representation_alive_if_family_known": bool(
                    m3237["decision"]["representation_alive_if_family_known"]
                ),
                "local_framewise_pretraining_closed": bool(
                    m3237["decision"]["local_framewise_pretraining_closed"]
                ),
            },
        },
        "inferred": {
            "selector_vs_representation": (
                "The structured decoder remains exact if the family is known. M3238 prices only "
                "whether the current local observation interface contains enough separability to "
                "select the required family before another training attempt."
            ),
            "rare_family_interpretation": (
                "The negative result is a route decision for this local selector interface, not a "
                "claim that the C5-prime structural ceiling target is absent."
            ),
        },
        "decision": decision,
        "elapsed_s": _round(time.time() - t0, digits=3),
    }
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    print(
        "c5prime_c1_family_selector_repricing "
        f"decision={payload['decision']['synthesis_decision']} "
        f"best_selector={payload['decision']['best_selector_by_validation_mse']} "
        f"best_mse={payload['decision']['best_selector_validation_mse']}"
    )


if __name__ == "__main__":
    main()
