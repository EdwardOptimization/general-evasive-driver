# Autonomous Drifting: RL + NMPC Reading Notes

Last updated: 2026-05-20

## One-Sentence Takeaway

这批论文共同指向一个清晰路线：在线控制层不要一开始做成纯 RL；先用可解释、可约束、可测时延的 NMPC/SQP 作为安全和约束骨架，再把 RL 和学习模型放到参考生成、模型残差、轮胎力/热模型、warm start 或策略层。

## Literature Map

| Thread | Main papers | Core message |
|---|---|---|
| Model-based drifting control | `weber2024modeling`, `goh2020toward`, `goel2020opening`, `peterson2023exploiting` | 漂移不是普通 path tracking；需要显式处理大侧偏角、后胎饱和、轮速动态、纵向载荷转移和执行器约束。 |
| Model fidelity | `subosits2021impacts`, `weber2024modeling`, `meijer2024nonlinear` | 模型越复杂不一定越好；单轨模型通常是第一个可用平衡点，双轨模型只在差动制动、LSD、IWD 或横向载荷转移成为核心时才值得引入。 |
| Tire uncertainty | `kobayashi2024trajectory`, `broadbent2024neural`, `djeumou2023autonomous`, `djeumou2025one` | 极限工况下误差主要来自轮胎：温度、磨耗、路面、载荷、前轮制动下的耦合滑移。学习模型最有价值的位置是 tire/residual/model-parameter 层。 |
| Reference-free RL | `djeumou2024referencefree`, `cai2020highspeed`, `domberg2022deep`, `zhou2025learning` | RL 能减少昂贵参考轨迹规划，尤其适合 waypoint/general-path 策略；但真实部署依赖高质量 simulator、domain randomization 或 learned dynamics。 |

## Primary Papers

### Weber and Gerdes 2024: Dynamic Drifting NMPC

This is the main model-based controller reference.

What it does:

- Uses a full-scale Toyota Supra platform.
- Formulates dynamic, non-equilibrium drifting as an NMPC tracking problem.
- Uses a single-track model, but adds two dynamics that matter in transient drift:
  wheel speed evolution and longitudinal load transfer.
- Tracks dynamic figure-8 style maneuvers while respecting nonlinear vehicle dynamics
  and actuator limits.

Key quantitative results:

- RMS path tracking error: about 13 cm.
- Peak path tracking error: about 47 cm.
- RMS speed error: about 0.24 m/s.
- RMS sideslip error: about 2.4 degrees.
- Reported mean NMPC solution time in experiment: about 18.91 ms.

Important interpretation:

- The residual tracking error is plausibly dominated by tire-parameter uncertainty.
  A simulation with roughly 10% tire parameter mismatch can reproduce similar error.
- Further increasing model fidelity, for example jumping to a full double-track model
  with lateral load transfer, may have diminishing returns unless the added actuators
  or tire-load mechanisms are central to the task.
- For AutoDrift, this is the best starting point for the first online solver: single-track
  curvilinear model, wheel-speed state, longitudinal load-transfer state, explicit input
  constraints, short horizon, deterministic solve-time measurement.

### Subosits and Gerdes 2021: Model Fidelity in Extreme Maneuvers

This paper is the model-selection guardrail.

What it compares:

- Point-mass, single-track, and double-track vehicle models.
- Trajectory optimization across ice, wet asphalt, and dry asphalt.
- Real full-size vehicle execution, not only simulation.

Core result:

- Model fidelity does not strongly change the optimal path or speed profile in many
  cases.
- Fidelity changes how well the model exposes the vehicle's limits and how it
  coordinates actuators.

Design implication:

- Point-mass can be acceptable for high-level trajectory shape under near-steady
  behavior.
- Single-track is the right first model when transient yaw/sideslip dynamics matter.
- Double-track becomes useful when the control authority itself is left/right asymmetric:
  individual braking, torque vectoring, IWD, or controllable differential behavior.

For AutoDrift:

- Do not begin with the most complex model unless the platform needs it.
- A staged model ladder is better:
  point-mass path sanity check -> single-track drift dynamics -> wheel-speed/load-transfer
  single-track -> double-track/IWD only if actuators require it.

### Kobayashi, Weber, and Gerdes 2024: Tire Thermodynamics

This paper explains why friction should not be treated as a fixed scalar.

What it does:

- Adds a simple rear-tire thermal model.
- Uses temperature-dependent friction in drifting trajectory generation.
- Computes quasi-equilibria as tire temperature changes, then uses LQR tracking.
- Tests on the Takumi full-size drifting platform.

Key results:

- In steady-state drifting, the thermodynamic trajectory keeps lateral tracking error
  stable and within roughly 10 cm in the reported experiment.
- In figure-8 dynamic drifting, the model improves consistency through transitions,
  with reported transition errors within roughly 50 cm.
- The thermal prediction is imperfect, but the trend is valuable enough to improve
  planning and feedback design.

For AutoDrift:

- Add tire temperature/friction adaptation earlier than a full double-track model.
- If direct tire temperature is unavailable, a latent thermal/friction state estimated
  from slip power and tracking residual may be enough for a first version.
- For RL, randomizing static friction is not enough; the simulator needs friction drift
  over time if long drifting episodes are in scope.

### Broadbent et al. 2024: Neural Network Tire Force Model

This is a compact example of learning inside NMPC.

What it does:

- Replaces the front Fiala brush lateral tire model with a small feedforward neural
  network.
- Uses vehicle states and controls similar to physics tire-model features.
- Keeps the NMPC architecture mostly unchanged.
- Focuses on front-axle braking while drifting, where front lateral force is hard to
  model.

Key observations:

- The NN model improves steady drifting path and state tracking under front braking.
- Drift initiation remains weaker because the training data underrepresents initiation;
  less than 5% of their training data is from initiation-like regions.
- Observer latency and target-label synchronization are treated as major risks.

For AutoDrift:

- Learned tire models should be trained with segment balance: initiation, steady drift,
  transitions, braking, recovery.
- Learned components should be small enough to fit inside the NMPC timing budget.
- Use learned model as a replaceable tire-force/residual module first, not as the
  entire controller.

### Djeumou et al. 2024: Reference-Free Formula Drift With RL

This is the strongest RL policy reference in the set.

What it does:

- Trains an RL policy to drift through waypoint configurations without a precomputed
  reference trajectory.
- Uses a neural SDE vehicle simulator learned from real driving data.
- Designs the objective around tire energy absorption and track-bound constraints.
- Demonstrates zero-shot deployment on full-size Toyota GR Supra and Lexus LC 500.

Important mechanisms:

- The learned simulator is uncertainty-aware and physics-constrained.
- Policy observation includes path/waypoint information rather than a dense reference
  trajectory.
- Jacobian regularization is used to improve smoothness and noise robustness.
- Model randomization across tire types improves transfer when tire conditions vary.

For AutoDrift:

- RL is attractive as a reference-free high-level behavior policy.
- The policy should output something NMPC can check or refine: desired waypoint,
  desired sideslip/velocity envelope, candidate control, or warm start.
- A direct policy-to-actuator path should stay a research baseline until the simulator,
  estimator, and safety envelope are strong.

### Zhou et al. 2025: IWD Scale-Car RL

This paper matters if AutoDrift chooses a small IWD platform.

What it does:

- Builds an open-source 1/10 scale individual-wheel-drive RC platform.
- Uses GPU-parallel simulation and systematic domain randomization.
- Trains RL for steady circular drift, direction transitions, eight-shaped paths, and
  variable-curvature tracking.
- Deploys to real hardware without real-world fine-tuning.

Key results:

- Reported real-world position RMSE is about 0.221 m on the eight-shaped path and
  about 0.231 m on the variable-curvature path.
- Ablation shows initial-state randomization and trajectory randomization are important.
- IWD creates extra yaw authority through differential wheel speeds.

For AutoDrift:

- GPU is clearly useful for massively parallel RL simulation.
- IWD changes the problem: action space, controllability, and model fidelity all differ
  from a RWD full-scale drift car.
- If the project uses IWD, a double-track or wheel-resolved model becomes relevant
  much earlier.

### Meijer, Bertipaglia, and Shyrokau 2024: Standard Passenger Vehicle NMPC

This is the actuator-interface warning.

What it does:

- Uses an NMPC architecture for drifting a standard passenger vehicle.
- Computes offline equilibrium maps for desired sideslip and path radius.
- Uses an NMPC state controller plus a path-following controller that adjusts curvature.
- Tests on a BMW M3 Competition.

Key lesson:

- The controller can compute plausible steering and drive-torque commands, but a
  standard vehicle interface can lack enough steering torque/angle authority for fully
  automated drifting.
- Semi-automated tests validate the torque command and show that appropriate steering
  actuation is still necessary.

For AutoDrift:

- Platform constraints are not afterthoughts. Before designing the final controller,
  decide whether the target is simulation, scale-car, modified full-size vehicle, or
  standard vehicle interface.
- Actuator limits and rate limits belong in the first solver prototype.

### Djeumou et al. 2025: Conditional Diffusion + MPC

This is a later-stage research direction, not the first MVP.

What it does:

- Learns a conditional diffusion model over parameters of a physics-informed neural
  stochastic dynamics model.
- Conditions on online measurements so the model can adapt to vehicle/tire/road
  variation.
- Keeps real-time MPC as the controller around the generated/adapted model.

For AutoDrift:

- This is the most relevant "future" architecture if one wants cross-vehicle and
  cross-tire generalization.
- It supports a useful principle: let learning adapt the model distribution; let MPC
  keep constraints and short-horizon decision making.

## Design Conclusions for AutoDrift

### 1. Use NMPC as the first safety-critical control layer

The papers with full-scale experimental evidence repeatedly keep a model-based layer
in the loop. Even when learning is introduced, it usually enters as:

- learned tire force model;
- learned stochastic simulator;
- learned parameter distribution;
- policy/warm-start/reference-free waypoint generator.

The first AutoDrift solver should therefore expose a small NMPC problem with:

- curvilinear path state: `s`, `e`, heading error;
- vehicle state: yaw rate, speed, sideslip;
- wheel-speed state if RWD drifting is targeted;
- optional tire thermal/friction latent state;
- controls: steering, drive torque, optional front brake;
- constraints: steering angle/rate, torque/rate, track bounds, speed/sideslip envelope.

### 2. Keep the first vehicle model single-track plus targeted missing dynamics

A reasonable first model is not "simple bicycle only" and not "full double-track".
The most defensible first model is:

- single-track rigid body dynamics;
- nonlinear tire force model;
- rear wheel-speed dynamics;
- longitudinal load transfer;
- optional first-order tire temperature/friction state.

Escalate to double-track only when one of these becomes central:

- IWD or torque vectoring;
- differential braking;
- lateral load transfer is required by the data;
- left/right tire temperature or force asymmetry is a target contribution.

### 3. Make RL responsible for the part NMPC is bad at

NMPC is strong at local constrained optimization. It is weaker at choosing global style,
waypoint behavior, and expensive reference generation. RL should initially target:

- reference-free waypoint progression;
- desired sideslip/speed/radius schedule;
- control warm start for NMPC;
- recovery-mode selection;
- simulator-based policy baseline for comparison.

Avoid making a pure RL policy the only actuator controller in the first milestone unless
it is explicitly isolated as one project baseline.

### 4. Treat tire uncertainty as the central research risk

The recurring failure mode is not "the controller has no math"; it is "the tire model is
wrong in exactly the region that matters." The useful modeling knobs are:

- friction coefficient uncertainty;
- tire temperature and wear;
- front lateral force under braking;
- observer latency in tire-force labels;
- transient initiation coverage;
- domain randomization over initial state, tire parameters, track shape, and disturbances.

### 5. Measure solver and policy quality with drift-specific metrics

Suggested evaluation matrix:

| Scenario | What it tests |
|---|---|
| constant-radius steady drift | equilibrium and tire/friction model sanity |
| drift initiation | data imbalance, actuator limits, warm-start quality |
| figure-8 transition | transient yaw/sideslip and wheel-speed dynamics |
| variable-curvature path | general path tracking |
| waypoint-only course | RL reference-free behavior |
| friction/temperature drift episode | adaptation and robustness |

Suggested metrics:

- lateral tracking error RMS and peak;
- sideslip error RMS and peak;
- speed error RMS;
- steering and torque smoothness;
- solve time distribution, not only mean;
- spin-out/off-track/failure rate;
- actuator saturation frequency;
- model residual grouped by segment type.

## Proposed First Project Milestone

The smallest useful AutoDrift MVP should be a simulation-first stack:

1. Implement a single-track drift model with curvilinear coordinates.
2. Add nonlinear tire force, wheel-speed dynamics, and actuator rate limits.
3. Build a short-horizon NMPC/SQP controller for a constant-radius and figure-8 task.
4. Add a simple tire-friction latent state or temperature schedule.
5. Train or script an RL high-level policy that outputs desired sideslip/speed/waypoint
   targets, while NMPC remains the final actuator command generator.
6. Compare three baselines:
   - model-only NMPC;
   - NMPC with learned residual/tire model;
   - RL high-level policy plus NMPC refinement.

This keeps the first engineering milestone measurable while preserving a path toward the
more ambitious reference-free RL and learned-model directions.

## Open Decisions

These decisions should be made before writing substantial code:

- Target platform: pure simulator, 1/10 scale IWD, RWD RC, or full-size vehicle data?
- Main product direction: RL-first simulator and benchmark suite, solver-focused
  control stack, or sim-to-real transfer stack?
- Solver stack: Python prototype, CasADi/ACADOS, custom C++ SQP, or MiniSolver-style
  embedded solver later?
- Data assumption: do we have real drifting logs, or must the first phase be synthetic?
- Actuator set: steering + throttle only, or steering + torque + front brake / IWD?

Until these are decided, the conservative architecture is: learned simulator and RL policy
for exploration, CPU NMPC/SQP for online constrained control, and tire uncertainty as the
main modeling target.
