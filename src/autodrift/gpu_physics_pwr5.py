"""PWR5 = pwr3 (gear-SEED fix) + the MEASURED DRIVELINE ROTATIONAL-INERTIA effect on throttle release.

This is gpu_physics_pwr3 with ONE physically-motivated, MEASURED addition: an explicit
engine/driveline angular-speed state that carries rotational inertia, so on a fast throttle
TRANSIENT the engine speed LEADS the rigid ``vx/r_eff * gear * final`` prediction (as Chrono does)
instead of tracking it instantly.

ROOT CAUSE (independently verified from the ground-truth replay telemetry
``runs/feasibility_audit/phase4_f2/avoid_term_decomp_{chrono,model_pwr3}.npz``):
  * The Chrono Sedan powertrain is EngineSimpleMap + AutomaticTransmissionSimpleMap (both MASSLESS
    maps; ``Advance()`` is a no-op) driving a ``ShaftsDriveline2WD`` -- a REAL ChShaft system whose
    inertias (Driveshaft 0.5, Differential 0.6 kg.m^2; Conical final-drive 0.2) plus the wheel-spin
    inertias couple the engine speed to the wheels through a STIFF shaft chain (NO torque converter).
  * MEASURED: at SETTLED steady cruise Chrono's engine rpm equals the model's rigid prediction
    (excess ~0-6 rpm -> the coupling IS rigid at steady state). On the throttle RELEASE down-ramp,
    Chrono's engine spins +260..+485 rpm (mean ~340, peaks ~560) ABOVE rigid: the spinning driveline
    inertia keeps the engine turning as the map torque drops -> the "+315 rpm" engine-inertia lead.
  * The lead DECAYS first-order with a MEASURED time constant tau = 189 ms (sigma 16 ms across the
    6 down-ramp episodes), fit to Chrono's rpm-excess decay trace (NOT to the avoid gate). This tau
    is consistent with the JSON shaft chain: I_eff (engine frame) ~ 0.74 kg.m^2 from the driveline +
    wheel inertias referred through gear^2*final^2 (the SimpleMap engine block itself is 0).

IMPLEMENTATION (A, the more-measured of the two): the engine-speed LEAD ``delta = omega_eng -
omega_rigid`` is a state carrying the driveline inertia, integrated by
    d(delta)/dt = T_eng / I_eff  -  delta / tau
so (i) under drive torque the lead BUILDS to the MEASURED steady windup (engine-speed excess ~ 1.71
rpm per Nm of driveshaft torque, corr 0.84 in the ground-truth trace) and (ii) on throttle RELEASE the
lead BLEEDS DOWN first-order over tau = 189 ms (the measured rpm-excess decay), while at zero drive the
lead -> 0 (steady cruise, matching Chrono's ~0 excess at the settled tail). I_eff = 0.83 kg.m^2 is the
engine-frame inertia implied by the windup slope, INDEPENDENTLY consistent with the JSON ChShaft chain
(~0.74 kg.m^2). The engine TORQUE map is then evaluated at the led rpm (omega_rigid + delta), so the
inertia reaction term ``-I_eff*(gear*final)^2*domega_axle/dt`` is carried implicitly and the drive force
is whatever the MEASURED engine map gives at the elevated rpm -- it is NOT tuned to the gate.

HONEST CAVEAT (measured, reported in the gate): the partial-throttle engine torque map is nearly FLAT
in the 1650-2000 rpm band (~50.4 Nm @ 1650 vs ~49.5 @ 1965 at thr=0.16), so the +315 rpm lead
produces only a SMALL sustained drive-force change. The "-0.435 m/s^2 down-ramp ax gap" in the raw
finite-diff ``ax`` telemetry is dominated by suspension/pitch noise, NOT a driveshaft-torque gap: the
measured ``T_driveshaft`` already matches pwr3 within ~140 N across the down-ramp. So this effect is a
faithful, measured correction of a real omission, but its avoid-gate impact is expected to be small.
The gate (scripts/feasibility_audit/gpu_pwr5_gate.py) reports the measured numbers either way.

The drift regime uses tiny throttle (the engine map is near idle/brake torque, the rigid rpm is
already on a flat part of the map and the lead is negligible at near-zero drive) so the lateral drift
beta should be ~untouched -- verified by the gate.

----------------------------------------------------------------------------------------------------
Inherited pwr3 docstring (gpu_physics_relax + the front-axle traction cap + gear seed), retained:

PWR-TMeasy: gpu_physics_relax with the MEASURED partial-throttle DRIVEN-force traction limit.

This is an exact copy of ``autodrift.gpu_physics_relax`` (L1 RELAX-TMeasy: EXACT Chrono TMeasy tyre
+ physical slip-relaxation, sigma measured) with TWO measured changes, both extracted from the real
isolated ``veh.Sedan()`` by ``scripts/feasibility_audit/extract_chrono_powertrain.py``:

  (1) A FRONT-AXLE DRIVE-FORCE TRACTION CAP (the localized cause of the avoidance vx over-speed).
      WHAT WAS MEASURED: the Chrono Sedan driveline is a ``ShaftsDriveline2WD`` whose
      ``GetDrivenAxleIndexes()`` is [0] = the FRONT axle (x=+1.388); ``GetSpindleTorque(0, L/R)``
      carries the full drive torque, the rear axle carries ZERO. The Sedan is FRONT-wheel drive. The
      STEADY-STATE engine-torque blend, gear schedule, conical final-drive (0.2) and rpm are all
      VERIFIED CORRECT (engine torque within 1.5% of Chrono at every throttle; gear 2 @ 8 m/s in
      both; final drive 0.2 in the JSON; F_wheel matches the read-off spindle force within ~1-7% at
      matched gear). So the partial-throttle TORQUE and the GEAR were NOT the bug.

      THE BUG is which axle's friction limit caps the drive force. gpu_physics_relax drives the REAR;
      the Sedan drives the FRONT. Under forward acceleration the quasi-static load transfer UNLOADS
      the front axle and LOADS the rear, so a rear-drive model has the friction cap of the load-
      GAINING axle while the real (front-drive) car is traction-limited on the load-LOSING FRONT.
      Measured at the avoid friction (e.g. mu=0.3625), a thr 0.16->0.55 step at 8 m/s gives ax=1.56
      m/s^2 / spindle force 2906 N in the real Chrono Sedan, vs 3.26 m/s^2 / 5677 N at mu=0.8 -- the
      driven force is FRICTION-LIMITED on the front axle. Replaying the avoid oracle, gpu_physics_
      relax shows ax ~3.0-3.3 m/s^2 in the throttle ramp where Chrono shows ~1.1-1.7 (the ~1.75x).

      THE FIX (this module): keep the RWD powertrain unchanged (so the drift regime, which depends on
      rear-drive longitudinal slip, is untouched) and add ONE traction cap: the net per-wheel drive
      force is capped by the FRONT friction circle sqrt((mu*Fz_front)^2 - Fy_front^2). The cap is
      derived from the MEASURED fact that Chrono's drive force is traction-limited on the front axle.
      At low drive (drift, ~1 kN) the cap is slack -> drift is preserved. At high drive on low-mu
      avoidance the cap bites -> the ~1.75x over-force is removed. This is NOT a tuned drive_scale;
      the cap value is the measured front-axle friction budget.

  (2) MEASURED cruise resistance (Chrono Sedan has NO aero body): drag_coeff = 0,
      rolling_resist_coeff = 0.0282 (extract_chrono_coastdown.py / gpu_physics_coast), replacing the
      drift-saddle-CALIBRATED drag=0.80 / Crr=0.03.

Everything else (the EXACT TMeasy tyre, sigma_scale, geometry, gearbox FSM, RWD wheel-spin states,
load transfer, sub-stepped integration) is IDENTICAL to gpu_physics_relax. Both gates are run by
``scripts/feasibility_audit/surrogate_physics_pwr_gate.py``.

----------------------------------------------------------------------------------------------------
Original gpu_physics_relax docstring (unchanged tyre/relaxation core, retained for reference):

RELAX-TMeasy branchless GPU physics vehicle-dynamics model for AutoDrift (faithful rewrite, L1).

This is the next incremental layer on top of ``autodrift.gpu_physics_tmeasy`` (the L0 EXACT-tyre
model). L0 already replaces the calibrated Pacejka tyre with Chrono's **EXACT TMeasy force
curves** (no grip fudge), reaching beta@24 p90 ~0.0403 but PLATEAUING there. The residual was
diagnosed as a SIGNED, sign-reversing TRANSIENT whose worst cases are deep drift-entries where
the planar single-body model recovers the drift entry FASTER than Chrono. That timing/sign
signature is the classic tyre RELAXATION transient: the tyre force does not respond instantly to
a slip change but builds up over a relaxation length ``sigma``.

L0 carried a FORCE-relaxation state (``fyf_relax``/``fyr_relax``) whose ``relax_len`` (~0.05-0.10 m)
was an ARTIFACT of calibrating against a wrong Pacejka tyre (effectively quasi-static). THIS
module (L1) replaces that with a PHYSICAL SLIP-relaxation: a per-axle/per-wheel lagged slip
state whose relaxation length ``sigma`` is MEASURED from the EXACT Chrono TMeasy tyre (NOT fit to
the drift data) by ``scripts/feasibility_audit/extract_chrono_tmeasy_relax.py``:

    sigma = dF0 / sigma0   (initial slip stiffness / TMeasy Dahl contact stiffness, sigma0=1e5 N/m)
    measured: sigma_alpha ~ 0.65 m, sigma_kappa ~ 0.80 m at the drift-relevant rear load (~4 kN),
    with a strong load dependence (sigma scales ~linearly with cornering stiffness / Fz).

The slip entering the EXACT-curve lookup is a relaxed/lagged version of the instantaneous slip:

    d(alpha_lag)/dt = (|v_x| / sigma_alpha(Fz)) * (alpha_inst - alpha_lag)
    d(kappa_lag)/dt = (|v_x| / sigma_kappa(Fz)) * (kappa_inst - kappa_lag)

force = EXACT_curve(alpha_lag, kappa_lag, Fz). The lag state initialises to the INSTANTANEOUS
slip at reset (tyre starts in slip equilibrium). The EXACT tyre, grips=1.0, and everything else
(geometry, mass, RWD powertrain, 6-speed auto gearbox, quasi-static load transfer, sub-stepped
semi-implicit integration) are IDENTICAL to ``gpu_physics_tmeasy`` — only the lag moved from the
force to the slip, and ``sigma`` is now the measured physical relaxation length.

Everything is BRANCHLESS and BATCHED over N environments: there is no python loop over N, no
per-env ``if``; all regime selection is ``torch.where`` / masking. It mirrors the style of
``gpu_surrogate.py`` (``ParamBatch``, ``make_param_batch``, ``[N,...]`` torch state).

State layout (PHYS_STATE_DIM = 17):
    [x, y, psi, vx, vy, yaw_rate, steer, throttle, brake, omega_rl, omega_rr,
     ax_f, ay_f, alpha_f_lag, alpha_r_lag, sx_rl_lag, sx_rr_lag]
where omega_{rl,rr} are the two rear-wheel angular speeds, ax_f/ay_f are the filtered body
accelerations feeding quasi-static load transfer, and alpha_f_lag/alpha_r_lag/sx_rl_lag/sx_rr_lag
are the relaxation-length-lagged tyre slips (front/rear slip angle + the two rear long. slips) —
the SLIP transient that holds the tyre force (and hence sideslip) up during a drift entry.

The model is validated offline against saved Chrono rollouts by
``scripts/feasibility_audit/surrogate_physics_relax_gate.py`` (same open-loop divergence gate as
the residual: beta-div @24, vx RMSE), next to the L0 exact-tyre 0.0403 and grey-box 0.0156.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

# Default location of the EXACT TMeasy curves extracted from the running Chrono Sedan tyre.
_CURVE_NPZ = Path(__file__).resolve().parents[2] / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz"

# ----------------------------------------------------------------------------- layout
# state: [x, y, psi, vx, vy, yaw_rate, steer, throttle, brake, omega_rl, omega_rr,
#         ax_f, ay_f, alpha_f_lag, alpha_r_lag, sx_rl_lag, sx_rr_lag]
# alpha_f_lag/alpha_r_lag/sx_rl_lag/sx_rr_lag are the relaxation-length-lagged tyre SLIPS
# (front/rear slip angle + the two rear longitudinal slips): the TMeasy SLIP transient that
# holds the tyre force (hence sideslip) up during a drift entry. The EXACT curve is evaluated at
# the LAGGED slip, so the force responds over the measured physical relaxation length sigma.
# PWR5: +1 slot (index 17) = omega_eng, the engine angular speed [rad/s] carrying driveline
# rotational inertia. It relaxes first-order toward the rigid value omega_eng_rigid =
# omega_axle / final_drive / gear_ratio over the MEASURED time constant DRIVELINE_TAU, so on a fast
# throttle transient the engine speed LEADS the rigid prediction (the +315 rpm Chrono effect) and the
# engine torque map is evaluated at the led rpm.
PHYS_STATE_DIM = 18
IDX = dict(
    x=0, y=1, psi=2, vx=3, vy=4, yaw_rate=5, steer=6, throttle=7, brake=8,
    omega_rl=9, omega_rr=10, ax_f=11, ay_f=12,
    alpha_f_lag=13, alpha_r_lag=14, sx_rl_lag=15, sx_rr_lag=16,
    omega_eng=17,
)
ACT_DIM = 3

# MEASURED driveline-inertia engine-speed relaxation time constant [s], fit to Chrono's rpm-excess
# decay on the avoid throttle-release down-ramp (avoid_term_decomp_chrono.npz, episodes 72-77):
# log-linear fit of (omega_eng - omega_eng_rigid) over the release window gives tau = 189 +/- 16 ms.
DRIVELINE_TAU = 0.189
# MEASURED engine-frame effective inertia [kg.m^2]: from the ground-truth torque-proportional windup
# slope (engine-speed excess ~ 1.71 rpm per Nm of driveshaft torque, corr 0.84). With the relation
# steady_lead = (tau/I_eff)*T_eng this gives I_eff = ratio*tau*(60/2pi)/1.71 = 0.83 kg.m^2 --
# INDEPENDENTLY consistent with the JSON ChShaft chain estimate ~0.74 kg.m^2 (Driveshaft 0.5 +
# Differential 0.6 referred by gear^2, + 2 axle-shaft 0.4 + 4 wheel 0.42 referred by (gear*final)^2;
# the SimpleMap engine block itself is 0 -- the inertia is all driveline + wheels). NOT fit to the gate.
DRIVELINE_I_EFF = 0.83

# Chrono Sedan spec (docs/chrono-sedan-physics-extracted.json) — engine + gearbox tables.
# Full-throttle engine torque map (rpm -> Nm).
ENGINE_RPM = (1000.0, 1400.0, 1600.0, 4500.0, 5000.0, 5500.0, 6000.0, 6500.0)
ENGINE_TQ_FULL = (236.8, 338.3, 370.0, 370.0, 353.3, 321.2, 294.4, 244.6)
# Zero-throttle (engine-braking) map (rpm -> Nm). Extrapolated below 1500 to 0.
ENGINE_BRAKE_RPM = (0.0, 1500.0, 3000.0, 4500.0, 5000.0, 6000.0, 6500.0)
ENGINE_TQ_BRAKE = (0.0, -10.0, -15.0, -30.0, -50.0, -70.0, -100.0)
# 6-speed automatic ratios (Chrono: T_out = T_in / ratio).
GEAR_RATIOS = (0.265, 0.489, 0.784, 1.063, 1.276, 1.499)
# Per-gear shift thresholds in *motor rpm* (down, up). gear index 0..5.
SHIFT_DOWN = (1000.0, 1200.0, 1400.0, 1600.0, 1800.0, 2000.0)
SHIFT_UP = (4000.0, 4500.0, 4500.0, 4500.0, 4500.0, 4500.0)


@dataclass
class PhysParams:
    """Scalar physics parameters for the Chrono Sedan (defaults from the extracted spec).

    A handful are *calibrated* against the saved Chrono drift data (noted inline); the
    rest are read directly off ``docs/chrono-sedan-physics-extracted.json``.
    """

    # --- geometry / mass (extracted spec) ---
    mass: float = 1683.97          # total vehicle mass [kg]
    izz: float = 1053.5            # yaw inertia [kg.m^2]
    wheelbase: float = 2.776       # [m]
    # symmetric suspension placement => lf=lr=wheelbase/2, but front axle load share 0.489.
    front_axle_share: float = 0.489
    h_cg: float = 0.43             # COM height [m] (extracted; effective transfer calibrated via h_cg_scale)
    track_f: float = 1.5958        # front wheeltrack [m]
    track_r: float = 1.6           # rear wheeltrack [m]
    gravity: float = 9.81

    # --- steering / actuators (match gpu_surrogate filter) ---
    max_steer: float = 0.43633     # max road-wheel steer [rad] (= 25 deg)
    max_steer_rate: float = 3.5    # [rad/s]
    steer_tau: float = 0.06        # [s]
    throttle_tau: float = 0.08     # [s] first-order actuator lag on throttle
    brake_tau: float = 0.08        # [s] first-order actuator lag on brake

    # --- tyre (EXACT Chrono TMeasy curves; NO Pacejka calibration, NO grip fudge) ---
    # The pac_* / k_deg fields below are UNUSED by the exact-TMeasy tyre (the force law is the
    # tabulated Chrono curve in chrono_tmeasy_curves.npz). They are retained only so this
    # PhysParams is a drop-in for gpu_physics.PhysParams (same field set / calibration script).
    mu0: float = 0.8               # reference friction (terrain mu enters as scale = mu/mu0)
    pac_Bx: float = 11.0           # UNUSED (exact-TMeasy)
    pac_Cx: float = 1.5            # UNUSED
    pac_Dx: float = 1.32           # UNUSED
    pac_Ex: float = 0.2            # UNUSED
    pac_By: float = 8.0            # UNUSED
    pac_Cy: float = 1.45           # UNUSED
    pac_Dy: float = 1.10           # UNUSED
    pac_Ey: float = -0.5           # UNUSED
    k_deg: float = 0.10            # UNUSED (degressive load dependence is IN the table)
    # L0 FORCE-relaxation lengths [m] are UNUSED here: L1 relaxes the SLIP instead (see below).
    # Retained only so this PhysParams is a drop-in for gpu_physics_tmeasy.PhysParams.
    relax_len_f: float = 0.10      # UNUSED in L1 (slip relaxation replaced force relaxation)
    relax_len_r: float = 0.05      # UNUSED in L1
    # --- PHYSICAL tyre SLIP-relaxation length sigma [m] (MEASURED, not fit to drift data) ---
    # Measured by extract_chrono_tmeasy_relax.py as sigma = dF0/sigma0 off the EXACT Chrono
    # TMeasy curves (sigma0 = 1e5 N/m Dahl contact stiffness). The drift-band (~4 kN) medians
    # are the defaults; the actual per-wheel sigma is scaled by the runtime load via
    # sigma(Fz) = sigma_alpha * (dFy0(Fz)/dFy0_nom) -- i.e. the measured LOAD DEPENDENCE, with
    # the per-load slope read straight off the same curves at runtime. sigma_scale is a single
    # global multiplier kept ONLY as a non-tyre sensitivity knob for the gate (default 1.0,
    # i.e. the raw measured value -- it is NOT fit to the drift data).
    sigma_alpha: float = 0.651     # MEASURED lateral relaxation length [m] @ drift load (~4 kN)
    sigma_kappa: float = 0.796     # MEASURED longitudinal relaxation length [m] @ drift load
    sigma_scale: float = 1.0       # global sigma multiplier (1.0 = raw measured; sensitivity only)
    # front/rear lateral grip scales: FAITHFUL REWRITE => both 1.0 (no fudge). The exact
    # TMeasy axle balance comes from the curve + load transfer, not a hand-tuned scale.
    front_grip_scale: float = 1.0
    rear_grip_scale: float = 1.0

    # --- powertrain / driveline ---
    r_eff: float = 0.3237          # effective rolling radius [m]
    i_wheel: float = 0.679         # per-wheel + lumped driveline inertia [kg.m^2]
    final_drive: float = 0.2       # conical final drive (T_axle = T_driveshaft / 0.2)
    max_engine_rpm: float = 6500.0
    idle_rpm: float = 800.0
    max_brake_torque: float = 2000.0  # per-wheel brake torque at full brake [N.m] (calibrated)
    # --- MEASURED cruise longitudinal resistance (Chrono Sedan COASTDOWN; Sedan has NO aero) ---
    # extract_chrono_coastdown.py: coast decel is ~constant ~0.28 m/s^2 (no v^2 growth). MEASURED.
    rolling_resist_coeff: float = 0.0282  # MEASURED Crr (mean coast decel 0.28 m/s^2 / g, 9-13 m/s)
    drag_coeff: float = 0.0        # MEASURED: Sedan has no aero body (coast decel is speed-flat)

    # --- MEASURED driveline rotational-inertia engine-speed relaxation (PWR5) ---
    # tau for d(omega_eng)/dt = (omega_eng_rigid - omega_eng)/tau. MEASURED from Chrono's rpm-excess
    # decay on the avoid release down-ramp (189 +/- 16 ms); NOT fit to the gate. See module header.
    driveline_tau: float = DRIVELINE_TAU

    # --- calibration knobs (tuned against saved Chrono data) ---
    h_cg_scale: float = 1.0        # effective CG-height multiplier for load transfer
    drive_scale: float = 1.0       # overall driveline torque scale
    substeps: int = 4              # internal sub-steps per control step

    def as_dict(self) -> dict[str, float]:
        return {k: float(getattr(self, k)) for k in self.__dataclass_fields__ if k != "substeps"} | {
            "substeps": int(self.substeps)
        }


# Per-env broadcastable scalar keys (everything except the LUT tables, which are shared).
_PARAM_KEYS = (
    "mass", "izz", "wheelbase", "front_axle_share", "h_cg", "track_f", "track_r", "gravity",
    "max_steer", "max_steer_rate", "steer_tau", "throttle_tau", "brake_tau",
    "mu0", "pac_Bx", "pac_Cx", "pac_Dx", "pac_Ex", "pac_By", "pac_Cy", "pac_Dy", "pac_Ey", "k_deg",
    "relax_len_f", "relax_len_r", "sigma_alpha", "sigma_kappa", "sigma_scale",
    "front_grip_scale", "rear_grip_scale",
    "r_eff", "i_wheel", "final_drive", "max_engine_rpm", "idle_rpm", "max_brake_torque",
    "rolling_resist_coeff", "drag_coeff", "driveline_tau", "h_cg_scale", "drive_scale",
)


@dataclass
class PhysParamBatch:
    """Per-environment physics parameters as [N] tensors + shared LUT tables + terrain mu."""

    t: dict[str, torch.Tensor]
    mu: torch.Tensor                       # [N] terrain friction
    substeps: int = 4
    luts: dict[str, torch.Tensor] = field(default_factory=dict)

    def __getitem__(self, k: str) -> torch.Tensor:
        return self.t[k]

    @property
    def device(self) -> torch.device:
        return self.t["mass"].device

    @property
    def dtype(self) -> torch.dtype:
        return self.t["mass"].dtype


# cache the raw numpy curve arrays so repeated batch builds don't re-read the npz from disk.
_CURVE_CACHE: dict[str, "np.ndarray"] = {}


def _load_curve_arrays(path: Path | str = _CURVE_NPZ) -> dict[str, "np.ndarray"]:
    """Load (and cache) the extracted EXACT-TMeasy curve arrays from the npz file."""
    key = str(path)
    cached = _CURVE_CACHE.get(key)
    if cached is not None:
        return cached
    d = np.load(path)
    arrays = {k: d[k] for k in d.files}
    _CURVE_CACHE[key] = arrays
    return arrays


def _curve_luts(arrays: dict[str, "np.ndarray"], device, dtype) -> dict[str, torch.Tensor]:
    """Convert the loaded TMeasy curve arrays into shared LUT tensors for the tyre interpolation.

    The tyre uses pure Fx(kappa,Fz)/Fy(alpha,Fz) surfaces stored as Fx/Fz and Fy/Fz vs the
    REPORTED slip coordinate (so the table is normalised by load and bilinear-interpolated by
    (slip, Fz)). The peak-slip locations are precomputed for the combined-slip projection."""
    fz_grid = np.asarray(arrays["fz_grid"], dtype=np.float64)
    kappa_grid = np.asarray(arrays["kappa_grid"], dtype=np.float64)
    alpha_grid = np.asarray(arrays["alpha_grid"], dtype=np.float64)
    Fx = np.asarray(arrays["Fx"], dtype=np.float64)   # [nK, nF]
    Fy = np.asarray(arrays["Fy"], dtype=np.float64)   # [nA, nF]
    Fz_at_K = np.asarray(arrays["Fz_at_K"], dtype=np.float64)
    Fz_at_A = np.asarray(arrays["Fz_at_A"], dtype=np.float64)
    # store as force RATIOS (Fx/Fz, Fy/Fz) per (slip, Fz) so interpolation by load is exact and
    # the tyre simply multiplies by the wheel's actual Fz at runtime.
    fx_ratio = Fx / np.clip(Fz_at_K, 1.0, None)       # [nK, nF]
    fy_ratio = Fy / np.clip(Fz_at_A, 1.0, None)       # [nA, nF]
    # peak-slip location per Fz column (where each pure curve maxes) for combined-slip normaliser.
    kappa_peak = kappa_grid[np.argmax(np.abs(Fx), axis=0)]    # [nF]
    alpha_peak = alpha_grid[np.argmax(np.abs(Fy), axis=0)]    # [nF]

    # ---- PHYSICAL slip-relaxation length per Fz: sigma = dF0/sigma0 (TMeasy Dahl model) ----
    # dF0 = initial slip stiffness (dFy/dsy at sy->0, sy=tan(alpha) ; dFx/dsx at sx->0), read off
    # the EXACT steady curves at the smallest symmetric slip about zero; sigma0 = 1e5 N/m is the
    # Chrono ChTMeasyTire Dahl contact stiffness. This is the MEASURED physical relaxation length
    # (matches extract_chrono_tmeasy_relax.py); it carries the load dependence exactly (sigma
    # grows ~linearly with cornering stiffness / Fz), NOT fit to the drift data.
    TMEASY_SIGMA0 = 100000.0
    ap = alpha_grid[alpha_grid > 0].min(); an = alpha_grid[alpha_grid < 0].max()
    ip = int(np.where(alpha_grid == ap)[0][0]); ineg = int(np.where(alpha_grid == an)[0][0])
    kp = kappa_grid[kappa_grid > 0].min(); kn = kappa_grid[kappa_grid < 0].max()
    jp = int(np.where(kappa_grid == kp)[0][0]); jn = int(np.where(kappa_grid == kn)[0][0])
    dfy0 = np.abs((Fy[ip] - Fy[ineg]) / (np.tan(ap) - np.tan(an)))   # [nF] N per unit sy
    dfx0 = np.abs((Fx[jp] - Fx[jn]) / (kp - kn))                     # [nF] N per unit sx
    sigma_alpha_fz = np.clip(dfy0 / TMEASY_SIGMA0, 0.02, None)       # [nF] relaxation length [m]
    sigma_kappa_fz = np.clip(dfx0 / TMEASY_SIGMA0, 0.02, None)       # [nF]

    tt = lambda a: torch.tensor(a, device=device, dtype=dtype)  # noqa: E731
    return {
        "tm_fz_grid": tt(fz_grid),
        "tm_kappa_grid": tt(kappa_grid),
        "tm_alpha_grid": tt(alpha_grid),
        "tm_fx_ratio": tt(fx_ratio),
        "tm_fy_ratio": tt(fy_ratio),
        "tm_kappa_peak": tt(kappa_peak),
        "tm_alpha_peak": tt(alpha_peak),
        "tm_sigma_alpha_fz": tt(sigma_alpha_fz),   # [nF] measured lateral relaxation length(Fz)
        "tm_sigma_kappa_fz": tt(sigma_kappa_fz),   # [nF] measured longitudinal relaxation length(Fz)
        "tm_mu0": tt(float(arrays["mu0"])),
    }


def make_phys_param_batch(
    params: PhysParams | Mapping[str, float],
    n: int,
    *,
    mu: float | torch.Tensor = 0.48,
    device: torch.device | str = "cpu",
    dtype: torch.dtype = torch.float32,
    curves: Path | str | dict | None = None,
) -> PhysParamBatch:
    """Broadcast a PhysParams (or dict of scalars/[N] tensors) to a [N] PhysParamBatch.

    ``mu`` is the per-env terrain friction (scalar or [N] tensor). ``curves`` selects the
    extracted TMeasy curve npz (default: chrono_tmeasy_curves.npz next to runs/)."""
    if isinstance(params, PhysParams):
        src: dict[str, object] = params.as_dict()
        substeps = int(params.substeps)
    else:
        src = dict(params)
        substeps = int(src.get("substeps", 4))
    t: dict[str, torch.Tensor] = {}
    for k in _PARAM_KEYS:
        v = src[k]
        if isinstance(v, torch.Tensor):
            t[k] = v.to(device=device, dtype=dtype).expand(n).clone()
        else:
            t[k] = torch.full((n,), float(v), device=device, dtype=dtype)
    if isinstance(mu, torch.Tensor):
        mu_t = mu.to(device=device, dtype=dtype).expand(n).clone()
    else:
        mu_t = torch.full((n,), float(mu), device=device, dtype=dtype)

    luts = {
        "eng_rpm": torch.tensor(ENGINE_RPM, device=device, dtype=dtype),
        "eng_full": torch.tensor(ENGINE_TQ_FULL, device=device, dtype=dtype),
        "ebr_rpm": torch.tensor(ENGINE_BRAKE_RPM, device=device, dtype=dtype),
        "ebr_tq": torch.tensor(ENGINE_TQ_BRAKE, device=device, dtype=dtype),
        "ratios": torch.tensor(GEAR_RATIOS, device=device, dtype=dtype),
        "shift_down": torch.tensor(SHIFT_DOWN, device=device, dtype=dtype),
        "shift_up": torch.tensor(SHIFT_UP, device=device, dtype=dtype),
    }
    # EXACT-TMeasy tyre curve tables (the heart of the faithful rewrite).
    if isinstance(curves, dict):
        arrays = curves
    else:
        arrays = _load_curve_arrays(_CURVE_NPZ if curves is None else curves)
    luts.update(_curve_luts(arrays, device, dtype))
    return PhysParamBatch(t=t, mu=mu_t, substeps=substeps, luts=luts)


# --------------------------------------------------------------------- branchless 1D interp
def _interp1d(x: torch.Tensor, xp: torch.Tensor, fp: torch.Tensor) -> torch.Tensor:
    """Vectorised piecewise-linear interpolation, clamped at the ends. x:[...], xp/fp:[K]."""
    K = xp.shape[0]
    xc = x.clamp(xp[0], xp[-1])
    # bin index in [1, K-1]
    idx = torch.searchsorted(xp, xc.contiguous(), right=True).clamp(1, K - 1)
    x0 = xp[idx - 1]
    x1 = xp[idx]
    y0 = fp[idx - 1]
    y1 = fp[idx]
    w = (xc - x0) / (x1 - x0).clamp_min(1e-9)
    return y0 + w * (y1 - y0)


def _interp2d_bilinear(x, y, xp, yp, table):
    """Branchless bilinear interpolation of ``table[i_x, j_y]`` at (x, y). Clamped at edges.

    x, y are [...] tensors; xp:[Kx], yp:[Ky] are the (sorted) grids; table:[Kx, Ky]. Used for
    the EXACT-TMeasy force-ratio surfaces Fx/Fz(kappa, Fz) and Fy/Fz(alpha, Fz)."""
    Kx = xp.shape[0]
    Ky = yp.shape[0]
    xc = x.clamp(xp[0], xp[-1])
    yc = y.clamp(yp[0], yp[-1])
    ix = torch.searchsorted(xp, xc.contiguous(), right=True).clamp(1, Kx - 1)
    iy = torch.searchsorted(yp, yc.contiguous(), right=True).clamp(1, Ky - 1)
    x0 = xp[ix - 1]; x1 = xp[ix]
    y0 = yp[iy - 1]; y1 = yp[iy]
    wx = ((xc - x0) / (x1 - x0).clamp_min(1e-12)).unsqueeze(-1) if x.dim() == 0 else (xc - x0) / (x1 - x0).clamp_min(1e-12)
    wy = (yc - y0) / (y1 - y0).clamp_min(1e-12)
    # gather the four corners (flatten the [Kx,Ky] table for index_select)
    flat = table.reshape(-1)
    def corner(a, b):
        return flat[a * Ky + b]
    f00 = corner(ix - 1, iy - 1)
    f10 = corner(ix, iy - 1)
    f01 = corner(ix - 1, iy)
    f11 = corner(ix, iy)
    f0 = f00 + wx * (f10 - f00)
    f1 = f01 + wx * (f11 - f01)
    return f0 + wy * (f1 - f0)


# --------------------------------------------------------------------- powertrain (branchless)
def _engine_torque(rpm: torch.Tensor, throttle: torch.Tensor, P: PhysParamBatch) -> torch.Tensor:
    """Blended engine torque T = (1-thr)*brake_map(rpm) + thr*full_map(rpm). [N] -> [N]."""
    rpm_c = torch.minimum(rpm.clamp_min(0.0), P["max_engine_rpm"])
    full = _interp1d(rpm_c, P.luts["eng_rpm"], P.luts["eng_full"])
    brake = _interp1d(rpm_c, P.luts["ebr_rpm"], P.luts["ebr_tq"])
    return (1.0 - throttle) * brake + throttle * full


def _gear_ratio(gear: torch.Tensor, P: PhysParamBatch) -> torch.Tensor:
    """Gather the active gear ratio. gear int tensor [N] in [0,5]."""
    return P.luts["ratios"][gear]


def _update_gear(gear: torch.Tensor, motor_rpm: torch.Tensor, P: PhysParamBatch) -> torch.Tensor:
    """Branchless automatic-gearbox FSM: at most one masked shift per call. gear int64 [N]."""
    up_thresh = P.luts["shift_up"][gear]
    down_thresh = P.luts["shift_down"][gear]
    up = (motor_rpm > up_thresh) & (gear < 5)
    down = (motor_rpm < down_thresh) & (gear > 0)
    return gear + up.long() - down.long()


# --------------------------------------------------------------------- tyre + load transfer
def _normal_loads(ax: torch.Tensor, ay: torch.Tensor, P: PhysParamBatch):
    """Quasi-static per-wheel normal loads [N] for FL,FR,RL,RR. ax,ay are body accelerations.

    Branchless signed-transfer: longitudinal transfer loads the rear under +ax (accel),
    lateral transfer loads the side opposite to +ay. Returns 4 tensors [N]."""
    m = P["mass"]
    g = P["gravity"]
    h = P["h_cg"] * P["h_cg_scale"]
    L = P["wheelbase"]
    share_f = P["front_axle_share"]
    static_f = m * g * share_f * 0.5        # per front wheel
    static_r = m * g * (1.0 - share_f) * 0.5  # per rear wheel

    dFz_long = m * ax * h / L                 # total front->rear transfer (signed by ax)
    # lateral transfer per axle (split by axle load share)
    dFz_lat_f = m * ay * h / P["track_f"] * share_f
    dFz_lat_r = m * ay * h / P["track_r"] * (1.0 - share_f)

    # +ax (accelerate) unloads front, loads rear. +ay loads the wheel on -y side.
    fz_fl = torch.clamp(static_f - 0.5 * dFz_long - dFz_lat_f, min=1.0)
    fz_fr = torch.clamp(static_f - 0.5 * dFz_long + dFz_lat_f, min=1.0)
    fz_rl = torch.clamp(static_r + 0.5 * dFz_long - dFz_lat_r, min=1.0)
    fz_rr = torch.clamp(static_r + 0.5 * dFz_long + dFz_lat_r, min=1.0)
    return fz_fl, fz_fr, fz_rl, fz_rr


def _wheel_forces(sx, alpha, fz, fz_nom, mu_scale, P: PhysParamBatch, grip_scale=1.0):
    """Per-wheel combined-slip Fx,Fy from Chrono's EXACT tabulated TMeasy curves.

    sx: longitudinal slip, alpha: slip angle [rad], fz: normal load [N]. ``fz_nom`` and
    ``grip_scale`` are kept for signature parity with gpu_physics (grip_scale=1.0 in the
    faithful rewrite; it only multiplies the lateral force and is a no-op at 1.0).

    The tyre interpolates the sampled force-RATIO surfaces Fx/Fz(kappa, Fz) and
    Fy/Fz(alpha, Fz) — which already carry TMeasy's degressive load dependence — by
    (slip, actual Fz). Combined slip uses the same slip-vector projection as the Chrono
    ``tmxy_combined``/``CombinedCoulombForces`` ellipse: normalise each slip by its
    per-load peak-slip, evaluate both pure curves on the combined magnitude, then split
    the force by slip direction. Terrain mu enters as ``mu_scale = mu/mu0`` on the caps.
    Returns (Fx, Fy)."""
    fz_grid = P.luts["tm_fz_grid"]
    kappa_grid = P.luts["tm_kappa_grid"]
    alpha_grid = P.luts["tm_alpha_grid"]
    fz_c = fz.clamp(fz_grid[0], fz_grid[-1])

    # per-load peak-slip locations (combined-slip normalisers), interpolated in Fz.
    kappa_pk = _interp1d(fz_c, fz_grid, P.luts["tm_kappa_peak"]).abs().clamp_min(0.02)
    alpha_pk = _interp1d(fz_c, fz_grid, P.luts["tm_alpha_peak"]).abs().clamp_min(0.02)

    # theoretical lateral slip sy = tan(alpha); normalise both slips by their peak-slip.
    sy = torch.tan(alpha.clamp(-1.45, 1.45))
    nx = sx / kappa_pk
    ny = sy / torch.tan(alpha_pk)
    s_comb = torch.sqrt(nx * nx + ny * ny + 1e-12)
    cx = nx / s_comb
    cy = ny / s_comb

    # combined slips projected back to physical scale for the table lookup.
    kappa_eval = s_comb * kappa_pk
    alpha_eval = torch.atan(s_comb * torch.tan(alpha_pk)).clamp(alpha_grid[0], alpha_grid[-1])

    # bilinear table lookup of the EXACT force ratios (Fx/Fz, Fy/Fz) at (combined slip, Fz).
    fx_ratio = _interp2d_bilinear(kappa_eval.clamp(kappa_grid[0], kappa_grid[-1]), fz_c,
                                  kappa_grid, fz_grid, P.luts["tm_fx_ratio"])
    fy_ratio = _interp2d_bilinear(alpha_eval, fz_c,
                                  alpha_grid, fz_grid, P.luts["tm_fy_ratio"])
    # the table is signed in slip; we evaluated at |combined| via the positive-slip branch,
    # so take magnitudes and re-apply the slip direction. mu_scale scales the friction caps.
    fx0 = fx_ratio.abs() * fz * mu_scale
    fy0 = fy_ratio.abs() * fz * mu_scale * grip_scale

    fx = fx0 * cx
    fy = -fy0 * cy
    return fx, fy


def _accel_from_forces(vx, vy, yaw_rate, steer, Fx_f, Fy_f, Fx_r, Fy_r, P: PhysParamBatch):
    """Combine axle forces (front in wheel frame, rotated by steer; rear in body frame).

    Fx_f/Fy_f: front-axle long/lat in the steered-wheel frame; Fx_r/Fy_r: rear-axle in body
    frame. Returns (vx_dot, vy_dot, yaw_dot, ax_body, ay_body)."""
    cs = torch.cos(steer)
    sn = torch.sin(steer)
    Fx_f_body = Fx_f * cs - Fy_f * sn
    Fy_f_body = Fx_f * sn + Fy_f * cs

    # aero drag + rolling resistance oppose vx
    drag = P["drag_coeff"] * vx * vx.abs()
    rolling = P["rolling_resist_coeff"] * P["mass"] * P["gravity"] * torch.tanh(vx)
    Fx_body = Fx_f_body + Fx_r - drag - rolling
    Fy_body = Fy_f_body + Fy_r

    lf = 0.5 * P["wheelbase"]
    lr = 0.5 * P["wheelbase"]
    Mz = lf * Fy_f_body - lr * Fy_r

    ax_body = Fx_body / P["mass"]
    ay_body = Fy_body / P["mass"]
    vx_dot = ax_body + yaw_rate * vy
    vy_dot = ay_body - yaw_rate * vx
    yaw_dot = Mz / P["izz"]
    return vx_dot, vy_dot, yaw_dot, ax_body, ay_body


def _sigma_at(fz, P: PhysParamBatch, channel: str):
    """Measured physical relaxation length sigma(Fz) [m] for the given slip channel.

    Interpolates the per-Fz sigma LUT (sigma = dF0/sigma0, derived from the EXACT curves) by the
    runtime wheel load, scaled by the global ``sigma_scale`` (default 1.0 = raw measured value).
    ``channel`` is 'alpha' (lateral) or 'kappa' (longitudinal). Branchless, batched."""
    fz_grid = P.luts["tm_fz_grid"]
    fz_c = fz.clamp(fz_grid[0], fz_grid[-1])
    lut = P.luts["tm_sigma_alpha_fz"] if channel == "alpha" else P.luts["tm_sigma_kappa_fz"]
    sig = _interp1d(fz_c, fz_grid, lut) * P["sigma_scale"]
    return sig.clamp_min(0.02)


def _continuous_derivs(vx, vy, yaw_rate, steer, omega_rl, omega_rr, throttle, brake, gear,
                       ax_f, ay_f, alpha_f_lag, alpha_r_lag, sx_rl_lag, sx_rr_lag, omega_eng,
                       P: PhysParamBatch, h: float):
    """Continuous-time derivatives with SLIP relaxation (the L1 transient).

    alpha_f_lag/alpha_r_lag/sx_rl_lag/sx_rr_lag are the relaxation-lagged tyre SLIPS: the EXACT
    curve is evaluated at the LAGGED slip, so the force builds up over the measured physical
    relaxation length sigma (this is the state that holds sideslip up during drift entry). The lag
    is advanced SEMI-IMPLICITLY by the sub-step ``h`` BEFORE the force eval (so the small-sigma
    limit faithfully reduces to quasi-static, with no spurious one-sub-step delay). All inputs
    [N]. Returns (vx_dot, vy_dot, yaw_dot, orl_dot, orr_dot,
    alpha_f_lag_new, alpha_r_lag_new, sx_rl_lag_new, sx_rr_lag_new, ax_body, ay_body)."""
    mu_scale = P.mu / P["mu0"]

    # ---- normal loads from filtered accelerations (explicit, no fixed point) ----
    fz_fl, fz_fr, fz_rl, fz_rr = _normal_loads(ax_f, ay_f, P)
    fz_nom_f = P["mass"] * P["gravity"] * P["front_axle_share"] * 0.5
    fz_nom_r = P["mass"] * P["gravity"] * (1.0 - P["front_axle_share"]) * 0.5

    # ---- INSTANTANEOUS slip angles (the relaxation targets) ----
    lf = 0.5 * P["wheelbase"]
    lr = 0.5 * P["wheelbase"]
    sign = torch.where(vx.abs() > 1e-6, torch.sign(vx), torch.ones_like(vx))
    vx_safe = sign * vx.abs().clamp_min(0.75)
    # lateral velocity at each axle
    vy_f = vy + lf * yaw_rate
    vy_r = vy - lr * yaw_rate
    alpha_f_inst = torch.atan2(vy_f, vx_safe.abs()) - steer
    alpha_r_inst = torch.atan2(vy_r, vx_safe.abs())

    # ---- INSTANTANEOUS rear longitudinal slip from wheel spin ----
    half_tr = 0.5 * P["track_r"]
    vx_rl = vx - yaw_rate * half_tr
    vx_rr = vx + yaw_rate * half_tr
    vx_rl_safe = torch.sign(vx_rl) * vx_rl.abs().clamp_min(0.75)
    vx_rr_safe = torch.sign(vx_rr) * vx_rr.abs().clamp_min(0.75)
    sx_rl_inst = (P["r_eff"] * omega_rl - vx_rl) / vx_rl_safe.abs().clamp_min(0.5)
    sx_rr_inst = (P["r_eff"] * omega_rr - vx_rr) / vx_rr_safe.abs().clamp_min(0.5)

    # ---- SLIP RELAXATION: advance each lagged slip toward its instantaneous value over sigma ----
    # d(slip_lag)/dt = (|vx| / sigma(Fz)) * (slip_inst - slip_lag). sigma is the MEASURED physical
    # relaxation length (sigma = dF0/sigma0 off the EXACT curves), load-dependent via the per-wheel
    # Fz. The lag is advanced by the EXACT first-order factor (1 - exp(-rate*h)) WITHIN this
    # sub-step BEFORE the force eval, so the force always sees the up-to-date lag (the small-sigma
    # limit -> quasi-static exactly, with no spurious one-sub-step delay; the update is also
    # unconditionally stable). The force is then evaluated at the advanced lag, so it responds over
    # the relaxation length -- slowing the drift-entry recovery to match Chrono.
    v_relax = vx.abs().clamp_min(1.0)
    sig_a_f = _sigma_at(0.5 * (fz_fl + fz_fr), P, "alpha")
    sig_a_r = _sigma_at(0.5 * (fz_rl + fz_rr), P, "alpha")
    sig_k_rl = _sigma_at(fz_rl, P, "kappa")
    sig_k_rr = _sigma_at(fz_rr, P, "kappa")
    af = 1.0 - torch.exp(-(v_relax / sig_a_f) * h)
    ar = 1.0 - torch.exp(-(v_relax / sig_a_r) * h)
    kl = 1.0 - torch.exp(-(v_relax / sig_k_rl) * h)
    kr = 1.0 - torch.exp(-(v_relax / sig_k_rr) * h)
    alpha_f_lag = alpha_f_lag + af * (alpha_f_inst - alpha_f_lag)
    alpha_r_lag = alpha_r_lag + ar * (alpha_r_inst - alpha_r_lag)
    sx_rl_lag = sx_rl_lag + kl * (sx_rl_inst - sx_rl_lag)
    sx_rr_lag = sx_rr_lag + kr * (sx_rr_inst - sx_rr_lag)

    # ---- tyre forces evaluated at the (advanced) LAGGED slips (the relaxed transient) ----
    # front wheels: no drive slip (sx=0), lateral from the LAGGED alpha_f. (free-rolling front)
    zero = torch.zeros_like(vx)
    gsf = P["front_grip_scale"]
    gsr = P["rear_grip_scale"]
    fx_fl, fy_fl = _wheel_forces(zero, alpha_f_lag, fz_fl, fz_nom_f, mu_scale, P, gsf)
    fx_fr, fy_fr = _wheel_forces(zero, alpha_f_lag, fz_fr, fz_nom_f, mu_scale, P, gsf)
    fx_rl, fy_rl = _wheel_forces(sx_rl_lag, alpha_r_lag, fz_rl, fz_nom_r, mu_scale, P, gsr)
    fx_rr, fy_rr = _wheel_forces(sx_rr_lag, alpha_r_lag, fz_rr, fz_nom_r, mu_scale, P, gsr)

    Fx_f = fx_fl + fx_fr
    Fx_r = fx_rl + fx_rr
    Fy_f = fy_fl + fy_fr
    Fy_r = fy_rl + fy_rr

    vx_dot, vy_dot, yaw_dot, ax_body, ay_body = _accel_from_forces(
        vx, vy, yaw_rate, steer, Fx_f, Fy_f, Fx_r, Fy_r, P,
    )

    # ---- powertrain torque to rear wheels ----
    # motor rpm from rear-wheel speed (avg) through final drive + gear ratio.
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio = _gear_ratio(gear, P)
    # driveshaft speed = axle speed / final_drive; motor speed = driveshaft / ratio
    motor_rad_rigid = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)

    # ---- PWR5: DRIVELINE ROTATIONAL-INERTIA engine-speed lead (the MEASURED release effect) ----
    # The Chrono engine/driveline shaft system (no torque converter) carries rotational inertia, so the
    # engine speed LEADS the rigid value by an amount that builds with the DRIVE TORQUE (shaft windup +
    # tyre drive-slip) and DECAYS over the MEASURED time constant DRIVELINE_TAU when torque drops. We
    # carry the LEAD delta = omega_eng - omega_rigid as the state, integrated by:
    #     d(delta)/dt = T_eng / I_eff  -  delta / tau
    # so steady-state delta = (tau/I_eff)*T_eng = the MEASURED torque-proportional windup
    # (1.71 rpm per Nm_driveshaft, corr 0.84 in the ground-truth trace), and on throttle RELEASE the
    # lead bleeds down first-order over tau=189 ms (the measured rpm-excess decay). I_eff=0.83 kg.m^2 is
    # the engine-frame inertia implied by that windup slope -- INDEPENDENTLY consistent with the JSON
    # ChShaft chain (~0.74 kg.m^2). BOTH tau and I_eff are MEASURED from Chrono, NOT fit to the gate.
    # The engine torque map is then read at the led rpm (omega_rigid + delta), carrying whatever
    # drive-force the measured map gives at the elevated rpm. To compute the torque-driven windup we
    # use the engine torque AT the previous led rpm (explicit within the sub-step), avoiding an
    # algebraic loop; the small delta makes this a near-exact split.
    tau = P["driveline_tau"].clamp_min(1e-3)
    motor_rpm_prev = (motor_rad_rigid + omega_eng).abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm_prev = torch.minimum(torch.maximum(motor_rpm_prev, P["idle_rpm"]), P["max_engine_rpm"])
    T_eng_prev = _engine_torque(motor_rpm_prev, throttle, P) * P["drive_scale"]
    # integrate the lead (semi-implicit in the -delta/tau decay term for unconditional stability):
    #   delta_new = (delta + h*T_eng/I_eff) / (1 + h/tau)
    delta = (omega_eng + h * T_eng_prev / DRIVELINE_I_EFF) / (1.0 + h / tau)
    omega_eng = delta                              # carried state IS the lead (delta)
    motor_rad = motor_rad_rigid + delta            # led engine speed = rigid + windup lead
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])

    T_eng = _engine_torque(motor_rpm, throttle, P) * P["drive_scale"]
    T_driveshaft = T_eng / ratio.clamp_min(1e-3)
    T_axle = T_driveshaft / P["final_drive"].clamp_min(1e-3)
    T_wheel = 0.5 * T_axle      # open diff splits equally

    # ---- MEASURED FRONT-AXLE TRACTION CAP on the drive force (the partial-throttle fix) ----
    # The Chrono Sedan is FRONT-wheel drive (ShaftsDriveline2WD, driven axle 0 = front), so the drive
    # force is traction-limited on the load-LOSING FRONT axle. This RWD model would otherwise put the
    # full engine force down on the load-GAINING rear axle (the ~1.75x over-force in the avoidance
    # throttle ramp). We cap each driven wheel's drive force by the FRONT friction circle budget
    # sqrt((mu*Fz_front)^2 - Fy_front^2) -- the remaining traction after the front lateral force. The
    # cap is the MEASURED front-axle friction limit (not a tuned drive_scale): slack at low drive
    # (drift, ~1 kN) so the drift powertrain is unchanged, biting only when the avoidance accel
    # demands more force than the front axle can put down. The cap is applied to T_wheel via the
    # equilibrium drive force T_wheel/r_eff so the rear wheel-spin dynamics shed the excess as slip.
    # Front friction budget per driven wheel = mu*Fz_front. The longitudinal cap is the friction
    # circle sqrt((mu*Fz)^2 - Fy^2), BUT floored at half the pure mu*Fz budget so that a transient
    # FULL lateral saturation of the front during a hard DRIFT ENTRY (Fy_front ~ mu*Fz, which would
    # otherwise zero the longitudinal budget for ~1 step) does not spuriously kill the rear drive and
    # corrupt the drift -- in the avoidance regime the front lateral force is small so the floor is
    # never active and the cap is the full measured friction circle. (The floor is the only non-pure-
    # measurement choice; it is bounded by the measured mu*Fz and is a numerical guard on the
    # planar-model drift-entry transient, NOT a tuned drive_scale.)
    fmu_fl = (mu_scale * P["mu0"]) * fz_fl * gsf       # front-left friction budget = mu*Fz_fl [N]
    fmu_fr = (mu_scale * P["mu0"]) * fz_fr * gsf
    fx_cap_l = torch.sqrt((fmu_fl * fmu_fl - fy_fl * fy_fl).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fl)
    fx_cap_r = torch.sqrt((fmu_fr * fmu_fr - fy_fr * fy_fr).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fr)
    # cap the per-wheel drive TORQUE so the equilibrium drive force T_wheel/r_eff <= front budget.
    T_cap_l = fx_cap_l * P["r_eff"]
    T_cap_r = fx_cap_r * P["r_eff"]
    T_wheel_l = torch.clamp(T_wheel, -T_cap_l, T_cap_l)
    T_wheel_r = torch.clamp(T_wheel, -T_cap_r, T_cap_r)

    # brake torque opposes each wheel's spin direction (all 4 wheels braked).
    T_brake_r = brake * P["max_brake_torque"]
    T_brake_rl = T_brake_r * torch.sign(omega_rl)
    T_brake_rr = T_brake_r * torch.sign(omega_rr)

    omega_rl_dot = (T_wheel_l - P["r_eff"] * fx_rl - T_brake_rl) / P["i_wheel"]
    omega_rr_dot = (T_wheel_r - P["r_eff"] * fx_rr - T_brake_rr) / P["i_wheel"]

    return (vx_dot, vy_dot, yaw_dot, omega_rl_dot, omega_rr_dot,
            alpha_f_lag, alpha_r_lag, sx_rl_lag, sx_rr_lag, omega_eng,
            ax_body, ay_body)


# --------------------------------------------------------------------------- step
def physics_step(state: torch.Tensor, action: torch.Tensor, gear: torch.Tensor,
                 P: PhysParamBatch, dt: float):
    """One control step of the branchless physics model, batched over N.

    state [N,17], action [N,3] (steer,throttle,brake in [-1,1]), gear int64 [N].
    Returns (next_state[N,17], next_gear[N], diagnostics dict)."""
    s = state
    vx = s[:, IDX["vx"]]
    vy = s[:, IDX["vy"]]
    yaw_rate = s[:, IDX["yaw_rate"]]
    steer = s[:, IDX["steer"]]
    throttle = s[:, IDX["throttle"]]
    brake = s[:, IDX["brake"]]
    omega_rl = s[:, IDX["omega_rl"]]
    omega_rr = s[:, IDX["omega_rr"]]
    ax_f = s[:, IDX["ax_f"]]
    ay_f = s[:, IDX["ay_f"]]
    alpha_f_lag = s[:, IDX["alpha_f_lag"]]
    alpha_r_lag = s[:, IDX["alpha_r_lag"]]
    sx_rl_lag = s[:, IDX["sx_rl_lag"]]
    sx_rr_lag = s[:, IDX["sx_rr_lag"]]
    omega_eng = s[:, IDX["omega_eng"]]
    psi = s[:, IDX["psi"]]

    # ---- actuator filters (mirror gpu_surrogate) ----
    steer_cmd = torch.clamp(action[:, 0], -1.0, 1.0) * P["max_steer"]
    throttle_cmd = 0.5 * (torch.clamp(action[:, 1], -1.0, 1.0) + 1.0)
    brake_cmd = 0.5 * (torch.clamp(action[:, 2], -1.0, 1.0) + 1.0)

    steer_rate_limit = P["max_steer_rate"] * dt
    steer_lag = torch.clamp(dt / torch.clamp(P["steer_tau"], min=dt), 0.0, 1.0)
    steer_target = steer + (steer_cmd - steer) * steer_lag
    new_steer = steer + torch.clamp(steer_target - steer, -steer_rate_limit, steer_rate_limit)

    thr_alpha = torch.clamp(dt / torch.clamp(P["throttle_tau"], min=dt), 0.0, 1.0)
    new_throttle = throttle + (throttle_cmd - throttle) * thr_alpha
    brk_alpha = torch.clamp(dt / torch.clamp(P["brake_tau"], min=dt), 0.0, 1.0)
    new_brake = brake + (brake_cmd - brake) * brk_alpha

    # ---- gear update (branchless FSM) once per control step ----
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio0 = _gear_ratio(gear, P)
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio0.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])
    new_gear = _update_gear(gear, motor_rpm, P)

    # ---- sub-stepped semi-implicit Euler integration ----
    nsub = max(int(P.substeps), 1)
    h = dt / nsub
    last_ax, last_ay = ax_f, ay_f
    for _ in range(nsub):
        # _continuous_derivs advances the slip-lag states semi-implicitly by h (returning the NEW
        # lag values, used both for this sub-step's force and as the carried state) and returns the
        # body-state derivatives evaluated at the relaxed (lagged) tyre forces.
        (vx_dot, vy_dot, yaw_dot, orl_dot, orr_dot,
         alpha_f_lag, alpha_r_lag, sx_rl_lag, sx_rr_lag, omega_eng, ax_body, ay_body) = _continuous_derivs(
            vx, vy, yaw_rate, new_steer, omega_rl, omega_rr, new_throttle, new_brake, new_gear,
            last_ax, last_ay, alpha_f_lag, alpha_r_lag, sx_rl_lag, sx_rr_lag, omega_eng, P, h,
        )
        vx = vx + h * vx_dot
        vy = vy + h * vy_dot
        yaw_rate = yaw_rate + h * yaw_dot
        omega_rl = omega_rl + h * orl_dot
        omega_rr = omega_rr + h * orr_dot
        # filter the body accelerations (quasi-static load-transfer source for next sub-step)
        last_ax, last_ay = ax_body, ay_body

    # pose integration (not gated, but kept for completeness)
    new_psi = psi + dt * s[:, IDX["yaw_rate"]]
    new_x = s[:, IDX["x"]] + dt * (s[:, IDX["vx"]] * torch.cos(psi) - s[:, IDX["vy"]] * torch.sin(psi))
    new_y = s[:, IDX["y"]] + dt * (s[:, IDX["vx"]] * torch.sin(psi) + s[:, IDX["vy"]] * torch.cos(psi))

    out = state.clone()
    out[:, IDX["x"]] = new_x
    out[:, IDX["y"]] = new_y
    out[:, IDX["psi"]] = new_psi
    out[:, IDX["vx"]] = vx
    out[:, IDX["vy"]] = vy
    out[:, IDX["yaw_rate"]] = yaw_rate
    out[:, IDX["steer"]] = new_steer
    out[:, IDX["throttle"]] = new_throttle
    out[:, IDX["brake"]] = new_brake
    out[:, IDX["omega_rl"]] = omega_rl
    out[:, IDX["omega_rr"]] = omega_rr
    out[:, IDX["ax_f"]] = last_ax
    out[:, IDX["ay_f"]] = last_ay
    out[:, IDX["alpha_f_lag"]] = alpha_f_lag
    out[:, IDX["alpha_r_lag"]] = alpha_r_lag
    out[:, IDX["sx_rl_lag"]] = sx_rl_lag
    out[:, IDX["sx_rr_lag"]] = sx_rr_lag
    out[:, IDX["omega_eng"]] = omega_eng

    diag = {"motor_rpm": motor_rpm, "gear": new_gear, "omega_eng": omega_eng}
    return out, new_gear, diag


def init_state(vx0: torch.Tensor, vy0: torch.Tensor, yaw0: torch.Tensor, P: PhysParamBatch):
    """Build an [N,17] initial state + gear from initial velocity. Wheel omega seeded to vx/r_eff,
    gear seeded to the highest gear consistent with the motor-speed band (so the gearbox does not
    have to upshift through every gear from a cold start)."""
    n = vx0.shape[0]
    dev, dt_ = P.device, P.dtype
    st = torch.zeros(n, PHYS_STATE_DIM, device=dev, dtype=dt_)
    st[:, IDX["vx"]] = vx0
    st[:, IDX["vy"]] = vy0
    st[:, IDX["yaw_rate"]] = yaw0
    # rolling rear wheels: omega = vx / r_eff (no initial slip)
    st[:, IDX["omega_rl"]] = vx0 / P["r_eff"]
    st[:, IDX["omega_rr"]] = vx0 / P["r_eff"]

    # seed gear: pick the gear whose motor rpm at this omega is inside [down,up].
    omega_axle = vx0 / P["r_eff"]
    ratios = P.luts["ratios"]
    # motor rpm for every gear: [N,6]
    motor_rpm_g = (omega_axle[:, None] / P["final_drive"][:, None].clamp_min(1e-3)
                   / ratios[None, :].clamp_min(1e-3)).abs() * 60.0 / (2.0 * torch.pi)
    up = P.luts["shift_up"][None, :]
    down = P.luts["shift_down"][None, :]
    # FAITHFUL cruise-entry seed: Chrono enters these scenarios having approached at speed, so its
    # automatic gearbox HOLDS the HIGHEST gear whose motor rpm is still inside the hysteresis band
    # [down, up] (it only downshifts once rpm drops below `down`). The previous "lowest gear under
    # its up-threshold" rule modelled accelerate-from-cold-rest and seeded one gear too LOW at cruise
    # (gear 2 vs Chrono's gear 3 @ 8 m/s -> 1.6x driveshaft over-torque -> avoid-vx over-accel).
    # Verified vs replay telemetry: docs/gpu-surrogate-design-2026-06.md "RESOLVED (2026-06-17)".
    in_band = (motor_rpm_g >= down) & (motor_rpm_g <= up)         # [N,6]
    # highest in-band gear per row (reverse-argmax). Fallback to lowest-<=up if no gear is in band.
    rev_idx = (in_band.shape[1] - 1) - torch.flip(in_band, dims=[1]).float().argmax(dim=1)
    le_up = motor_rpm_g <= up
    fallback = torch.where(le_up.any(dim=1), le_up.float().argmax(dim=1),
                           torch.full((n,), 5, device=dev, dtype=torch.float))
    gear = torch.where(in_band.any(dim=1), rev_idx.float(), fallback).long()

    # seed the relaxation-lagged SLIPS to their INSTANTANEOUS values at the init state (so the
    # tyre starts in slip equilibrium and the relaxation transient only fires once the slip
    # actually changes -- the lag must start matched, not ramping from zero).
    lf = 0.5 * P["wheelbase"]
    vx_safe = torch.sign(vx0) * vx0.abs().clamp_min(0.75)
    alpha_f0 = torch.atan2(vy0 + lf * yaw0, vx_safe.abs())  # steer=0 at init
    alpha_r0 = torch.atan2(vy0 - lf * yaw0, vx_safe.abs())
    st[:, IDX["alpha_f_lag"]] = alpha_f0
    st[:, IDX["alpha_r_lag"]] = alpha_r0
    st[:, IDX["sx_rl_lag"]] = 0.0   # omega seeded to vx/r_eff => zero initial longitudinal slip
    st[:, IDX["sx_rr_lag"]] = 0.0
    # PWR5: omega_eng carries the engine-speed LEAD (delta = omega_eng - omega_rigid). At a settled
    # cruise entry the measured engine excess is ~0 rpm, BUT there is a non-zero steady windup whenever
    # there is drive torque. Seed the lead to its steady-state value for the entry throttle (~0 if the
    # car coasts in, growing as soon as the oracle commands drive) -- here 0 is the faithful cruise-entry
    # seed (Chrono's pre-maneuver approach is near-coast; the lead builds over tau once drive is applied).
    st[:, IDX["omega_eng"]] = 0.0
    return st, gear
