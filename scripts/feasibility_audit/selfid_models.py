"""Self-ID models that REPLACE the FiLM vehicle one-hot with vehicle identity INFERRED FROM INTERACTION
(a human doesn't get a vehicle label; they feel the car out). Four-arm VoI experiment (see task #42):

  A  one-hot          : the certified FiLMAvoidActorCritic (oracle-ID ceiling)   [distill_both_3vehicle_film.py]
  B  no-ID            : FiLMZ with z=0 / single shared head (no vehicle info; the floor)
  C1 RMA two-phase    : teacher z = encoder(real extrinsics) -> FiLM; student z_hat = phi((obs,action) history)
                        regressed to z; deploy with z_hat ONLY (no label). Continuous z -> generalises to unseen veh.
  C2 end-to-end GRU   : GRU over (obs72, prev_action3) history -> implicit z -> gate + heads. No label, no teacher.

KEY GROUNDED FACTS (from the infra dig, 2026-06-18):
- On Chrono (the validation arbiter) the 3 vehicles are distinct multibody VARIANTS; mass, FWD/RWD drivetrain,
  TMeasy tyre and CG genuinely differ. The planar lf/lr/cf/cr are INERT for Chrono (variant template owns them).
- On the GPU planar surrogate the "3 vehicles" differ ONLY in total mass (gpu_physics_pwrBD is a single Sedan model
  + a RWD-kludge), so faithful self-ID must be measured on CHRONO, not the surrogate.
- Deploy contract is obs72 with NO frame-stacking; the (obs,action) history window for phi / the GRU is maintained
  OUTSIDE the env (in the rollout loop + run_episode), never changing the obs72 contract.

z = real extractable per-vehicle extrinsics (NOT the road param mu, which would be a leakage trap):
  [mass/2000, front_drive_share(FWD=1,RWD=0)]  -> sedan(0.725,1.0) uazbus(1.429,0.0) bmw(0.900,0.0): 3 distinct pts.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase4_f2_train as f2  # noqa: E402

OBS72 = f2.HUMAN_VIEW_OBS_DIM          # 72
ACT_DIM = f2.ACT_DIM                   # 3
HID = f2.HIDDEN_SIZE                   # 256
PRIV_DIM = f2.PRIV_DIM                 # 6 (critic parity, unused at deploy)
LOG_STD_INIT = f2.LOG_STD_INIT

# Real per-vehicle extrinsics the policy could only get by FEELING THE CAR OUT (Chrono-faithful; mu excluded).
# front_drive_share: FWD=1.0 (Sedan) / RWD=0.0 (UAZBUS, BMW). mass in kg.
VEHICLE_MASS = {"sedan": 1450.0, "uazbus": 2858.0, "bmw": 1800.0}
VEHICLE_FRONT_DRIVE = {"sedan": 1.0, "uazbus": 0.0, "bmw": 0.0}
Z_DIM = 2

def vehicle_extrinsics(name: str) -> np.ndarray:
    """The teacher's privileged z: real, continuous, generalises to an unseen 4th vehicle."""
    return np.asarray([VEHICLE_MASS[name] / 2000.0, VEHICLE_FRONT_DRIVE[name]], dtype=np.float32)


# =====================================================================================
# C1 / B model: FiLM conditioned on a CONTINUOUS z (replaces the 3-way one-hot). Single drift + single
# avoid head on the z-FiLM trunk (the z-FiLM trunk IS the per-vehicle representation -- the proven S2 lever;
# continuous z cannot hard-route discrete heads, so we collapse the 3 avoid heads into 1 z-conditioned head).
# Input layout: obs_in = [obs72 | z(Z_DIM)]  (mirrors how the one-hot model used obs75 = [obs72 | onehot3]).
# =====================================================================================
class FiLMZActorCritic(nn.Module):
    def __init__(self, z_dim: int = Z_DIM, *, obs72: int = OBS72, act_dim: int = ACT_DIM,
                 hidden: int = HID, priv_dim: int = PRIV_DIM):
        super().__init__()
        self.z_dim = int(z_dim); self.obs72 = int(obs72); self.act_dim = int(act_dim)
        self.hidden = int(hidden); self.priv_dim = int(priv_dim)
        self.obs_dim = self.obs72 + self.z_dim          # the [obs72 | z] input contract
        self.gated = True
        self.trunk_fc1 = nn.Linear(self.obs72, hidden)  # trunk reads obs72 ONLY; z enters via FiLM
        self.trunk_fc2 = nn.Linear(hidden, hidden)
        self.film1 = nn.Linear(self.z_dim, 2 * hidden)
        self.film2 = nn.Linear(self.z_dim, 2 * hidden)
        for film in (self.film1, self.film2):           # FiLM-identity init (gamma=1, beta=0)
            nn.init.zeros_(film.weight)
            with torch.no_grad():
                film.bias[:hidden] = 1.0
                film.bias[hidden:] = 0.0
        self.actor_gate = nn.Linear(hidden, 1)
        self.drift_head = nn.Linear(hidden, act_dim)
        self.avoid_head = nn.Linear(hidden, act_dim)    # SINGLE z-conditioned avoid head
        self.log_std = nn.Parameter(torch.full((act_dim,), float(LOG_STD_INIT)))
        self.critic = nn.Sequential(
            nn.Linear(self.obs_dim + priv_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def _split(self, obs_in: torch.Tensor):
        return obs_in[..., :self.obs72], obs_in[..., self.obs72:self.obs72 + self.z_dim]

    def _film(self, film, z):
        gb = film(z); return gb[..., :self.hidden], gb[..., self.hidden:]

    def _trunk(self, obs_in: torch.Tensor) -> torch.Tensor:
        o, z = self._split(obs_in)
        g1, b1 = self._film(self.film1, z); g2, b2 = self._film(self.film2, z)
        h1 = torch.tanh(g1 * self.trunk_fc1(o) + b1)
        return torch.tanh(g2 * self.trunk_fc2(h1) + b2)

    def actor(self, obs_in): return self._trunk(obs_in)

    def _raw_mean(self, obs_in: torch.Tensor) -> torch.Tensor:
        if obs_in.shape[-1] != self.obs_dim:
            raise ValueError(f"actor input must be obs{self.obs_dim} ([obs72|z{self.z_dim}]); got {obs_in.shape[-1]}")
        h = self._trunk(obs_in)
        g = torch.sigmoid(self.actor_gate(h))
        return g * self.drift_head(h) + (1.0 - g) * self.avoid_head(h)

    def actor_forward(self, obs_in): return torch.tanh(self._raw_mean(obs_in))

    @torch.no_grad()
    def act(self, obs_in: np.ndarray) -> np.ndarray:
        arr = np.asarray(obs_in, dtype=np.float32); single = arr.ndim == 1
        out = self.actor_forward(torch.as_tensor(arr.reshape(1, -1) if single else arr,
                                                 dtype=torch.float32)).cpu().numpy().astype(np.float32)
        return out[0] if single else out


# =====================================================================================
# C1 phase-2: adaptation module phi((obs72, prev_action3) history window) -> z_hat, regressed to teacher z.
# Flattened-window MLP (RMA's encoder is a small 1D-conv/MLP; an MLP over a fixed window is the simplest form).
# =====================================================================================
class AdaptationMLP(nn.Module):
    def __init__(self, *, window: int = 20, obs72: int = OBS72, act_dim: int = ACT_DIM,
                 z_dim: int = Z_DIM, hidden: int = 128):
        super().__init__()
        self.window = int(window); self.in_per_step = obs72 + act_dim
        self.net = nn.Sequential(
            nn.Linear(self.window * self.in_per_step, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, z_dim))

    def forward(self, window_flat: torch.Tensor) -> torch.Tensor:
        return self.net(window_flat)   # (N, z_dim)


# =====================================================================================
# C2 model: end-to-end GRU over (obs72, prev_action3). Hidden state IS the implicit vehicle embedding;
# gate + heads read it directly (no label, no teacher z). Deploy: carry hidden state across the episode.
# =====================================================================================
class GRUSelfIDActorCritic(nn.Module):
    def __init__(self, *, obs72: int = OBS72, act_dim: int = ACT_DIM, hidden: int = HID, priv_dim: int = PRIV_DIM):
        super().__init__()
        self.obs72 = int(obs72); self.act_dim = int(act_dim); self.hidden = int(hidden); self.priv_dim = int(priv_dim)
        self.in_dim = self.obs72 + self.act_dim   # per-step input = [obs72 | prev_action3]
        self.gated = True
        self.gru = nn.GRU(self.in_dim, hidden, batch_first=True)
        self.actor_gate = nn.Linear(hidden, 1)
        self.drift_head = nn.Linear(hidden, act_dim)
        self.avoid_head = nn.Linear(hidden, act_dim)
        self.log_std = nn.Parameter(torch.full((act_dim,), float(LOG_STD_INIT)))
        self.critic = nn.Sequential(
            nn.Linear(hidden + priv_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def _heads(self, h: torch.Tensor) -> torch.Tensor:
        g = torch.sigmoid(self.actor_gate(h))
        return torch.tanh(g * self.drift_head(h) + (1.0 - g) * self.avoid_head(h))

    def forward_seq(self, seq: torch.Tensor) -> torch.Tensor:
        """seq (N, T, obs72+act) -> action mean (N, T, act) over the whole trajectory (BPTT BC)."""
        out, _ = self.gru(seq)
        return self._heads(out)

    @torch.no_grad()
    def act_step(self, obs72_prev_act: np.ndarray, hidden_state):
        """One deploy step. obs72_prev_act = [obs72 | prev_action3] (in_dim,). Returns (action3, new_hidden)."""
        x = torch.as_tensor(np.asarray(obs72_prev_act, dtype=np.float32).reshape(1, 1, -1))
        out, h_new = self.gru(x, hidden_state)
        a = self._heads(out[:, -1, :]).cpu().numpy().astype(np.float32)[0]
        return a, h_new
