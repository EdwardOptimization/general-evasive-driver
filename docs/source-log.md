# Source Log

Last updated: 2026-05-20

This log records papers that were actually located and used for the first
AutoDrift literature pass. `references.bib` is the citation source of truth.

## Primary Papers Requested

| Key | Status | Local PDF | Canonical link | Use |
|---|---|---|---|---|
| `broadbent2024neural` | arXiv preprint / AVEC 2024 | `papers/2407.13760v1-neural-network-tire-force-modeling-for-automated-drifting.pdf` | <https://arxiv.org/abs/2407.13760> | Learned front lateral tire force as an NMPC drop-in under front braking. |
| `djeumou2024referencefree` | arXiv preprint | `papers/2410.20990v1-reference-free-formula-drift-with-rl.pdf` | <https://arxiv.org/abs/2410.20990> | Reference-free RL policy with tire-energy-inspired reward and neural SDE simulator. |
| `zhou2025learning` | arXiv preprint | `papers/2507.23339v1-learning-to-drift-iwd.pdf` | <https://arxiv.org/abs/2507.23339> | IWD scale-car RL, GPU-parallel simulation, domain randomization, sim-to-real evidence. |
| `kobayashi2024trajectory` | arXiv preprint / IV 2024 | `papers/2407.12989v1-trajectory-planning-tire-thermodynamics.pdf` | <https://arxiv.org/abs/2407.12989> | Tire temperature as a state that changes available friction and reference feasibility. |
| `weber2024modeling` | IEEE T-IV, open-access PDF supplied by user | `papers/modeling-and-control-for-dynamic-drifting-trajectories.pdf` | <https://doi.org/10.1109/TIV.2023.3340918> | Full-scale dynamic drifting NMPC with wheel-speed and longitudinal load-transfer dynamics. |
| `subosits2021impacts` | IEEE T-IV, open-access PDF supplied by user | `papers/impacts-of-model-fidelity-on-trajectory-optimization-for-extreme-maneuvers.pdf` | <https://doi.org/10.1109/TIV.2021.3051325> | Model-fidelity tradeoff for trajectory optimization near friction limits. |

## High-Value Related Papers Added From Citations

| Key | Status | Local PDF | Canonical link | Why it matters |
|---|---|---|---|---|
| `djeumou2023autonomous` | ICRA 2023 / arXiv | `papers/2306.06330v2-autonomous-drifting-with-3-minutes-of-data.pdf` | <https://arxiv.org/abs/2306.06330> | Predecessor to the NN tire and reference-free RL papers; shows learned tire models inside NMPC. |
| `meijer2024nonlinear` | AIM 2024 / arXiv | `papers/2405.10859v1-nmpc-automated-drifting-standard-passenger-vehicle.pdf` | <https://arxiv.org/abs/2405.10859> | NMPC on an unmodified standard passenger vehicle; actuator authority becomes a central bottleneck. |
| `cai2020highspeed` | IEEE RA-L / arXiv | `papers/2001.01377v1-high-speed-autonomous-drifting-with-drl.pdf` | <https://arxiv.org/abs/2001.01377> | SAC-style end-to-end RL baseline for high-speed drifting in simulation. |
| `djeumou2025one` | CoRL 2024 / PMLR 2025 proceedings | `papers/djeumou2025-one-model-to-drift-them-all.pdf` | <https://proceedings.mlr.press/v270/djeumou25a.html> | Conditional diffusion over physics-informed model parameters, integrated with real-time MPC. |

## Emergency Drift / AEB-Failure Avoidance Papers

| Key | Status | Local PDF | Canonical link | Why it matters |
|---|---|---|---|---|
| `zhao2022justifying` | IFAC-PapersOnLine, open PDF | `papers/emergency/2022-justifying-emergency-drift-control.pdf` | <https://doi.org/10.1016/j.ifacol.2022.10.275> | Defines when a beyond-limit controller is justified: trigger only after reachability shows conventional control is inevitably unsafe. |
| `zhou2025safepsf` | IROS 2025 / arXiv | `papers/emergency/2506.22894v1-safe-rl-predictive-safety-filter-drifting.pdf` | <https://arxiv.org/abs/2506.22894> | Safe RL planner learns friction/curvature and sends filtered references to a model predictive drift controller. |
| `toth2024simtoreal` | Vehicles 2024, open PDF | `papers/emergency/2024-sim-to-real-rl-real-vehicle-drifting.pdf` | <https://doi.org/10.3390/vehicles6020037> | Full-size real-vehicle RL drifting with SAC and domain randomization; important sim-to-real baseline. |
| `toth2025rarl` | Engineering Proceedings 2025, open PDF | `papers/emergency/2025-rarl-dynamically-changing-road-friction.pdf` | <https://doi.org/10.3390/engproc2025113005> | Robust adversarial RL for circular drift under dynamically changing road adhesion. |
| `stano2024enhanced` | IEEE T-IV, open repository PDF | `papers/emergency/2024-enhanced-active-safety-integrated-drifting-dymc-nmpc.pdf` | <https://doi.org/10.1109/TIV.2023.3340992> | Emergency active-safety NMPC that allows drift/direct-yaw-moment behavior only when it helps collision avoidance. |
| `bertipaglia2023mpcc` | IAVSD 2023 / arXiv | `papers/emergency/2308.06742v2-mpcc-obstacle-avoidance-limit-handling.pdf` | <https://arxiv.org/abs/2308.06742> | MPCC for obstacle avoidance at handling limits with friction-circle constraints and real-time rapid-prototyping evidence. |
| `bertipaglia2024mpcctv` | AIM 2024 / arXiv | `papers/emergency/2405.10847v1-mpcc-obstacle-avoidance-limit-torque-vectoring.pdf` | <https://arxiv.org/abs/2405.10847> | Extends MPCC with torque vectoring and wheel longitudinal-force optimization for double-lane-change avoidance. |
| `vaskov2023friction` | arXiv preprint | `papers/emergency/2305.03798v1-friction-adaptive-stochastic-nmpc.pdf` | <https://arxiv.org/abs/2305.03798> | Online tire-road friction learning plus stochastic NMPC; useful baseline for uncertainty-aware constraints. |
| `dallas2023hierarchical` | arXiv preprint | `papers/emergency/2304.12263v2-hierarchical-adaptive-nmpc-maximizing-tire-force.pdf` | <https://arxiv.org/abs/2304.12263> | Hierarchical adaptive NMPC with online friction estimation and tire-force usage near the limit. |
| `zhou2025adaptive` | Robotics and Autonomous Systems / arXiv | `papers/emergency/2502.04696v1-adaptive-learning-based-mpc-drift-vehicles.pdf` | <https://arxiv.org/abs/2502.04696> | Bayesian-optimization supervisor learns drift equilibrium/path tracking parameters for MPC under friction/model mismatch. |
| `liu2025survey` | AppliedMath 2025, open PDF | `papers/emergency/2025-autonomous-drifting-survey.pdf` | <https://doi.org/10.3390/appliedmath5020033> | Survey of autonomous drifting methods, platforms, generalization gaps, and safety-verification gaps. |

## Cited Work Kept as Metadata Only

These are important for background but were not downloaded in this pass.

| Key | Status | Link | Use |
|---|---|---|---|
| `liu2026abrupt` | IEEE RA-L, closed | <https://doi.org/10.1109/LRA.2025.3640975> | Directly targets abrupt obstacle avoidance with a drift path planner and RSAC controller; no open PDF located. |
| `li2023planning` | Control Engineering Practice, closed | <https://doi.org/10.1016/j.conengprac.2023.105625> | Drift-based emergency collision avoidance with optimal-control planning and road tests. |
| `zhao2024reachability` | Advanced Engineering Informatics, closed | <https://doi.org/10.1016/j.aei.2024.102801> | Reachability-guided RL extreme maneuver controller with real-vehicle validation. |
| `zhao2021transitional` | IEEE ITSC, closed | <https://doi.org/10.1109/ITSC48978.2021.9564496> | Transitional drift controller used by later emergency-justification work. |
| `zhao2024dynamicdriftingddev` | IEEE T-TE, closed | <https://doi.org/10.1109/TTE.2024.3380629> | Dynamic drifting obstacle avoidance for distributed-drive EVs via NMPC planning and LMPRE constraints. |
| `brown2020coordinating` | IEEE T-IV, closed | <https://doi.org/10.1109/TIV.2019.2955362> | Classic NMPC obstacle avoidance at tire-force limits; important non-drift emergency baseline. |
| `ding2024unknown` | IEEE IV, closed | <https://doi.org/10.1109/IV55156.2024.10588474> | Online neural vehicle model inside NMPC for drifting with unknown tires, full-size Lexus LC500 validation per TRI summary. |
| `wei2026mpcrlselfadapt` | Proc. IMechE Part D, closed | <https://doi.org/10.1177/09544070251410614> | New MPC + RL parameter self-adaptation result with CarSim and full-size real-vehicle drifting tests. |
| `velenis2011steady` | peer-reviewed journal | <https://doi.org/10.1016/j.conengprac.2011.07.010> | Steady-state RWD drift stabilization baseline. |
| `voser2010analysis` | peer-reviewed journal | <https://doi.org/10.1080/00423111003746140> | High-sideslip dynamics and early control analysis. |
| `hindiyeh2014controller` | peer-reviewed journal | <https://doi.org/10.1115/1.4027471> | Experimental autonomous drifting controller framework. |
| `goh2016simultaneous` | IEEE conference | <https://doi.org/10.1109/IVS.2016.7535448> | Basic simultaneous stabilization and tracking. |
| `goh2020toward` | peer-reviewed journal | <https://doi.org/10.1115/1.4045320> | General-path drifting and wheel-speed control. |
| `goel2020opening` | IEEE conference | <https://doi.org/10.1109/IV47402.2020.9304728> | Front braking as an additional drifting actuator. |
| `peterson2023exploiting` | peer-reviewed journal | <https://doi.org/10.1109/TIV.2022.3171734> | Linear structure inside highly nonlinear drifting dynamics. |
| `domberg2022deep` | IEEE conference | <https://doi.org/10.1109/ICRA46639.2022.9812249> | PPO-style arbitrary-trajectory drift RL, important comparison for reference-free RL. |
| `chen2023dynamic` | peer-reviewed journal | <https://doi.org/10.1109/TIV.2023.3235007> | General path tracking dynamic drifting controller. |
| `farroni2014trt` | peer-reviewed journal | <https://doi.org/10.1007/s11012-013-9821-9> | Detailed tire thermal modeling reference. |
| `sorniotti2009tire` | SAE technical paper | <https://doi.org/10.4271/2009-01-0441> | Thermal tire model reference for vehicle dynamics simulation. |

## Reading Caveats

- The arXiv papers are treated as preprints unless a peer-reviewed venue is
  explicitly verified in the citation entry.
- The project notes use only summarized technical content. They do not store
  extracted full text from the papers.
- Several related papers are useful but paywalled; those are logged through
  verified DOI metadata only.
