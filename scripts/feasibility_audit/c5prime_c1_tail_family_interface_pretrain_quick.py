"""Quick supervised pretrain smoke for the C1 tail-family interface.

This is the first pretraining check admitted by M3235. It uses the frozen v2
C1 structured-oracle rows, adds deterministic rare-tail train support where
the quick target split was under-supported, trains a small tail-family
classifier on tail frames only, and evaluates whether predicted tail families
can reconstruct validation tail actions through the frozen structured decoder.

It does not run PPO, does not mutate the incumbent, does not rank a driver,
and does not admit C2.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

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
    / "c5prime_c1_tail_family_interface_pretrain_quick_prereg.json"
)
OUTPUT_JSON = (
    REPO
    / "experiments"
    / "feasibility_audit"
    / "c5prime_c1_tail_family_interface_pretrain_quick.json"
)
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_tail_family_interface_pretrain_quick" / "quick"
DATASET_NPZ = RUN_DIR / "interface_pretrain_dataset.npz"
CHECKPOINT_PT = RUN_DIR / "interface_head.pt"
M3235_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_smoke.json"

SEED = 20260913
OBS_DIM = 72
HIDDEN = 64

CLAIM_BOUNDARY = (
    "M3236 C1 tail-family interface pretrain quick only: supervised "
    "tail-family classifier training over frozen structured-oracle tail frames. "
    "No PPO, no guarded RL, no incumbent mutation, no driver-performance claim, "
    "no validation ranking, no promotion, no high-fidelity sufficiency claim, "
    "no C2 admission, and no self-ID claim."
)


class TailFamilyNet(nn.Module):
    def __init__(self, obs_dim: int, hidden: int, num_families: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, num_families),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs)


def _round(value: float | int | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _path_text(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _role_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row["bc_role"]) for row in rows)
    return {role: int(counts.get(role, 0)) for role in ("train", "selection", "validation")}


def build_pretrain_rows(prereg: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the frozen M3236 row split with extra rare-tail train support."""

    thresholds = prereg["thresholds"]
    rows = list(c1._rows_for_mode(c1.load_preregistration(revision=c1.REVISION_V2), quick=False))
    selected_ids = {str(row["row_id"]) for row in rows}
    eligible = c1._eligible_rows()
    required_families = set(prereg["required_rare_validation_families"])
    min_train_rows = int(thresholds["min_train_rows_per_required_rare_family"])

    def train_count(family: str) -> int:
        return sum(row["bc_role"] == "train" and row["oracle_by"] == family for row in rows)

    for family in sorted(required_families):
        while train_count(family) < min_train_rows:
            candidates = [
                row
                for row in eligible
                if row["oracle_by"] == family and c1._source_row_id(row) not in selected_ids
            ]
            if not candidates:
                break
            candidates.sort(
                key=lambda row: (
                    c1._stable_hash(SEED, "m3236-extra-train", family, row["level"], row["instance"], row["eval_seed"]),
                    row["level"],
                    int(row["instance"]),
                    int(row["eval_seed"]),
                )
            )
            chosen = candidates[0]
            rows.append(
                c1._selected_record(
                    chosen,
                    role="train",
                    selection_source="m3236_extra_rare_tail_train_support",
                )
            )
            selected_ids.add(c1._source_row_id(chosen))
    return rows


def replay_and_encode(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_rows = c1._source_row_by_id()
    fixed_cfg = c1._fixed_star_cfg()
    families = sorted({str(row["oracle_by"]) for row in rows})
    family_to_id = {family: idx for idx, family in enumerate(families)}
    role_to_id = {"train": 0, "selection": 1, "validation": 2}

    obs_parts: list[np.ndarray] = []
    action_parts: list[np.ndarray] = []
    family_parts: list[np.ndarray] = []
    phase_parts: list[np.ndarray] = []
    role_parts: list[np.ndarray] = []
    row_id_parts: list[np.ndarray] = []
    demo_outcomes: dict[str, Any] = {}
    per_row: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        demo = c1.rollout_oracle_demo(source_rows[row["row_id"]], row, fixed_cfg)
        demo_outcomes[str(row["row_id"])] = {
            "role": demo["role"],
            "oracle_by": demo["oracle_by"],
            "outcome_bucket": demo["outcome_bucket"],
            "steps": int(demo["steps"]),
        }
        obs = np.asarray(demo["obs"], dtype=np.float32)
        actions = np.asarray(demo["actions"], dtype=np.float32)
        reveal_step = int(row["reveal_step"])
        tail_obs = obs[reveal_step:]
        tail_actions = actions[reveal_step:]
        phases = np.arange(len(tail_actions), dtype=np.int16)
        family_id = family_to_id[str(row["oracle_by"])]
        decoded = np.asarray(
            [c1.structured_tail_action(str(row["oracle_by"]), int(phase)) for phase in phases],
            dtype=np.float32,
        )
        error = decoded - tail_actions
        per_row.append(
            {
                "row_id": row["row_id"],
                "role": row["bc_role"],
                "oracle_by": row["oracle_by"],
                "selection_source": row.get("selection_source", ""),
                "steps": int(len(actions)),
                "reveal_step": reveal_step,
                "tail_frames": int(len(tail_actions)),
                "tail_reconstruction_mse": _round(float(np.mean(np.square(error))) if len(error) else 0.0, 12),
                "tail_max_abs_error": _round(float(np.max(np.abs(error))) if len(error) else 0.0, 12),
            }
        )
        obs_parts.append(tail_obs)
        action_parts.append(tail_actions)
        family_parts.append(np.full((len(tail_actions),), family_id, dtype=np.int16))
        phase_parts.append(phases)
        role_parts.append(np.full((len(tail_actions),), role_to_id[str(row["bc_role"])], dtype=np.int8))
        row_id_parts.append(np.full((len(tail_actions),), row_index, dtype=np.int16))

    obs_all = np.concatenate(obs_parts, axis=0)
    actions_all = np.concatenate(action_parts, axis=0)
    family_all = np.concatenate(family_parts, axis=0)
    phase_all = np.concatenate(phase_parts, axis=0)
    role_all = np.concatenate(role_parts, axis=0)
    row_id_all = np.concatenate(row_id_parts, axis=0)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        DATASET_NPZ,
        obs=obs_all.astype(np.float32),
        oracle_actions=actions_all.astype(np.float32),
        family_id=family_all.astype(np.int16),
        tail_phase=phase_all.astype(np.int16),
        role_id=role_all.astype(np.int8),
        row_id=row_id_all.astype(np.int16),
        family_names=np.asarray(families),
    )
    return {
        "families": families,
        "dataset": {
            "artifact": _path_text(DATASET_NPZ),
            "frames": int(len(obs_all)),
            "tail_frames_by_role": {
                role: int(np.sum(role_all == role_id))
                for role, role_id in role_to_id.items()
            },
            "tail_frames_by_family_role": _family_role_counts(family_all, role_all, families),
            "per_row": per_row,
        },
        "arrays": {
            "obs": obs_all.astype(np.float32),
            "actions": actions_all.astype(np.float32),
            "family_id": family_all.astype(np.int64),
            "tail_phase": phase_all.astype(np.int64),
            "role_id": role_all.astype(np.int64),
        },
        "demo_outcomes": demo_outcomes,
    }


def _family_role_counts(family_ids: np.ndarray, role_ids: np.ndarray, family_names: list[str]) -> dict[str, dict[str, int]]:
    role_names = {0: "train", 1: "selection", 2: "validation"}
    out: dict[str, dict[str, int]] = {
        family: {"train": 0, "selection": 0, "validation": 0}
        for family in family_names
    }
    for family_id, role_id in zip(family_ids, role_ids):
        out[family_names[int(family_id)]][role_names[int(role_id)]] += 1
    return out


def _centroid_predictions(obs: np.ndarray, family_id: np.ndarray, train_idx: np.ndarray, eval_idx: np.ndarray, n: int) -> np.ndarray:
    centroids = []
    for family in range(n):
        idx = train_idx[family_id[train_idx] == family]
        if len(idx) == 0:
            centroids.append(np.zeros((obs.shape[1],), dtype=np.float32))
        else:
            centroids.append(obs[idx].mean(axis=0))
    centroid_arr = np.asarray(centroids, dtype=np.float32)
    distances = np.sum(np.square(obs[eval_idx, None, :] - centroid_arr[None, :, :]), axis=2)
    return distances.argmin(axis=1)


def _accuracy(pred: np.ndarray, target: np.ndarray) -> float:
    if len(target) == 0:
        return 0.0
    return float(np.mean(pred == target))


def train_interface_head(arrays: dict[str, np.ndarray], families: list[str], prereg: dict[str, Any]) -> dict[str, Any]:
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    obs = arrays["obs"]
    family_id = arrays["family_id"]
    role_id = arrays["role_id"]
    train_idx = np.where(role_id == 0)[0]
    selection_idx = np.where(role_id == 1)[0]
    validation_idx = np.where(role_id == 2)[0]
    n_families = len(families)

    train_counts = np.bincount(family_id[train_idx], minlength=n_families)
    class_weights = np.sqrt(max(float(train_counts.max()), 1.0) / np.maximum(train_counts, 1))
    x = torch.as_tensor(obs, dtype=torch.float32)
    y = torch.as_tensor(family_id, dtype=torch.long)
    weights = torch.as_tensor(class_weights, dtype=torch.float32)
    model = TailFamilyNet(OBS_DIM, HIDDEN, n_families)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(prereg["training"]["lr"]), weight_decay=float(prereg["training"]["weight_decay"]))
    rng = np.random.default_rng(SEED)
    best: dict[str, Any] = {
        "selection_accuracy": -1.0,
        "selection_cross_entropy": float("inf"),
        "epoch": 0,
        "state": {key: value.detach().clone() for key, value in model.state_dict().items()},
    }
    history: list[dict[str, Any]] = []
    batch_size = int(prereg["training"]["batch_size"])
    epochs = int(prereg["training"]["epochs"])
    eval_every = int(prereg["training"]["eval_every"])
    for epoch in range(1, epochs + 1):
        perm = rng.permutation(train_idx)
        model.train()
        for start in range(0, len(perm), batch_size):
            idx = torch.as_tensor(perm[start : start + batch_size], dtype=torch.long)
            logits = model(x[idx])
            loss = F.cross_entropy(logits, y[idx], weight=weights)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if epoch % eval_every == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                selection_logits = model(x[selection_idx])
                selection_ce = float(F.cross_entropy(selection_logits, y[selection_idx]).item())
                selection_pred = selection_logits.argmax(dim=1)
                selection_acc = float((selection_pred == y[selection_idx]).float().mean().item())
                train_logits = model(x[train_idx])
                train_acc = float((train_logits.argmax(dim=1) == y[train_idx]).float().mean().item())
            history.append(
                {
                    "epoch": epoch,
                    "train_accuracy": _round(train_acc),
                    "selection_accuracy": _round(selection_acc),
                    "selection_cross_entropy": _round(selection_ce),
                }
            )
            if (selection_acc, -selection_ce, -epoch) > (
                float(best["selection_accuracy"]),
                -float(best["selection_cross_entropy"]),
                -int(best["epoch"]),
            ):
                best = {
                    "selection_accuracy": selection_acc,
                    "selection_cross_entropy": selection_ce,
                    "epoch": epoch,
                    "state": {key: value.detach().clone() for key, value in model.state_dict().items()},
                }
    model.load_state_dict(best["state"])
    model.eval()
    with torch.no_grad():
        logits = model(x)
        pred = logits.argmax(dim=1).cpu().numpy().astype(np.int64)
        ce_by_role = {
            role: float(F.cross_entropy(logits[role_id == role_id_value], y[role_id == role_id_value]).item())
            for role, role_id_value in {"train": 0, "selection": 1, "validation": 2}.items()
        }
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "model_config": {"obs_dim": OBS_DIM, "hidden": HIDDEN, "num_families": n_families},
            "family_names": families,
            "preregistration": _path_text(PREREG_JSON),
            "claim_boundary": CLAIM_BOUNDARY,
            "checkpoint_type": "tail_family_interface_head_not_policy",
        },
        CHECKPOINT_PT,
    )
    return {
        "checkpoint": _path_text(CHECKPOINT_PT),
        "history": history,
        "best_epoch": int(best["epoch"]),
        "class_weights": {families[idx]: _round(value) for idx, value in enumerate(class_weights)},
        "predictions": pred,
        "cross_entropy_by_role": {role: _round(value) for role, value in ce_by_role.items()},
    }


def compute_metrics(arrays: dict[str, np.ndarray], families: list[str], predictions: np.ndarray) -> dict[str, Any]:
    obs = arrays["obs"]
    family_id = arrays["family_id"]
    role_id = arrays["role_id"]
    phases = arrays["tail_phase"]
    actions = arrays["actions"]
    train_idx = np.where(role_id == 0)[0]
    selection_idx = np.where(role_id == 1)[0]
    validation_idx = np.where(role_id == 2)[0]
    majority = Counter(family_id[train_idx].tolist()).most_common(1)[0][0]
    centroid_selection = _centroid_predictions(obs, family_id, train_idx, selection_idx, len(families))
    centroid_validation = _centroid_predictions(obs, family_id, train_idx, validation_idx, len(families))

    def family_metrics(idx: np.ndarray) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for family_index, family in enumerate(families):
            mask = idx[family_id[idx] == family_index]
            if len(mask) == 0:
                continue
            out[family] = {
                "frames": int(len(mask)),
                "accuracy": _round(_accuracy(predictions[mask], family_id[mask])),
                "predicted_counts": {
                    families[int(predicted)]: int(np.sum(predictions[mask] == predicted))
                    for predicted in sorted(set(predictions[mask].tolist()))
                },
            }
        return out

    validation_pred_actions = np.asarray(
        [
            c1.structured_tail_action(families[int(pred)], int(phase))
            for pred, phase in zip(predictions[validation_idx], phases[validation_idx])
        ],
        dtype=np.float32,
    )
    true_pred_actions = np.asarray(
        [
            c1.structured_tail_action(families[int(target)], int(phase))
            for target, phase in zip(family_id[validation_idx], phases[validation_idx])
        ],
        dtype=np.float32,
    )
    reconstruction_error = validation_pred_actions - actions[validation_idx]
    true_error = true_pred_actions - actions[validation_idx]
    return {
        "accuracy_by_role": {
            "train": _round(_accuracy(predictions[train_idx], family_id[train_idx])),
            "selection": _round(_accuracy(predictions[selection_idx], family_id[selection_idx])),
            "validation": _round(_accuracy(predictions[validation_idx], family_id[validation_idx])),
        },
        "floors": {
            "train_majority_family": families[int(majority)],
            "selection_train_majority_accuracy": _round(_accuracy(np.full_like(family_id[selection_idx], majority), family_id[selection_idx])),
            "validation_train_majority_accuracy": _round(_accuracy(np.full_like(family_id[validation_idx], majority), family_id[validation_idx])),
            "selection_centroid_accuracy": _round(_accuracy(centroid_selection, family_id[selection_idx])),
            "validation_centroid_accuracy": _round(_accuracy(centroid_validation, family_id[validation_idx])),
        },
        "selection_family_metrics": family_metrics(selection_idx),
        "validation_family_metrics": family_metrics(validation_idx),
        "validation_predicted_family_reconstruction_mse": _round(float(np.mean(np.square(reconstruction_error))), 6),
        "validation_true_family_reconstruction_mse": _round(float(np.mean(np.square(true_error))), 12),
    }


def evaluate_gates(prereg: dict[str, Any], rows: list[dict[str, Any]], encoded: dict[str, Any], metrics: dict[str, Any]) -> dict[str, bool]:
    thresholds = prereg["thresholds"]
    role_counts = _role_counts(rows)
    train_families = {str(row["oracle_by"]) for row in rows if row["bc_role"] == "train"}
    heldout_families = {str(row["oracle_by"]) for row in rows if row["bc_role"] in {"selection", "validation"}}
    validation_family_acc = [
        float(item["accuracy"])
        for item in metrics["validation_family_metrics"].values()
        if item["frames"] >= int(thresholds["min_validation_frames_per_family"])
    ]
    required_rare_acc = [
        float(metrics["validation_family_metrics"].get(family, {}).get("accuracy", 0.0))
        for family in prereg["required_rare_validation_families"]
    ]
    validation_floor = max(
        float(metrics["floors"]["validation_train_majority_accuracy"]),
        float(metrics["floors"]["validation_centroid_accuracy"]),
    )
    gates = {
        "m3235_interface_smoke_passed": bool(read_json(M3235_JSON)["gates"]["all_passed"]),
        "role_split_present": all(role_counts[role] > 0 for role in ("train", "selection", "validation")),
        "heldout_family_train_coverage_passed": heldout_families <= train_families,
        "required_rare_train_support_passed": all(
            sum(row["bc_role"] == "train" and row["oracle_by"] == family for row in rows)
            >= int(thresholds["min_train_rows_per_required_rare_family"])
            for family in prereg["required_rare_validation_families"]
        ),
        "demo_replay_all_success": all(
            outcome["outcome_bucket"] == "success_obstacle_pass"
            for outcome in encoded["demo_outcomes"].values()
        ),
        "dataset_exists": DATASET_NPZ.exists(),
        "interface_checkpoint_exists": CHECKPOINT_PT.exists(),
        "selection_accuracy_gate_passed": (
            float(metrics["accuracy_by_role"]["selection"]) >= float(thresholds["min_selection_family_accuracy"])
        ),
        "validation_accuracy_gate_passed": (
            float(metrics["accuracy_by_role"]["validation"]) >= max(
                float(thresholds["min_validation_family_accuracy"]),
                validation_floor + float(thresholds["min_validation_accuracy_over_best_floor"]),
            )
        ),
        "validation_family_min_gate_passed": (
            bool(validation_family_acc)
            and min(validation_family_acc) >= float(thresholds["min_per_validation_family_accuracy"])
        ),
        "required_rare_validation_family_gate_passed": (
            bool(required_rare_acc)
            and min(required_rare_acc) >= float(thresholds["min_required_rare_validation_family_accuracy"])
        ),
        "predicted_family_reconstruction_gate_passed": (
            float(metrics["validation_predicted_family_reconstruction_mse"])
            <= float(thresholds["max_validation_predicted_family_reconstruction_mse"])
        ),
        "true_family_reconstruction_gate_passed": (
            float(metrics["validation_true_family_reconstruction_mse"])
            <= float(thresholds["max_validation_true_family_reconstruction_mse"])
        ),
    }
    gates["all_passed"] = all(gates.values())
    return gates


def run() -> dict[str, Any]:
    t0 = time.time()
    prereg = read_json(PREREG_JSON)
    rows = build_pretrain_rows(prereg)
    encoded = replay_and_encode(rows)
    training = train_interface_head(encoded["arrays"], encoded["families"], prereg)
    metrics = compute_metrics(encoded["arrays"], encoded["families"], training["predictions"])
    gates = evaluate_gates(prereg, rows, encoded, metrics)
    decision = {
        "c1_status": "open",
        "c2_admitted": False,
        "c3_admitted": False,
        "quick_pretrain_passed": bool(gates["all_passed"]),
        "next_training_admitted": False,
        "next_branch": (
            "c5prime_track_c_c1_tail_family_interface_controlled_rollout_design"
            if gates["all_passed"]
            else "c5prime_track_c_c1_tail_family_interface_reprice"
        ),
        "recommended_next": (
            "Register a separate controlled rollout design/quick milestone; do not admit C2."
            if gates["all_passed"]
            else "Do not continue local interface pretraining; synthesize/reprice the tail-family interface after the rare-family gate failure."
        ),
    }
    payload = {
        "protocol": "c5prime_c1_tail_family_interface_pretrain_quick",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": _path_text(PREREG_JSON),
        "source_artifacts": prereg["source_artifacts"],
        "row_split": {
            "rows": [
                {
                    "row_id": row["row_id"],
                    "role": row["bc_role"],
                    "oracle_by": row["oracle_by"],
                    "selection_source": row.get("selection_source", ""),
                    "reveal_step": int(row["reveal_step"]),
                }
                for row in rows
            ],
            "role_counts": _role_counts(rows),
        },
        "dataset": encoded["dataset"],
        "demo_outcomes": encoded["demo_outcomes"],
        "training": {
            "seed": SEED,
            "model": {"obs_dim": OBS_DIM, "hidden": HIDDEN, "num_families": len(encoded["families"])},
            "checkpoint": training["checkpoint"],
            "best_epoch": training["best_epoch"],
            "class_weights": training["class_weights"],
            "cross_entropy_by_role": training["cross_entropy_by_role"],
            "history": training["history"],
        },
        "metrics": metrics,
        "gates": gates,
        "decision": decision,
        "elapsed_s": _round(time.time() - t0, 3),
    }
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    print(
        f"wrote {_path_text(OUTPUT_JSON)} all_passed={payload['gates']['all_passed']} "
        f"val_acc={payload['metrics']['accuracy_by_role']['validation']} "
        f"val_recon_mse={payload['metrics']['validation_predicted_family_reconstruction_mse']}"
    )
    if not payload["gates"]["all_passed"]:
        raise SystemExit("M3236 tail-family interface pretrain quick gate failed")


if __name__ == "__main__":
    main()
