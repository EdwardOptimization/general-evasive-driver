# Emergency Drift Avoidance Related Work

Last updated: 2026-05-20

## Scope

This note focuses on the exact scenario discussed for AutoDrift:

> AEB-only is already infeasible; the controller must decide whether and how to
> use AES, high-sideslip drift, or other limit-handling actions to avoid an
> obstacle under uncertain road friction.

It separates direct competitors from supporting work on safe RL, NMPC/MPCC,
friction adaptation, and sim-to-real RL.

## Direct Competitors

| Key | Local PDF | Uses RL | Uses MPC/NMPC | Real Vehicle | Friction Adaptation | Direct relevance |
|---|---:|---:|---:|---:|---:|---|
| `liu2026abrupt` | no | yes | unclear from public metadata | unclear | public metadata says robust across road conditions | Closest match: drift obstacle avoidance with a cubic-spline planner and RSAC controller. |
| `zhao2024reachability` | no | yes | no, reachability-guided RL controller | yes, per abstract | not the main mechanism | Extreme maneuver controller triggered by Min-BRT infeasibility. |
| `li2023planning` | no | no | optimal-control planner + controller | yes, per abstract | tests varied conditions | Drift-based collision avoidance under emergency driving. |
| `stano2024enhanced` | yes | no | yes | no, high-fidelity simulation | low-friction simulation, Monte Carlo | Emergency active safety: NMPC can induce drift/DYM only when useful. |
| `zhao2021transitional` | no | no | model/controller switching | unclear | not primary | Transitional drift controller used by later reachability justification work. |
| `zhao2024dynamicdriftingddev` | no | no | yes | HIL | not primary | DDEV dynamic drifting obstacle avoidance with NMPC planning and LMPRE constraint. |

The project is not empty ground: there are already direct papers on drift-based
collision avoidance and even DRL abrupt obstacle avoidance. The open gap is more
specific:

- train for AEB-infeasible obstacle avoidance directly, not only steady drift or
  path tracking;
- require broad friction generalization and friction changes inside an episode;
- compare direct RL against reachability-triggered drift control, MPCC/NMPC, and
  hybrid RL-plus-safety-filter baselines;
- show why the learned policy adapts when the model/tire/friction assumptions are
  wrong.

## What the Open PDFs Show

### `zhao2022justifying`: Reachability Trigger for Extreme Control

This paper is the cleanest safety argument. It does not say "always drift";
it says to keep the conventional controller until backward reachability indicates
that collision is mathematically unavoidable under the conventional model. Only
then is a more capable beyond-limit controller considered.

For AutoDrift, this suggests a benchmark trigger:

- baseline AEB/AES controller;
- compute or approximate an infeasible set for conventional maneuvers;
- only activate RL drift avoidance in that set;
- report false trigger and missed trigger rates.

### `zhou2025safepsf`: Safe RL Planner + Predictive Safety Filter + MPDC

This is the most relevant open hybrid architecture. The RL module does not send
raw throttle/steering to the vehicle. It learns reference curvature and road
friction, then a predictive safety filter adjusts unsafe curvature before a
model predictive drift controller computes the low-level controls.

The key design lesson is that "RL adapts" and "constraints are enforced" can be
separate responsibilities. If AutoDrift starts with direct actuator RL, this
paper should be a serious baseline or safety-filter comparison.

### `toth2024simtoreal`: Full-Size Real-Vehicle RL Drifting

This is the strongest open evidence that RL drift can transfer from simulation to
a real car. The task is steady circular drifting, not obstacle avoidance. The
paper uses SAC, a MATLAB/Simulink simulator, actuator/sensor delay modeling, and
domain randomization. The real test is zero-shot transfer on a production sports
car modified for by-wire control.

The important limitation is equally clear: their successful range is still a
steady drift task, and the authors identify low-friction, trajectory following,
and collision avoidance as future extensions. That is close to our project gap.

### `toth2025rarl`: Robust Adversarial RL Under Changing Road Friction

This proceeding is small but directly aligned with the "any friction road"
motivation. It trains an adversarial agent to change road adhesion during
circular drift training. The main finding is that standard RL is weak under
sudden adhesion loss, especially during initiation, while robust adversarial RL
improves resilience.

This should become an early ablation for AutoDrift:

- static domain randomization;
- scheduled friction-step randomization;
- adversarial friction perturbation;
- history-aware policy versus memoryless policy.

### `stano2024enhanced`: Emergency NMPC With Drifting and Direct Yaw Moment

This paper is a strong non-RL active-safety baseline. It formulates path tracking
NMPC with steering, front-to-total longitudinal force distribution, and direct
yaw moment. In emergency conditions it can relax conventional stability limits
and use drift-like behavior to avoid collisions.

For AutoDrift, this is the main "why not just NMPC?" comparison. It is likely
strong when the model and friction estimate are good, and weaker when friction,
tire state, actuator response, or vehicle parameters are wrong.

### `bertipaglia2023mpcc` and `bertipaglia2024mpcctv`: MPCC Obstacle Avoidance

These papers are not drift-specific, but they target obstacle avoidance at the
limit of handling. They combine motion planning, path tracking, stability, and
obstacle-distance objectives in one MPCC. The 2024 torque-vectoring version adds
individual longitudinal wheel forces and friction-circle constraints.

For AutoDrift, they are useful baseline designs for AEB/AES scenarios where the
best answer is not a full drift but a limit-handling double-lane-change maneuver.

### `vaskov2023friction` and `dallas2023hierarchical`: Adaptive NMPC

These papers do not directly solve drift obstacle avoidance, but they address the
central weakness of fixed-model MPC: unknown tire-road friction near the handling
limit.

- `vaskov2023friction` couples Bayesian tire-friction learning with stochastic
  NMPC and propagates uncertainty into constraints.
- `dallas2023hierarchical` combines online UKF friction estimation with
  hierarchical NMPC and validates high tire-force usage on a full-size vehicle.

These are strong baselines for "MPC + learned/adaptive tire model" and should be
included before claiming RL is uniquely adaptive.

### `zhou2025adaptive`: Bayesian-Optimization Supervisor for Drift MPC

This is an intermediate hybrid: not end-to-end RL, but learning above MPC. The
upper layer learns drift equilibrium and adaptive path-tracking parameters, while
MPC remains the drift controller. It is tested in MATLAB-CarSim, including a
misidentified road-friction case.

For AutoDrift, this is a good "learning tunes the model/controller" baseline.
It may be easier to validate than direct actuator RL, but less flexible in abrupt
obstacle scenes.

### `liu2025survey`: Field Map

The survey confirms the two main camps:

- model-based/dynamical methods: precise and interpretable when models are right,
  but sensitive to tire/friction/model errors and real-time compute limits;
- deep learning/RL methods: better adaptation potential, but weaker safety
  verification, sample efficiency, and sim-to-real evidence.

This supports the project direction, but does not by itself prove direct RL is
better. The benchmark must show the adaptation advantage explicitly.

## Metadata-Only Papers To Revisit

These are important but no open PDF was located in this pass:

- `liu2026abrupt`: closest direct competitor; need full text if possible.
- `zhao2024reachability`: reachability-guided RL for emergency extreme control.
- `li2023planning`: drift collision avoidance with road tests.
- `zhao2021transitional`: HOTDOG-style transitional drift control.
- `zhao2024dynamicdriftingddev`: DDEV dynamic drifting obstacle avoidance.
- `ding2024unknown`: online neural dynamics model inside NMPC for unknown tires.
- `wei2026mpcrlselfadapt`: MPC with RL parameter self-adaptation and full-size
  real-vehicle drifting tests.

## Project Direction

AutoDrift should be treated as a complete engineering project, not a paper-first
novelty hunt. The practical target is:

> Build a runnable simulator, training stack, and benchmark suite where
> history-aware/adversarially trained RL can be evaluated on high-sideslip
> obstacle avoidance across wide and changing friction conditions, with
> reachability or safety-filter layers available for emergency-only activation.

Minimum credible comparison set:

- AEB-only;
- AES/MPCC without drift objective;
- fixed-friction drift MPC/NMPC;
- adaptive-friction MPC/NMPC;
- RL direct control;
- RL with history or latent friction adaptation;
- RL with reachability trigger or predictive safety filter.

Minimum task progression:

1. Circular drift with static random friction.
2. Circular drift with friction steps during initiation and steady drift.
3. Figure-8 or direction transition with friction randomization.
4. Single pop-up obstacle where AEB-only is infeasible but AES may work.
5. Pop-up obstacle where conventional AES is infeasible and drift/high-sideslip
   control is required.
