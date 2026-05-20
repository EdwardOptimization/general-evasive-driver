# M7 Related Papers

Last updated: 2026-05-21

## Search Scope

This note collects papers relevant to the M7 goal: a universal closed-loop RL
operator that directly outputs steering and throttle/brake commands across
vehicle, tire, brake, actuator, and road-surface variation.

The search focused on:

- autonomous drifting with RL;
- AEB-infeasible or emergency collision avoidance with extreme maneuvers;
- end-to-end vehicle control with sim-to-real transfer;
- domain randomization and online adaptation;
- recurrent policies for partial observability;
- asymmetric actor-critic training with privileged critic inputs.

## Highest-Relevance Papers

| Paper | Status | Why it matters for AutoDrift |
| --- | --- | --- |
| [High-speed Autonomous Drifting with Deep Reinforcement Learning](https://arxiv.org/abs/2001.01377), Cai et al., IEEE RA-L 2020 | peer-reviewed, arXiv available | Closest early match to direct model-free drift control. Uses SAC and reports generalization to unseen vehicle physical properties such as mass and tire friction. |
| [Reference-Free Formula Drift with Reinforcement Learning](https://arxiv.org/abs/2410.20990), Djeumou et al., 2024 | arXiv preprint | Very close to the "operator" idea: reference-free RL drifting, no expensive online trajectory optimization, zero-shot deployment on full-size vehicles, learned neural SDE vehicle model. |
| [Learning to Drift with Individual Wheel Drive](https://arxiv.org/abs/2507.23339), Zhou et al., 2025 | arXiv preprint | Shows GPU-parallel RL training plus systematic domain randomization for sim-to-real drifting on a 1/10 IWD platform, including transitions and variable-curvature tracking. |
| [Deep Drifting: Autonomous Drifting of Arbitrary Trajectories using Deep Reinforcement Learning](https://research.uni-luebeck.de/en/publications/deep-drifting-autonomous-drifting-of-arbitrary-trajectories-using/), Domberg et al., ICRA 2022 | peer-reviewed | Trains a small neural policy from measurements and control inputs; reports generalization to arbitrary unknown trajectories and different driving conditions, then validates on a model car. |
| [Autonomous vehicle extreme control for emergency collision avoidance via Reachability-Guided reinforcement learning](https://doi.org/10.1016/j.aei.2024.102801), Zhao et al., Advanced Engineering Informatics 2024 | peer-reviewed | Very close to the AEB-failure framing. Uses backward reachable tubes to identify where conventional avoidance is infeasible, then trains an RL extreme maneuver controller and validates with real vehicles. |
| [Autonomous Drifting Based on Maximal Safety Probability Learning](https://arxiv.org/abs/2409.03160), Hoshino et al., IEEE ITSC 2024 | peer-reviewed, arXiv available | Useful for reducing reward-shaping dependency: learns drift behavior from sparse binary safety rewards plus physics-informed loss, without a fixed reference trajectory. |
| [MPC-based drifting control with reinforcement-learning-enhanced parameter self-adaptation](https://doi.org/10.1177/09544070251410614), Wei et al., 2026 | peer-reviewed, restricted access | Very recent hybrid baseline. The main controller remains MPC, while RL adjusts MPC parameters online during closed-loop drift control. Useful as a comparison against the direct RL operator, not as the preferred M7 architecture. |

## General Operator and Adaptation Foundations

| Paper | Status | Project implication |
| --- | --- | --- |
| [Preparing for the Unknown: Learning a Universal Policy with Online System Identification](https://arxiv.org/abs/1702.02453), Yu et al., RSS 2017 | peer-reviewed, arXiv available | Core "universal policy" reference. Uses recent state/action history to infer hidden dynamics. For AutoDrift, use it as a baseline or ablation; the preferred M7 actor should learn latent adaptation from history without requiring explicit true parameters. |
| [Recurrent Model-Free RL Can Be a Strong Baseline for Many POMDPs](https://arxiv.org/abs/2110.05038), Ni et al., ICML 2022 | peer-reviewed, arXiv available | Supports adding GRU/LSTM/temporal encoders before overdesigning specialized adaptation. Hidden friction and vehicle properties make AutoDrift naturally a POMDP. |
| [Asymmetric Actor Critic for Image-Based Robot Learning](https://arxiv.org/abs/1710.06542), Pinto et al., 2017 | arXiv preprint | Direct support for actor/critic information separation: actor sees deployable observations, critic uses privileged simulator state during training. |
| [Sim-to-Real Transfer of Robotic Control with Dynamics Randomization](https://arxiv.org/abs/1710.06537), Peng et al., ICRA 2018 | peer-reviewed, arXiv available | Key dynamics-randomization reference for mass, inertia, friction, actuator, and calibration robustness. |
| [Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World](https://arxiv.org/abs/1703.06907), Tobin et al., IROS 2017 | peer-reviewed, arXiv available | Foundational visual domain randomization reference. Less vehicle-specific, but important if AutoDrift later uses camera or raster observations. |
| [Incorporating Recurrent Reinforcement Learning into Model Predictive Control for Adaptive Control in Autonomous Driving](https://arxiv.org/abs/2301.13313), Ding et al., 2023 | arXiv preprint | Hybrid comparison point: recurrent RL adapts model parameters inside MPC. This is not the main M7 controller, but it is a useful baseline against "RL as adapter for MPC." |

## End-to-End Vehicle Control and Racing Sim-to-Real

| Paper | Status | Project implication |
| --- | --- | --- |
| [Learning to Drive in a Day](https://arxiv.org/abs/1807.00412), Kendall et al., 2018 | arXiv preprint | Strong conceptual support for direct model-free closed-loop driving that moves away from hand-coded logic, mapping, and direct supervision. Scope is simpler lane following, not emergency drift. |
| [Sim-to-real reinforcement learning applied to end-to-end vehicle control](https://arxiv.org/abs/2012.07461), Kalapos et al., 2020 | arXiv preprint / IEEE copyright notice | PPO image policy directly outputs continuous vehicle control; uses domain randomization and real-track metrics. Useful for end-to-end interface and evaluation design. |
| [Sim-To-Real Transfer for Miniature Autonomous Car Racing](https://arxiv.org/abs/2011.05617), Chu et al., 2020 | arXiv preprint | Shows the tradeoff between robustness and lap time under domain randomization; supports adding balanced/targeted randomization rather than naive broad randomization. |
| [Zero-Shot Policy Transfer in Autonomous Racing: Reinforcement Learning vs Imitation Learning](https://doi.org/10.1109/ICAA52185.2022.00011), Hamilton et al., ICAA 2022 | peer-reviewed | Useful for comparing RL and imitation learning under zero-shot racing transfer. Full text may require access; DOI and metadata are available. |

## Model-Based and Learned-Model References

| Paper | Status | Project implication |
| --- | --- | --- |
| [Neural Network Tire Force Modeling for Automated Drifting](https://arxiv.org/abs/2407.13760), Broadbent et al., AVEC 2024 | peer-reviewed workshop/symposium, arXiv available | Important model-based counterpoint: learned tire force model inside NMPC improves drifting trajectory tracking, especially where front braking exposes unmodeled dynamics. |
| [Trajectory Planning Using Tire Thermodynamics for Automated Drifting](https://arxiv.org/abs/2407.12989), Kobayashi et al., IEEE IV 2024 | peer-reviewed, arXiv available | Shows hidden tire temperature/friction dynamics matter. Useful for deciding which hidden variables to randomize or infer in M7. |
| [Sim-to-Real Application of Reinforcement Learning Agents for Autonomous, Real Vehicle Drifting](https://www.mdpi.com/2624-8921/6/2/37), Toth et al., Vehicles 2024 | peer-reviewed | Useful survey-like entry point for RL drifting, real vehicle drift, and references to Cutler/How, Cai et al., Deep Drifting, and other drift-control works. |

## Cross-Domain Robotics Evidence

| Paper | Status | Project implication |
| --- | --- | --- |
| [Learning Quadrupedal Locomotion over Challenging Terrain](https://arxiv.org/abs/2010.11251), Lee et al., Science Robotics 2020 | peer-reviewed, arXiv available | Strong analogy for AutoDrift: proprioceptive RL, trained in simulation, robust zero-shot deployment to terrain and disturbances that were not explicitly represented by rules. |

## Project Takeaways

1. Direct RL drift control is already a real research line, not a speculative
   idea. The strongest matches are Cai et al. 2020, Domberg et al. 2022,
   Djeumou et al. 2024, Hoshino et al. 2024, and Zhou et al. 2025.
2. The M7 "operator" direction is supported by recurrent/POMDP and universal
   policy literature. The key design choice is whether to expose inferred
   dynamics parameters to the actor. AutoDrift should test both, but the main
   target remains a history-conditioned actor that does not require explicit
   true parameters at deployment.
3. Domain randomization is necessary but not sufficient. Racing and robotics
   papers repeatedly show that naive randomization can trade performance for
   robustness. AutoDrift needs held-out buckets and balanced sampling.
4. Emergency collision avoidance with reachability-guided RL is directly
   relevant to the AEB-infeasible setting. It suggests adding a benchmark label
   for "standard maneuver infeasible" that is stronger than the current simple
   stopping/lateral envelope labels.
5. Model-based and learned tire-model papers remain useful as baselines and
   diagnostics, but they do not invalidate the direct RL operator objective.
6. Recent hybrid MPC+RL drifting work is strong evidence that online adaptation
   matters, but it still keeps a rule/model-based controller in the loop. It is
   best treated as a benchmark family for AutoDrift rather than the main
   architecture.

## Immediate Reading Priority

1. Zhao et al. 2024 reachability-guided emergency RL.
2. Djeumou et al. 2024 reference-free formula drift RL.
3. Zhou et al. 2025 IWD domain-randomized drift RL.
4. Cai et al. 2020 high-speed autonomous drifting with SAC.
5. Ni et al. 2022 recurrent model-free RL.
6. Yu et al. 2017 universal policy with online system identification.
7. Pinto et al. 2017 asymmetric actor-critic.
8. Wei et al. 2026 MPC+RL parameter self-adaptation baseline.
