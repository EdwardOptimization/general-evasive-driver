"""WP1 bounded-iteration orchestrator (harness milestone M3217): the SINGLE
pre-registered excitation/representation iteration granted by the M3216
all-arms-fail route (docs/m3216-wp1-modular-belief-experiment.md Section 7,
route ``all_arms_fail_one_bounded_iteration_then_accept_bound``; plan
docs/research-plan-phase2-capability-boundary-tracking.md WP1.4: <= 1 week,
<= 4 h CPU, then accept the bound). PASS or FAIL, the outcome is the WP1
terminal verdict -- there is no second iteration.

Iteration design (frozen BEFORE any run in
experiments/feasibility_audit/wp1_iter1_prereg.json; the gated criteria are
UNCHANGED from experiments/feasibility_audit/wp1_prereg.json):

A. Distribution-shift repair (M3216 measured substitution-time L3 mu error
   0.137-0.263 vs dataset-val MAE 0.021-0.142): the training set mixes
   50/50 scripted mu-decoupled episodes (the M3216 behavior family,
   re-based seeds) with CLOSED-LOOP episodes rolled out by the M3216
   best-selection seeker configs (no injected belief, collection-only
   mu-free dv jitter U(-0.75,+0.75)); labels remain true mu. The
   pre-registered dataset leak gate is RERUN on the pooled mixed set
   (decision-frame single-frame -> mu OOF R^2 <= 0.1, linear + MLP); any
   cell failing stops the run before training and the stop is TERMINAL.

B. Injection-timing repair (M3216 injected only at the decision tick, so the
   belief never touched the entry-speed component of the prize and the
   reveal-tick override replaced a sometimes-competent internal detector):
   heteroscedastic 3-member ensembles output per-tick (mu_hat, sigma_total);
   the seeker consumes the estimate CONTINUOUSLY pre-reveal (entry-speed
   law, force-limit estimate) iff sigma_total <= 0.12, freezes the belief at
   the reveal, and falls back to its internal detector when not confident
   (RampPolicyController injection_mode="continuous").

Arms: L3_GRU (primary, unchanged rule: recapture >= 50% of the re-measured
matched prize in >= 3 of 4 cells with one-sided 97.5% lower bounds > 0 under
the frozen two-way SE) + L0_frame (current-frame leak control, unchanged L0
route). L2 windows / C3 / L4 are cut ex ante (frozen scope). Floor, matched
oracle, and the 240-episode paired validation budget are unchanged and
re-measured on fresh seed streams (base 20270301, same layout as stage 2,
re-based because every M3216 subst_val outcome was read by the diagnosis).

Run:
    PYTHONPATH=src python scripts/feasibility_audit/wp1_iter1_full_run.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/wp1_iter1_full_run.py --full
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts/feasibility_audit"
sys.path.insert(0, str(SCRIPTS))

import wp1_full_run as wp1  # shared frozen machinery (M3216 orchestrator)

ITER_PREREG_JSON = REPO / "experiments/feasibility_audit/wp1_iter1_prereg.json"
BASE_PREREG_JSON = REPO / "experiments/feasibility_audit/wp1_prereg.json"
M3216_SUMMARY = REPO / "runs/feasibility_audit/wp1_full/summary.json"
M3215_SUMMARY = REPO / "runs/feasibility_audit/wp0_degraded_sweep/summary.json"
DEFAULT_RUN_DIR = REPO / "runs/feasibility_audit/wp1_iter1_full"

ITER_SEED_BASE = 20270301           # frozen re-base (layout identical to stage 2)
CL_BLOCK = 300_000                  # closed-loop dataset index block inside roles
SIGMA_MAX = 0.12                    # frozen confidence gate (mixture sigma)
STALE_MAX = 50                      # frames (1.0 s) a confident estimate may persist
DV_JITTER = 0.75                    # collection-only mu-free dv jitter half-width
ENSEMBLE_M = 3
ITER_ARMS = ("L0_frame", "L3_GRU")
ARM_INDEX = {"L0_frame": 0, "L3_GRU": 4}   # M3216 arm indexing preserved
PRIMARY_ARM = "L3_GRU"
N_TRAIN_SEEDS = 8
MAX_EPOCHS_FULL = 150
LR_FULL = 1e-3
EVAL_EVERY = 10
BATCH_SIZE = 16
OBS_DIM = 72
H_FRAME = 56
H_GRU = 32
L0_CUT_ELAPSED_S = 5400.0           # operationalized 2.5 h budget rule (see prereg)

# frozen collection policies = the M3216 best-SELECTION seeker configs
CL_SEEKER_SPECS = {
    "delay5": {"type": "seeker", "rate": 20000.0, "w": 1, "tau": 0.08, "backoff": 0.15,
               "dv": 0.75, "name": "cl_collect_delay5"},
    "delay12": {"type": "seeker", "rate": 20000.0, "w": 1, "tau": 0.08, "backoff": 0.06,
                "dv": 0.75, "name": "cl_collect_delay12"},
    "delay25": {"type": "seeker", "rate": 20000.0, "w": 1, "tau": 0.08, "backoff": 0.06,
                "dv": 0.75, "name": "cl_collect_delay25"},
    "noise0.05": {"type": "seeker", "rate": 6000.0, "w": 25, "tau": 0.444, "backoff": 0.06,
                  "dv": 0.0, "name": "cl_collect_noise0.05"},
}

CLAIM_BOUNDARY = (
    "Feasibility-audit WP1 bounded-iteration substitution measurement only (Phase-2 manual "
    "takeover, harness milestone M3217): the single pre-registered excitation/representation "
    "iteration granted by the M3216 all-arms-fail route, on the unchanged criteria, "
    "construction, and statistics, with mixed scripted+closed-loop training data and "
    "confidence-gated continuous belief injection. The outcome is terminal for WP1 either "
    "way. Auxiliary measurement; the engineering incumbent and ActiveSafetyReflexDriver are "
    "unchanged. No driver promotion, validation ranking, repair-success, gate-validity, "
    "paper, high-fidelity, robustness-result, feasibility-proof, or self-ID capability claim."
)


def _ensure_mods_iter() -> None:
    """Load the M3216 stack, then re-base every seed stream to the iteration
    base (same layout; all rng tuples re-key on 20270301)."""
    wp1._ensure_mods()
    wp1.PIPE.SEED_BASE = ITER_SEED_BASE
    wp1.PIPE.EPISODE_SEED_BASE = ITER_SEED_BASE * 100


def jsonable(value: Any) -> Any:
    return wp1.jsonable(value)


# ------------------------------------------------------------- het estimators


def _build_torch():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)

    class HetL0Net(nn.Module):
        def __init__(self, h: int = H_FRAME):
            super().__init__()
            self.in_proj = nn.Linear(OBS_DIM, h)
            self.body = nn.Linear(h, h)
            self.head = nn.Linear(h, 2)

        def forward(self, frame):  # [B, 72] -> (mu [B], sigma [B])
            z = torch.relu(self.in_proj(frame))
            z = torch.relu(self.body(z))
            o = self.head(z)
            return o[..., 0], F.softplus(o[..., 1]) + 1e-3

    class HetGRUNet(nn.Module):
        def __init__(self, h: int = H_GRU):
            super().__init__()
            self.gru = nn.GRU(OBS_DIM, h, batch_first=True)
            self.head = nn.Linear(h, 2)

        def forward_all(self, frames):  # [B, T, 72] -> (mu [B,T], sigma [B,T])
            out, _ = self.gru(frames)
            o = self.head(out)
            return o[..., 0], F.softplus(o[..., 1]) + 1e-3

        def forward_step(self, frame, hidden):
            out, hidden = self.gru(frame.view(1, 1, -1), hidden)
            o = self.head(out[:, -1]).squeeze(0)
            return o[0], F.softplus(o[1]) + 1e-3, hidden

    return torch, nn, HetL0Net, HetGRUNet


def build_iter_arm(arm: str):
    torch, _, HetL0Net, HetGRUNet = _build_torch()
    return HetL0Net() if arm == "L0_frame" else HetGRUNet()


def _mixture(ms: list[float], ss: list[float]) -> tuple[float, float]:
    m = float(np.mean(ms))
    var = float(np.mean([s * s + mm * mm for s, mm in zip(ss, ms)]) - m * m)
    return m, math.sqrt(max(var, 0.0))


class EnsembleHetInjector:
    """Duck-typed injected_belief for injection_mode='continuous': per-tick
    3-member heteroscedastic mixture (mu_hat, sigma_total)."""

    def __init__(self, arm: str, models: list):
        self.arm = arm
        self.models = [m.eval() for m in models]
        self._hidden: list = [None] * len(models)
        self._last: tuple[float, float] | None = None

    def observe(self, obs: np.ndarray) -> None:
        import torch

        frame = np.asarray(obs, dtype=np.float32)[:OBS_DIM]
        ms: list[float] = []
        ss: list[float] = []
        with torch.no_grad():
            if self.arm == "L3_GRU":
                x = torch.tensor(frame)
                for i, model in enumerate(self.models):
                    mu, sig, self._hidden[i] = model.forward_step(x, self._hidden[i])
                    ms.append(float(mu))
                    ss.append(float(sig))
            else:
                x = torch.tensor(frame).view(1, -1)
                for model in self.models:
                    mu, sig = model(x)
                    ms.append(float(mu[0]))
                    ss.append(float(sig[0]))
        self._last = _mixture(ms, ss)

    def estimate_with_conf(self) -> tuple[float, float] | None:
        return self._last

    def estimate(self) -> float | None:
        return None if self._last is None else self._last[0]


def make_iter_injector(spec: dict[str, Any] | None):
    if spec is None:
        return None
    import torch

    models = []
    for path in spec["paths"]:
        model = build_iter_arm(spec["arm"])
        model.load_state_dict(torch.load(path, map_location="cpu"))
        models.append(model)
    return EnsembleHetInjector(spec["arm"], models)


# ---------------------------------------------------------------- data stage


def run_cl_episode(cell: dict[str, Any], mu: float, seed: int, role: str) -> dict[str, Any]:
    """Closed-loop dataset episode: scripted prefix, then the frozen collection
    seeker (no belief, collection-only dv jitter) to the decision tick + 1."""
    PIPE = wp1.PIPE
    mods = wp1.MODS
    reg, bd = mods["reg"], mods["bd"]
    cid = cell["cell_id"]
    base_spec = CL_SEEKER_SPECS[cid]
    rng = np.random.default_rng([ITER_SEED_BASE, 313, int(seed)])
    dv_cl = float(base_spec["dv"] + rng.uniform(-DV_JITTER, DV_JITTER))
    spec = dict(base_spec, dv=dv_cl)
    env, _, d_total = PIPE.make_episode_env(mods, cell, mu, seed, "standard", False)
    cap_r = reg.TIRE_CAP * mu * reg.FZR
    behavior = PIPE.BehaviorScript(mods, "standard", seed)
    controller = wp1.build_controller(spec, mu, None)
    controller.reset()
    rls = bd.VehicleRLS(r_noise_ax=max((15.0 * float(cell["degradation"].get("noise_std", 0.0))) ** 2, 0.04))
    frames: list[np.ndarray] = []
    decision_tick = -1
    last_excitation_step = -1
    prefix_max_util = 0.0
    initial_transient_max_util = 0.0
    task_max_util_nonexcite = 0.0
    try:
        obs, _ = env.reset(seed=seed)
        frames.append(np.asarray(obs, dtype=np.float32).copy())
        for t in range(PIPE.MAX_STEPS_STD):
            obs_arr = np.asarray(obs, dtype=np.float64)
            if t < PIPE.PREFIX_STEPS:
                rls.update_obs(obs_arr)
                action = behavior.act(t, obs_arr)
            else:
                action = controller.act(obs_arr)
            obs, _, terminated, truncated, _ = env.step(np.asarray(action, dtype=np.float64))
            frames.append(np.asarray(obs, dtype=np.float32).copy())
            forces = env.last_forces
            util = math.hypot(float(forces.fx_rear), float(forces.fy_rear)) / max(cap_r, 1.0)
            frame_idx = t + 1
            if frame_idx <= PIPE.PREFIX_TRANSIENT_SKIP:
                initial_transient_max_util = max(initial_transient_max_util, util)
            elif frame_idx <= PIPE.PREFIX_STEPS:
                prefix_max_util = max(prefix_max_util, util)
            if util > PIPE.EXCITATION_UTIL_BAR:
                last_excitation_step = frame_idx
            elif frame_idx > PIPE.PREFIX_STEPS:
                task_max_util_nonexcite = max(task_max_util_nonexcite, util)
            if decision_tick < 0 and float(frames[-1][44]) > 0.5:
                decision_tick = frame_idx
            if decision_tick >= 0 and frame_idx >= decision_tick + PIPE.POST_DECISION_FRAMES:
                break
            if terminated or truncated:
                break
    finally:
        env.close()
    kb_hat, kd_hat = rls.kappas
    decision_time_task_s = ((decision_tick - PIPE.PREFIX_STEPS) * PIPE.DT) if decision_tick >= 0 else float("nan")
    has_excitation = last_excitation_step >= 0
    if decision_tick >= 0 and has_excitation:
        gap_s = (decision_tick - last_excitation_step) * PIPE.DT
    elif decision_tick >= 0:
        gap_s = decision_tick * PIPE.DT
    else:
        gap_s = float("nan")
    return {
        "frames": np.stack(frames).astype(np.float32),
        "mu": float(mu), "seed": int(seed), "role": role, "variant": "standard",
        "decision_tick": int(decision_tick),
        "decision_time_task_s": float(decision_time_task_s),
        "last_excitation_step": int(last_excitation_step),
        "has_excitation": bool(has_excitation),
        "excitation_to_decision_gap_s": float(gap_s),
        "prefix_max_util": float(prefix_max_util),
        "initial_transient_max_util": float(initial_transient_max_util),
        "task_max_util_nonexcite": float(task_max_util_nonexcite),
        "kappa_b_hat": float(kb_hat), "kappa_d_hat": float(kd_hat),
        "rls_frames": int(rls.n_frames),
        "behavior_params": {"kind_code": 3.0, "v_target": 0.0, "ramp_rate": spec["rate"],
                            "ramp_peak_n": 0.0, "ramp_t0": -1.0, "ramp_hold_steps": 0.0},
        "d_total": float(d_total),
        "dv_collect": dv_cl,
    }


def task_iter_data_chunk(cell_id: str, specs: list[tuple[float, int, str, str, bool]]) -> list[dict[str, Any]]:
    _ensure_mods_iter()
    cell = wp1.cell_by_id(cell_id)
    records = []
    for mu, seed, kind, role, on_grid in specs:
        if kind == "scripted":
            rec = wp1.PIPE.run_episode(wp1.MODS, cell, mu, seed, "standard", role, False)
            rec["dv_collect"] = float("nan")
        else:
            rec = run_cl_episode(cell, mu, seed, role)
        rec["mu_on_grid"] = on_grid
        rec["closed_loop"] = (kind == "closed_loop")
        records.append(rec)
    return records


def save_cell_npz_iter(path: Path, records: list[dict[str, Any]]) -> None:
    t_max = max(len(r["frames"]) for r in records)
    n = len(records)
    obs = np.zeros((n, t_max, OBS_DIM), dtype=np.float32)
    for i, r in enumerate(records):
        obs[i, : len(r["frames"])] = r["frames"]
    role_code = {"train": 0, "sel": 1, "val": 2}
    bp_keys = ("kind_code", "v_target", "ramp_rate", "ramp_peak_n", "ramp_t0", "ramp_hold_steps")
    np.savez_compressed(
        path,
        obs=obs,
        length=np.array([len(r["frames"]) for r in records], dtype=np.int32),
        decision_tick=np.array([r["decision_tick"] for r in records], dtype=np.int32),
        mu=np.array([r["mu"] for r in records], dtype=np.float32),
        seed=np.array([r["seed"] for r in records], dtype=np.int64),
        role=np.array([role_code[r["role"]] for r in records], dtype=np.int8),
        variant=np.zeros(n, dtype=np.int8),
        closed_loop=np.array([r["closed_loop"] for r in records], dtype=bool),
        dv_collect=np.array([r.get("dv_collect", float("nan")) for r in records], dtype=np.float32),
        mu_on_grid=np.array([r.get("mu_on_grid", False) for r in records], dtype=bool),
        prefix_max_util=np.array([r["prefix_max_util"] for r in records], dtype=np.float32),
        initial_transient_max_util=np.array([r["initial_transient_max_util"] for r in records],
                                            dtype=np.float32),
        kappa_b_hat=np.array([r["kappa_b_hat"] for r in records], dtype=np.float32),
        kappa_d_hat=np.array([r["kappa_d_hat"] for r in records], dtype=np.float32),
        behavior_params=np.array([[r["behavior_params"][k] for k in bp_keys] for r in records],
                                 dtype=np.float32),
        behavior_param_keys=np.array(bp_keys),
        prefix_steps=np.array([wp1.PIPE.PREFIX_STEPS], dtype=np.int32),
    )


# ------------------------------------------------------------- training stage


def _decision_frame_stats(model, arm: str, seqs, lens, y):
    import torch

    with torch.no_grad():
        if arm == "L3_GRU":
            mu, sig = model.forward_all(seqs)
            idx = (lens - 1).clamp(min=0).view(-1, 1)
            mu_d = mu.gather(1, idx).squeeze(1)
            sig_d = sig.gather(1, idx).squeeze(1)
        else:
            frames = seqs[torch.arange(seqs.size(0)), (lens - 1).clamp(min=0)]
            mu_d, sig_d = model(frames)
        nll = (torch.log(sig_d) + 0.5 * ((y - mu_d) / sig_d) ** 2).mean()
    return float(nll), mu_d.numpy(), sig_d.numpy()


def task_train_iter(cell_id: str, arm: str, train_seed: int, member: int, npz_path: str,
                    max_epochs: int, model_path: str) -> dict[str, Any]:
    _ensure_mods_iter()
    torch, nn, _, _ = _build_torch()

    with np.load(npz_path) as z:
        data = {k: z[k] for k in z.files}
    role, variant = data["role"], data["variant"]
    valid = data["decision_tick"] >= 0
    tr = np.where((role == 0) & (variant == 0) & valid)[0]
    se = np.where((role == 1) & (variant == 0) & valid)[0]
    va = np.where((role == 2) & (variant == 0) & valid)[0]
    TRAINER = wp1.TRAINER
    seq_tr, len_tr, y_tr = TRAINER.episode_tensors(data, tr)
    seq_se, len_se, y_se = TRAINER.episode_tensors(data, se)
    prefix = int(data["prefix_steps"][0])

    torch.manual_seed(ITER_SEED_BASE + 1000 * ARM_INDEX[arm] + 17 * train_seed + 100_003 * member)
    model = build_iter_arm(arm)
    opt = torch.optim.Adam(model.parameters(), lr=LR_FULL)
    order_rng = np.random.default_rng([ITER_SEED_BASE, 404, ARM_INDEX[arm], train_seed, member])
    n = len(tr)
    t_grid = torch.arange(seq_tr.size(1))
    lens_np = len_tr.numpy()
    best = {"sel_nll": float("inf")}
    for epoch in range(1, max_epochs + 1):
        model.train()
        perm = order_rng.permutation(n)
        for b0 in range(0, n, BATCH_SIZE):
            bi_np = perm[b0: b0 + BATCH_SIZE]
            bi = torch.tensor(bi_np)
            opt.zero_grad()
            if arm == "L3_GRU":
                mu, sig = model.forward_all(seq_tr[bi])
                mask = (t_grid.unsqueeze(0) >= prefix) & (t_grid.unsqueeze(0) < len_tr[bi].unsqueeze(1))
                nll = torch.log(sig) + 0.5 * ((y_tr[bi].unsqueeze(1) - mu) / sig) ** 2
                loss = nll[mask].mean()
            else:
                ticks = np.array([int(order_rng.integers(prefix, max(int(ln), prefix + 1)))
                                  for ln in lens_np[bi_np]])
                frames = seq_tr[bi, torch.tensor(ticks)]
                mu, sig = model(frames)
                loss = (torch.log(sig) + 0.5 * ((y_tr[bi] - mu) / sig) ** 2).mean()
            loss.backward()
            opt.step()
        if epoch % EVAL_EVERY == 0 or epoch == max_epochs:
            model.eval()
            sel_nll, _, _ = _decision_frame_stats(model, arm, seq_se, len_se, y_se)
            if sel_nll < best["sel_nll"]:
                best = {"sel_nll": sel_nll, "epoch": epoch,
                        "state": {k: v.clone() for k, v in model.state_dict().items()}}
    model = build_iter_arm(arm)
    model.load_state_dict(best["state"])
    model.eval()
    torch.save(model.state_dict(), model_path)
    return {
        "arm": arm, "train_seed": train_seed, "member": member,
        "n_train": int(len(tr)), "n_sel": int(len(se)), "n_val": int(len(va)),
        "selected": {"lr": LR_FULL, "epoch": best["epoch"], "sel_nll": round(best["sel_nll"], 5)},
        "model_path": model_path,
    }


def task_ensemble_val(cell_id: str, arm: str, train_seed: int, npz_path: str,
                      paths: list[str]) -> dict[str, Any]:
    """Decision-tick mixture metrics of one 3-member ensemble on the val split
    (mixed + scripted-only + closed-loop-only)."""
    _ensure_mods_iter()
    torch, _, _, _ = _build_torch()
    with np.load(npz_path) as z:
        data = {k: z[k] for k in z.files}
    role, variant = data["role"], data["variant"]
    valid = data["decision_tick"] >= 0
    va = np.where((role == 2) & (variant == 0) & valid)[0]
    seq_va, len_va, y_va = wp1.TRAINER.episode_tensors(data, va)
    mus, sigs = [], []
    for path in paths:
        model = build_iter_arm(arm)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        _, mu_d, sig_d = _decision_frame_stats(model, arm, seq_va, len_va, y_va)
        mus.append(mu_d)
        sigs.append(sig_d)
    mus_a, sigs_a = np.stack(mus), np.stack(sigs)
    mix_mu = mus_a.mean(0)
    mix_var = (sigs_a ** 2 + mus_a ** 2).mean(0) - mix_mu ** 2
    mix_sig = np.sqrt(np.clip(mix_var, 0.0, None))
    y = y_va.numpy()
    cl = data["closed_loop"][va]

    def _metrics(mask: np.ndarray) -> dict[str, Any] | None:
        if not mask.any():
            return None
        err = mix_mu[mask] - y[mask]
        ss_tot = float(np.sum((y[mask] - y[mask].mean()) ** 2))
        return {
            "n": int(mask.sum()),
            "mae": round(float(np.mean(np.abs(err))), 4),
            "r2": round(1.0 - float(np.sum(err ** 2)) / max(ss_tot, 1e-12), 4),
            "sigma_mean": round(float(mix_sig[mask].mean()), 4),
            "confident_fraction": round(float(np.mean(mix_sig[mask] <= SIGMA_MAX)), 4),
        }

    return {
        "arm": arm, "train_seed": train_seed,
        "val_mixed": _metrics(np.ones(len(va), dtype=bool)),
        "val_scripted": _metrics(~cl),
        "val_closed_loop": _metrics(cl),
    }


# --------------------------------------------------------- substitution stage


def run_std_episode_cont(cell: dict[str, Any], mu: float, seed: int, ctrl_spec: dict[str, Any],
                         injector_spec: dict[str, Any], max_steps: int) -> dict[str, Any]:
    """Mirror of wp1.run_std_episode with injection_mode='continuous'."""
    env, _ = wp1.make_eval_env(cell, mu, seed, "standard", False, max_steps)
    behavior = wp1.PIPE.BehaviorScript(wp1.MODS, "standard", seed)
    injector = make_iter_injector(injector_spec)
    mods = wp1.MODS
    controller = wp1.CTRL_CLS(
        mods["mod_b"], mods["interp"], wp1.DESIGN, ctrl_spec["name"],
        smooth_window=int(ctrl_spec["w"]), mode="seeker", ramp_rate=ctrl_spec["rate"],
        tau=ctrl_spec["tau"], backoff=ctrl_spec["backoff"], strategy="hold",
        dv=ctrl_spec["dv"], injected_belief=injector, injection_mode="continuous",
        injection_sigma_max=SIGMA_MAX, injection_stale_max=STALE_MAX)
    controller.reset()
    ep_return = 0.0
    try:
        obs, _ = env.reset(seed=seed)
        term = trunc = False
        info: dict[str, Any] = {}
        for t in range(wp1.PIPE.PREFIX_STEPS):
            injector.observe(np.asarray(obs, dtype=np.float64))
            action = behavior.act(t, np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
            if term or trunc:
                break
        while not (term or trunc):
            action = controller.act(np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
        bucket = wp1._bucket(info, term, trunc)
    finally:
        env.close()
    mu_injected = controller.mu_injected
    return {
        "seed": int(seed), "mu": round(float(mu), 4),
        "success": bucket == "success_obstacle_pass", "bucket": bucket,
        "collided": bucket == "collision_failure",
        "timeout": bucket == "max_steps_noncompletion",
        "return": round(ep_return, 3),
        "mu_hat": controller.mu_hat,
        "censored": bool(controller.censored),
        "mu_injected": (None if mu_injected is None else round(float(mu_injected), 4)),
        "injection_step": int(controller.injection_step),
        "conf_fraction": round(controller._conf_frames / max(controller._obs_frames, 1), 4),
        "fallback_at_reveal": bool(controller._reveal_frozen and mu_injected is None),
    }


def task_iter_arm(cell_id: str, arm_name: str, ctrl_spec: dict[str, Any],
                  injector_spec: dict[str, Any], phase: str, ks: list[int],
                  max_steps: int, rows_path: str | None) -> dict[str, Any]:
    _ensure_mods_iter()
    cell = wp1.cell_by_id(cell_id)
    rows = []
    for point, mu in enumerate(wp1.mu_grid()):
        for k in ks:
            seed = wp1.subst_seed(cell_id, phase, point, k)
            row = run_std_episode_cont(cell, mu, seed, ctrl_spec, injector_spec, max_steps)
            row.update({"point": point, "k": int(k), "arm": arm_name,
                        "cell": cell_id, "phase": phase})
            rows.append(row)
    if rows_path:
        from autodrift.artifacts import write_csv_rows

        write_csv_rows(Path(rows_path), rows)
    inj = [r for r in rows if r["mu_injected"] is not None]
    return {
        "arm": arm_name, "cell": cell_id, "phase": phase, "n": len(rows),
        "success": round(float(np.mean([r["success"] for r in rows])), 4),
        "return": round(float(np.mean([r["return"] for r in rows])), 4),
        "episode_success": {f"{r['point']}:{r['k']}": (1 if r["success"] else 0) for r in rows},
        "injection_fired_fraction": (round(len(inj) / len(rows), 4) if rows else None),
        "fallback_at_reveal_fraction": round(float(np.mean([r["fallback_at_reveal"] for r in rows])), 4),
        "conf_fraction_mean": round(float(np.mean([r["conf_fraction"] for r in rows])), 4),
        "mu_injected_abs_err_mean": (round(float(np.mean([abs(r["mu_injected"] - r["mu"])
                                                          for r in inj])), 4) if inj else None),
        "rows_path": rows_path,
    }


def task_std_arm_iter(*args, **kwargs) -> dict[str, Any]:
    _ensure_mods_iter()
    return wp1.task_std_arm(*args, **kwargs)


def task_oracle_sel_iter(*args, **kwargs) -> dict[str, Any]:
    _ensure_mods_iter()
    return wp1.task_oracle_sel(*args, **kwargs)


# ------------------------------------------------------------------------ main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="end-to-end smoke (1 cell, tiny counts)")
    parser.add_argument("--full", action="store_true", help="pre-registered bounded-iteration run")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    if args.quick == args.full:
        parser.error("exactly one of --quick / --full is required")

    _ensure_mods_iter()
    quick = args.quick
    run_dir = Path(args.output_dir or (DEFAULT_RUN_DIR.parent / (DEFAULT_RUN_DIR.name + "_quick")
                                       if quick else DEFAULT_RUN_DIR))
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rows").mkdir(exist_ok=True)
    (run_dir / "models").mkdir(exist_ok=True)
    progress_path = run_dir / "progress.jsonl"

    iter_prereg = json.loads(ITER_PREREG_JSON.read_text(encoding="utf-8"))
    base_prereg = json.loads(BASE_PREREG_JSON.read_text(encoding="utf-8"))
    if args.full:
        appendix = iter_prereg["continuous_injection_appendix_frozen"]
        assert "0.12" in appendix["confidence_gate"] and SIGMA_MAX == 0.12
        assert iter_prereg["seed_streams_frozen"]["iter_seed_base"] == ITER_SEED_BASE
        cells = list(wp1.ELIGIBLE_CELL_IDS)
        counts = {"train": 240, "sel": 40, "val_offgrid": 24}
        n_seeds, n_members, max_epochs = N_TRAIN_SEEDS, ENSEMBLE_M, MAX_EPOCHS_FULL
        sel_ks = list(range(wp1.SEL_KS))
        val_ks = list(range(wp1.VAL_KS))
    else:
        cells = ["delay5"]
        counts = {"train": 16, "sel": 6, "val_offgrid": 2}
        n_seeds, n_members, max_epochs = 2, 2, 20
        sel_ks = [0]
        val_ks = [0, 1, 2]

    std_max_steps = wp1.PIPE.PREFIX_STEPS + 0 + wp1.B2K2_TASK_STEPS
    m3215 = json.loads(M3215_SUMMARY.read_text(encoding="utf-8"))
    cal_f1 = m3215["calibration"]["family1"]
    m3216 = json.loads(M3216_SUMMARY.read_text(encoding="utf-8"))

    done: dict[str, Any] = {}
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["unit"]] = rec["payload"]

    def mark_done(unit: str, payload_unit: Any) -> None:
        done[unit] = payload_unit
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(jsonable({"unit": unit, "payload": payload_unit})) + "\n")

    started = time.time()
    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_wp1_iter1_bounded_iteration_full_run",
        "generated_by": "scripts/feasibility_audit/wp1_iter1_full_run.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "quick_mode": bool(quick),
        "preregistration": {
            "iteration_file": str(ITER_PREREG_JSON), "iteration_echo": iter_prereg,
            "criteria_file": str(BASE_PREREG_JSON),
            "criteria_echo_note": "gated criteria unchanged from wp1_prereg.json (statistics_frozen, primary_frozen, outcome routes for L0); construction unchanged",
            "criteria_echo": {k: base_prereg[k] for k in
                              ("statistics_frozen", "primary_frozen", "construction_frozen")},
        },
        "iteration_constants": {
            "iter_seed_base": ITER_SEED_BASE, "mix_ratio": "50/50",
            "sigma_max": SIGMA_MAX, "stale_max_frames": STALE_MAX,
            "dv_jitter": DV_JITTER, "ensemble_members": n_members,
            "cl_collection_specs": CL_SEEKER_SPECS,
            "max_epochs": max_epochs, "lr": LR_FULL, "batch_size": BATCH_SIZE,
            "std_max_steps": std_max_steps,
        },
        "eligible_cells": cells,
        "data": {}, "training": {}, "selection": {}, "validation": {},
        "m3216_comparison": {}, "verdicts": {},
        "status": "running",
    }

    def flush_partial(final: bool = False) -> None:
        payload["elapsed_s"] = round(time.time() - started, 1)
        target = run_dir / ("summary.json" if final else "summary_partial.json")
        target.write_text(json.dumps(jsonable(payload), indent=2), encoding="utf-8")

    pool = ProcessPoolExecutor(max_workers=args.workers)

    # ------------------------------------------------- [1/5] mixed dataset
    print(f"[1/5] mixed dataset: cells={cells} counts={counts} (+ closed-loop mirror)", flush=True)
    PIPE = wp1.PIPE
    for cid in cells:
        unit = f"data_{cid}"
        npz_path = run_dir / f"{cid}.npz"
        if unit in done and npz_path.exists():
            payload["data"][cid] = done[unit]
            continue
        ci = wp1.cell_index(cid)
        specs: list[tuple[float, int, str, str, bool]] = []
        for role, n in (("train", counts["train"]), ("sel", counts["sel"])):
            for i in range(n):
                seed_s = PIPE.episode_seed(ci, role, i)
                specs.append((PIPE.draw_mu(seed_s), seed_s, "scripted", role, False))
                seed_c = PIPE.episode_seed(ci, role, CL_BLOCK + i)
                specs.append((PIPE.draw_mu(seed_c), seed_c, "closed_loop", role, False))
        val_mus = ([(m, True) for m in PIPE.mu_grid()]
                   + [(m, False) for m in PIPE.mu_offgrid(counts["val_offgrid"])])
        for i, (mu, on_grid) in enumerate(val_mus):
            specs.append((mu, PIPE.episode_seed(ci, "val", i), "scripted", "val", on_grid))
            specs.append((mu, PIPE.episode_seed(ci, "val", CL_BLOCK + i), "closed_loop", "val", on_grid))
        chunk = max(len(specs) // (args.workers * 2), 4)
        futures = [pool.submit(task_iter_data_chunk, cid, specs[i: i + chunk])
                   for i in range(0, len(specs), chunk)]
        records: list[dict[str, Any]] = []
        for f in futures:
            records.extend(f.result())
        save_cell_npz_iter(npz_path, records)
        pooled = [r for r in records if r["decision_tick"] >= 0]
        scripted = [r for r in pooled if not r["closed_loop"]]
        closed = [r for r in pooled if r["closed_loop"]]
        summary = {
            "n_episodes": len(records),
            "n_closed_loop": sum(1 for r in records if r["closed_loop"]),
            "n_invalid_decision": sum(1 for r in records if r["decision_tick"] < 0),
            "probe_gate_pooled": PIPE.probe_gate(pooled),
            "probe_scripted_only": PIPE.probe_gate(scripted),
            "probe_closed_loop_only": PIPE.probe_gate(closed),
            "prefix_max_util_overall": round(max(r["prefix_max_util"] for r in records), 4),
            "kappa_b_hat_median": round(float(np.median([r["kappa_b_hat"] for r in records])), 4),
            "npz": str(npz_path),
        }
        payload["data"][cid] = summary
        mark_done(unit, summary)
        print(f"  {cid}: n={summary['n_episodes']} cl={summary['n_closed_loop']} "
              f"invalid={summary['n_invalid_decision']} "
              f"pooled_lin={summary['probe_gate_pooled'].get('r2_linear_oof')} "
              f"pooled_mlp={summary['probe_gate_pooled'].get('r2_mlp_oof')} "
              f"cl_lin={summary['probe_closed_loop_only'].get('r2_linear_oof')}", flush=True)
        flush_partial()

    gate_all = all(payload["data"][cid]["probe_gate_pooled"].get("gate_pass") is True for cid in cells)
    payload["data"]["dataset_gate_pass_all_cells"] = bool(gate_all)
    if args.full and not gate_all:
        payload["status"] = "stopped_dataset_leak_gate_failed_iter1"
        payload["verdicts"] = {
            "primary_verdict": "FAIL",
            "primary_fail_mode": "mixed_dataset_leak_gate_failed",
            "route": ("terminal_bound_accepted: the closed-loop mixing required to close the "
                      "behavior-policy gap is itself current-frame mu-readable on this "
                      "construction; no further iteration is pre-authorized"),
        }
        flush_partial(final=True)
        print("HEADLINE: mixed dataset leak gate FAILED -> terminal stop per iteration prereg", flush=True)
        pool.shutdown()
        return

    # ---------------------------------------------------- [2/5] training
    train_units = [(cid, arm, s, m) for cid in cells for arm in ITER_ARMS
                   for s in range(n_seeds) for m in range(n_members)]
    print(f"[2/5] training: {len(train_units)} member runs "
          f"({len(ITER_ARMS)} arms x {n_seeds} seeds x {n_members} members x {len(cells)} cells)",
          flush=True)
    pending = {}
    for cid, arm, s, m in train_units:
        unit = f"train_{cid}_{arm}_s{s}_m{m}"
        model_path = run_dir / "models" / f"{cid}_{arm}_s{s}_m{m}.pt"
        if unit in done and model_path.exists():
            continue
        pending[unit] = pool.submit(task_train_iter, cid, arm, s, m,
                                    str(run_dir / f"{cid}.npz"), max_epochs, str(model_path))
    for unit, fut in pending.items():
        mark_done(unit, fut.result())
    capacity = {arm: wp1.TRAINER.param_counts(build_iter_arm(arm)) for arm in ITER_ARMS}
    spread = (max(v["non_input_projection"] for v in capacity.values())
              - min(v["non_input_projection"] for v in capacity.values())) / \
        min(v["non_input_projection"] for v in capacity.values())
    payload["training"]["capacity_report"] = capacity
    payload["training"]["capacity_nonproj_spread"] = round(spread, 4)
    assert spread <= 0.10, f"capacity mismatch {capacity}"
    # ensemble val metrics per (cell, arm, seed)
    pending = {}
    for cid in cells:
        for arm in ITER_ARMS:
            for s in range(n_seeds):
                unit = f"valmetrics_{cid}_{arm}_s{s}"
                if unit in done:
                    continue
                paths = [str(run_dir / "models" / f"{cid}_{arm}_s{s}_m{m}.pt")
                         for m in range(n_members)]
                pending[unit] = pool.submit(task_ensemble_val, cid, arm, s,
                                            str(run_dir / f"{cid}.npz"), paths)
    for unit, fut in pending.items():
        mark_done(unit, fut.result())
    payload["training"]["runs"] = {u: done[u] for u in (f"train_{cid}_{arm}_s{s}_m{m}"
                                                        for cid in cells for arm in ITER_ARMS
                                                        for s in range(n_seeds) for m in range(n_members))}
    payload["training"]["ensemble_val"] = {u: done[u] for u in (f"valmetrics_{cid}_{arm}_s{s}"
                                                                for cid in cells for arm in ITER_ARMS
                                                                for s in range(n_seeds))}
    for cid in cells:
        for arm in ITER_ARMS:
            mm = [done[f"valmetrics_{cid}_{arm}_s{s}"]["val_mixed"]["mae"] for s in range(n_seeds)]
            cf = [done[f"valmetrics_{cid}_{arm}_s{s}"]["val_closed_loop"]["mae"] for s in range(n_seeds)]
            print(f"  {cid} {arm:<10} ens val MAE mixed {np.mean(mm):.4f} closed-loop {np.mean(cf):.4f}",
                  flush=True)
    flush_partial()

    # ------------------------------------------- [3/5] floor/oracle selection
    print("[3/5] floor/oracle selection on the iteration subst_sel stream", flush=True)
    selection: dict[str, Any] = {}
    for cid in cells:
        unit = f"sel_{cid}"
        if unit in done:
            selection[cid] = done[unit]
            payload["selection"][cid] = done[unit]
            continue
        cell = wp1.cell_by_id(cid)
        specs = wp1.floor_seeker_specs(cell, cal_f1[cid]) + wp1.fixed_specs()
        futures = {s["name"]: pool.submit(task_std_arm_iter, cid, s["name"], s, None, "sel",
                                          sel_ks, std_max_steps, None, None)
                   for s in specs}
        oracle_fut = pool.submit(task_oracle_sel_iter, cid, sel_ks, std_max_steps)
        results = {n: f.result() for n, f in futures.items()}
        spec_by_name = {s["name"]: s for s in specs}
        seekers = {n: r for n, r in results.items() if spec_by_name[n]["type"] == "seeker"}
        fixeds = {n: r for n, r in results.items() if spec_by_name[n]["type"] != "seeker"}
        best_seeker = max(seekers, key=lambda n: (seekers[n]["success"], seekers[n]["return"]))
        best_fixed = max(fixeds, key=lambda n: (fixeds[n]["success"], fixeds[n]["return"]))
        osel = oracle_fut.result()
        sel_payload = {
            "best_seeker": {"name": best_seeker, "spec": spec_by_name[best_seeker],
                            "sel_success": results[best_seeker]["success"]},
            "best_fixed": {"name": best_fixed, "spec": spec_by_name[best_fixed],
                           "sel_success": results[best_fixed]["success"]},
            "oracle_dv_by_point": osel["dv_by_point"],
            "n_seeker_configs": len(seekers), "n_fixed_configs": len(fixeds),
            "sel_table": {n: r["success"] for n, r in results.items()},
        }
        selection[cid] = sel_payload
        payload["selection"][cid] = sel_payload
        mark_done(unit, sel_payload)
        print(f"  {cid}: best_seeker={best_seeker} ({results[best_seeker]['success']}) "
              f"best_fixed={best_fixed} ({results[best_fixed]['success']})", flush=True)
        flush_partial()

    # ------------------------------------------------ [4/5] paired validation
    elapsed_now = time.time() - started
    cut_l0 = bool(args.full and elapsed_now > L0_CUT_ELAPSED_S)
    subst_arms = [a for a in ITER_ARMS if not (cut_l0 and a == "L0_frame")]
    payload["validation"]["l0_substitution_cut_by_budget_rule"] = cut_l0
    print(f"[4/5] paired validation: {len(cells)} cells x (floor+oracle+"
          f"{len(subst_arms)}x{n_seeds} injected) x {12 * len(val_ks)} episodes"
          + (" [L0 substitution cut by budget rule]" if cut_l0 else ""), flush=True)
    pending = {}
    for cid in cells:
        sel = selection[cid]
        base_arms = [
            ("floor_seeker", sel["best_seeker"]["spec"], None),
            ("floor_fixed", sel["best_fixed"]["spec"], None),
            ("oracle", {"type": "oracle", "dv": 0.0, "name": "oracle_per_point"},
             sel["oracle_dv_by_point"]),
        ]
        for arm_name, spec, dvs in base_arms:
            unit = f"val_{cid}_{arm_name}"
            if unit in done:
                continue
            pending[unit] = pool.submit(task_std_arm_iter, cid, arm_name, spec, None, "val",
                                        val_ks, std_max_steps, dvs,
                                        str(run_dir / "rows" / f"{unit}.csv"))
        for arm in subst_arms:
            for s in range(n_seeds):
                unit = f"val_{cid}_{arm}_s{s}"
                if unit in done:
                    continue
                inj = {"kind": "ensemble_het", "arm": arm,
                       "paths": [str(run_dir / "models" / f"{cid}_{arm}_s{s}_m{m}.pt")
                                 for m in range(n_members)]}
                spec = dict(sel["best_seeker"]["spec"], name=f"injected_{arm}_s{s}")
                pending[unit] = pool.submit(task_iter_arm, cid, f"{arm}_s{s}", spec, inj, "val",
                                            val_ks, std_max_steps,
                                            str(run_dir / "rows" / f"val_{cid}_{arm}_s{s}.csv"))
    for unit, fut in pending.items():
        mark_done(unit, fut.result())
        flush_partial()
    pool.shutdown()

    # ---------------------------------------------------- [5/5] adjudication
    print("[5/5] adjudication", flush=True)
    n_val = len(wp1.mu_grid()) * len(val_ks)
    wilson = wp1.MODS["wp0"].wilson_ci
    newcombe = wp1.MODS["wp0"].newcombe_diff_ci
    cells_out: dict[str, Any] = {}
    primary_pass_cells = []
    l0_pass_cells = []
    for cid in cells:
        floor_seeker = done[f"val_{cid}_floor_seeker"]
        floor_fixed = done[f"val_{cid}_floor_fixed"]
        oracle = done[f"val_{cid}_oracle"]
        floor = floor_seeker if floor_seeker["success"] >= floor_fixed["success"] else floor_fixed
        floor_name = (selection[cid]["best_seeker"]["name"] if floor is floor_seeker
                      else selection[cid]["best_fixed"]["name"])
        prize = oracle["success"] - floor["success"]
        cell_out: dict[str, Any] = {
            "floor": {"arm": floor_name, "success_val": floor["success"],
                      "wilson95": wilson(floor["success"], n_val),
                      "candidates": {"seeker": floor_seeker["success"],
                                     "fixed": floor_fixed["success"]}},
            "oracle": {"success_val": oracle["success"],
                       "wilson95": wilson(oracle["success"], n_val),
                       "dv_by_point": selection[cid]["oracle_dv_by_point"]},
            "prize_matched_remeasured": round(prize, 4),
            "prize_ci95_newcombe": newcombe(oracle["success"], n_val, floor["success"], n_val),
            "arms": {},
        }
        floor_eps = floor["episode_success"]
        for arm in subst_arms:
            arm_eps = {s: done[f"val_{cid}_{arm}_s{s}"]["episode_success"] for s in range(n_seeds)}
            stats = wp1.two_way_diff_stats(arm_eps, floor_eps)
            succ = float(np.mean([done[f"val_{cid}_{arm}_s{s}"]["success"] for s in range(n_seeds)]))
            recapture = (stats["delta"] / prize) if prize > 0 else None
            cell_pass = bool(prize > 0 and recapture is not None
                             and recapture >= wp1.RECAPTURE_BAR
                             and stats["lower_975_one_sided"] > 0)
            cell_out["arms"][arm] = {
                "success_val_mean_over_seeds": round(succ, 4),
                "per_seed_success": [done[f"val_{cid}_{arm}_s{s}"]["success"] for s in range(n_seeds)],
                "diff_vs_floor": stats,
                "recapture_fraction": (round(recapture, 4) if recapture is not None else None),
                "cell_pass_recapture_and_ci": cell_pass,
                "injection_fired_fraction": round(float(np.mean(
                    [done[f"val_{cid}_{arm}_s{s}"]["injection_fired_fraction"] or 0.0
                     for s in range(n_seeds)])), 4),
                "fallback_at_reveal_fraction": round(float(np.mean(
                    [done[f"val_{cid}_{arm}_s{s}"]["fallback_at_reveal_fraction"]
                     for s in range(n_seeds)])), 4),
                "conf_fraction_mean": round(float(np.mean(
                    [done[f"val_{cid}_{arm}_s{s}"]["conf_fraction_mean"] for s in range(n_seeds)])), 4),
                "mu_injected_abs_err_mean": (lambda errs: round(float(np.mean(errs)), 4) if errs else None)(
                    [done[f"val_{cid}_{arm}_s{s}"]["mu_injected_abs_err_mean"] for s in range(n_seeds)
                     if done[f"val_{cid}_{arm}_s{s}"]["mu_injected_abs_err_mean"] is not None]),
            }
            if arm == PRIMARY_ARM and cell_pass:
                primary_pass_cells.append(cid)
            if arm == "L0_frame" and cell_pass:
                l0_pass_cells.append(cid)
        cells_out[cid] = cell_out
        # descriptive M3216 comparison (different episode population, never gated)
        ref = m3216.get("validation", {}).get("cells", {}).get(cid)
        if ref is not None:
            payload["m3216_comparison"][cid] = {
                "m3216": {"floor": ref["floor"]["success_val"],
                          "oracle": ref["oracle"]["success_val"],
                          "prize": ref["prize_matched_remeasured"],
                          "l3_delta": ref["arms"]["L3_GRU"]["diff_vs_floor"]["delta"],
                          "l3_lo975": ref["arms"]["L3_GRU"]["diff_vs_floor"]["lower_975_one_sided"],
                          "l3_recapture": ref["arms"]["L3_GRU"]["recapture_fraction"]},
                "iter1": {"floor": floor["success"], "oracle": oracle["success"],
                          "prize": round(prize, 4),
                          "l3_delta": cell_out["arms"][PRIMARY_ARM]["diff_vs_floor"]["delta"],
                          "l3_lo975": cell_out["arms"][PRIMARY_ARM]["diff_vs_floor"]["lower_975_one_sided"],
                          "l3_recapture": cell_out["arms"][PRIMARY_ARM]["recapture_fraction"]},
            }
    payload["validation"]["n_val_episodes_per_arm_per_cell"] = n_val
    payload["validation"]["cells"] = cells_out

    primary_pass = len(primary_pass_cells) >= wp1.PRIMARY_CELLS_REQUIRED
    if primary_pass:
        route = "wp1_iter1_primary_pass_g_b_opens_wp2"
    else:
        route = ("wp1_iter1_fail_terminal_bound_accepted: C2 = mu belief is learnable from "
                 "history (M3216 estimator-level R^2 0.91-0.99) but NOT redeemable through "
                 "this substitution interface at the pre-registered recapture bar; no further "
                 "iteration is pre-authorized")
    if len(l0_pass_cells) >= wp1.PRIMARY_CELLS_REQUIRED:
        route += " | l0_succeeds_leak_audit_interpretation_claims_scoped_down"
    payload["verdicts"] = {
        "primary_arm": PRIMARY_ARM,
        "primary_rule": (f"recapture >= {wp1.RECAPTURE_BAR} of the re-measured matched prize in >= "
                         f"{wp1.PRIMARY_CELLS_REQUIRED} eligible cells, each with one-sided 97.5% "
                         "lower bound of the episode-paired (arm - floor) difference > 0 "
                         "(two-way episode + seed-cluster SE) -- UNCHANGED from wp1_prereg.json"),
        "primary_pass_cells": primary_pass_cells,
        "primary_verdict": ("PASS" if primary_pass else "FAIL"),
        "l0_pass_cells": l0_pass_cells,
        "route": route,
        "terminal": True,
        "dataset_gate": payload["data"]["dataset_gate_pass_all_cells"],
    }
    payload["status"] = "completed"
    payload["artifacts"] = {
        "summary_json": str(run_dir / "summary.json"),
        "progress_jsonl": str(progress_path),
        "rows_dir": str(run_dir / "rows"),
        "models_dir": str(run_dir / "models"),
        "iteration_preregistration_json": str(ITER_PREREG_JSON),
        "criteria_preregistration_json": str(BASE_PREREG_JSON),
    }
    flush_partial(final=True)
    print(f"results -> {run_dir / 'summary.json'}", flush=True)
    print("HEADLINE: primary=" + payload["verdicts"]["primary_verdict"]
          + f" cells={primary_pass_cells} route={route[:80]}..."
          + f" | elapsed {payload['elapsed_s']}s", flush=True)


if __name__ == "__main__":
    main()
