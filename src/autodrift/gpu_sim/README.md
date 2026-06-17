# gpu_sim — multi-fidelity GPU vehicle simulator (sub-project)

A GPU-batched vehicle simulator exposed as a **ladder of fidelity rungs behind one set of interfaces**,
so PPO can pretrain on a fast-coarse config and posttrain on an accurate-slow config without the
consumers (env, training loop, certificate harness) ever knowing which rung they hold.

**Design spec:** `docs/multi-fidelity-gpu-rewrite-design-2026-06.md` (the *why*; this README is the *how/what*).

## Directory
```
gpu_sim/
├── contracts.py        # THE interfaces (import-cheap, no Chrono): Model, FidelityConfig,
│                       #   FidelityCertificate, StateContract (PLANAR_SUBSTATE)
├── resolver.py         # build_model(cfg) -> Model ; available_rungs()
├── rungs/
│   ├── __init__.py     # ModuleModel adapter (wraps a flat physics module behind Model)
│   ├── rung0_planar.py     # wraps gpu_physics_pwr3   (17-dim, fast/coarse — PRETRAIN)
│   ├── rung1_kinematic.py  # wraps gpu_vehicle_tier_a (30-dim; RED cert; +geometric_fz variant)
│   └── rung2_dae.py        # full-linkage DAE — NOT built (gated on the T3a falsification)
├── certify.py          # certify(cfg) -> FidelityCertificate (vs frozen Chrono)   [T0, stub]
├── env.py              # build_env(cfg) for PPO                                    [T0, stub]
└── README.md
```

## The three interface contracts (`contracts.py`)

### 1. `StateContract` — `PLANAR_SUBSTATE`
The 9 canonical names `(x, y, psi, vx, vy, yaw_rate, steer, throttle, brake)` every rung MUST expose
in its `IDX`. A rung may carry any extra DOFs (roll/pitch/corner-travel/…) in any layout; the obs72,
reward, termination and certificate readers address state **only by these names** (never raw integer
columns). `validate_state_contract(idx, name)` enforces it; rung-1 supplies aliases
(`psi→yaw`, `yaw_rate→wz`). This is the seam that makes the rungs a coherent ladder.

### 2. `Model` (Protocol)
The runtime stepping interface — the call signature pwr3 and tier_a already share verbatim:
```
make_param_batch(phys, n, mu, device, dtype) -> P
init_state(vx0, vy0, yaw0, P)                 -> (state[N, state_dim], gear[N])
physics_step(state, action[N,3], gear, P, dt) -> (next_state, next_gear, diag)
```
plus `name`, `state_dim`, `IDX` (StateContract-valid), `deterministic_switches`. The `ModuleModel`
adapter (`rungs/__init__.py`) wraps any flat physics module to satisfy this.

### 3. `FidelityConfig` / `FidelityCertificate`
`FidelityConfig` = the `(vehicle_variant × rung × knobs)` selector (knobs: `substeps`, `tyre_transient`,
`sigma_scale`, `n_iter`, `dof_flags`). `build_model(cfg)` maps it to a `Model`.
`FidelityCertificate` = the **measured** accuracy-vs-Chrono a config earns (`drift_beta24`,
`avoid_vx_rmse`, `collision_bal_acc`, `throughput`). **The arbiter for pretrain/posttrain config
selection is `.dominates()` on the certificate — NEVER DOF count** (the dig showed higher order does
not monotonically help: tier_a regressed drift). `gate emission requires `deterministic_switches=True`.

## Consumer contract (how to use it)
```python
from autodrift.gpu_sim import FidelityConfig, build_model
cfg   = FidelityConfig(rung=0, vehicle_variant="sedan_tmeasy", sigma_scale=0.165)
model = build_model(cfg)
P     = model.make_param_batch(model.build_phys(cfg), N, mu=0.48, device="cuda", dtype=torch.float32)
st, g = model.init_state(vx0, vy0, yaw0, P)
st, g, diag = model.physics_step(st, action, g, P, 0.02)
vx    = st[:, model.IDX["vx"]]          # by NAME — works on every rung
```
Smoke: `python scripts/feasibility_audit/gpu_sim_smoke.py` (drives rung-0 & rung-1 through one path).

## Build status (maps to the design roadmap §6)
| piece | status |
|---|---|
| `contracts.py` (interfaces) | ✅ done |
| `resolver.py` + `rungs/` (rung-0, rung-1 adapters) | ✅ done, smoke-passing |
| rung-1 `geometric_fz` (T3a experiment) | ✅ wired (verdict: did NOT close drift — see T3a gate) |
| obs72-by-name builder (obs72_from_state accepts idx) | ✅ done — default=planar (byte-identical, 19 tests pass); rung-agnostic |
| gear dead-band → `deterministic_switches=True` | ⬜ T0 (blocks certificate emission) |
| `certify.py` (FidelityCertificate harness) | ✅ done — drift+avoid by-name, eager, validated vs gates |
| torch.compile throughput bench (gpu_throughput.json) | ✅ done — 126x @16k, peak ~380M st/s (adapter); raw-leaf 582M |
| `env.py` (build_env for PPO) | ⬜ T0 (needs obs72-by-name) |
| `rung2_dae.py` (full-linkage DAE) | ⛔ gated on T3a GO |
