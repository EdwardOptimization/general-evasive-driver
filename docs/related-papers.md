# Related Papers From Citation Snowballing

Last updated: 2026-05-20

This file filters the references from the requested papers for AutoDrift. It is
not a complete bibliography; it is a priority list for building an RL + NMPC
autonomous drifting stack.

## P0: Read Before Designing the First Controller

| Key | Paper | Why P0 |
|---|---|---|
| `liu2026abrupt` | Deep Reinforcement Learning Based Autonomous Drift System for Abrupt Obstacle Avoidance | Closest direct competitor to the AEB-failure idea: drift path planner plus deep RL controller for abrupt obstacles. Closed paper; public metadata only so far. |
| `zhao2022justifying` | Justifying Emergency Drift Control for Automated Vehicles | Gives the clean trigger logic: use extreme/drift control only after reachability proves conventional control cannot avoid collision. |
| `zhou2025safepsf` | Safe RL with a Predictive Safety Filter for Drifting | Strong hybrid reference: RL adapts friction/curvature, PSF enforces road-boundary safety, MPDC handles low-level drift control. |
| `toth2024simtoreal` | Sim-to-Real Application of RL Agents for Autonomous, Real Vehicle Drifting | Best full-size real-car RL drift transfer reference; domain randomization and real actuator/sensor delays are central. |
| `weber2024modeling` | Modeling and Control for Dynamic Drifting Trajectories | The best starting point for an online NMPC formulation: curvilinear path tracking, dynamic drifting, wheel-speed dynamics, longitudinal load transfer, actuator limits, and full-scale evidence. |
| `subosits2021impacts` | Impacts of Model Fidelity on Trajectory Optimization for Autonomous Vehicles in Extreme Maneuvers | Sets the modeling bar: more fidelity does not automatically improve trajectories; single-track captures transients, double-track matters when differential braking/LSD/torque vectoring is central. |
| `kobayashi2024trajectory` | Trajectory Planning Using Tire Thermodynamics for Automated Drifting | Makes tire temperature/friction drift a planning and control variable instead of a nuisance parameter. |
| `djeumou2024referencefree` | Reference-Free Formula Drift with Reinforcement Learning | Strongest direct reference for RL as a reference-free waypoint policy on full-scale vehicles. |
| `djeumou2023autonomous` | Autonomous Drifting with 3 Minutes of Data via Learned Tire Models | Clean bridge between learning and NMPC: learned tire models as drop-in replacements, not a replacement for constraints. |

## P1: Use to Shape Baselines and Ablations

| Key | Paper | Use |
|---|---|---|
| `broadbent2024neural` | Neural Network Tire Force Modeling for Automated Drifting | A small front-tire NN can improve NMPC under front braking, but data coverage and observer latency hurt transient initiation. |
| `meijer2024nonlinear` | A Nonlinear Model Predictive Control for Automated Drifting with a Standard Passenger Vehicle | Important reality check: actuator interfaces on standard vehicles can block fully automated steering even when NMPC commands are reasonable. |
| `cai2020highspeed` | High-Speed Autonomous Drifting With Deep Reinforcement Learning | Good simulation RL baseline using SAC-style trajectory following; useful for reward/state design comparison. |
| `domberg2022deep` | Deep Drifting: Autonomous Drifting of Arbitrary Trajectories using Deep Reinforcement Learning | Important arbitrary-trajectory RL comparison; especially useful for analyzing why sim policies fail on transient real-world transfer. |
| `toth2025rarl` | Autonomous Vehicle Drifting Under Dynamically Changing Road Friction Using Adversarial Agents | Directly targets sudden friction changes during circular drifting with robust adversarial RL. |
| `zhou2025adaptive` | Adaptive Learning-Based MPC Strategy for Drift Vehicles | Useful hybrid baseline: Bayesian optimization learns drift equilibrium and path-tracking parameters under friction/model mismatch. |
| `stano2024enhanced` | Enhanced Active Safety Through Integrated Autonomous Drifting and Direct Yaw Moment Control via NMPC | Strong NMPC emergency active-safety baseline with drift/DYM enabled only when useful. |
| `bertipaglia2023mpcc` | MPCC for Vehicle Obstacle Avoidance at the Limit of Handling | Good non-RL obstacle-avoidance baseline; merges planning, tracking, stability, and obstacle distance in one MPCC. |
| `zhou2025learning` | Learning to Drift with Individual Wheel Drive | Useful if the project chooses an IWD scale platform or needs GPU-parallel RL training infrastructure. |
| `djeumou2025one` | One Model to Drift Them All | Advanced direction: conditional diffusion can generate/adapt model parameters while real-time MPC remains the control layer. |

## P2: Background and Model Components

| Key | Paper | Use |
|---|---|---|
| `velenis2011steady` | Steady-state Drifting Stabilization of RWD Vehicles | Steady-state drift equilibria and stabilization baseline. |
| `hindiyeh2014controller` | A Controller Framework for Autonomous Drifting | Earlier experimental controller framework and stability treatment. |
| `goh2016simultaneous` | Simultaneous Stabilization and Tracking of Basic Automobile Drifting Trajectories | Basic path tracking plus sideslip stabilization. |
| `goh2020toward` | Toward Automated Vehicle Control Beyond the Stability Limits | General-path drifting with physically interpretable model inversion and wheel-speed control. |
| `goel2020opening` | Opening New Dimensions | Front braking as a valuable extra actuator for simultaneous speed/path/sideslip control. |
| `peterson2023exploiting` | Exploiting Linear Structure | Explains why drift dynamics can remain computationally manageable despite nonlinearity. |
| `chen2023dynamic` | Dynamic Drifting Control for General Path Tracking | Additional model-based general-path tracking reference. |
| `farroni2014trt` | TRT: Thermo Racing Tyre | Tire thermal physics reference if the project goes beyond a lumped thermal state. |
| `sorniotti2009tire` | Tire Thermal Model for Enhanced Vehicle Dynamics Simulation | Lightweight thermal-model reference for vehicle simulation. |

## Project-Specific Interpretation

The references point to a conservative first design:

1. Start with a CPU online NMPC or SQP controller around a single-track model.
2. Add wheel-speed and longitudinal load-transfer dynamics before adding a full
   double-track model.
3. Treat learned tire/thermal models as replaceable model components inside the
   controller.
4. Use RL first for reference-free waypoint behavior, warm starts, residual
   choices, or high-level target generation.
5. Keep full end-to-end RL as a baseline, not the main safety-critical control
   layer, until the simulator and domain randomization evidence are strong.

The exception is an IWD scale-car path. If AutoDrift targets a 1/10 IWD platform,
then `zhou2025learning` becomes a P0 system reference because wheel torque
vectoring changes both the action space and model-fidelity requirements.
