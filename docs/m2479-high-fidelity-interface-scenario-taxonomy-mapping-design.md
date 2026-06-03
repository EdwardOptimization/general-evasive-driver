# M2479 High-Fidelity Interface Scenario Taxonomy Mapping Design

- status: completed
- decision: `scenario_taxonomy_mapping_route_to_materialization_preflight`
- manifest: `experiments/manifests/m2479-high-fidelity-interface-scenario-taxonomy-mapping-design.json`
- parent current-sim adapter: `docs/m2474-high-fidelity-interface-current-sim-adapter-smoke.md`
- parent source-only four-wheel adapter: `docs/m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight.md`
- route plan: `docs/post-m2470-route-plan.md`
- next milestone: `m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight`
- external high-fidelity simulation installed/imported/executed in M2479: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2479: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2479 designs the scenario taxonomy that HF0 adapter surfaces must share before
any pilot, external backend work, or validation route. The taxonomy is an
artifact-side role map. It is not actor input.

The actor-visible contract remains:

```text
P0 observation shape: 72
action shape: 3
P0ObservationExtractor input: ActorView only
```

Scenario labels, feasibility classes, target roles, and validation buckets stay
in manifest/config/artifact metadata and diagnostics.

## Taxonomy Roles

HF0 uses five role families:

```text
stable_avoidable
stable_aes
drift_required_recovery
hidden_dynamics_robustness
unavoidable_mitigation
```

Role definitions:

```text
stable_avoidable:
  Obstacle avoidance should be feasible with stable braking/steering behavior.
  AEB-style stopping or mild evasive steering is expected to be physically
  plausible. The role is useful as a baseline safety-control fixture.

stable_aes:
  AEB-only stopping is not intended to be feasible, but stable active evasive
  steering should be plausible. This role tests emergency steering without
  requiring drift.

drift_required_recovery:
  Handling-limit recovery or large sideslip response may be required. This role
  motivates richer dynamics and recovery evidence, but the label must not be
  actor-visible.

hidden_dynamics_robustness:
  The same actor contract must handle changes in friction, mass, CG, tire,
  brake, drive, steering lag, and other hidden vehicle parameters without
  reading those parameters.

unavoidable_mitigation:
  A collision or large violation may be physically unavoidable. The objective is
  mitigation and stable degradation, not binary success. The role label must
  remain metadata because actor-visible observation cannot reveal an oracle
  unavoidable verdict.
```

## Surface Mapping

Current-sim HF0 surface:

```text
surface_id: current_sim_autodrift_hf0
source: AutoDriftEnv through CurrentSimDynamicsBackend
available roles:
  stable_avoidable
  stable_aes
  drift_required_recovery
  hidden_dynamics_robustness
  unavoidable_mitigation
actor-visible fields:
  ego response, actuator response, previous commands, road boundary geometry,
  obstacle slots
metadata-only fields:
  obstacle_label, feasibility labels, friction step timing, mu, mass, CG,
  tire/brake/drive/actuator scales, reward terms, termination reason
```

Source-only four-wheel HF0 surface:

```text
surface_id: source_only_four_wheel_hf0
source: FourWheelDriftModel through FourWheelHF0Backend
available roles:
  stable_avoidable
  hidden_dynamics_robustness
limited or fixture-only roles:
  stable_aes
  drift_required_recovery
  unavoidable_mitigation
actor-visible fields:
  ego response, actuator response, previous commands, deterministic road
  fixture, deterministic obstacle slots
metadata-only fields:
  per-wheel forces, slip/load-like force details, fault scales, vehicle params,
  source model state
```

Mapping implications:

```text
1. current_sim_autodrift_hf0 is the richer scenario-role surface because it
   already carries obstacle scenario metadata and current-sim task roles.
2. source_only_four_wheel_hf0 is the richer four-contact-patch dynamics surface
   but currently has only deterministic road/obstacle fixtures.
3. M2480 should materialize both surfaces in one artifact while marking which
   roles are supported, limited, or blocked per surface.
4. A role being available in artifact metadata does not make the role visible
   to the actor.
```

## Actor Boundary

Allowed actor-visible values remain exactly the deployable P0 channels:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
recurrent/latent state maintained by the policy
```

Forbidden actor-visible values:

```text
scenario role label
AEB/AES/drift-required/unavoidable feasibility class
mu, mass, CG, tire stiffness, brake scale, drive scale, actuator tau
wheel force, slip, load, per-wheel fault scale
speed_ref, beta_target, path error, heading error, curvature
TTC, oracle stopping distance, required clearance
reward terms, success labels, termination labels
```

Hand-written diagnostics and model baselines may read metadata in `info` or
summary artifacts, but deployable RL actor policies must not.

## M2480 Materialization Design

M2480 should produce a small machine-readable mapping artifact:

```text
runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json
runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv
```

Recommended columns:

```text
surface_id
role_family
support_status
actor_observation_shape
action_shape
actor_visible_inputs
metadata_only_fields
blocked_reason
next_fixture_requirement
```

Allowed `support_status` values:

```text
supported
limited_fixture
blocked
```

Minimum M2480 checks:

```text
all rows preserve actor_observation_shape 72
all rows preserve action_shape 3
scenario role labels do not enter actor_visible_inputs
hidden dynamics and wheel diagnostics are metadata_only_fields
current-sim and source-only four-wheel surfaces are both represented
```

## Evidence Scope

M2479 is scenario taxonomy mapping design only. It supports a bounded
materialization/preflight of HF0 role metadata across adapter surfaces.

M2479 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification.

## Next

Route to
`m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight`.
