# M1264 Paper-Route Richer-Fault Capability-Source Synthesis

## Summary

M1264 synthesizes the `paper_route_richer_fault_capability_source` branch from
M1258 through M1263.

Decision:

```text
richer_fault_capability_source_synthesis_pivot_to_fidelity_source_design
```

Close the current branch:

```text
paper_route_richer_fault_capability_source
```

Open the next branch:

```text
paper_route_fidelity_fault_source_design
```

The current single-track/current-model proxy-fault branch improved source
diagnostics, but it still did not produce strict capability-separable rows.
M1262 specifically tested the best available low-regret repair target and found
that obstacle-geometry retargeting preserves action divergence but does not
amplify two-sided regret.

## Evidence Summary

| Milestone | Evidence variable | Accepted rows | Key result |
| --- | --- | ---: | --- |
| M1258 | richer v4 proxy-fault design | n/a | admitted bounded current-model richer-fault source smoke |
| M1259 | v4 proxy faults + trajectory proposals + viability relocation | 0 | 8 near-boundary viable pairs, 4 action-divergent pairs, but low regret |
| M1260 | source result audit | n/a | identified pair 5 as viable/action-divergent/low-regret repair target |
| M1261 | regret-boundary retarget design | n/a | selected fixed-action obstacle-geometry retarget around pair 5 |
| M1262 | fixed-action geometry retarget | 0 | 441 geometry candidates, 1764 rollouts, max min-regret only `0.0043813964` |
| M1263 | retarget result audit | n/a | stopped same-axis geometry retargeting and routed to synthesis |

The best current target, pair 5, has:

```text
fault_family_pair: global_mu_drop->brake_authority_drop
best_action_l2: 0.7001441121
source min_cross_regret: 0.0042178858
M1262 max min_cross_regret: 0.0043813964
required min_cross_regret: 0.02
```

So the action sequences differ, but the outcomes do not separate enough.

## Supported Claims

Supported engineering claims:

```text
The richer-fault source infrastructure works.
The strict accepted-source semantics are now protected by tests.
M1259/M1262 artifacts are reproducible and guardrails are explicit.
Actor inputs remained human-view/no-privileged.
No source labels, hidden parameters, oracle outcomes, or search outputs entered
deployable actor inputs.
```

Supported scientific/process claims:

```text
Current-model proxy faults improve source shape compared with the previous
local source branch.

Action divergence alone is insufficient. A paper-route source row needs
branch-specific outcome regret, not merely different commands.

Geometry/timing can change difficulty and create collisions, but it did not
make the fixed pair-5 action sequences branch-specific under current dynamics.
```

## Falsified Claims

Falsified for this branch:

```text
The current single-track/current-model richer proxy-fault family plus
trajectory proposals and obstacle-geometry retargeting is sufficient to produce
strict accepted capability-separable rows under the current thresholds.
```

Also falsified:

```text
A larger same-axis geometry grid around M1259 pair 5 is likely to solve the
source-positive gap.
```

Not falsified:

```text
the overall General Evasive Driver objective;
the value of recurrent command-response history;
the possibility of source-positive rows under higher-fidelity dynamics;
the possibility that local teacher/optimizer-derived trajectories expose
branch-specific regret in a richer simulator;
the need for closed-loop RL after source evidence exists.
```

## Failure Taxonomy Summary

Primary failure type:

```text
scenario_sampling_failure
```

Subtypes observed:

```text
richer_fault_source_low_regret
regret_boundary_geometry_retarget_negative
fixed_action_geometry_retarget_exhausted_for_pair5
```

Resolved process issue:

```text
metric_artifact:
  asymmetric_success_drop was previously counted as accepted;
  M1259 corrected accepted = symmetric_margin_accept.
```

Not observed:

```text
contract_violation
private_holdout_contamination
training_instability
proof_washout
promotion_gate_failure
```

## Public-Gate Overfit Risk

Continuing the same branch has high overfit risk:

```text
M1259 pair 5 has now been selected, retargeted, and audited.
M1262 tested 441 nearby public geometries around that pair.
The strongest min-regret remains below 0.005.
```

More public repair around the same pair would mostly optimize the harness
surface. It would not yet answer whether the underlying simulator has
capability-separable emergency cases.

## Next Branch Decision

Pivot to a fidelity-source design branch:

```text
paper_route_fidelity_fault_source_design
```

Next milestone:

```text
m1265-paper-route-fidelity-fault-source-design
```

The next branch should not immediately train or run PPO. It should design the
minimum source-fidelity upgrade needed to produce realistic capability changes:

```text
single-wheel grip loss / blowout proxy with asymmetric force effects
left-right split-mu
single-wheel brake pull / stuck caliper yaw moment
halfshaft or drive-side torque asymmetry
front/rear axle authority loss with load-transfer effects
actuator delay / brake authority faults coupled with per-wheel limits
```

The design should separate:

```text
current in-repo single-track proxy limits,
minimum in-repo four-wheel/fault extension,
external high-fidelity simulator validation options,
and paper-route source acceptance gates.
```

Acceptance thresholds must not be relaxed. The goal is to change source
fidelity or source generation, not to lower the proof standard.

## Guardrails

M1264 is synthesis-only:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
threshold_relaxation_allowed: false
```

No self-identification claim is made. Self-ID evidence remains blocked until
strict source-positive cases exist and can be used for history-necessity gates.
