"""A1.ii — learned rear-saturation head. The A1.iii test left 17 conservative false-negatives:
sustain-run breaks, dominated by the crude `|alpha_rear|>=0.10` proxy disagreeing with Chrono's
measured rear saturation (rear_sat per-step agree 0.973; a single mid-run break resets the 24-run).
Here we replace the proxy with a small head trained to predict Chrono's `rear_saturated` from the
surrogate state, then re-run the drift-success consistency.

Self-contained (defines the head locally; folds into gpu_surrogate.py once A2 lands). Saves
rear_sat_head.pt and prints the before/after confusion vs Chrono drift_success.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
sys.path.insert(0, str(ROOT / "src"))

import phase4_e4_drift_regime_pricing as e4  # noqa: E402
from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import make_param_batch, grey_box_step, ResidualDynamicsMLP  # noqa: E402

DT = 0.02
DEV = "cpu"  # tiny sequential replay -> CPU avoids per-step GPU sync; frees GPU for the physics agent
torch.set_default_dtype(torch.float32)
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_labels.npz"
MLP = ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseA.pt"
HEAD_OUT = ROOT / "runs/feasibility_audit/phase4_f2/rear_sat_head.pt"
B_THR, RS_THR, SUSTAIN = e4.BETA_THRESHOLD_RAD, e4.REAR_SLIP_ANGLE_THRESHOLD_RAD, e4.MIN_SUSTAIN_STEPS
VMIN, VMAX, WLIM = e4.MIN_SPEED_MPS, e4.MAX_SPEED_MPS, e4.YAW_RATE_LIMIT_RAD_S
FEAT = 8  # [vx, vy, yaw, beta, alpha_rear, steer_state, drive_state/1e4, |alpha_rear|]


class RearSaturationHead(torch.nn.Module):
    def __init__(self, in_dim=FEAT, hidden=64):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, hidden), torch.nn.SiLU(), torch.nn.Linear(hidden, 1))
        self.register_buffer("mean", torch.zeros(in_dim))
        self.register_buffer("std", torch.ones(in_dim))

    def set_norm(self, x):
        self.mean.copy_(x.mean(0)); self.std.copy_(x.std(0).clamp_min(1e-6))

    def forward(self, x):
        return self.net((x - self.mean) / self.std).squeeze(-1)


def longest_run(flags):
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def replay(actions, init, P, mlp, lr):
    """Grey-box replay -> per-step features[T,FEAT] + (vx,beta,yaw)[T,3]."""
    T = actions.shape[0]
    st = torch.zeros(1, 8); st[0, 3:6] = torch.tensor(init)
    A = torch.tensor(actions.astype(np.float32))
    feat = np.zeros((T, FEAT)); kin = np.zeros((T, 3))
    with torch.no_grad():
        for t in range(T):
            st, _ = grey_box_step(st, A[t:t+1], P, DT, mlp)
            vx, vy, yaw, ss, ds = (float(st[0, i]) for i in (3, 4, 5, 6, 7))
            beta = np.arctan2(vy, abs(vx) + 1e-6); ar = np.arctan2(vy - lr * yaw, abs(vx) + 1e-6)
            feat[t] = (vx, vy, yaw, beta, ar, ss, ds / 1e4, abs(ar)); kin[t] = (vx, beta, yaw)
    return feat, kin


def drift_success_from(rsat_pred, kin):
    cd = ((np.abs(kin[:, 1]) >= B_THR) & rsat_pred & (kin[:, 0] >= VMIN) & (kin[:, 0] <= VMAX)
          & (np.abs(kin[:, 2]) <= WLIM) & np.isfinite(kin).all(1))
    return longest_run(cd) >= SUSTAIN


def confusion(pred, truth):
    pred, truth = np.asarray(pred, bool), np.asarray(truth, bool)
    tp = int((pred & truth).sum()); tn = int((~pred & ~truth).sum())
    fp = int((pred & ~truth).sum()); fn = int((~pred & truth).sum())
    agree = (tp + tn) / len(pred); bal = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
    return dict(tp=tp, tn=tn, fp=fp, fn=fn, agree=agree, bal=bal)


def main():
    d = np.load(DATA, allow_pickle=True)
    actions, init = d["actions"], d["init"].astype(np.float32)
    rear_sat, succ_c = d["rear_sat"], d["drift_success"].astype(bool)
    mu = float(d["mu"][0]); R = len(actions)
    P = make_param_batch(VehicleParams(mu=mu, mass=1684.0), 1, dtype=torch.float32)
    lr = float(P["lr"][0])
    mlp = ResidualDynamicsMLP(); mlp.load_state_dict(torch.load(MLP, map_location=DEV)); mlp.eval()

    feats, kins = [], []
    for i in range(R):
        f, k = replay(actions[i], init[i], P, mlp, lr); feats.append(f); kins.append(k)

    rng = np.random.default_rng(0); idx = rng.permutation(R); tr, va = idx[:130], idx[130:]
    Xtr = np.concatenate([feats[i] for i in tr]).astype(np.float32)
    Ytr = np.concatenate([rear_sat[i].astype(np.float32) for i in tr])
    X = torch.tensor(Xtr); Y = torch.tensor(Ytr)
    head = RearSaturationHead(); head.set_norm(X)
    pos_w = torch.tensor([(Y == 0).sum() / max((Y == 1).sum(), 1)])
    opt = torch.optim.Adam(head.parameters(), lr=2e-3)
    lossf = torch.nn.BCEWithLogitsLoss(pos_weight=pos_w)
    n = len(Y)
    for ep in range(400):
        opt.zero_grad(); b = torch.randint(0, n, (4096,))
        loss = lossf(head(X[b]), Y[b]); loss.backward(); opt.step()
    head.eval()

    # per-step rear_sat agreement (val) with proxy vs head
    proxy_ag = head_ag = stot = 0
    for i in va:
        ar = np.abs(np.array(feats[i])[:, 4]); proxy = ar >= RS_THR
        with torch.no_grad():
            hp = (head(torch.tensor(np.array(feats[i], np.float32))) > 0).numpy()
        truth = rear_sat[i].astype(bool)
        proxy_ag += int((proxy == truth).sum()); head_ag += int((hp == truth).sum()); stot += len(truth)
    print(f"val rear_sat per-step agree:  proxy={proxy_ag/stot:.3f}  head={head_ag/stot:.3f}")

    # drift_success consistency (ALL rollouts) proxy vs head
    for tag, use_head in (("proxy |alpha_rear|>=0.10", False), ("learned head", True)):
        pred = np.zeros(R, bool)
        for i in range(R):
            if use_head:
                with torch.no_grad():
                    rs = (head(torch.tensor(np.array(feats[i], np.float32))) > 0).numpy()
            else:
                rs = np.abs(np.array(feats[i])[:, 4]) >= RS_THR
            pred[i] = drift_success_from(rs, np.array(kins[i]))
        c = confusion(pred, succ_c)
        print(f"  [{tag:28s}] agree={c['agree']:.3f} bal_acc={c['bal']:.3f} "
              f"TP={c['tp']} TN={c['tn']} FP={c['fp']} FN={c['fn']}")

    torch.save(head.state_dict(), HEAD_OUT)
    print(f"saved {HEAD_OUT}")
    print(f"GATE A1.iii: agree>=0.90 AND bal_acc>=0.90 (FP stays 0 = safe-to-train)")


if __name__ == "__main__":
    main()
