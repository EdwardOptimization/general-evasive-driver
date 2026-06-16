"""Fit a small MLP tyre to Chrono's EXACT sampled TMeasy curves (NN-FITTED-TYRE variant).

This is the training half of the NN-tyre faithful-rewrite sibling of the TABLE variant
(``gpu_physics_tmeasy.py``, which bilinear-interpolates the same curves). Instead of a
bilinear LUT, the tyre force law becomes two tiny MLPs that map the runtime slip + normal
load to the force RATIO:

    mlp_x : (kappa, Fz) -> Fx / Fz
    mlp_y : (alpha, Fz) -> Fy / Fz

trained on the sampled curve points from
``runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz``:
  - inputs  : kappa_rep / Fz_at_K  (Fx branch), alpha_rep / Fz_at_A (Fy branch)
  - targets : Fx / Fz_at_K, Fy / Fz_at_A

Inputs and outputs are normalised (z-score on slip, [grid->[-1,1]] on log? no — simple
min/scale on Fz, z-score on slip; targets z-scored) so the net trains tightly. The fitted
weights + normalisation stats + architecture are saved to
``runs/feasibility_audit/phase4_f2/tmeasy_tyre_nn.pt`` for the runtime tyre in
``autodrift.gpu_physics_nn``.

The script reports train MSE on the force ratio and two sanity values vs the table/spec:
    Fx/Fz @ kappa=0.10,  Fz=4000 N  -> table 0.990
    Fy/Fz @ alpha=0.10 rad, Fz=4000 N -> table 0.851 (magnitude; table is signed -0.851)

Usage:
    python scripts/feasibility_audit/fit_tmeasy_tyre_nn.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

CURVE_NPZ = ROOT / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz"
OUT_PT = ROOT / "runs/feasibility_audit/phase4_f2/tmeasy_tyre_nn.pt"

# Architecture: small MLP, slip+Fz -> ratio. Two separate nets (x and y).
HIDDEN = 32
N_LAYERS = 3           # hidden layers (so depth = N_LAYERS + output)
EPOCHS = 20000
LR = 2e-3
WEIGHT_DECAY = 0.0
SEED = 0


class TyreMLP(nn.Module):
    """tanh MLP: 2 normalised inputs (slip_n, Fz_n) -> 1 normalised output (ratio_n)."""

    def __init__(self, hidden: int = HIDDEN, n_layers: int = N_LAYERS):
        super().__init__()
        layers: list[nn.Module] = []
        d = 2
        for _ in range(n_layers):
            layers += [nn.Linear(d, hidden), nn.Tanh()]
            d = hidden
        layers += [nn.Linear(d, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def _norm_stats(slip: np.ndarray, fz: np.ndarray, ratio: np.ndarray) -> dict[str, float]:
    """Normalisation stats: z-score slip + ratio, affine map Fz to ~[-1,1] over its grid."""
    return {
        "slip_mean": float(slip.mean()),
        "slip_std": float(slip.std() + 1e-9),
        "fz_lo": float(fz.min()),
        "fz_hi": float(fz.max()),
        "ratio_mean": float(ratio.mean()),
        "ratio_std": float(ratio.std() + 1e-9),
    }


def _encode(slip, fz, st):
    slip_n = (slip - st["slip_mean"]) / st["slip_std"]
    fz_n = 2.0 * (fz - st["fz_lo"]) / (st["fz_hi"] - st["fz_lo"]) - 1.0
    return torch.stack([slip_n, fz_n], dim=-1)


def _decode(ratio_n, st):
    return ratio_n * st["ratio_std"] + st["ratio_mean"]


def _train_branch(slip_np, fz_np, ratio_np, name, device):
    """Train one MLP branch on flattened (slip, Fz)->ratio sample points. Returns model, stats."""
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    st = _norm_stats(slip_np, fz_np, ratio_np)
    slip = torch.tensor(slip_np, dtype=torch.float64, device=device)
    fz = torch.tensor(fz_np, dtype=torch.float64, device=device)
    ratio = torch.tensor(ratio_np, dtype=torch.float64, device=device)
    X = _encode(slip, fz, st)
    y_n = (ratio - st["ratio_mean"]) / st["ratio_std"]

    model = TyreMLP().to(device=device, dtype=torch.float64)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    best = float("inf")
    for ep in range(EPOCHS):
        opt.zero_grad()
        pred_n = model(X)
        loss = ((pred_n - y_n) ** 2).mean()
        loss.backward()
        opt.step()
        sched.step()
        if loss.item() < best:
            best = loss.item()
    # final train MSE on the actual force RATIO (decoded units), not normalised.
    with torch.no_grad():
        pred_ratio = _decode(model(X), st)
        mse_ratio = float(((pred_ratio - ratio) ** 2).mean())
        max_abs = float((pred_ratio - ratio).abs().max())
    print(f"[{name}] train MSE(ratio)={mse_ratio:.3e}  max|err|={max_abs:.4f}  (norm loss={best:.3e})")
    return model, st, mse_ratio, max_abs


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    d = np.load(CURVE_NPZ)
    fz_grid = np.asarray(d["fz_grid"], dtype=np.float64)          # [7]
    kappa_grid = np.asarray(d["kappa_grid"], dtype=np.float64)    # [17]
    alpha_grid = np.asarray(d["alpha_grid"], dtype=np.float64)    # [19]
    Fx = np.asarray(d["Fx"], dtype=np.float64)                    # [17,7]
    Fy = np.asarray(d["Fy"], dtype=np.float64)                    # [19,7]
    FzK = np.asarray(d["Fz_at_K"], dtype=np.float64)              # [17,7]
    FzA = np.asarray(d["Fz_at_A"], dtype=np.float64)              # [19,7]
    kappa_rep = np.asarray(d["kappa_rep"], dtype=np.float64)      # [17,7] reported slip per sample
    alpha_rep = np.asarray(d["alpha_rep"], dtype=np.float64)      # [19,7]

    # targets = force ratios; inputs = reported slip + actual Fz at each sample.
    fx_ratio = Fx / np.clip(FzK, 1.0, None)                       # [17,7]
    fy_ratio = Fy / np.clip(FzA, 1.0, None)                       # [19,7]

    # flatten the (slip, Fz) sample grid for the x branch and the y branch.
    kx = kappa_rep.reshape(-1)
    fzx = FzK.reshape(-1)
    rx = fx_ratio.reshape(-1)
    ay = alpha_rep.reshape(-1)
    fzy = FzA.reshape(-1)
    ry = fy_ratio.reshape(-1)

    print(f"device={device}  x-samples={kx.size}  y-samples={ay.size}")
    print(f"  kappa range [{kx.min():.3f},{kx.max():.3f}]  alpha range [{ay.min():.3f},{ay.max():.3f}] rad")
    print(f"  Fz range [{fzx.min():.0f},{fzx.max():.0f}] N")

    mx, stx, mse_x, mxa_x = _train_branch(kx, fzx, rx, "mlp_x(kappa,Fz)->Fx/Fz", device)
    my, sty, mse_y, mxa_y = _train_branch(ay, fzy, ry, "mlp_y(alpha,Fz)->Fy/Fz", device)

    # ---- sanity values vs table/spec at Fz=4000 ----
    mx.eval(); my.eval()
    with torch.no_grad():
        def predx(kappa, fz):
            X = _encode(torch.tensor([kappa], dtype=torch.float64, device=device),
                        torch.tensor([fz], dtype=torch.float64, device=device), stx)
            return float(_decode(mx(X), stx))
        def predy(alpha, fz):
            X = _encode(torch.tensor([alpha], dtype=torch.float64, device=device),
                        torch.tensor([fz], dtype=torch.float64, device=device), sty)
            return float(_decode(my(X), sty))
        fx_010 = predx(0.10, 4000.0)
        fy_010 = predy(0.10, 4000.0)

    # table values for comparison (bilinear on the same surfaces, matching the TABLE variant).
    def bilin(grid, ratio_surf, slip, fz):
        ik = int(np.searchsorted(grid, slip, "right")); ik = max(1, min(len(grid) - 1, ik))
        jf = int(np.searchsorted(fz_grid, fz, "right")); jf = max(1, min(len(fz_grid) - 1, jf))
        wx = (slip - grid[ik - 1]) / (grid[ik] - grid[ik - 1])
        wf = (fz - fz_grid[jf - 1]) / (fz_grid[jf] - fz_grid[jf - 1])
        f0 = ratio_surf[ik - 1, jf - 1] + wx * (ratio_surf[ik, jf - 1] - ratio_surf[ik - 1, jf - 1])
        f1 = ratio_surf[ik - 1, jf] + wx * (ratio_surf[ik, jf] - ratio_surf[ik - 1, jf])
        return f0 + wf * (f1 - f0)

    tbl_fx = bilin(kappa_grid, fx_ratio, 0.10, 4000.0)
    tbl_fy = bilin(alpha_grid, fy_ratio, 0.10, 4000.0)

    print("\n=== sanity: force ratio @ Fz=4000 N ===")
    print(f"  Fx/Fz @ kappa=0.10 :  NN={fx_010:.4f}   table={tbl_fx:.4f}   spec=0.990")
    print(f"  Fy/Fz @ alpha=0.10 :  NN={fy_010:.4f}   table={tbl_fy:.4f}   spec=0.851")

    # ---- extrapolation probe: outside the sampled slip range ----
    with torch.no_grad():
        print("\n=== extrapolation probe (OUTSIDE sampled range; runtime clamps slip to grid) ===")
        for kp in (0.30, 0.45, 0.60):
            print(f"  Fx/Fz @ kappa={kp:.2f} Fz=4000 : NN={predx(kp,4000.0):+.4f}"
                  f"  table(clamped)={bilin(kappa_grid, fx_ratio, min(kp,kappa_grid[-1]), 4000.0):+.4f}")
        for ap in (0.40, 0.60, 0.80):
            print(f"  Fy/Fz @ alpha={ap:.2f} Fz=4000 : NN={predy(ap,4000.0):+.4f}"
                  f"  table(clamped)={bilin(alpha_grid, fy_ratio, min(ap,alpha_grid[-1]), 4000.0):+.4f}")

    # ---- save weights + norm stats + arch + grids (for runtime clamping) ----
    payload = {
        "arch": {"hidden": HIDDEN, "n_layers": N_LAYERS},
        "mlp_x_state": {k: v.detach().cpu().double() for k, v in mx.state_dict().items()},
        "mlp_y_state": {k: v.detach().cpu().double() for k, v in my.state_dict().items()},
        "stx": stx,
        "sty": sty,
        "kappa_grid": kappa_grid,
        "alpha_grid": alpha_grid,
        "fz_grid": fz_grid,
        "train_mse_x": mse_x,
        "train_mse_y": mse_y,
        "max_abs_x": mxa_x,
        "max_abs_y": mxa_y,
        "sanity": {"fx_010": fx_010, "fy_010": fy_010, "tbl_fx": tbl_fx, "tbl_fy": tbl_fy},
    }
    OUT_PT.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, OUT_PT)
    print(f"\nsaved NN tyre weights -> {OUT_PT}")


if __name__ == "__main__":
    main()
