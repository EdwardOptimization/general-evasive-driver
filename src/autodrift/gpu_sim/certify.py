"""certify — measure a config's FidelityCertificate against frozen Chrono (design §5.1).

    certify(cfg) -> FidelityCertificate

Builds the model via resolver.build_model(cfg) and replays the frozen Chrono rollouts through it,
reading state BY NAME (the StateContract) so the SAME harness certifies any rung. Runs EAGER (so the
measurement is run-to-run deterministic regardless of the rung's gear-FSM op-reorder sensitivity); the
certificate records `deterministic_switches` to flag whether the COMPILED training path will match.
The certificate — never DOF count — is the arbiter for pretrain/posttrain config selection.

Frozen Chrono rollouts:
  drift: runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz  (held-out split idx[130:])
  avoid: runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from .contracts import FidelityConfig, FidelityCertificate
from .resolver import build_model

_ROOT = Path(__file__).resolve().parents[3]
_DRIFT = _ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
_AVOID = _ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"


def _drift_metrics(model, cfg, device, dt=0.02):
    d = np.load(_DRIFT, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    V = np.stack(d["chrono_v"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    mu = float(d["mu"][0])
    va = np.random.default_rng(0).permutation(A.shape[0])[130:]   # SAME held-out split as every gate
    Av, Vv, iv = A[va], V[va], init[va]
    R, T, _ = Av.shape
    P = model.make_param_batch(model.build_phys(cfg), R, mu=mu, device=device, dtype=torch.float32)
    A_t = torch.tensor(Av, device=device); it = torch.tensor(iv, device=device)
    st, gear = model.init_state(it[:, 0], it[:, 1], it[:, 2], P)
    ix = model.IDX
    sur = torch.zeros(R, T, 3, device=device)
    with torch.no_grad():
        for t in range(T):
            st, gear, _ = model.physics_step(st, A_t[:, t, :], gear, P, dt)
            sur[:, t, 0] = st[:, ix["vx"]]; sur[:, t, 1] = st[:, ix["vy"]]; sur[:, t, 2] = st[:, ix["yaw_rate"]]
    Vt = torch.tensor(Vv, device=device)
    k = min(23, T - 1)
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    p90 = float(torch.quantile((beta_c - beta_s).abs()[:, k], 0.9))
    beta_st = torch.atan2(sur[..., 1], Vt[..., 0].abs() + 1e-6)   # HONEST: with Chrono's TRUE vx
    p90_true = float(torch.quantile((beta_c - beta_st).abs()[:, k], 0.9))
    vx_rmse = float(((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt())
    return p90, p90_true, vx_rmse


def _avoid_metrics(model, cfg, device, dt=0.02):
    d = np.load(_AVOID, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    A_l, S_l, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    R = len(A_l)
    lens = np.array([min(len(np.asarray(A_l[i])), len(np.asarray(S_l[i]))) for i in range(R)])
    Tmax = int(lens.max())
    A = np.zeros((R, Tmax, 3), np.float32); Sx = np.zeros((R, Tmax), np.float32)
    for i in range(R):
        T = lens[i]; A[i, :T] = np.asarray(A_l[i])[:T, :3]; Sx[i, :T] = np.asarray(S_l[i])[:T, 3]
    mu = torch.tensor([float(params[i][pk.index("mu")]) for i in range(R)], dtype=torch.float32)
    pv0 = lambda k: float(params[0][pk.index(k)])  # noqa: E731
    # the avoid frozen data was generated at mass 1450 / izz 2300 / front_share lr/(lf+lr) — thread it
    avoid_cfg = cfg.with_overrides(param_overrides=(
        ("mass", pv0("mass")), ("izz", pv0("iz")), ("wheelbase", 2.776),
        ("front_axle_share", pv0("lr") / (pv0("lf") + pv0("lr")))))
    P = model.make_param_batch(model.build_phys(avoid_cfg), R, mu=mu.to(device), device=device, dtype=torch.float32)
    v = torch.tensor(init.astype(np.float32), device=device)
    st, gear = model.init_state(v[:, 3], v[:, 4], v[:, 5], P)
    st = st.clone(); ix = model.IDX
    st[:, ix["x"]], st[:, ix["y"]], st[:, ix["psi"]] = v[:, 0], v[:, 1], v[:, 2]
    A_arr = torch.tensor(A, device=device); Sx_t = torch.tensor(Sx, device=device)
    lens_t = torch.tensor(lens, device=device)
    valid = (torch.arange(Tmax, device=device)[None, :] < lens_t[:, None])
    se_x = torch.zeros(R, device=device)
    with torch.no_grad():
        for t in range(Tmax):
            st, gear, _ = model.physics_step(st, A_arr[:, t, :], gear, P, dt)
            se_x = se_x + valid[:, t].float() * (st[:, ix["vx"]] - Sx_t[:, t]) ** 2
    return float(torch.sqrt(se_x.sum() / valid.float().sum()))


def certify(cfg: FidelityConfig, *, device: str | None = None) -> FidelityCertificate:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(cfg)
    p90, p90_true, dvx = _drift_metrics(model, cfg, device)
    avx = _avoid_metrics(model, cfg, device)
    return FidelityCertificate(
        config_id=cfg.config_id,
        drift_beta24_p90=p90, drift_beta24_truevx_p90=p90_true, avoid_vx_rmse=avx,
        deterministic_switches=model.deterministic_switches,
        notes=f"{model.name} (state_dim={model.state_dim}); eager certify on frozen Chrono drift+avoid.",
    )
