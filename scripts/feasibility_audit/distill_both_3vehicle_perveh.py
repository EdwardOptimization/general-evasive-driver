r"""PER-VEHICLE-AVOID-HEAD variant of distill_both_3vehicle_conditioned: dedicate ONE avoid
head PER VEHICLE so each head serves only its own safe-entry-speed budget (no cross-vehicle
pooling on the avoid heads -> the shared-avoid-head INTERFERENCE is removed).

WHY (the S2/conditioning finding this resolves):
  * S2 vehicle-AGNOSTIC obs72 driver: DRIFT generalizes (Sedan/UAZBUS/BMW = 1.00/1.00/0.85,
    at baseline) but AVOID collapses on every vehicle (0.10/0.25/0.05 vs 1.00/1.00/1.00),
    because the 3 vehicles' entry-speed budgets conflict and one shared avoid head cannot
    serve all 3 at once.
  * S2 + vehicle ONE-HOT (distill_both_3vehicle_conditioned, obs72 -> obs75): recovered ONLY
    Sedan (0.975) -- UAZBUS/BMW still collapsed, and the agg/tie-break selection was Sedan-
    biased. CONCLUSION: the bottleneck is shared-avoid-head INTERFERENCE, not the missing
    vehicle id; adding the id is necessary (to ROUTE) but the single shared head still cannot
    fit 3 conflicting budgets.

THE FIX UNDER TEST: ONE shared trunk + the regime gate (drift vs avoid, learned from the
conditioned obs) + ONE shared DRIFT head (drift is vehicle-general -- confirmed S2:
1.0/1.0/0.85) + THREE avoid heads (one per vehicle), where WITHIN avoid the vehicle one-hot
HARD-ROUTES to avoid_head[sedan|uazbus|bmw]. Because the one-hot is a hard selector (exactly
one 1.0), each vehicle's avoid demos produce gradient ONLY on its own avoid head -> the other
two avoid heads receive zero gradient -> NO cross-vehicle pooling on the avoid heads -> NO
interference. The drift demos from all 3 vehicles train the ONE shared drift head; the trunk
and the regime gate are shared and see everything.

  mean = g(h) * drift_head(h) + (1-g(h)) * sum_v onehot[v] * avoid_head[v](h)
         \_____ drift, shared _/             \____ avoid, routed by the vehicle one-hot ____/

KEY VERDICT: do ALL 3 vehicles' AVOID now recover toward their ~1.0 baseline (each head
serving its own budget -> interference removed)? Drift must stay ~1.0/1.0/0.85 (shared head).
If all 3 recover: the PRACTICAL cross-vehicle-general driver is DELIVERED (one network, drift
shared-general + avoid per-vehicle). If a vehicle stays low, say which + why. No recovery
claim without the honest per-(vehicle, regime) Chrono numbers.

WHAT THIS CHANGES vs distill_both_3vehicle_conditioned (NEW FILE ONLY; reuses the conditioned
machinery + the per-vehicle teacher/oracle patch modules VERBATIM; no protected module is
modified):
  1. Demo collection + the obs72 -> obs75 one-hot append + pooling are IDENTICAL (reused from
     distill_both_3vehicle_conditioned / distill_both_3vehicle, verbatim).
  2. The student is a NEW PerVehicleAvoidActorCritic (obs75): shared trunk + regime gate +
     ONE drift head + THREE avoid heads routed by obs75[72:75] (the one-hot). It exposes the
     SAME deployment interface as f2.AsymmetricActorCritic (.actor, .actor_gate, .actor_forward,
     .act, .actor_parameters) so the conditioned Chrono eval/select/A5 helpers run unchanged.
  3. BC-distill: drift frames train trunk+gate+drift_head; avoid frames train trunk+gate and
     ONLY the routed avoid head (the one-hot zeroes the other two heads' contribution -> zero
     gradient on them). Same pooled per-regime sample weighting + best-on-both-holdouts ckpt.
  4. 3-seed sweep, SELECT on the WORST-vehicle avoid (min over the 3 vehicles), then worst
     drift, then aggregate (the conditioning run's bug was selecting on agg -> Sedan-biased).
  5. Per-(vehicle, regime) A5 validation on Chrono with the correct one-hot per vehicle (the
     conditioned validator, reused verbatim). Save distill_3vehicle_perveh_policy.pt.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_3vehicle_perveh.py \
        --workers 16 --drift-seeds 8 --avoid-seeds-per-cell 2 --epochs 4000 \
        --seed-sweep 3 \
        --out runs/feasibility_audit/phase4_f2/distill_3vehicle_perveh_policy.pt
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import phase4_f2_train as f2  # noqa: E402
import distill_both as db  # noqa: E402  (recipe machinery, imported VERBATIM)
import distill_both_uazbus as uaz  # noqa: E402  (UAZBUS patches + ResilientChronoClient)
import distill_both_bmw as bmw  # noqa: E402  (BMW patches)
import distill_both_3vehicle as d3v  # noqa: E402  (unconditioned collection machinery, VERBATIM)
import distill_both_3vehicle_conditioned as cond  # noqa: E402  (one-hot append + eval/select/A5, VERBATIM)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_3vehicle_perveh_policy.pt"

ResilientChronoClient = uaz.ResilientChronoClient

# Reuse the FROZEN contract from the conditioned script (one-hot order, dims, append helper).
VEHICLES = cond.VEHICLES                 # ("sedan", "uazbus", "bmw")
ONEHOT_DIM = cond.ONEHOT_DIM             # 3
COND_OBS_DIM = cond.COND_OBS_DIM         # 75
OBS72_DIM = f2.HUMAN_VIEW_OBS_DIM        # 72  (the one-hot occupies obs75[72:75])
_vehicle_onehot = cond._vehicle_onehot
_append_onehot = cond._append_onehot


# =====================================================================================
# Per-vehicle-avoid-head model. Mirrors f2.AsymmetricActorCritic's gated trunk + the
# deployment interface (.actor, .actor_gate, .actor_forward, .act, .actor_parameters)
# so the CONDITIONED Chrono eval/select/A5 helpers (cond._conditioned_task_eval, etc.)
# run on it UNCHANGED. The only difference from the gated dual-head model is that the
# "avoid" branch is THREE heads routed by the vehicle one-hot (obs75[72:75]) instead of
# one shared head -- so each vehicle's avoid demos train ONLY its own avoid head.
# =====================================================================================


class PerVehicleAvoidActorCritic(nn.Module):
    """obs75 actor with a shared trunk, a learned regime gate, ONE shared drift head, and
    THREE avoid heads routed by the vehicle one-hot.

      h    = trunk(obs75)                                   # shared, sees everything
      g    = sigmoid(gate(h)) in [0,1]                      # regime gate: 1=>drift, 0=>avoid
      a_v  = sum_v onehot[v] * avoid_head[v](h)             # avoid, HARD-routed by the one-hot
      mean = tanh( g*drift_head(h) + (1-g)*a_v )

    Because onehot is a hard selector, an avoid frame for vehicle v has gradient ONLY through
    avoid_head[v] (the other two heads are multiplied by 0). Drift frames have gradient only
    through drift_head. trunk + gate are shared. The critic mirrors f2's privileged critic so
    the saved interface is the same; the critic is unused here (BC-only distillation)."""

    def __init__(self, obs_dim: int = COND_OBS_DIM, act_dim: int = f2.ACT_DIM, *,
                 priv_dim: int = f2.PRIV_DIM, hidden_size: int = f2.HIDDEN_SIZE,
                 vehicles: tuple[str, ...] = VEHICLES, onehot_dim: int = ONEHOT_DIM):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.act_dim = int(act_dim)
        self.priv_dim = int(priv_dim)
        self.vehicles = tuple(vehicles)
        self.onehot_dim = int(onehot_dim)
        self.gated = True  # interface parity with f2.AsymmetricActorCritic
        # shared trunk (identical shape to f2.AsymmetricActorCritic.actor)
        self.actor = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
        )
        # regime gate (drift vs avoid) from the shared trunk -- same as the gated model's gate.
        self.actor_gate = nn.Linear(hidden_size, 1)
        # ONE shared drift head (drift is vehicle-general).
        self.drift_head = nn.Linear(hidden_size, act_dim)
        # THREE avoid heads, one per vehicle (ModuleList indexed by VEHICLES order).
        self.avoid_heads = nn.ModuleList([nn.Linear(hidden_size, act_dim) for _ in self.vehicles])
        # learnable per-action log_std (parity with f2).
        self.log_std = nn.Parameter(torch.full((act_dim,), float(f2.LOG_STD_INIT)))
        # privileged critic (parity; unused in BC distillation).
        self.critic = nn.Sequential(
            nn.Linear(obs_dim + priv_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1),
        )

    def actor_parameters(self):
        params = list(self.actor.parameters()) + list(self.actor_gate.parameters()) \
            + list(self.drift_head.parameters())
        for head in self.avoid_heads:
            params += list(head.parameters())
        params += [self.log_std]
        return params

    def critic_parameters(self):
        return list(self.critic.parameters())

    def _onehot_of(self, obs75: torch.Tensor) -> torch.Tensor:
        """Slice the vehicle one-hot out of obs75 (the FROZEN last `onehot_dim` channels)."""
        return obs75[..., OBS72_DIM:OBS72_DIM + self.onehot_dim]

    def _raw_mean(self, obs75: torch.Tensor) -> torch.Tensor:
        if obs75.shape[-1] != self.obs_dim:
            raise ValueError(f"actor input must be obs{self.obs_dim}; got {obs75.shape[-1]}")
        h = self.actor(obs75)
        g = torch.sigmoid(self.actor_gate(h))               # (N,1): 1=>drift, 0=>avoid
        drift_mean = self.drift_head(h)                      # (N, act)
        oh = self._onehot_of(obs75)                          # (N, V)
        # stack the 3 avoid heads -> (N, V, act); weight by the one-hot -> hard route -> (N, act)
        avoid_stack = torch.stack([head(h) for head in self.avoid_heads], dim=-2)  # (N, V, act)
        avoid_mean = (oh.unsqueeze(-1) * avoid_stack).sum(dim=-2)                   # (N, act)
        return g * drift_mean + (1.0 - g) * avoid_mean

    def actor_forward(self, obs75: torch.Tensor) -> torch.Tensor:
        """Squashed deterministic action mean from obs75 (deployment map). Same as f2's."""
        return torch.tanh(self._raw_mean(obs75))

    @torch.no_grad()
    def act(self, obs75: np.ndarray) -> np.ndarray:
        """Deterministic deployable action from obs75 ONLY (policy mean). No priv path."""
        arr = np.asarray(obs75, dtype=np.float32)
        single = arr.ndim == 1
        batch = arr.reshape(1, -1) if single else arr
        out = self.actor_forward(torch.as_tensor(batch, dtype=torch.float32)).cpu().numpy().astype(np.float32)
        return out[0] if single else out


# =====================================================================================
# Per-vehicle-avoid-head distillation. A VERBATIM copy of cond._distill_conditioned, but the
# student is PerVehicleAvoidActorCritic. The loss is identical (pooled drift+avoid frames, the
# 0.5/n per-regime sample weighting, best-on-both-holdouts ckpt); the per-vehicle routing is a
# property of the MODEL (the one-hot hard-selects the avoid head), so the BC objective does not
# change -- the avoid frames for vehicle v simply have zero gradient on the other vehicles' heads.
# =====================================================================================


def _distill_perveh(drift_demo: dict, avoid_demo: dict, *, epochs: int, lr: float, batch: int,
                    holdout_frac: float, seed: int) -> tuple[PerVehicleAvoidActorCritic, dict]:
    torch.manual_seed(f2._seed_for("distill_init", seed))
    np.random.seed(f2._seed_for("distill_np", seed) % (2**32))

    (dtr_o, dtr_a), (dho_o, dho_a) = db._holdout_split(drift_demo["obs"], drift_demo["act"], frac=holdout_frac, seed=seed + 1)
    (atr_o, atr_a), (aho_o, aho_a) = db._holdout_split(avoid_demo["obs"], avoid_demo["act"], frac=holdout_frac, seed=seed + 2)

    train_o = np.concatenate([dtr_o, atr_o], 0).astype(np.float32)
    train_a = np.concatenate([dtr_a, atr_a], 0).astype(np.float32)
    train_reg = np.concatenate([np.ones(len(dtr_o), np.int64), np.zeros(len(atr_o), np.int64)], 0)  # 1=drift 0=avoid

    print(f"  distill train: {len(dtr_o)} drift + {len(atr_o)} avoid frames (obs{train_o.shape[1]}); "
          f"holdout: {len(dho_o)} drift + {len(aho_o)} avoid", flush=True)

    model = PerVehicleAvoidActorCritic(obs_dim=COND_OBS_DIM)  # FRESH per-vehicle-avoid-head student
    opt = Adam(model.actor_parameters(), lr=lr)

    obs_t = torch.as_tensor(train_o, dtype=torch.float32)
    act_t = torch.clamp(torch.as_tensor(train_a, dtype=torch.float32), -1.0, 1.0)
    reg_t = torch.as_tensor(train_reg, dtype=torch.long)
    n_d = max(1, int((reg_t == 1).sum())); n_a = max(1, int((reg_t == 0).sum()))
    w = torch.where(reg_t == 1, 0.5 / n_d, 0.5 / n_a).float()
    w = w / w.sum() * len(w)

    dho_o_t = torch.as_tensor(dho_o, dtype=torch.float32)
    dho_a_t = torch.clamp(torch.as_tensor(dho_a, dtype=torch.float32), -1.0, 1.0)
    aho_o_t = torch.as_tensor(aho_o, dtype=torch.float32)
    aho_a_t = torch.clamp(torch.as_tensor(aho_a, dtype=torch.float32), -1.0, 1.0)

    # per-vehicle avoid holdout split (diagnostic: each head's own-budget fit)
    aho_oh = aho_o_t[:, OBS72_DIM:OBS72_DIM + ONEHOT_DIM]
    veh_idx = aho_oh.argmax(dim=-1)

    n = obs_t.shape[0]
    rng = np.random.default_rng(f2._seed_for("distill_mb", seed))
    t0 = time.time()
    best_combined = float("inf")
    best_state = None
    for ep in range(int(epochs)):
        order = rng.permutation(n)
        if batch <= 0 or batch >= n:
            mbs = [order]
        else:
            mbs = [order[s:s + batch] for s in range(0, n, batch)]
        for mb in mbs:
            idx = torch.as_tensor(mb, dtype=torch.long)
            mean = model.actor_forward(obs_t[idx])
            err = (mean - act_t[idx]).pow(2).mean(dim=-1)
            loss = (w[idx] * err).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.actor_parameters(), 1.0)
            opt.step()
        if ep % max(1, epochs // 20) == 0 or ep == epochs - 1:
            with torch.no_grad():
                d_mse = float((model.actor_forward(dho_o_t) - dho_a_t).pow(2).mean())
                a_mse = float((model.actor_forward(aho_o_t) - aho_a_t).pow(2).mean())
            combined = d_mse + a_mse
            if combined < best_combined:
                best_combined = combined
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            if ep % max(1, epochs // 10) == 0 or ep == epochs - 1:
                # per-vehicle avoid holdout MSE: confirm each head fits its own budget
                with torch.no_grad():
                    pred_a = model.actor_forward(aho_o_t)
                    per_v = {}
                    for vi, name in enumerate(VEHICLES):
                        m = (veh_idx == vi)
                        per_v[name] = float((pred_a[m] - aho_a_t[m]).pow(2).mean()) if int(m.sum()) else float("nan")
                pv = "  ".join(f"{nm}={per_v[nm]:.2e}" for nm in VEHICLES)
                print(f"    ep {ep:5d}  drift_holdout_MSE={d_mse:.2e}  avoid_holdout_MSE={a_mse:.2e}  "
                      f"[per-veh avoid MSE: {pv}]", flush=True)
    if best_state is not None:
        model.load_state_dict(best_state)

    with torch.no_grad():
        d_mse = float((model.actor_forward(dho_o_t) - dho_a_t).pow(2).mean())
        a_mse = float((model.actor_forward(aho_o_t) - aho_a_t).pow(2).mean())

        def _gate(obs):
            h = model.actor(obs)
            return torch.sigmoid(model.actor_gate(h)).squeeze(-1)
        g_drift = float(_gate(dho_o_t).mean())
        g_avoid = float(_gate(aho_o_t).mean())
        pred_a = model.actor_forward(aho_o_t)
        per_v_avoid_mse = {}
        for vi, name in enumerate(VEHICLES):
            m = (veh_idx == vi)
            per_v_avoid_mse[name] = float((pred_a[m] - aho_a_t[m]).pow(2).mean()) if int(m.sum()) else float("nan")
    print(f"  distillation done in {time.time()-t0:.1f}s  "
          f"drift_holdout_MSE={d_mse:.3e}  avoid_holdout_MSE={a_mse:.3e}", flush=True)
    print(f"  per-vehicle avoid holdout MSE (each head, own budget): "
          + "  ".join(f"{nm}={per_v_avoid_mse[nm]:.3e}" for nm in VEHICLES), flush=True)
    print(f"  gate routing (mean sigmoid; 1=>drift_head, 0=>avoid_heads): "
          f"drift={g_drift:.3f}  avoid={g_avoid:.3f}  |separation|={abs(g_drift-g_avoid):.3f}", flush=True)
    return model, {
        "drift_holdout_mse": d_mse, "avoid_holdout_mse": a_mse,
        "per_vehicle_avoid_holdout_mse": per_v_avoid_mse,
        "gate_mean_drift": g_drift, "gate_mean_avoid": g_avoid,
        "n_train_drift": int(len(dtr_o)), "n_train_avoid": int(len(atr_o)),
        "n_holdout_drift": int(len(dho_o)), "n_holdout_avoid": int(len(aho_o)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="PER-VEHICLE-AVOID-HEAD 3-vehicle do-both driver (obs75; 1 drift head + 3 avoid heads).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds", type=int, default=8, help="drift demo seeds PER difficulty PER vehicle")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="avoid demo seeds per reveal x mu cell PER vehicle")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=3)
    ap.add_argument("--select-avoid-units", type=int, default=8, help="select avoid episodes PER vehicle")
    ap.add_argument("--select-drift-units", type=int, default=5, help="select drift episodes PER vehicle")
    ap.add_argument("--a5-avoid-units", type=int, default=40, help="A5 avoid validation episodes PER vehicle")
    ap.add_argument("--a5-drift-units", type=int, default=20, help="A5 drift validation episodes PER vehicle")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    print(f"[3vehicle-perveh] pooling demos from {VEHICLES} into ONE network: shared trunk + regime "
          f"gate + ONE drift head + THREE avoid heads (obs{COND_OBS_DIM}). The vehicle one-hot HARD-"
          f"ROUTES the avoid branch -> each vehicle's avoid demos train ONLY its own avoid head "
          f"(no cross-vehicle interference).", flush=True)
    print(f"  one-hot order (FROZEN): {[(v, list(_vehicle_onehot(v))) for v in VEHICLES]}", flush=True)

    clients = [ResilientChronoClient(stderr_log=RUN_DIR / f"distill3vp_w{w}_stderr.log")
               for w in range(args.workers)]
    report: dict[str, Any] = {
        "vehicles": list(VEHICLES), "onehot_dim": ONEHOT_DIM, "cond_obs_dim": COND_OBS_DIM,
        "architecture": "shared_trunk + regime_gate + 1_drift_head + 3_avoid_heads(routed_by_onehot)",
        "baselines": {"sedan": {"drift": 1.0, "avoid": 1.0}, "uazbus": {"drift": 1.0, "avoid": 1.0},
                      "bmw": {"drift": 0.85, "avoid": 1.0}},
        "s2_unconditioned_a5": {"sedan": {"drift": 1.0, "avoid": 0.10}, "uazbus": {"drift": 1.0, "avoid": 0.25},
                                "bmw": {"drift": 0.85, "avoid": 0.05}},
        "conditioned_onehot_a5": {"sedan": {"avoid": 0.975}, "uazbus": {"avoid": "collapsed"},
                                  "bmw": {"avoid": "collapsed"}}}
    t0 = time.time()
    pooled = None
    best = None  # (score, state_dict, stats, seed, sel)
    try:
        # ---- 1. collect demos PER vehicle (VERBATIM from distill_both_3vehicle) ----
        per_vehicle_demos: dict[str, Any] = {}
        for name in VEHICLES:
            print(f"\n################### COLLECTING {name.upper()} DEMOS ###################", flush=True)
            per_vehicle_demos[name] = d3v._collect_vehicle_demos(
                name, clients, drift_seeds=args.drift_seeds, avoid_seeds_per_cell=args.avoid_seeds_per_cell)

        # ---- 2. APPEND per-vehicle one-hot (obs72 -> obs75), then POOL (VERBATIM) ----
        drift_obs = np.concatenate([_append_onehot(per_vehicle_demos[v]["drift"]["obs"], v) for v in VEHICLES], 0)
        drift_act = np.concatenate([per_vehicle_demos[v]["drift"]["act"] for v in VEHICLES], 0)
        avoid_obs = np.concatenate([_append_onehot(per_vehicle_demos[v]["avoid"]["obs"], v) for v in VEHICLES], 0)
        avoid_act = np.concatenate([per_vehicle_demos[v]["avoid"]["act"] for v in VEHICLES], 0)
        assert drift_obs.shape[1] == COND_OBS_DIM and avoid_obs.shape[1] == COND_OBS_DIM, \
            f"conditioned obs dim mismatch: {drift_obs.shape[1]}/{avoid_obs.shape[1]} != {COND_OBS_DIM}"
        drift_demo = {"obs": drift_obs, "act": drift_act,
                      "n_episodes": sum(per_vehicle_demos[v]["drift"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["drift"]["n_success"] for v in VEHICLES)}
        avoid_demo = {"obs": avoid_obs, "act": avoid_act,
                      "n_episodes": sum(per_vehicle_demos[v]["avoid"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["avoid"]["n_success"] for v in VEHICLES)}
        pooled = {"drift": drift_demo, "avoid": avoid_demo}
        report["pooled_demo"] = {
            "drift_frames": int(drift_obs.shape[0]), "avoid_frames": int(avoid_obs.shape[0]),
            "cond_obs_dim": int(drift_obs.shape[1]),
            "per_vehicle": {v: {
                "drift_frames": int(per_vehicle_demos[v]["drift"]["obs"].shape[0]),
                "drift_teacher_success": int(per_vehicle_demos[v]["drift"]["n_success"]),
                "drift_episodes": int(per_vehicle_demos[v]["drift"]["n_episodes"]),
                "avoid_frames": int(per_vehicle_demos[v]["avoid"]["obs"].shape[0]),
                "avoid_teacher_success": int(per_vehicle_demos[v]["avoid"]["n_success"]),
                "avoid_episodes": int(per_vehicle_demos[v]["avoid"]["n_episodes"]),
                "onehot": list(_vehicle_onehot(v)),
            } for v in VEHICLES}}
        report["scenario_verification"] = {v: per_vehicle_demos[v]["verify"] for v in VEHICLES}
        print(f"\nPOOLED demos: {drift_obs.shape[0]} drift + {avoid_obs.shape[0]} avoid frames "
              f"(obs{drift_obs.shape[1]}, from 3 vehicles WITH one-hot; avoid frames route per vehicle)", flush=True)
        for v in VEHICLES:
            print(f"   {v:7s} oh={list(_vehicle_onehot(v))}: "
                  f"drift {per_vehicle_demos[v]['drift']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['drift']['n_success']}/{per_vehicle_demos[v]['drift']['n_episodes']} succ) | "
                  f"avoid {per_vehicle_demos[v]['avoid']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['avoid']['n_success']}/{per_vehicle_demos[v]['avoid']['n_episodes']} succ) "
                  f"-> avoid_head[{v}]", flush=True)

        # ---- 3. build the pooled (per-vehicle-tagged) Chrono select set (VERBATIM from cond) ----
        select_items = cond._pooled_select_items(int(args.select_avoid_units), int(args.select_drift_units))

        # ---- 4. distill N seeds on the POOLED demos; select by WORST-vehicle avoid Chrono task score ----
        per_seed = []
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- 3vehicle PER-VEHICLE-AVOID-HEAD distill seed {s} ---", flush=True)
            m, st = _distill_perveh(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                                    holdout_frac=args.holdout_frac, seed=s)
            sel = cond._pooled_conditioned_select(clients, m, select_items)
            agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
            worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
            print(f"  seed {s} POOLED SELECT: avoid agg={agg_av:.3f} (WORST {worst_av:.3f}) "
                  f"drift agg={agg_dr:.3f} (worst {worst_dr:.3f})", flush=True)
            st["select_avoid"] = agg_av; st["select_drift"] = agg_dr
            st["select_worst_avoid"] = worst_av; st["select_worst_drift"] = worst_dr
            st["select_per_vehicle"] = sel["per_vehicle"]; st["distill_seed"] = s
            per_seed.append({"seed": s, "select_avoid": agg_av, "select_drift": agg_dr,
                             "worst_avoid": worst_av, "worst_drift": worst_dr,
                             "per_vehicle": sel["per_vehicle"],
                             "drift_holdout_mse": st["drift_holdout_mse"], "avoid_holdout_mse": st["avoid_holdout_mse"],
                             "per_vehicle_avoid_holdout_mse": st["per_vehicle_avoid_holdout_mse"]})
            # SELECTION OBJECTIVE: maximise the WORST-vehicle avoid (the generality bottleneck) FIRST,
            # then worst-vehicle drift, then aggregate avoid, then aggregate drift. (The conditioning
            # run's bug was selecting on the AGGREGATE, which favoured Sedan; we select on the min.)
            score = (worst_av, worst_dr, agg_av, agg_dr)
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
        report["distill_per_seed"] = per_seed

        model = PerVehicleAvoidActorCritic(obs_dim=COND_OBS_DIM)
        model.load_state_dict(best[1])
        stats = best[2]
        print(f"\nSELECTED seed {best[3]} on WORST-vehicle avoid "
              f"(pooled select avoid agg={stats['select_avoid']:.3f} drift agg={stats['select_drift']:.3f} | "
              f"WORST avoid={stats['select_worst_avoid']:.3f} worst drift={stats['select_worst_drift']:.3f})", flush=True)
        report["distill_selected"] = {
            "seed": int(best[3]), "select_avoid": float(stats["select_avoid"]),
            "select_drift": float(stats["select_drift"]),
            "select_worst_avoid": float(stats["select_worst_avoid"]),
            "select_worst_drift": float(stats["select_worst_drift"]),
            "selection_objective": "max worst-vehicle avoid (min over 3), then worst drift, then agg avoid, then agg drift",
            "per_vehicle": stats["select_per_vehicle"]}

        # ---- 5. save the policy BEFORE the (longer) A5 validation, so a crash can't lose it ----
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_stats = {k: v for k, v in stats.items() if k != "select_per_vehicle"}
        torch.save({
            "state_dict": model.state_dict(), "gated": True,
            "model_class": "PerVehicleAvoidActorCritic",
            "obs_dim": COND_OBS_DIM, "onehot_dim": ONEHOT_DIM, "vehicle_order": list(VEHICLES),
            "label": "distill_both_3vehicle_perveh", "vehicles": list(VEHICLES),
            "architecture": "shared_trunk + regime_gate + 1_drift_head + 3_avoid_heads(routed_by_onehot)",
            "conditioning": "3way_vehicle_onehot_appended_obs72_to_obs75; avoid branch hard-routed per vehicle",
            "drift_teacher": "pooled_{sedan_gpu_expert, uazbus_feedback, bmw_feedback}",
            "avoid_teacher": "per_vehicle_{sedan_oracle, uazbus_oracle, bmw_rephys_oracle} -> own avoid head",
            "drift_demo_frames": int(pooled["drift"]["obs"].shape[0]),
            "avoid_demo_frames": int(pooled["avoid"]["obs"].shape[0]),
            "select_per_vehicle": stats["select_per_vehicle"],
            **save_stats,
        }, out)
        print(f"\nsaved PER-VEHICLE-AVOID-HEAD 3-vehicle distilled student -> {out}", flush=True)

        # ---- 6. per-(vehicle, regime) A5 validation on Chrono (correct one-hot per vehicle; VERBATIM) ----
        a5 = cond._validate_per_vehicle(clients, model, int(args.a5_avoid_units), int(args.a5_drift_units))
        report["a5_per_vehicle"] = {v: {k: a5[v][k] for k in ("avoid", "drift", "n_avoid", "n_drift", "variant", "mass")}
                                    for v in VEHICLES}
    finally:
        for c in clients:
            c.close()

    report["elapsed_s"] = round(time.time() - t0, 1)

    # ---- verdict: did the per-vehicle avoid heads recover avoid on all 3? ----
    base = report["baselines"]; s2 = report["s2_unconditioned_a5"]; a5p = report["a5_per_vehicle"]
    recovered = {v: bool(a5p[v]["avoid"] >= 0.80) for v in VEHICLES}
    improved = {v: bool(a5p[v]["avoid"] > s2[v]["avoid"] + 1e-9) for v in VEHICLES}
    near_baseline = {v: bool(a5p[v]["avoid"] >= base[v]["avoid"] - 0.10) for v in VEHICLES}
    drift_held = {v: bool(a5p[v]["drift"] >= base[v]["drift"] - 1e-9) for v in VEHICLES}
    all_recovered = all(recovered.values())
    any_improved = any(improved.values())
    report["verdict"] = {
        "avoid_recovered_per_vehicle": recovered,
        "avoid_improved_vs_s2_per_vehicle": improved,
        "avoid_near_baseline_per_vehicle": near_baseline,
        "drift_held_at_baseline_per_vehicle": drift_held,
        "ALL_avoid_recovered": all_recovered,
        "ANY_avoid_improved": any_improved,
        "key": ("YES -- PER-VEHICLE avoid heads RECOVER avoid on all 3 vehicles (each >= 0.80, each "
                "head serving its own entry-speed budget): the PRACTICAL cross-vehicle-general driver "
                "is DELIVERED (ONE network: drift shared-general + avoid per-vehicle). The bottleneck "
                "was shared-avoid-head INTERFERENCE, now removed by dedicating a head per vehicle."
                if all_recovered else
                ("PARTIAL -- per-vehicle heads recover avoid on at least one vehicle but NOT all 3 to "
                 ">= 0.80: name the laggard(s) and why (NOT interference, since each head is now "
                 "dedicated -- look to demo/oracle quality or drift-gate routing for that vehicle)."
                 if any_improved else
                 "NO -- avoid still collapses even with PER-VEHICLE avoid heads: a deeper finding "
                 "(the per-vehicle avoid failure is NOT shared-head interference).")),
    }

    report_path = RUN_DIR / "distill_3vehicle_perveh_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"saved report -> {report_path}", flush=True)

    # ---- consolidated, re-verifiable per-(vehicle, regime) table ----
    consolidated = {
        "experiment": "PER-VEHICLE-AVOID-HEAD 3-vehicle do-both driver (obs75; 1 drift head + 3 avoid heads)",
        "question": "Do PER-VEHICLE avoid heads (interference removed) recover avoid on all 3 vehicles?",
        "policy": str(args.out), "policy_label": "distill_both_3vehicle_perveh",
        "architecture": "shared_trunk + regime_gate + 1_drift_head + 3_avoid_heads(routed_by_onehot)",
        "obs_dim": COND_OBS_DIM, "onehot_order": list(VEHICLES),
        "selected_seed": int(best[3]),
        "selection_objective": "max WORST-vehicle avoid (min over 3 vehicles)",
        "pooled_demo_frames": {"drift": int(pooled["drift"]["obs"].shape[0]), "avoid": int(pooled["avoid"]["obs"].shape[0])},
        "distill_holdout_mse": {"drift": float(stats["drift_holdout_mse"]), "avoid": float(stats["avoid_holdout_mse"]),
                                "per_vehicle_avoid": stats["per_vehicle_avoid_holdout_mse"]},
        "a5_validation_units_per_vehicle": {"avoid": int(args.a5_avoid_units), "drift": int(args.a5_drift_units)},
        "per_vehicle_regime_chrono_PERVEH": {
            v: {"variant": a5p[v]["variant"], "mass": a5p[v]["mass"],
                "drift": round(float(a5p[v]["drift"]), 4), "avoid": round(float(a5p[v]["avoid"]), 4),
                "onehot_fed": list(_vehicle_onehot(v)),
                "drift_baseline": base[v]["drift"], "avoid_baseline": base[v]["avoid"],
                "s2_unconditioned_avoid": s2[v]["avoid"],
                "conditioned_1head_avoid": report["conditioned_onehot_a5"][v]["avoid"]}
            for v in VEHICLES},
        "verdict": report["verdict"]["key"],
    }
    cons_path = RUN_DIR / "a5_3vehicle_perveh_consolidated.json"
    cons_path.write_text(json.dumps(consolidated, indent=2, default=str), encoding="utf-8")
    print(f"saved consolidated table -> {cons_path}", flush=True)

    # ---- human-readable verdict ----
    print("\n" + "=" * 100, flush=True)
    print("=== PER-VEHICLE-AVOID-HEAD 3-VEHICLE DO-BOTH DRIVER: per-(vehicle, regime) Chrono ===", flush=True)
    print(f"{'vehicle':8s} | {'drift':>7s} (base) | {'avoid':>7s} (base) | {'avoid S2':>9s} | {'avoid 1head':>11s} | recovered?", flush=True)
    cond_a = report["conditioned_onehot_a5"]
    for v in VEHICLES:
        c1 = cond_a[v]["avoid"]
        c1s = f"{c1:.3f}" if isinstance(c1, (int, float)) else str(c1)
        print(f"{v:8s} | {a5p[v]['drift']:7.3f} ({base[v]['drift']:.2f}) | "
              f"{a5p[v]['avoid']:7.3f} ({base[v]['avoid']:.2f}) | {s2[v]['avoid']:9.3f} | {c1s:>11s} | "
              f"{'YES' if recovered[v] else ('improved' if improved[v] else 'no')}", flush=True)
    print("-" * 100, flush=True)
    print(f"KEY VERDICT: {report['verdict']['key']}", flush=True)
    print(f"  drift held at baseline (1.0/1.0/0.85): { {v: drift_held[v] for v in VEHICLES} }", flush=True)
    print("=" * 100, flush=True)


if __name__ == "__main__":
    main()
