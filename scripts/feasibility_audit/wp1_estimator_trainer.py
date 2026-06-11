"""WP1 stage-1 estimator trainer (Phase-2 plan WP1.2/WP1.3 infrastructure):
capacity/compute-matched supervised mu estimators on the wp1_data_pipeline
datasets, plus the belief-injection substitution smoke.

Plan anchors: docs/research-plan-phase2-capability-boundary-tracking.md WP1.2
(arms L0 current-frame / L2_window_25/50/100 / L3_GRU + reset-eval control;
capacity matching counts NON-INPUT-PROJECTION parameters only; window arms
use a shared per-frame encoder (72->h) + temporal pooling so the matched
quantity is encoder+head; compute-matched = same epochs x same samples;
per-arm LR/epoch mini-grid selected on selection-split episodes only;
held-out mu points off the 12-point grid in evaluation) and WP1.3 (the
estimator's decision-tick output replaces mu in the SAME scripted seeker via
the RampPolicyController injected-belief hook).

Capacity rule, applied (non-input-projection parameter counts):
  L0 / L2_window_*  hidden h=56: body h*h + biases + head = h^2+3h+1 = 3305
  L3_GRU            hidden h=32: W_hh 3h^2 + b_ih/b_hh 6h + head h+1 = 3297
  (input projections excluded: Linear(72->h).weight, GRU weight_ih_l0;
   max relative spread asserted <= 10%.)

Arms are EXPLORATORY at this stage; the pre-registered primary arm for the
full run is L3_GRU per the plan. The stage-1 smoke makes no measurement
claim: it validates that the chain (dataset -> 5 arms x 1 seed -> injection
-> 1 cell x 12 episodes) runs end to end and reports raw numbers.

Seed streams: training seeds torch.manual_seed(20270101 + 1000*arm_index +
17*train_seed); injection-smoke episodes use the data pipeline's
"smoke_eval" role offset (+800000), disjoint from train/sel/val streams and
from all 20260611..20260625-based streams
(experiments/feasibility_audit/wp1_seed_streams.json).

Run:
    PYTHONPATH=src python scripts/feasibility_audit/wp1_estimator_trainer.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/wp1_estimator_trainer.py --full
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_DIR = REPO / "runs/feasibility_audit/wp1_dataset"
DEFAULT_RUN_DIR = REPO / "runs/feasibility_audit/wp1_estimator"

SEED_BASE = 20270101
OBS_DIM = 72
H_FRAME = 56  # L0 + window arms
H_GRU = 32
WINDOWS = (25, 50, 100)
RESET_WINDOW = 25  # L3 reset-eval control: state truncated to the last 25 frames
CAPACITY_TOLERANCE = 0.10
ARMS = ("L0_frame", "L2_window_25", "L2_window_50", "L2_window_100", "L3_GRU")

CLAIM_BOUNDARY = (
    "Feasibility-audit WP1 estimator-training infrastructure only (Phase-2 manual takeover): "
    "capacity/compute-matched supervised mu estimators are trained on wp1_data_pipeline "
    "rollouts and smoke-tested through the RampPolicyController injected-belief hook. "
    "Stage-1 smoke numbers are infrastructure validation, not pre-registered measurements. "
    "No driver promotion, repair-success, gate-validity, paper, high-fidelity, "
    "robustness-result, feasibility-proof, or self-ID capability claim."
)


# ------------------------------------------------------------------ estimators


class L0Net(nn.Module):
    def __init__(self, h: int = H_FRAME):
        super().__init__()
        self.in_proj = nn.Linear(OBS_DIM, h)
        self.body = nn.Linear(h, h)
        self.head = nn.Linear(h, 1)

    def forward(self, frame: torch.Tensor) -> torch.Tensor:  # [B, 72]
        z = torch.relu(self.in_proj(frame))
        z = torch.relu(self.body(z))
        return self.head(z).squeeze(-1)


class WindowNet(nn.Module):
    """Shared per-frame encoder (72->h) + masked temporal mean pooling + head."""

    def __init__(self, window: int, h: int = H_FRAME):
        super().__init__()
        self.window = int(window)
        self.in_proj = nn.Linear(OBS_DIM, h)
        self.body = nn.Linear(h, h)
        self.head = nn.Linear(h, 1)

    def forward(self, frames: torch.Tensor) -> torch.Tensor:  # [B, W, 72]
        z = torch.relu(self.in_proj(frames))  # [B, W, h]
        z = z.mean(dim=1)
        z = torch.relu(self.body(z))
        return self.head(z).squeeze(-1)


class GRUNet(nn.Module):
    def __init__(self, h: int = H_GRU):
        super().__init__()
        self.gru = nn.GRU(OBS_DIM, h, batch_first=True)
        self.head = nn.Linear(h, 1)

    def forward(self, frames: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(frames)  # [B, T, h]
        idx = (lengths - 1).clamp(min=0).view(-1, 1, 1).expand(-1, 1, out.size(-1))
        last = out.gather(1, idx).squeeze(1)
        return self.head(last).squeeze(-1)

    def forward_step(self, frame: torch.Tensor, hidden: torch.Tensor | None):
        out, hidden = self.gru(frame.view(1, 1, -1), hidden)
        return self.head(out[:, -1]).squeeze(), hidden


def build_arm(arm: str) -> nn.Module:
    if arm == "L0_frame":
        return L0Net()
    if arm.startswith("L2_window_"):
        return WindowNet(int(arm.rsplit("_", 1)[1]))
    if arm == "L3_GRU":
        return GRUNet()
    raise ValueError(arm)


def param_counts(model: nn.Module) -> dict[str, int]:
    """total / input-projection / non-input-projection parameter counts.

    Input projection = the weight matrices that multiply the raw 72-dim frame
    (Linear(72->h).weight; GRU weight_ih_l0). Everything else (biases,
    recurrent/body weights, head) is the matched capacity quantity.
    """
    input_proj = 0
    total = 0
    for name, p in model.named_parameters():
        total += p.numel()
        if name in ("in_proj.weight", "gru.weight_ih_l0"):
            input_proj += p.numel()
    return {"total": total, "input_projection": input_proj,
            "non_input_projection": total - input_proj}


def assert_capacity_matched(report: dict[str, dict[str, int]]) -> float:
    counts = [v["non_input_projection"] for v in report.values()]
    spread = (max(counts) - min(counts)) / max(min(counts), 1)
    assert spread <= CAPACITY_TOLERANCE, f"capacity mismatch {report}"
    return spread


# --------------------------------------------------------------------- dataset


def load_dataset(dataset_dir: Path, cell_ids: list[str]) -> dict[str, dict[str, np.ndarray]]:
    out = {}
    for cid in cell_ids:
        with np.load(dataset_dir / f"{cid}.npz") as z:
            out[cid] = {k: z[k] for k in z.files}
    return out


def episode_tensors(data: dict[str, np.ndarray], idx: np.ndarray):
    """sequences up to the decision tick (inclusive) + labels."""
    dt = data["decision_tick"][idx]
    lengths = dt + 1
    t_max = int(lengths.max())
    seqs = np.zeros((len(idx), t_max, OBS_DIM), dtype=np.float32)
    for j, (i, ln) in enumerate(zip(idx, lengths)):
        seqs[j, :ln] = data["obs"][i, :ln]
    return (torch.tensor(seqs), torch.tensor(lengths.astype(np.int64)),
            torch.tensor(data["mu"][idx].astype(np.float32)))


def arm_inputs(arm: str, seqs: torch.Tensor, lengths: torch.Tensor):
    if arm == "L0_frame":
        idx = (lengths - 1).view(-1, 1, 1).expand(-1, 1, seqs.size(-1))
        return (seqs.gather(1, idx).squeeze(1),)
    if arm.startswith("L2_window_"):
        w = int(arm.rsplit("_", 1)[1])
        out = torch.zeros(seqs.size(0), w, seqs.size(-1))
        for j in range(seqs.size(0)):
            ln = int(lengths[j])
            if ln >= w:
                out[j] = seqs[j, ln - w:ln]
            else:  # left-pad with the first frame (sequences are >= prefix length in practice)
                out[j, : w - ln] = seqs[j, 0]
                out[j, w - ln:] = seqs[j, :ln]
        return (out,)
    return (seqs, lengths)


def metrics(pred: np.ndarray, y: np.ndarray) -> dict[str, float]:
    err = pred - y
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {"mae": round(float(np.mean(np.abs(err))), 4),
            "rmse": round(float(np.sqrt(np.mean(err ** 2))), 4),
            "r2": round(1.0 - float(np.sum(err ** 2)) / max(ss_tot, 1e-12), 4)}


# -------------------------------------------------------------------- training


def train_arm(arm: str, data: dict[str, np.ndarray], train_seed: int,
              lr_grid: tuple[float, ...], max_epochs: int, eval_every: int,
              batch_size: int = 16, variant_filter: int = 0) -> dict[str, Any]:
    role, variant = data["role"], data["variant"]
    valid = data["decision_tick"] >= 0
    tr = np.where((role == 0) & (variant == variant_filter) & valid)[0]
    se = np.where((role == 1) & (variant == variant_filter) & valid)[0]
    va = np.where((role == 2) & (variant == variant_filter) & valid)[0]
    if len(se) == 0:  # c3 variant has no sel split: carve from train
        se = tr[: max(len(tr) // 5, 2)]
        tr = tr[max(len(tr) // 5, 2):]
    seq_tr, len_tr, y_tr = episode_tensors(data, tr)
    seq_se, len_se, y_se = episode_tensors(data, se)
    seq_va, len_va, y_va = episode_tensors(data, va)
    in_tr, in_se, in_va = (arm_inputs(arm, seq_tr, len_tr), arm_inputs(arm, seq_se, len_se),
                           arm_inputs(arm, seq_va, len_va))

    best = {"sel_mse": float("inf")}
    arm_idx = ARMS.index(arm)
    for lr in lr_grid:
        torch.manual_seed(SEED_BASE + 1000 * arm_idx + 17 * train_seed)
        model = build_arm(arm)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        n = len(tr)
        order_rng = np.random.default_rng([SEED_BASE, 404, arm_idx, train_seed])
        for epoch in range(1, max_epochs + 1):
            model.train()
            perm = order_rng.permutation(n)
            for b0 in range(0, n, batch_size):
                bi = torch.tensor(perm[b0: b0 + batch_size])
                batch_in = tuple(x[bi] for x in in_tr)
                opt.zero_grad()
                loss = nn.functional.mse_loss(model(*batch_in), y_tr[bi])
                loss.backward()
                opt.step()
            if epoch % eval_every == 0 or epoch == max_epochs:
                model.eval()
                with torch.no_grad():
                    sel_mse = float(nn.functional.mse_loss(model(*in_se), y_se))
                if sel_mse < best["sel_mse"]:
                    best = {"sel_mse": sel_mse, "lr": lr, "epoch": epoch,
                            "state": {k: v.clone() for k, v in model.state_dict().items()}}
    model = build_arm(arm)
    model.load_state_dict(best["state"])
    model.eval()
    with torch.no_grad():
        pred_va = model(*in_va).numpy()
    res = {
        "arm": arm,
        "train_seed": train_seed,
        "n_train": int(len(tr)), "n_sel": int(len(se)), "n_val": int(len(va)),
        "selected": {"lr": best["lr"], "epoch": best["epoch"],
                     "sel_mse": round(best["sel_mse"], 5)},
        "val": metrics(pred_va, y_va.numpy()),
    }
    if "mu_on_grid" in data:
        off = ~data["mu_on_grid"][va]
        if off.any():
            res["val_offgrid_mu"] = metrics(pred_va[off], y_va.numpy()[off])
    if arm == "L3_GRU":  # reset-eval control: state truncated to the last RESET_WINDOW frames
        in_reset = arm_inputs(f"L2_window_{RESET_WINDOW}", seq_va, len_va)[0]
        lens_reset = torch.minimum(len_va, torch.tensor(RESET_WINDOW))
        with torch.no_grad():
            pred_reset = model(in_reset, lens_reset).numpy()
        res["val_reset_control"] = metrics(pred_reset, y_va.numpy())
    return res, model


# ------------------------------------------------------------ belief injection


class BeliefInjector:
    """Duck-typed injected_belief for RampPolicyController: feeds every degraded
    observation the controller sees into the trained estimator and returns the
    current estimate at the decision tick. The GRU path is updated
    incrementally (asserted equal to the batch forward in tests)."""

    def __init__(self, model: nn.Module, arm: str):
        self.model = model.eval()
        self.arm = arm
        self.frames: list[np.ndarray] = []
        self._hidden: torch.Tensor | None = None
        self._last: float | None = None

    def observe(self, obs: np.ndarray) -> None:
        frame = np.asarray(obs, dtype=np.float32)[:OBS_DIM].copy()
        self.frames.append(frame)
        if self.arm == "L3_GRU":
            with torch.no_grad():
                est, self._hidden = self.model.forward_step(torch.tensor(frame), self._hidden)
            self._last = float(est)

    def estimate(self) -> float | None:
        if not self.frames:
            return None
        with torch.no_grad():
            if self.arm == "L3_GRU":
                return self._last
            if self.arm == "L0_frame":
                return float(self.model(torch.tensor(self.frames[-1]).view(1, -1)))
            w = self.model.window
            stack = np.stack(self.frames[-w:])
            if len(stack) < w:
                pad = np.repeat(stack[:1], w - len(stack), axis=0)
                stack = np.concatenate([pad, stack], axis=0)
            return float(self.model(torch.tensor(stack).unsqueeze(0)))


def injection_smoke(models: dict[str, nn.Module], cell_id: str, arm: str,
                    n_points: int = 12) -> dict[str, Any]:
    """1 cell x 12 episodes: prefix-carrying episodes, scripted prefix driving,
    then the M3215 floor-config seeker with/without the injected estimator.
    Infrastructure smoke only; numbers are not a pre-registered measurement."""
    import wp1_data_pipeline as pipe  # loaded below via load_module if needed

    mods = pipe.load_stack()
    reg, mod_b, deg, wp0 = mods["reg"], mods["mod_b"], mods["deg"], mods["wp0"]
    interp = mods["interp"]
    cell = pipe.cells_by_id(wp0)[cell_id]
    _, controller_cls = deg.make_classes(reg)
    design = reg.make_design(mod_b, pipe.REVEAL)
    mus = pipe.mu_grid(n_points)
    rows = []
    for point, mu in enumerate(mus):
        seed = pipe.episode_seed(pipe.ELIGIBLE_CELL_IDS.index(cell_id), "smoke_eval", point)
        for arm_name, injector in (("seeker_floor", None),
                                   (f"seeker+{arm}", BeliefInjector(models[arm], arm))):
            env, _, _ = pipe.make_episode_env(mods, cell, mu, seed, "standard", False)
            behavior = pipe.BehaviorScript(mods, "standard", seed)
            controller = controller_cls(mod_b, interp, design, arm_name, smooth_window=1,
                                        mode="seeker", ramp_rate=20000.0, tau=0.08,
                                        backoff=0.06, strategy="hold", dv=0.0,
                                        injected_belief=injector)
            controller.reset()
            try:
                obs, _ = env.reset(seed=seed)
                if injector is not None:
                    injector.observe(np.asarray(obs, dtype=np.float64))
                for t in range(pipe.PREFIX_STEPS):  # scripted sub-limit prefix
                    action = behavior.act(t, np.asarray(obs, dtype=np.float64))
                    obs, _, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
                    if injector is not None:
                        injector.observe(np.asarray(obs, dtype=np.float64))
                    if term or trunc:
                        break
                episode_return, term, trunc = 0.0, False, False
                while not (term or trunc):
                    action = controller.act(np.asarray(obs, dtype=np.float64))
                    obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
                    episode_return += float(r)
                bucket = mod_b.outcome_bucket_from_info(info, terminated=term, truncated=trunc)
                rows.append({
                    "arm": arm_name, "mu": round(mu, 4), "seed": seed,
                    "success": bucket == "success_obstacle_pass",
                    "bucket": bucket,
                    "mu_injected": getattr(controller, "mu_injected", None),
                    "injection_step": getattr(controller, "injection_step", -1),
                })
            finally:
                env.close()
    out: dict[str, Any] = {"cell_id": cell_id, "n_points": n_points, "rows": rows,
                           "note": ("controller distance bookkeeping starts at the task segment "
                                    "while the obstacle carries the prefix distance offset; "
                                    "smoke-only caveat, the reaction layer uses observed bx")}
    for arm_name in {r["arm"] for r in rows}:
        sub = [r for r in rows if r["arm"] == arm_name]
        out[arm_name] = {"success_rate": round(float(np.mean([r["success"] for r in sub])), 4)}
    inj = [r for r in rows if r["mu_injected"] is not None and not math.isnan(r["mu_injected"] or 0.0)]
    if inj:
        out["mu_injected_abs_err_mean"] = round(
            float(np.mean([abs(r["mu_injected"] - r["mu"]) for r in inj])), 4)
        out["injection_fired_fraction"] = round(len(inj) / max(n_points, 1), 4)
    return out


# ------------------------------------------------------------------------ main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="smoke: 1 cell, 1 seed/arm, tiny grid")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--dataset-dir", type=Path, default=None)
    parser.add_argument("--cells", type=str, default=None)
    parser.add_argument("--seeds", type=int, default=None, help="training seeds per arm")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--skip-injection", action="store_true")
    args = parser.parse_args()
    if args.quick == args.full:
        parser.error("exactly one of --quick / --full is required")

    quick = args.quick
    dataset_dir = args.dataset_dir or (DEFAULT_DATASET_DIR.parent / (DEFAULT_DATASET_DIR.name + "_quick")
                                       if quick else DEFAULT_DATASET_DIR)
    run_dir = args.output_dir or (DEFAULT_RUN_DIR.parent / (DEFAULT_RUN_DIR.name + "_quick")
                                  if quick else DEFAULT_RUN_DIR)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    cell_ids = ([c.strip() for c in args.cells.split(",")] if args.cells
                else (["delay5"] if quick else ["delay5", "delay12", "delay25", "noise0.05"]))
    n_seeds = args.seeds or (1 if quick else 8)
    lr_grid = (1e-3,) if quick else (1e-3, 3e-4)
    max_epochs, eval_every = (60, 10) if quick else (200, 10)

    # make wp1_data_pipeline importable for the injection stage
    import sys as _sys
    _sys.path.insert(0, str(REPO / "scripts/feasibility_audit"))

    started = time.time()
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    capacity = {arm: param_counts(build_arm(arm)) for arm in ARMS}
    spread = assert_capacity_matched(capacity)

    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_wp1_estimator_trainer",
        "generated_by": "scripts/feasibility_audit/wp1_estimator_trainer.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "quick_mode": bool(quick),
        "arms": list(ARMS),
        "primary_arm_preregistered": "L3_GRU",
        "capacity_report": capacity,
        "capacity_nonproj_spread": round(spread, 4),
        "compute_matching": f"same epochs (max {max_epochs}) x same samples per arm; "
                            f"lr grid {list(lr_grid)} + epoch selected on the sel split only",
        "dataset_dir": str(dataset_dir),
        "cells": {},
        "status": "running",
    }
    print(f"[wp1 trainer] capacity(non-input-proj): "
          + " ".join(f"{a}={capacity[a]['non_input_projection']}" for a in ARMS)
          + f" (spread {spread:.3f})", flush=True)

    datasets = load_dataset(dataset_dir, cell_ids)
    models_by_cell: dict[str, dict[str, Any]] = {}
    for cid in cell_ids:
        data = datasets[cid]
        cell_out: dict[str, Any] = {"arms": {}}
        models: dict[str, Any] = {}
        for arm in ARMS:
            arm_runs = []
            for s in range(n_seeds):
                res, model = train_arm(arm, data, s, lr_grid, max_epochs, eval_every)
                arm_runs.append(res)
                if s == 0:
                    models[arm] = model
                    torch.save(model.state_dict(), run_dir / f"{cid}_{arm}_seed{s}.pt")
            cell_out["arms"][arm] = arm_runs
            v = arm_runs[0]["val"]
            extra = ""
            if "val_reset_control" in arm_runs[0]:
                extra = f" reset_r2={arm_runs[0]['val_reset_control']['r2']}"
            print(f"  {cid} {arm:<14} val mae={v['mae']} r2={v['r2']}"
                  f" (lr={arm_runs[0]['selected']['lr']} ep={arm_runs[0]['selected']['epoch']})"
                  + extra, flush=True)
        models_by_cell[cid] = models
        payload["cells"][cid] = cell_out

    if not args.skip_injection:
        cid = cell_ids[0]
        print(f"[wp1 trainer] injection smoke on {cid} (12 episodes, L3_GRU)", flush=True)
        payload["injection_smoke"] = injection_smoke(models_by_cell[cid], cid, "L3_GRU")
        sm = payload["injection_smoke"]
        print("  " + " ".join(f"{k}={v}" for k, v in sm.items()
                              if isinstance(v, dict) and "success_rate" in v)
              + f" mu_err={sm.get('mu_injected_abs_err_mean')}", flush=True)

    payload["elapsed_s"] = round(time.time() - started, 1)
    payload["status"] = "completed"
    (run_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"results -> {run_dir / 'summary.json'}", flush=True)
    print("HEADLINE: " + " | ".join(
        f"{arm}: r2={payload['cells'][cell_ids[0]]['arms'][arm][0]['val']['r2']}"
        for arm in ARMS) + f" | elapsed {payload['elapsed_s']}s", flush=True)


if __name__ == "__main__":
    main()
