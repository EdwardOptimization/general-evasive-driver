# Feasibility Route Step 3: Chrono HF Vehicle Backend (2026-06)

## Scope / claim boundary

Route step 3 of `docs/feasibility-takeover-2026-06-route-decision.md`
("Unblock Chrono (HF backend)"): a pychrono-based `DynamicsBackend`
implementation, a closed-loop smoke of the M3105 incumbent on it, and a
16+7-row mini discrepancy measurement against current-sim. Measurement and
scaffolding only; **no** driver-performance verdict, validation, ranking,
promotion, repair-success, fidelity-sufficiency, full-HF4, paper, or self-ID
claim is made. The mini panel is 23 fixed rows; it is *not* the full HF4
discrepancy report.

## Delivery status

| Level | Deliverable | Status |
|---|---|---|
| A1 | `src/autodrift/chrono_vehicle_backend.py` (DynamicsBackend over pychrono Sedan) | **delivered, verified** |
| A2 | `scripts/feasibility_audit/chrono_backend_smoke.py` -> `runs/feasibility_audit/chrono_smoke_summary.json` | **delivered, status_pass=True** |
| A3 | `scripts/feasibility_audit/chrono_mini_discrepancy.py` -> `experiments/feasibility_audit/chrono_mini_discrepancy.csv` | **delivered, 23/23 rows measured** |

Execution environment: pychrono **10.0.0** in conda env `chrono`
(python 3.10); `gymnasium 1.3.0` was additionally installed into that env
(numpy 1.26.4 was already present). The incumbent driver's import chain needs
torch (via `checkpoints`/`evaluate`/`train_ppo`), which is not installed in
the chrono env, so the closed loop is split: the **driver runs in the base
environment** and the **backend runs in the chrono env** behind a JSONL
stdin/stdout worker (`scripts/feasibility_audit/chrono_backend_worker.py`,
client `scripts/feasibility_audit/chrono_worker_client.py`). Protocol lines
are prefixed `@CHRONO@` so stray native output cannot corrupt them.

## A1: backend design and mapping table

Vehicle: **Chrono Sedan** wrapper model (double-wishbone/multilink, RWD,
4-speed automatic, TMeasy handling tires), data files complete under the env's
`share/chrono/data/vehicle/sedan/`. Stock total mass 1683.97 kg (chassis
1515.0 + 168.97 non-chassis); AutoDrift base mass is 1450 kg — the chassis
body mass is overridden per scenario so the *total* matches the sampled
hidden mass exactly (verified: sampled range 1232–1740 kg always leaves a
positive chassis mass). Terrain: `FlatTerrain` (pure height/friction query —
TMeasy needs no rigid contact), friction = scenario `mu`.

Stepping: internal Chrono step **1e-3 s**, tire step 1e-3 s, control at
**50 Hz** (20 substeps per control step), matching AutoDrift `dt = 0.02`.

Action mapping (`action3 [steer, throttle, brake] in [-1,1]`): the exact
AutoDrift actuator layer (`SingleTrackDriftModel.step` formulas: steer
first-order lag `steer_tau` + rate limit `max_steer_rate`, drive-force
first-order lag `drive_tau` toward `throttle*max_drive_force −
brake*max_brake_force`, negative-throttle-as-zero via the same 0.5*(a+1)
mapping) is replicated at 50 Hz in front of the Chrono driver inputs; the
lagged states feed `DriverInputs` as `m_steering = steer/max_steer`,
`m_throttle = clip01(throttle_state * drive_scale)`,
`m_braking = clip01(brake_state * brake_scale)`.

obs72: road boundary and obstacle features are **not** taken from Chrono
terrain queries — they reuse AutoDrift's analytic geometry
(`autodrift.tasks.CircleTrack` + the exact `env.py` formulas for
`_road_boundary_features`, `_obstacle_slot_features`, warmup-gate slot
arbitration, perception reveal step/distance) fed by the Chrono chassis
pose. Ego 9-dim comes from the chassis (body-frame vx/vy/yaw-rate; ax/ay as
finite differences over the control step) plus the replicated actuator
states. `off_track` (|lateral_error| > track_width = 5.0), collision
(distance <= ego_half_width + obstacle_half_width), pass
(longitudinal <= −finish_pass_distance), and the termination-reason order
(non_finite -> off_track -> obstacle_collision -> speed<1 -> speed>32 ->
|yaw_rate|>6) copy `env.py` exactly, so the task semantics are unchanged and
the fidelity upgrade is concentrated in the vehicle dynamics.

Episode start: deterministic straight-line **spin-up on mu=1.0** terrain to
the scenario speed, then an exact **rigid teleport + rigid velocity-field
boost** of all 20 multibody bodies onto the scenario's initial
(x, y, psi, vx, vy, yaw_rate); terrain is then swapped to the scenario mu.
This was adopted after measuring a ~2 m/s cold-start driveline transient when
velocities were injected into a non-spun-up vehicle; with the handoff, the
initial planar state is matched to ~1e-3 and the spin-up speed gap on the 23
A3 rows is <= 0.33 m/s (handoff occurs at the *achieved* spin-up speed; the
gap is recorded per row as `chrono_spinup_speed_gap`).

Hidden-parameter mapping:

| AutoDrift hidden param | Chrono mapping | status |
|---|---|---|
| `mu` (incl. friction step) | FlatTerrain friction; at the friction-step step index the terrain object is swapped to `new_mu` (verified effective: braking distance 8.1 m at mu 0.9 vs 26–29 m after runtime switch to 0.3) | mapped |
| friction-step replacement mu | the env's only post-reset RNG draw; pre-computed from a sacrificial reset and replayed at the same step index | mapped |
| `mass` | chassis-body mass override so total vehicle mass equals the sampled mass | mapped |
| `drive_scale` / `brake_scale` | multiplicative throttle/brake input scaling, clipped at 1.0 (scales > 1 saturate) | approximate |
| `steer_tau`, `drive_tau`, `max_steer_rate` (actuator tau scale) | exact AutoDrift first-order filter at the 50 Hz layer | mapped (command shaping) |
| `max_steer` | normalized: full-scale command = Sedan full lock 0.4363 rad vs AutoDrift 0.62 rad (physical gain ~0.70x) | known difference |
| `iz` / inertia_scale, cg_shift (`lf`/`lr`), `cf`/`cr` tire stiffness scales | not mapped (Sedan geometry/tire JSON fixed) | **not mapped** |
| drag/rolling coefficients | Sedan's own aero/rolling apply | not mapped |

Full machine-readable list: `KNOWN_DIFFERENCES` in
`src/autodrift/chrono_vehicle_backend.py` (also embedded in both output
JSONs). Additional measured difference — **effective grip**: open-loop
full-brake peak deceleration is 1.08–1.15x AutoDrift's mu*g
(mu 0.3: 3.17 m/s² vs 2.94; mu 0.6: 6.76 vs 5.89; mu 0.9: 9.96 vs 8.83), i.e.
the TMeasy Sedan tire is ~10% "grippier" at the same nominal mu.

API findings recorded for reproducibility: `Sedan.SetInitFwdVel` and
`SetInitWheelAngVel` do **not** take effect in this pychrono build (the
latter rejects every available std::vector proxy), `FrictionFunctor` is
abstract (no SWIG director) so runtime friction must be done by terrain-object
swap, and `RigidTerrain` patch-material `SetFriction` after `AddPatch` does
not propagate to TMeasy (patch friction is cached at creation) — hence
`FlatTerrain`. Vehicle-level getters (`GetVehicle().GetPos/GetRot`) are stale
immediately after manual body-state writes; the backend therefore reads pose
exclusively from the chassis body plus a precomputed body-frame ref-offset.

## A2: closed-loop smoke (status_pass = True)

`PYTHONPATH=src python scripts/feasibility_audit/chrono_backend_smoke.py`

Incumbent `ActiveSafetyReflexDriver` (`DRIVER_ID =
active_safety_reflex_driver_m3105_incumbent_v4_no_regression`) closed-loop,
320 control steps x 3 procedural circle scenarios (seeds 901500–901502),
termination events recorded but not stopping the loop (smoke-only flag
`terminate_on_failure=false`):

| mu | speed_ref | steps | all checks | speed mean/max | abs lat-err mean/max | events |
|---|---|---|---|---|---|---|
| 0.3 | 5.30 | 320 | pass | 7.97 / 11.11 | 3.24 / 14.94 | off_track @244 (recorded, loop continued) |
| 0.6 | 6.17 | 320 | pass | 9.05 / 11.33 | 1.57 / 2.50 | none |
| 0.9 | 7.88 | 320 | pass | 8.61 / 9.05 | 2.20 / 2.74 | none |

Checks (all true on every step of all scenarios): obs shape (72,), obs all
finite, action finite and in [-1,1], |x|,|y| <= 300 m, speed <= 35 m/s, ride
height in [0, 0.6] m. The obstacle was passed (raw) in all three scenarios.
A bitwise repeat of the mu=0.3 episode is identical
(`determinism_repeat_identical = true`). Throughput ~3400 internal steps/s
(one 480-step episode ~2.8 s wall).

Output: `runs/feasibility_audit/chrono_smoke_summary.json`
(worker stderr: `runs/feasibility_audit/chrono_smoke_worker_stderr.log`).

## A3: HF4-mini discrepancy, 16 + 7 rows

`PYTHONPATH=src python scripts/feasibility_audit/chrono_mini_discrepancy.py`

Rows from `experiments/feasibility_audit/panel_feasibility_labels.csv` (old
panel, seeds 401500-base): per-spec first recorded-success row (16) + all 7
recorded residual-failure rows (panel rows 0007/0010/0025/0026/0029
collisions, 0013/0024 offtracks). Same-task guarantee: the scenario (hidden
vehicle params, initial state, obstacle world position/half-width, warmup
gate, reveal step, friction-step index and replacement mu) is read from the
current-sim env after `reset(seed)` via
`chrono_vehicle_backend.scenario_from_env` and copied to the Chrono side
(scenario JSONs archived under `runs/feasibility_audit/chrono_mini_scenarios/`).
The current-sim side re-measured all 23 rows through the exact
M3088/M3090 path and **reproduced all 23 recorded M3105 outcomes**
(`current_sim_reproduces_recorded_outcomes = true`).

Result: **23/23 outcome agreement** between current-sim and Chrono.

| row set | n | current-sim outcomes | Chrono outcomes | agreement |
|---|---|---|---|---|
| spec success rows | 16 | 16 success | 16 success | 16/16 |
| residual failure rows | 7 | 5 collision + 2 offtrack | 5 collision + 2 offtrack (same rows, same modes) | 7/7 |

Transition table (current -> Chrono): `success->success` 16,
`collision->collision` 5, `offtrack->offtrack` 2. No success row flipped on
the Chrono backend and no infeasible-labeled failure row was rescued by the
higher-fidelity dynamics — consistent with (not proof of) the route-decision
conclusion that the 7 residual rows are physically unavoidable.

Quantitative closeness on identical tasks (per-row in the CSV):
- min clearance margin: mean |Δ| = **0.33 m**, max |Δ| = 2.69 m (the max is a
  far-from-obstacle success row, margin 24.5 vs 21.8 m); on the 7 failure
  rows |Δ| <= 0.08 m (collision margins −0.27..−0.03 m on both backends).
- episode length: mean |Δ| = 3.1 steps, max 21 steps.
- episode mean speed: agrees to ~0.1–1.2 m/s.
- Chrono determinism re-run of 2 rows: bitwise identical.

Outputs: `experiments/feasibility_audit/chrono_mini_discrepancy.csv`,
`runs/feasibility_audit/chrono_mini_discrepancy_summary.json`.

## Verified / not verified

Verified (measured in this session, deterministic, re-runnable):
- backend obs/action contract (shape 72 / 3, finiteness) under closed loop;
- bitwise determinism (smoke episode repeat + 2 discrepancy-row repeats);
- runtime friction-step effectiveness (braking-distance probe);
- mass override effectiveness (chassis body mass set; total matches target);
- spin-up/teleport handoff accuracy (initial planar state ~1e-3; speed gap
  <= 0.33 m/s recorded per row);
- 23/23 outcome agreement and the margin/step-count deltas above;
- current-sim re-measurement reproduces the recorded M3105 outcomes 23/23.

Not verified / out of scope:
- behavior on the remaining 41 panel rows and any fresh-seed panel (this is
  the *mini* panel only — no fidelity-sufficiency claim);
- trajectory-level agreement (only outcome/margin/step aggregates compared);
- the unmapped hidden parameters (inertia, cg shift, tire stiffness scales)
  — their effect is absorbed into the model-difference budget, not tested;
- closed-loop sensitivity to the ~10% grip surplus and the ~0.70x physical
  steering-gain difference (both could mask marginal current-sim failures on
  rows not in this panel);
- Sedan vs AutoDrift parameter identity (mass matched per scenario, but the
  Sedan remains a different vehicle).

## Reproduction

```
conda run -n chrono pip install gymnasium          # one-time (numpy already present)
PYTHONPATH=src python scripts/feasibility_audit/chrono_backend_smoke.py
PYTHONPATH=src python scripts/feasibility_audit/chrono_mini_discrepancy.py
```

Both orchestrators spawn the chrono-env worker themselves via
`conda run --no-capture-output -n chrono python scripts/feasibility_audit/chrono_backend_worker.py`.

## Artifacts

- `src/autodrift/chrono_vehicle_backend.py` (backend, scenario helpers, `KNOWN_DIFFERENCES`)
- `scripts/feasibility_audit/chrono_backend_worker.py` (chrono-env JSONL worker)
- `scripts/feasibility_audit/chrono_worker_client.py` (base-env client)
- `scripts/feasibility_audit/chrono_backend_smoke.py` (A2)
- `scripts/feasibility_audit/chrono_mini_discrepancy.py` (A3)
- `runs/feasibility_audit/chrono_smoke_summary.json`
- `experiments/feasibility_audit/chrono_mini_discrepancy.csv`
- `runs/feasibility_audit/chrono_mini_discrepancy_summary.json`
- `runs/feasibility_audit/chrono_mini_scenarios/` (23 scenario JSONs)
