# M1232 Paper-Route Extreme Fault Source-Generation Design

## Summary

M1232 opens a new source-generation branch after M1230 produced a real but
source-collapsed short-horizon wrong-history materialization signal.

Decision:

```text
extreme_fault_source_generation_design_admit_smoke
```

The selected route is not another grid-tuning pass over the M1226/M1230 public
pool. It is a source-generation branch that creates hidden-dynamics stress
cases where vehicle capability changes should matter to closed-loop evasive
control.

No training, PPO, checkpoint repair, promotion, private holdout, profile tuning,
actor-input expansion, or self-identification claim occurs in M1232.

## Why Pivot

M1230 showed that the terminal-boundary materialization machinery can produce
short-horizon wrong-history success drops:

```text
accepted_wrong_rows: 80
success_drop_fraction: 1.0
```

But the active set was too narrow:

```text
accepted_wrong_left_steps: 2
accepted_wrong_targets: 1
accepted_wrong_checkpoints: 1
accepted_wrong_normal_margin_buckets: 1
```

Continuing to tune the same public source pool risks making a gate-passing
artifact instead of finding source-diverse evidence. The next source family
should deliberately vary hidden vehicle capability, fault timing, and emergency
difficulty.

## Claim Boundary

The current simulator is a single-track / axle-level vehicle model. It can
represent or proxy some hidden dynamics changes, but it cannot honestly support
true per-wheel physical fault claims.

Current-model executable or proxy families:

| Family | Current meaning | Claim boundary |
| --- | --- | --- |
| `global_mu_drop` | global friction / tire-road authority drop | current-model fault |
| `front_lateral_authority_drop` | front axle lateral authority reduction through `cf` scaling | current-model proxy |
| `rear_lateral_authority_drop` | rear axle lateral authority reduction through `cr` scaling | current-model proxy |
| `brake_authority_drop` | global braking authority loss or fade | current-model fault |
| `drive_authority_drop` | rear drive authority loss | current-model proxy |
| `steering_fault` | steering authority, rate, or lag degradation | current-model fault |
| `delay_noise_fault` | actuator delay / response lag proxy | current-model proxy |
| `mass_cg_shift` | mass, inertia, or CG shift | current-model fault/proxy |
| `combined_fault` | coupled capability losses | current-model proxy |

Future high-fidelity-only families:

```text
true single-wheel puncture or blowout
true single-corner grip collapse
left/right split-mu patch
stuck single caliper or single-wheel brake pull
single-wheel brake pressure loss
asymmetric half-shaft or CV joint torque loss
open or locked differential failure
per-wheel ABS fault
wheel-speed sensor failure as physical wheel dynamics
corner suspension or toe damage
tire pressure, temperature, wear, or delamination dynamics
road crown, banking, curbstone, or load-transfer asymmetry
```

Those future families may be documented as motivation or roadmap. They must not
be reported as physically faithful current-model results until a four-wheel or
higher-fidelity vehicle dynamics engine exists.

## Actor-Input Guardrails

Fault labels, severities, activation steps, and hidden parameters are scenario
metadata only.

They may be used for:

```text
scenario generation
logging
pairing and source-diversity accounting
corpus mining
diagnostic teacher/oracle baselines
future training-time weights
```

They must not enter deployable actor observations. The mainline actor contract
remains:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed evidence remains:

```text
ego kinematics / IMU-like response
steering, throttle, and brake actuator state
previous physical commands
ego-frame road / free-space / obstacle geometry
recurrent state from past command-response history
```

Disallowed:

```text
mu, mass, CG, tire stiffness, brake scale, actuator time constants
fault family / fault severity / activation step
oracle feasibility labels
AEB/AES/drift-required labels
TTC, required clearance, oracle stopping distance
path/reference errors
success/collision/progress labels
```

## Source-Mining Outputs

The source branch should produce artifacts that remain compatible with the
existing matched-history and intervention harnesses:

```text
summary.json
scenario_summary.csv
snapshot_candidates.csv
matched_hidden_condition_pairs.csv
matched_cross_fault_pairs.csv
intervention_rollouts.csv
accepted_rows.csv
reset_only_rows.csv
rejected_rows.csv
fault_family_summary.csv
fault_family_pair_summary.csv
severity_summary.csv
severity_pair_summary.csv
cross_fault_pair_summary.csv
model_fidelity_limits.md
```

Accepted rows should preserve enough fields for later conversion into:

```text
matched-current history gates
terminal-boundary relocation candidates
temporal sequence intervention corpora
exact objective / replay tensors
```

## Source-Diversity Gates

Future source waves should not pass because one fault, seed, target, or time
window dominates.

Minimum accounting dimensions:

```text
fault family
wrong-history fault family
fault-family pair
severity
seed
activation phase
emergency difficulty
obstacle timing / target
left step or snapshot step
normal-margin bucket
```

Initial smoke gates:

```text
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
artifact set exists
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
model_fidelity_limits.md exists
```

Later source-positive gates should require something like:

```text
accepted wrong-history rows >= 20
history-action-critical rows >= 10
unique accepted fault families >= 3
unique accepted seeds >= 12
unique accepted severities >= 2
max accepted seed dominance <= 0.30
max accepted fault-family-pair dominance <= 0.40
```

If a run is reset-only positive or action-only positive, it must be audited
instead of treated as self-identification proof.

## First Bounded Implementation Step

M1233 should run a current-checkpoint no-training smoke through the existing
fault-event corpus harness:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m990_capability_step_fault_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 123300 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m1233_paper_route_extreme_fault_source_smoke
```

This deliberately reuses the existing M990 smoke config instead of introducing
new physics or a larger grid. The question is compatibility and source shape
under the current paper-route L3 checkpoint, not performance.

M1233 should pass if the core artifacts exist, matched pairs are produced, the
actor checksum is stable, and no training/PPO/promotion/private holdout occurs.
Accepted rows are diagnostic at smoke scale, not required.

## Follow-Up Rules

If M1233 passes with useful but sparse accepted rows:

```text
run a larger no-training source wave before any objective or PPO work
```

If M1233 passes only with reset-only or temporal-history sensitivity:

```text
audit the result and route to sequence-level intervention source design
```

If M1233 fails because normal branches collide or source pairs are missing:

```text
repair scenario timing / matching windows in a pre-registered milestone
```

If the desired fault is not physically supported by the single-track model:

```text
record it as future high-fidelity work, not as a current-model claim
```

## Decision

```text
extreme_fault_source_generation_design_admit_smoke
```

M1233 is admitted as a bounded, no-training compatibility/source-shape smoke.
