r"""FiLM + DAgger variant of distill_both_3vehicle_perveh: throw BOTH indicated levers at the
cross-vehicle AVOID failure -- per-vehicle FiLM trunk-conditioning + DAgger on avoid.

WHY (the diagnosis from the 3 prior cross-vehicle-avoid attempts):
  * S2 vehicle-AGNOSTIC obs72 driver: DRIFT generalizes (Sedan/UAZBUS/BMW = 1.00/1.00/0.85)
    but AVOID collapses on every vehicle (0.10/0.25/0.05 vs 1.00/1.00/1.00 baselines) -- the
    3 vehicles' safe-entry-speed budgets conflict and one shared head/representation cannot
    serve all 3.
  * S2 + vehicle ONE-HOT (conditioned, obs75, 1 shared avoid head): recovered ONLY Sedan
    (0.975); UAZBUS/BMW still collapsed -> the missing id ROUTES but the shared avoid head
    still cannot fit 3 conflicting budgets.
  * S2 + one-hot + PER-VEHICLE avoid HEADS (perveh): Sedan 0.575 / UAZBUS 0.20 / BMW 0.85 --
    a private OUTPUT head per vehicle did NOT fix it (Sedan even REGRESSED). DIAGNOSIS (a):
    the SHARED TRUNK co-encoding 3 vehicles degrades each vehicle's avoid REPRESENTATION; a
    per-vehicle output head on top of a polluted shared representation is not enough.
  * AND DIAGNOSIS (b): avoid is CLOSED-LOOP-sensitive (the F2/G1' compound-error finding):
    low BC holdout MSE but Chrono collisions, because the student visits states the open-loop
    oracle demos never showed (the textbook BC distribution-shift failure).

THE TWO LEVERS UNDER TEST (both at once):
  1. PER-VEHICLE FiLM TRUNK CONDITIONING. The vehicle one-hot (obs75[72:75]) generates a
     per-vehicle (gamma, beta) for EACH shared-trunk hidden layer: h' = gamma*h + beta. The
     trunk WEIGHTS stay shared (so drift's vehicle-general structure is preserved) but each
     vehicle gets a TAILORED trunk REPRESENTATION -- not just a per-vehicle output. This is the
     new lever vs perveh (which only had per-vehicle output heads on ONE shared representation).
     We keep 1 shared drift head + 3 per-vehicle avoid heads (FiLM gives the per-vehicle
     representation; the per-vehicle avoid heads give the per-vehicle output on top of it).
  2. DAgger ON AVOID (per vehicle). After BC, roll the student out PER VEHICLE on real Chrono
     (install that vehicle's patches -> obs72 from the backend, append the vehicle one-hot,
     student.act; the OBSTACLE-REVEAL-POST states it actually visits), relabel each visited
     state with THAT vehicle's avoid ORACLE action, append to that vehicle's avoid demo pool
     (tagged with its one-hot), and re-BC (drift demos FROZEN). This closes the closed-loop
     compound-error gap on each vehicle's own state distribution.

SELECT on the WORST-vehicle avoid (min over the 3 vehicles), not the aggregate (the prior
conditioning run's bug was selecting on the aggregate -> Sedan-biased). Save
distill_3vehicle_film_policy.pt. Validate per-(vehicle, regime) on real Chrono feeding the
correct one-hot per vehicle (the conditioned validator, reused verbatim).

KEY VERDICT: do ALL 3 vehicles' avoid recover toward ~1.0 (FiLM gives per-vehicle
representation + DAgger closes the closed-loop gap)? Drift must stay ~1.0/1.0/0.85.
  * YES (all >= 0.80, ideally ~1.0): the ONE-network cross-vehicle-general driver is DELIVERED
    -- the strongest, most general driver (full spectrum + drift-general + avoid-recovered-via-
    FiLM).
  * NO: name which vehicle stays low + the honest conclusion that avoid is genuinely
    vehicle-specific (-> per-vehicle drivers are the practical strongest). No recovery claim
    without the honest per-(vehicle, regime) Chrono numbers.

WHAT THIS CHANGES vs distill_both_3vehicle_perveh (NEW FILE ONLY; reuses ALL the conditioned /
3vehicle / DAgger machinery VERBATIM; no protected module is modified):
  1. Demo collection + obs72 -> obs75 one-hot append + pooling: IDENTICAL (reused verbatim).
  2. The student is a NEW FiLMAvoidActorCritic (obs75): shared trunk with PER-LAYER FiLM
     conditioned on the one-hot + regime gate + 1 drift head + 3 per-vehicle avoid heads. It
     exposes the SAME deployment interface as f2.AsymmetricActorCritic (.actor, .actor_gate,
     .actor_forward, .act, .actor_parameters) so the conditioned Chrono eval/select/A5 helpers
     (cond._conditioned_task_eval / _pooled_conditioned_select / _validate_per_vehicle) run on
     it UNCHANGED.
  3. BC-distill the FiLM student (same pooled per-regime sample weighting + best-on-both-
     holdouts ckpt as the perveh/conditioned distill).
  4. THEN DAgger on avoid, per vehicle: roll the BC student out per vehicle on Chrono, relabel
     with that vehicle's avoid oracle, append per-vehicle one-hot-tagged recovery labels, re-BC
     (drift FROZEN). Iterate --dagger-rounds. (Reuses dagger_avoid's _dagger_episode /
     collect_dagger machinery verbatim, with the vehicle's patches installed so the oracle is
     the per-vehicle re-physicalized one, and the one-hot appended at act-time.)
  5. Per-(vehicle, regime) A5 validation on Chrono with the correct one-hot per vehicle
     (cond._validate_per_vehicle, reused verbatim). Save distill_3vehicle_film_policy.pt.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_3vehicle_film.py \
        --workers 16 --drift-seeds 8 --avoid-seeds-per-cell 2 --epochs 4000 \
        --seed-sweep 3 --dagger-rounds 2 --dagger-hard-cell-seeds 10 --dagger-easy-cell-seeds 2 \
        --out runs/feasibility_audit/phase4_f2/distill_3vehicle_film_policy.pt
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
import dagger_avoid as dag  # noqa: E402  (DAgger episode + oracle-relabel machinery, VERBATIM)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_3vehicle_film_policy.pt"

ResilientChronoClient = uaz.ResilientChronoClient

# Reuse the FROZEN contract from the conditioned script (one-hot order, dims, append helper).
VEHICLES = cond.VEHICLES                 # ("sedan", "uazbus", "bmw")
ONEHOT_DIM = cond.ONEHOT_DIM             # 3
COND_OBS_DIM = cond.COND_OBS_DIM         # 75
OBS72_DIM = f2.HUMAN_VIEW_OBS_DIM        # 72  (the one-hot occupies obs75[72:75])
_vehicle_onehot = cond._vehicle_onehot
_append_onehot = cond._append_onehot

# The avoid HARD cells (smallest reveal + lowest grip) where the closed-loop compound error
# shows up. DAgger pours most of its rollout budget here (per vehicle). dagger_avoid.py exposes
# HARD_REVEALS x HARD_MUS (the perveh hard set); we form the cross product here.
HARD_CELLS = tuple((float(r), float(m)) for r in dag.HARD_REVEALS for m in dag.HARD_MUS)


# =====================================================================================
# FiLM-conditioned model. Shared trunk whose hidden activations are FiLM-modulated by the
# vehicle one-hot (per-vehicle gamma, beta per hidden layer) -> each vehicle gets a TAILORED
# trunk REPRESENTATION while the trunk weights stay shared. Regime gate + 1 shared drift head
# + 3 per-vehicle avoid heads (routed by the one-hot). Mirrors the f2 deployment interface so
# the conditioned Chrono eval/select/A5 helpers run on it UNCHANGED.
# =====================================================================================


class FiLMAvoidActorCritic(nn.Module):
    """obs75 actor: shared trunk with PER-VEHICLE FiLM + regime gate + 1 drift head + 3 avoid heads.

      one-hot = obs75[72:75]                                    # the FROZEN vehicle id channels
      (g1,b1),(g2,b2) = FiLM(one-hot)                           # per-vehicle scale+shift per layer
      h1  = tanh( g1 * W1(obs75) + b1 )                         # FiLM-modulated layer-1 activations
      h   = tanh( g2 * W2(h1)    + b2 )                         # FiLM-modulated layer-2 activations
      gate= sigmoid(gate(h))  in [0,1]                          # regime gate: 1=>drift, 0=>avoid
      a_v = sum_v onehot[v] * avoid_head[v](h)                  # avoid, HARD-routed by the one-hot
      mean= tanh( gate*drift_head(h) + (1-gate)*a_v )

    The trunk LINEAR WEIGHTS (W1, W2) are SHARED across vehicles (preserving drift's vehicle-
    general structure); only the FiLM gamma/beta (a small linear: onehot[3] -> 2*hidden per
    layer) and the 3 avoid heads are per-vehicle. This gives AVOID a per-vehicle REPRESENTATION
    (the perveh fix only gave a per-vehicle OUTPUT on ONE shared representation). gamma is
    initialised to 1 and beta to 0 (FiLM-identity) so the FiLM student starts as the plain
    shared trunk and learns the per-vehicle modulation. The critic mirrors f2's privileged
    critic for interface parity; it is unused (BC-only distillation)."""

    def __init__(self, obs_dim: int = COND_OBS_DIM, act_dim: int = f2.ACT_DIM, *,
                 priv_dim: int = f2.PRIV_DIM, hidden_size: int = f2.HIDDEN_SIZE,
                 vehicles: tuple[str, ...] = VEHICLES, onehot_dim: int = ONEHOT_DIM):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.act_dim = int(act_dim)
        self.priv_dim = int(priv_dim)
        self.hidden_size = int(hidden_size)
        self.vehicles = tuple(vehicles)
        self.onehot_dim = int(onehot_dim)
        self.gated = True  # interface parity with f2.AsymmetricActorCritic

        # shared trunk linears (weights shared across vehicles; same shapes as f2's trunk).
        self.trunk_fc1 = nn.Linear(obs_dim, hidden_size)
        self.trunk_fc2 = nn.Linear(hidden_size, hidden_size)

        # FiLM generator: one-hot[V] -> per-layer (gamma, beta). One linear per layer; we init it
        # so that gamma=1, beta=0 at start (FiLM-identity: the FiLM trunk == the plain shared
        # trunk before any training, so the FiLM student is a strict generalisation of perveh).
        self.film1 = nn.Linear(onehot_dim, 2 * hidden_size)
        self.film2 = nn.Linear(onehot_dim, 2 * hidden_size)
        for film in (self.film1, self.film2):
            nn.init.zeros_(film.weight)
            with torch.no_grad():
                film.bias[:hidden_size] = 1.0   # gamma bias = 1
                film.bias[hidden_size:] = 0.0   # beta  bias = 0

        # regime gate (drift vs avoid) from the FiLM-modulated trunk.
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

    # ---- interface parity helpers ----

    def actor_parameters(self):
        params = (list(self.trunk_fc1.parameters()) + list(self.trunk_fc2.parameters())
                  + list(self.film1.parameters()) + list(self.film2.parameters())
                  + list(self.actor_gate.parameters()) + list(self.drift_head.parameters()))
        for head in self.avoid_heads:
            params += list(head.parameters())
        params += [self.log_std]
        return params

    def critic_parameters(self):
        return list(self.critic.parameters())

    def _onehot_of(self, obs75: torch.Tensor) -> torch.Tensor:
        """Slice the vehicle one-hot out of obs75 (the FROZEN last `onehot_dim` channels)."""
        return obs75[..., OBS72_DIM:OBS72_DIM + self.onehot_dim]

    def _film(self, film: nn.Linear, oh: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        gb = film(oh)
        gamma = gb[..., :self.hidden_size]
        beta = gb[..., self.hidden_size:]
        return gamma, beta

    def _trunk(self, obs75: torch.Tensor) -> torch.Tensor:
        """FiLM-modulated shared trunk: per-vehicle gamma/beta on each hidden layer's pre-activation."""
        oh = self._onehot_of(obs75)
        g1, b1 = self._film(self.film1, oh)
        g2, b2 = self._film(self.film2, oh)
        h1 = torch.tanh(g1 * self.trunk_fc1(obs75) + b1)
        h = torch.tanh(g2 * self.trunk_fc2(h1) + b2)
        return h

    def actor(self, obs75: torch.Tensor) -> torch.Tensor:
        """Expose the FiLM-modulated trunk as `.actor(obs)` so cond's gate diagnostics
        (`model.actor(obs)` then `model.actor_gate(...)`) work UNCHANGED."""
        return self._trunk(obs75)

    def _raw_mean(self, obs75: torch.Tensor) -> torch.Tensor:
        if obs75.shape[-1] != self.obs_dim:
            raise ValueError(f"actor input must be obs{self.obs_dim}; got {obs75.shape[-1]}")
        h = self._trunk(obs75)
        g = torch.sigmoid(self.actor_gate(h))               # (N,1): 1=>drift, 0=>avoid
        drift_mean = self.drift_head(h)                      # (N, act)
        oh = self._onehot_of(obs75)                          # (N, V)
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
# FiLM distillation. A copy of cond._distill_conditioned / perveh._distill_perveh, but the
# student is FiLMAvoidActorCritic. The loss is identical (pooled drift+avoid frames, the 0.5/n
# per-regime sample weighting, best-on-both-holdouts ckpt); the per-vehicle FiLM + routing is a
# property of the MODEL, so the BC objective does not change.  `init_state` (optional) warm-
# starts from the BC checkpoint so the DAgger re-BC continues rather than restarts.
# =====================================================================================


def _distill_film(drift_demo: dict, avoid_demo: dict, *, epochs: int, lr: float, batch: int,
                  holdout_frac: float, seed: int,
                  init_state: dict | None = None) -> tuple[FiLMAvoidActorCritic, dict]:
    torch.manual_seed(f2._seed_for("distill_init", seed))
    np.random.seed(f2._seed_for("distill_np", seed) % (2**32))

    (dtr_o, dtr_a), (dho_o, dho_a) = db._holdout_split(drift_demo["obs"], drift_demo["act"], frac=holdout_frac, seed=seed + 1)
    (atr_o, atr_a), (aho_o, aho_a) = db._holdout_split(avoid_demo["obs"], avoid_demo["act"], frac=holdout_frac, seed=seed + 2)

    train_o = np.concatenate([dtr_o, atr_o], 0).astype(np.float32)
    train_a = np.concatenate([dtr_a, atr_a], 0).astype(np.float32)
    train_reg = np.concatenate([np.ones(len(dtr_o), np.int64), np.zeros(len(atr_o), np.int64)], 0)  # 1=drift 0=avoid

    print(f"  distill train: {len(dtr_o)} drift + {len(atr_o)} avoid frames (obs{train_o.shape[1]}); "
          f"holdout: {len(dho_o)} drift + {len(aho_o)} avoid", flush=True)

    model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)  # FRESH FiLM student
    if init_state is not None:
        model.load_state_dict(init_state)  # warm-start (DAgger re-BC continues from BC ckpt)
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

    # per-vehicle avoid holdout split (diagnostic: each vehicle's own-budget fit)
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
    print(f"  per-vehicle avoid holdout MSE (FiLM rep + own head): "
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


# =====================================================================================
# DAgger on avoid, PER VEHICLE. For each vehicle: install its patches (so the avoid oracle is
# the per-vehicle re-physicalized one and the scenario builders thread the right variant/mass),
# build a hard-cell-focused rollout set, roll the CURRENT FiLM student out (the student sees
# obs75 = obs72 + the vehicle one-hot), relabel each visited reveal-post state with the
# vehicle's avoid ORACLE action, and append (obs75 -> oracle_action) recovery labels to THAT
# vehicle's avoid pool. The drift pool is FROZEN (never rolled out / re-collected), so drift
# cannot regress by construction. Reuses dagger_avoid._dagger_episode VERBATIM via a thin
# one-hot-appending student wrapper (the oracle still labels on obs72, the wrapper appends the
# one-hot before model.act).
# =====================================================================================


def _hard_focus_specs_for_vehicle(name: str, hard_cell_seeds: int, easy_cell_seeds: int,
                                   round_idx: int) -> list[dict]:
    """Per-vehicle hard-cell-focused DAgger rollout set. The vehicle's patches MUST be installed
    so f2._avoidance_scenario threads the vehicle's mass/variant. Disjoint 'dagger_film' seed
    namespace keyed by (vehicle, round) so successive rounds visit FRESH states (DAgger needs new
    states). The A5 'validation' grid + the 'distill'/'distill_select' namespaces are untouched."""
    grid = f2._avoidance_grid(quick=False)
    hard_set = {(round(r, 4), round(m, 4)) for (r, m) in HARD_CELLS}
    specs: list[dict] = []
    for ci, (reveal, mu) in enumerate(grid):
        is_hard = (round(reveal, 4), round(mu, 4)) in hard_set
        n = hard_cell_seeds if is_hard else easy_cell_seeds
        for i in range(n):
            seed = int(f2._seed_for("dagger_film", name, round_idx, ci, i, round(reveal, 4), round(mu, 4)))
            specs.append({
                "regime": "avoidance", "seed": seed, "mu": float(mu), "reveal": float(reveal),
                "scenario": f2._avoidance_scenario(seed, max_steps=db.AVOID_MAX_STEPS,
                                                   reveal=float(reveal), mu=float(mu)),
                "is_hard": is_hard,
            })
    return specs


class _OneHotStudent:
    """Thin wrapper exposing .act(obs72) that appends a fixed vehicle one-hot (obs72 -> obs75)
    before calling the FiLM student. dagger_avoid._dagger_episode calls model.act(obs72) (obs72
    from the backend) and queries the oracle on obs72; we append the one-hot so the FiLM student
    routes to the right vehicle representation/head while the oracle still labels on obs72."""

    def __init__(self, model: FiLMAvoidActorCritic, name: str):
        self._model = model
        self._oh = _vehicle_onehot(name)

    def act(self, obs72: np.ndarray) -> np.ndarray:
        obs75 = np.concatenate([np.asarray(obs72, dtype=np.float32), self._oh], 0)
        return self._model.act(obs75)


def _dagger_collect_per_vehicle(clients, model: FiLMAvoidActorCritic, *,
                                hard_cell_seeds: int, easy_cell_seeds: int, round_idx: int) -> dict[str, Any]:
    """Roll the CURRENT FiLM student out PER VEHICLE; relabel visited avoid states with that
    vehicle's oracle. Returns per-vehicle (obs75 -> oracle_action) recovery labels + rollout stats.

    The recovery labels are tagged with the vehicle's one-hot (obs72 -> obs75) so they pool into
    the same conditioned avoid demo set the FiLM student trains on."""
    out: dict[str, Any] = {}
    for name in VEHICLES:
        d3v._install_vehicle(name)  # installs the vehicle's avoid ORACLE (re-physicalized) + scenarios
        specs = _hard_focus_specs_for_vehicle(name, hard_cell_seeds, easy_cell_seeds, round_idx)
        n_hard = sum(1 for s in specs if s["is_hard"])
        oh_student = _OneHotStudent(model, name)
        # dagger_avoid.collect_dagger rolls out oh_student (obs72 in, obs72 out) and labels each
        # visited reveal-post obs72 with f2.make_avoidance_teacher(reveal, mu) -- which, with the
        # vehicle's patches installed, is the per-vehicle re-physicalized oracle.
        dagout = dag.collect_dagger(clients, specs, oh_student)
        obs72 = dagout["obs"]
        obs75 = _append_onehot(obs72, name) if obs72.shape[0] > 0 else np.zeros((0, COND_OBS_DIM), np.float32)
        out[name] = {
            "obs75": obs75, "act": dagout["act"],
            "n_episodes": int(dagout["n_episodes"]), "n_success": int(dagout["n_success"]),
            "n_offtrack": int(dagout["n_offtrack"]), "n_collision": int(dagout["n_collision"]),
            "n_other_fail": int(dagout["n_other_fail"]), "n_hard_eps": int(n_hard),
            "fail_cells": dagout["fail_cells"], "other_reasons": dagout["other_reasons"],
            "labels": int(obs75.shape[0]),
        }
        succ_rate = dagout["n_success"] / max(1, dagout["n_episodes"])
        print(f"    [{name}] DAgger rollout: {dagout['n_success']}/{dagout['n_episodes']} succ "
              f"({succ_rate:.3f}; off_track={dagout['n_offtrack']} coll={dagout['n_collision']} "
              f"other={dagout['n_other_fail']}) -> {obs75.shape[0]} recovery labels -> avoid_head[{name}]",
              flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="FiLM + DAgger 3-vehicle do-both driver (obs75; FiLM trunk + 1 drift head + 3 avoid heads + per-vehicle DAgger).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds", type=int, default=8, help="drift demo seeds PER difficulty PER vehicle")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="avoid demo seeds per reveal x mu cell PER vehicle")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--dagger-epochs", type=int, default=4000, help="re-BC epochs per DAgger round (warm-started)")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=3)
    ap.add_argument("--dagger-rounds", type=int, default=2, help="DAgger rounds on avoid (per vehicle)")
    ap.add_argument("--dagger-hard-cell-seeds", type=int, default=10, help="student roll-out seeds per HARD cell / vehicle / round")
    ap.add_argument("--dagger-easy-cell-seeds", type=int, default=2, help="student roll-out seeds per non-hard cell / vehicle / round")
    ap.add_argument("--select-avoid-units", type=int, default=8, help="select avoid episodes PER vehicle")
    ap.add_argument("--select-drift-units", type=int, default=5, help="select drift episodes PER vehicle")
    ap.add_argument("--a5-avoid-units", type=int, default=40, help="A5 avoid validation episodes PER vehicle")
    ap.add_argument("--a5-drift-units", type=int, default=20, help="A5 drift validation episodes PER vehicle")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    print(f"[3vehicle-FiLM+DAgger] pooling demos from {VEHICLES} into ONE network: FiLM-conditioned "
          f"shared trunk (per-vehicle gamma/beta from the one-hot) + regime gate + ONE drift head + "
          f"THREE avoid heads (obs{COND_OBS_DIM}). FiLM gives AVOID a per-vehicle REPRESENTATION; "
          f"DAgger (per vehicle) closes the closed-loop compound-error gap.", flush=True)
    print(f"  one-hot order (FROZEN): {[(v, list(_vehicle_onehot(v))) for v in VEHICLES]}", flush=True)
    print(f"  DAgger: {args.dagger_rounds} rounds, {args.dagger_hard_cell_seeds}/hard-cell + "
          f"{args.dagger_easy_cell_seeds}/easy-cell per vehicle per round; drift demos FROZEN.", flush=True)

    clients = [ResilientChronoClient(stderr_log=RUN_DIR / f"distill3vfilm_w{w}_stderr.log")
               for w in range(args.workers)]
    report: dict[str, Any] = {
        "vehicles": list(VEHICLES), "onehot_dim": ONEHOT_DIM, "cond_obs_dim": COND_OBS_DIM,
        "architecture": "FiLM_shared_trunk(per_vehicle_gamma_beta) + regime_gate + 1_drift_head + 3_avoid_heads(routed) + per_vehicle_DAgger",
        "baselines": {"sedan": {"drift": 1.0, "avoid": 1.0}, "uazbus": {"drift": 1.0, "avoid": 1.0},
                      "bmw": {"drift": 0.85, "avoid": 1.0}},
        "s2_unconditioned_a5": {"sedan": {"drift": 1.0, "avoid": 0.10}, "uazbus": {"drift": 1.0, "avoid": 0.25},
                                "bmw": {"drift": 0.85, "avoid": 0.05}},
        "perveh_head_a5": {"sedan": {"avoid": 0.575}, "uazbus": {"avoid": 0.20}, "bmw": {"avoid": 0.85}},
        "dagger_rounds": int(args.dagger_rounds)}
    t0 = time.time()
    pooled = None
    best = None  # (score, state_dict, stats, seed, sel)
    dagger_history: list[dict] = []
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
        # keep avoid demos SEPARATE PER VEHICLE so DAgger appends each vehicle's recovery labels
        # to its own pool; the pooled avoid_demo for distill is just the concat of the 3 pools.
        per_vehicle_avoid: dict[str, dict[str, np.ndarray]] = {
            v: {"obs75": _append_onehot(per_vehicle_demos[v]["avoid"]["obs"], v),
                "act": np.asarray(per_vehicle_demos[v]["avoid"]["act"], dtype=np.float32)}
            for v in VEHICLES}
        per_vehicle_base_n = {v: int(per_vehicle_avoid[v]["obs75"].shape[0]) for v in VEHICLES}

        def _pool_avoid() -> dict[str, np.ndarray]:
            ao = np.concatenate([per_vehicle_avoid[v]["obs75"] for v in VEHICLES], 0).astype(np.float32)
            aa = np.concatenate([per_vehicle_avoid[v]["act"] for v in VEHICLES], 0).astype(np.float32)
            return {"obs": ao, "act": aa,
                    "n_episodes": sum(per_vehicle_demos[v]["avoid"]["n_episodes"] for v in VEHICLES),
                    "n_success": sum(per_vehicle_demos[v]["avoid"]["n_success"] for v in VEHICLES)}

        drift_demo = {"obs": drift_obs, "act": drift_act,
                      "n_episodes": sum(per_vehicle_demos[v]["drift"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["drift"]["n_success"] for v in VEHICLES)}
        avoid_demo = _pool_avoid()
        assert drift_obs.shape[1] == COND_OBS_DIM and avoid_demo["obs"].shape[1] == COND_OBS_DIM, \
            f"conditioned obs dim mismatch: {drift_obs.shape[1]}/{avoid_demo['obs'].shape[1]} != {COND_OBS_DIM}"
        pooled = {"drift": drift_demo, "avoid": avoid_demo}
        report["pooled_demo"] = {
            "drift_frames": int(drift_obs.shape[0]), "avoid_frames": int(avoid_demo["obs"].shape[0]),
            "cond_obs_dim": int(drift_obs.shape[1]),
            "per_vehicle": {v: {
                "drift_frames": int(per_vehicle_demos[v]["drift"]["obs"].shape[0]),
                "drift_teacher_success": int(per_vehicle_demos[v]["drift"]["n_success"]),
                "drift_episodes": int(per_vehicle_demos[v]["drift"]["n_episodes"]),
                "avoid_frames": int(per_vehicle_base_n[v]),
                "avoid_teacher_success": int(per_vehicle_demos[v]["avoid"]["n_success"]),
                "avoid_episodes": int(per_vehicle_demos[v]["avoid"]["n_episodes"]),
                "onehot": list(_vehicle_onehot(v)),
            } for v in VEHICLES}}
        report["scenario_verification"] = {v: per_vehicle_demos[v]["verify"] for v in VEHICLES}
        print(f"\nPOOLED demos: {drift_obs.shape[0]} drift + {avoid_demo['obs'].shape[0]} avoid frames "
              f"(obs{drift_obs.shape[1]}, from 3 vehicles WITH one-hot; FiLM rep + avoid routed per vehicle)", flush=True)
        for v in VEHICLES:
            print(f"   {v:7s} oh={list(_vehicle_onehot(v))}: "
                  f"drift {per_vehicle_demos[v]['drift']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['drift']['n_success']}/{per_vehicle_demos[v]['drift']['n_episodes']} succ) | "
                  f"avoid {per_vehicle_base_n[v]:6d} frames "
                  f"({per_vehicle_demos[v]['avoid']['n_success']}/{per_vehicle_demos[v]['avoid']['n_episodes']} succ) "
                  f"-> avoid_head[{v}]", flush=True)

        # ---- 3. build the pooled (per-vehicle-tagged) Chrono select set (VERBATIM from cond) ----
        select_items = cond._pooled_select_items(int(args.select_avoid_units), int(args.select_drift_units))

        # ---- 4. BC-distill N seeds on the POOLED demos; select by WORST-vehicle avoid Chrono task score ----
        per_seed = []
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- 3vehicle FiLM BC distill seed {s} ---", flush=True)
            m, st = _distill_film(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                                  holdout_frac=args.holdout_frac, seed=s)
            sel = cond._pooled_conditioned_select(clients, m, select_items)
            agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
            worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
            print(f"  seed {s} POOLED SELECT (BC): avoid agg={agg_av:.3f} (WORST {worst_av:.3f}) "
                  f"drift agg={agg_dr:.3f} (worst {worst_dr:.3f})", flush=True)
            st["select_avoid"] = agg_av; st["select_drift"] = agg_dr
            st["select_worst_avoid"] = worst_av; st["select_worst_drift"] = worst_dr
            st["select_per_vehicle"] = sel["per_vehicle"]; st["distill_seed"] = s
            per_seed.append({"seed": s, "select_avoid": agg_av, "select_drift": agg_dr,
                             "worst_avoid": worst_av, "worst_drift": worst_dr,
                             "per_vehicle": sel["per_vehicle"],
                             "drift_holdout_mse": st["drift_holdout_mse"], "avoid_holdout_mse": st["avoid_holdout_mse"],
                             "per_vehicle_avoid_holdout_mse": st["per_vehicle_avoid_holdout_mse"]})
            # SELECT on WORST-vehicle avoid (the generality bottleneck) FIRST, then worst drift, then agg.
            score = (worst_av, worst_dr, agg_av, agg_dr)
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
        report["bc_distill_per_seed"] = per_seed

        # the best BC student (seed) is the DAgger warm-start.
        bc_score, bc_state, bc_stats, bc_seed, bc_sel = best
        print(f"\nBEST BC seed {bc_seed}: WORST avoid={bc_score[0]:.3f} worst drift={bc_score[1]:.3f} "
              f"(agg avoid={bc_score[2]:.3f} drift={bc_score[3]:.3f}) -> DAgger warm-start", flush=True)
        report["bc_selected"] = {
            "seed": int(bc_seed), "select_worst_avoid": float(bc_score[0]),
            "select_worst_drift": float(bc_score[1]), "select_avoid": float(bc_score[2]),
            "select_drift": float(bc_score[3]), "per_vehicle": bc_sel["per_vehicle"]}

        # ---- 5. DAgger on avoid (per vehicle): roll out -> relabel with oracle -> augment -> re-BC ----
        cur_model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)
        cur_model.load_state_dict(bc_state)
        cur_model.eval()
        for rd in range(int(args.dagger_rounds)):
            print(f"\n========================= DAgger-FiLM ROUND {rd} (per vehicle) =========================", flush=True)
            # 5a) roll the current student out per vehicle; relabel visited states with the vehicle oracle.
            dag_out = _dagger_collect_per_vehicle(
                clients, cur_model, hard_cell_seeds=args.dagger_hard_cell_seeds,
                easy_cell_seeds=args.dagger_easy_cell_seeds, round_idx=rd)
            # 5b) append each vehicle's recovery labels to its own avoid pool.
            for v in VEHICLES:
                if dag_out[v]["obs75"].shape[0] > 0:
                    per_vehicle_avoid[v]["obs75"] = np.concatenate(
                        [per_vehicle_avoid[v]["obs75"], dag_out[v]["obs75"]], 0).astype(np.float32)
                    per_vehicle_avoid[v]["act"] = np.concatenate(
                        [per_vehicle_avoid[v]["act"], dag_out[v]["act"]], 0).astype(np.float32)
            avoid_demo = _pool_avoid()
            for v in VEHICLES:
                print(f"  [{v}] avoid pool: {per_vehicle_avoid[v]['obs75'].shape[0]} frames "
                      f"(base {per_vehicle_base_n[v]} + DAgger {per_vehicle_avoid[v]['obs75'].shape[0]-per_vehicle_base_n[v]})",
                      flush=True)

            # 5c) re-BC on (FROZEN drift) + (augmented avoid); seed sweep; select on WORST-vehicle avoid.
            round_best = None
            round_per_seed = []
            for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
                print(f"\n--- DAgger round {rd} re-BC seed {s} ---", flush=True)
                # warm-start from the best BC state so re-BC continues (faster + on-distribution).
                m, st = _distill_film(drift_demo, avoid_demo, epochs=args.dagger_epochs, lr=args.lr,
                                      batch=args.batch, holdout_frac=args.holdout_frac, seed=s,
                                      init_state=bc_state)
                sel = cond._pooled_conditioned_select(clients, m, select_items)
                agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
                worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
                print(f"  round {rd} seed {s} SELECT: avoid agg={agg_av:.3f} (WORST {worst_av:.3f}) "
                      f"drift agg={agg_dr:.3f} (worst {worst_dr:.3f})", flush=True)
                st["select_avoid"] = agg_av; st["select_drift"] = agg_dr
                st["select_worst_avoid"] = worst_av; st["select_worst_drift"] = worst_dr
                st["select_per_vehicle"] = sel["per_vehicle"]; st["distill_seed"] = s; st["dagger_round"] = rd
                round_per_seed.append({"seed": s, "select_avoid": agg_av, "select_drift": agg_dr,
                                       "worst_avoid": worst_av, "worst_drift": worst_dr,
                                       "per_vehicle": sel["per_vehicle"]})
                score = (worst_av, worst_dr, agg_av, agg_dr)
                if round_best is None or score > round_best[0]:
                    round_best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
                # global best across BC + all DAgger rounds (select on worst-vehicle avoid).
                if score > best[0]:
                    best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)

            r_score, r_state, r_stats, r_seed, r_sel = round_best
            # the NEXT DAgger round rolls out THIS round's selected student (iterate on its own states).
            cur_model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)
            cur_model.load_state_dict(r_state)
            cur_model.eval()
            dagger_history.append({
                "round": rd,
                "round_best_seed": int(r_seed),
                "round_best_worst_avoid": float(r_score[0]), "round_best_worst_drift": float(r_score[1]),
                "round_best_agg_avoid": float(r_score[2]), "round_best_agg_drift": float(r_score[3]),
                "round_best_per_vehicle": r_sel["per_vehicle"],
                "per_seed": round_per_seed,
                "rollout": {v: {k: dag_out[v][k] for k in
                                ("n_episodes", "n_success", "n_offtrack", "n_collision", "n_other_fail",
                                 "n_hard_eps", "labels", "fail_cells")} for v in VEHICLES},
                "avoid_pool_frames": {v: int(per_vehicle_avoid[v]["obs75"].shape[0]) for v in VEHICLES},
            })
            print(f"\n  ROUND {rd} BEST seed {r_seed}: WORST avoid={r_score[0]:.3f} (agg {r_score[2]:.3f}) "
                  f"worst drift={r_score[1]:.3f} (agg {r_score[3]:.3f})", flush=True)
        report["dagger_history"] = dagger_history

        # ---- 6. finalize the globally-best model (BC or any DAgger round, by worst-vehicle avoid) ----
        model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)
        model.load_state_dict(best[1])
        stats = best[2]
        sel_round = stats.get("dagger_round", "BC")
        print(f"\nSELECTED seed {best[3]} (round {sel_round}) on WORST-vehicle avoid "
              f"(select avoid agg={stats['select_avoid']:.3f} drift agg={stats['select_drift']:.3f} | "
              f"WORST avoid={stats['select_worst_avoid']:.3f} worst drift={stats['select_worst_drift']:.3f})", flush=True)
        report["distill_selected"] = {
            "seed": int(best[3]), "dagger_round": sel_round,
            "select_avoid": float(stats["select_avoid"]), "select_drift": float(stats["select_drift"]),
            "select_worst_avoid": float(stats["select_worst_avoid"]),
            "select_worst_drift": float(stats["select_worst_drift"]),
            "selection_objective": "max WORST-vehicle avoid (min over 3), then worst drift, then agg avoid, then agg drift",
            "per_vehicle": stats["select_per_vehicle"]}

        # ---- 7. save the policy BEFORE the (longer) A5 validation, so a crash can't lose it ----
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_stats = {k: v for k, v in stats.items() if k != "select_per_vehicle"}
        torch.save({
            "state_dict": model.state_dict(), "gated": True,
            "model_class": "FiLMAvoidActorCritic",
            "obs_dim": COND_OBS_DIM, "onehot_dim": ONEHOT_DIM, "vehicle_order": list(VEHICLES),
            "label": "distill_both_3vehicle_film", "vehicles": list(VEHICLES),
            "architecture": "FiLM_shared_trunk(per_vehicle_gamma_beta) + regime_gate + 1_drift_head + 3_avoid_heads(routed) + per_vehicle_DAgger",
            "conditioning": "3way_vehicle_onehot_appended_obs72_to_obs75; FiLM trunk modulation + avoid branch routed per vehicle",
            "drift_teacher": "pooled_{sedan_gpu_expert, uazbus_feedback, bmw_feedback}",
            "avoid_teacher": "per_vehicle_{sedan_oracle, uazbus_oracle, bmw_rephys_oracle} + per_vehicle_DAgger -> own avoid head",
            "drift_demo_frames": int(pooled["drift"]["obs"].shape[0]),
            "avoid_demo_frames_final": int(avoid_demo["obs"].shape[0]),
            "per_vehicle_avoid_frames_final": {v: int(per_vehicle_avoid[v]["obs75"].shape[0]) for v in VEHICLES},
            "per_vehicle_avoid_base_frames": per_vehicle_base_n,
            "dagger_rounds": int(args.dagger_rounds),
            "selected_dagger_round": sel_round,
            "select_per_vehicle": stats["select_per_vehicle"],
            **save_stats,
        }, out)
        print(f"\nsaved FiLM+DAgger 3-vehicle distilled student -> {out}", flush=True)

        # ---- 8. per-(vehicle, regime) A5 validation on Chrono (correct one-hot per vehicle; VERBATIM) ----
        a5 = cond._validate_per_vehicle(clients, model, int(args.a5_avoid_units), int(args.a5_drift_units))
        report["a5_per_vehicle"] = {v: {k: a5[v][k] for k in ("avoid", "drift", "n_avoid", "n_drift", "variant", "mass")}
                                    for v in VEHICLES}
    finally:
        for c in clients:
            c.close()

    report["elapsed_s"] = round(time.time() - t0, 1)

    # ---- verdict: did FiLM + DAgger recover avoid on all 3? ----
    base = report["baselines"]; s2 = report["s2_unconditioned_a5"]; a5p = report["a5_per_vehicle"]
    pv = report["perveh_head_a5"]
    recovered = {v: bool(a5p[v]["avoid"] >= 0.80) for v in VEHICLES}
    improved_vs_perveh = {v: bool(a5p[v]["avoid"] > pv[v]["avoid"] + 1e-9) for v in VEHICLES}
    near_baseline = {v: bool(a5p[v]["avoid"] >= base[v]["avoid"] - 0.10) for v in VEHICLES}
    drift_held = {v: bool(a5p[v]["drift"] >= base[v]["drift"] - 1e-9) for v in VEHICLES}
    all_recovered = all(recovered.values())
    any_improved = any(improved_vs_perveh.values())
    laggards = [v for v in VEHICLES if not recovered[v]]
    report["verdict"] = {
        "avoid_recovered_per_vehicle": recovered,
        "avoid_improved_vs_perveh_head_per_vehicle": improved_vs_perveh,
        "avoid_near_baseline_per_vehicle": near_baseline,
        "drift_held_at_baseline_per_vehicle": drift_held,
        "ALL_avoid_recovered": all_recovered,
        "ANY_avoid_improved_vs_perveh": any_improved,
        "laggards": laggards,
        "key": ("YES -- FiLM (per-vehicle REPRESENTATION) + DAgger (closed-loop gap) RECOVER avoid on "
                "all 3 vehicles (each >= 0.80): the ONE-network cross-vehicle-general driver is DELIVERED "
                "(full spectrum + drift-general + avoid-recovered-via-FiLM) -- the strongest, most general driver."
                if all_recovered else
                (f"NO (cross-vehicle avoid stays vehicle-specific) -- laggard(s) {laggards} remain < 0.80 even "
                 f"with FiLM per-vehicle representation + DAgger. Honest conclusion: avoid is genuinely "
                 f"vehicle-specific (the closed-loop entry-speed budget does not co-train in one network); "
                 f"the per-vehicle drivers are the practical strongest." if not any_improved else
                 f"PARTIAL -- FiLM+DAgger IMPROVE avoid over the per-vehicle-head attempt on at least one "
                 f"vehicle but NOT all 3 to >= 0.80; laggard(s) {laggards}. Avoid is (at least partly) "
                 f"genuinely vehicle-specific; per-vehicle drivers remain the practical strongest.")),
    }

    report_path = RUN_DIR / "distill_3vehicle_film_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"saved report -> {report_path}", flush=True)

    # ---- consolidated, re-verifiable per-(vehicle, regime) table ----
    consolidated = {
        "experiment": "FiLM + DAgger 3-vehicle do-both driver (obs75; FiLM trunk + 1 drift head + 3 avoid heads + per-vehicle DAgger)",
        "question": "Do FiLM (per-vehicle representation) + DAgger (closed-loop gap) recover avoid on all 3 vehicles?",
        "policy": str(args.out), "policy_label": "distill_both_3vehicle_film",
        "architecture": report["architecture"],
        "obs_dim": COND_OBS_DIM, "onehot_order": list(VEHICLES),
        "selected_seed": int(best[3]), "selected_dagger_round": report["distill_selected"]["dagger_round"],
        "selection_objective": "max WORST-vehicle avoid (min over 3 vehicles)",
        "dagger_rounds": int(args.dagger_rounds),
        "pooled_demo_frames": {"drift": int(pooled["drift"]["obs"].shape[0]),
                               "avoid_final": int(avoid_demo["obs"].shape[0])},
        "distill_holdout_mse": {"drift": float(stats["drift_holdout_mse"]), "avoid": float(stats["avoid_holdout_mse"]),
                                "per_vehicle_avoid": stats["per_vehicle_avoid_holdout_mse"]},
        "a5_validation_units_per_vehicle": {"avoid": int(args.a5_avoid_units), "drift": int(args.a5_drift_units)},
        "per_vehicle_regime_chrono_FILM": {
            v: {"variant": a5p[v]["variant"], "mass": a5p[v]["mass"],
                "drift": round(float(a5p[v]["drift"]), 4), "avoid": round(float(a5p[v]["avoid"]), 4),
                "onehot_fed": list(_vehicle_onehot(v)),
                "drift_baseline": base[v]["drift"], "avoid_baseline": base[v]["avoid"],
                "s2_agnostic_avoid": s2[v]["avoid"],
                "perveh_head_avoid": pv[v]["avoid"]}
            for v in VEHICLES},
        "verdict": report["verdict"]["key"],
    }
    cons_path = RUN_DIR / "a5_3vehicle_film_consolidated.json"
    cons_path.write_text(json.dumps(consolidated, indent=2, default=str), encoding="utf-8")
    print(f"saved consolidated table -> {cons_path}", flush=True)

    # ---- human-readable verdict ----
    print("\n" + "=" * 110, flush=True)
    print("=== FiLM + DAgger 3-VEHICLE DO-BOTH DRIVER: per-(vehicle, regime) Chrono ===", flush=True)
    print(f"{'vehicle':8s} | {'drift':>7s} (base) | {'avoid':>7s} (base) | {'avoid S2':>9s} | "
          f"{'avoid perveh':>12s} | recovered?", flush=True)
    for v in VEHICLES:
        print(f"{v:8s} | {a5p[v]['drift']:7.3f} ({base[v]['drift']:.2f}) | "
              f"{a5p[v]['avoid']:7.3f} ({base[v]['avoid']:.2f}) | {s2[v]['avoid']:9.3f} | "
              f"{pv[v]['avoid']:12.3f} | "
              f"{'YES' if recovered[v] else ('improved' if improved_vs_perveh[v] else 'no')}", flush=True)
    print("-" * 110, flush=True)
    print(f"KEY VERDICT: {report['verdict']['key']}", flush=True)
    print(f"  drift held at baseline (1.0/1.0/0.85): { {v: drift_held[v] for v in VEHICLES} }", flush=True)
    print("=" * 110, flush=True)


if __name__ == "__main__":
    main()
