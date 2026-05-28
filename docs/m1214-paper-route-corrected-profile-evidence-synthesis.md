# M1214 Paper-Route Corrected Profile Evidence Synthesis

## Summary

M1214 synthesizes the corrected profile-comparison branch from M1199 through
M1213.

Decision:

```text
corrected_profile_synthesis_promote_to_causal_history_gate_design
```

No training, PPO, candidate replay, promotion, private holdout, profile tuning,
or actor-input change occurs in M1214.

## Evidence Reviewed

Key artifacts:

```text
docs/m1199-paper-route-fair-comparison-pilot-run.md
docs/m1201-paper-route-profile-separability-audit.md
docs/m1204-paper-route-profile-control-repair-smoke-run.md
docs/m1209-paper-route-corrected-profile-pilot-run.md
docs/m1212-paper-route-corrected-profile-repeat-run.md
docs/m1213-paper-route-corrected-profile-repeat-result-audit.md
```

The branch moved from an initial L2 trend to corrected controls:

```text
M1199: L2 looked strongest, but controls were incomplete.
M1201: found current-frame substitution risk and reset-control eval artifact.
M1203/M1204/M1207/M1208: implemented and verified corrected controls.
M1209: L3 family strongest, but reset parity and L2/current-tiled parity blocked claims.
M1212: L2/current-tiled family strongest, L3 online beat reset but L3 family ranking conflicted with M1209.
M1213: cross-block audit found stable L2 negative evidence and unstable L3 ranking.
```

## Supported Claims

Supported:

```text
corrected profile infrastructure is usable;
fixed public profile pilots can be run reproducibly;
current-tiled controls are necessary for finite-window claims;
L2 finite-window aggregate performance is not evidence of history necessity;
L3 online-GRU can sometimes train into useful reactive behavior;
public profile rankings are seed-block sensitive.
```

The most reliable result is the negative one:

```text
L2 finite-window trend should not be used as self-identification or history-necessity evidence.
```

## Blocked Claims

Blocked:

```text
finite-window history necessity;
GRU recurrent-hidden benefit;
online self-identification;
paper-level architecture ranking;
private-holdout generalization;
promotion of any profile checkpoint.
```

Reason:

```text
Current-tiled controls explain or outperform L2.
Corrected reset-control prevents a clean L3 recurrent-hidden claim.
M1209 and M1212 disagree on the best architecture family.
```

## Process Lesson

Aggregate profile comparison is useful for engineering cleanup, but it is a
weak instrument for proving self-identification. It can show whether a profile
family is trainable under a fixed public protocol, but it cannot prove that the
policy causally uses command-response history.

The next branch must test:

```text
same or matched current observation;
different command-response history;
normal vs reset/delayed/wrong history;
terminal margin or action degradation;
no hidden/oracle actor inputs.
```

## Decision

Stop automatic broad profile repeats for now.

Route to:

```text
paper_route_causal_history_evidence
```

The next milestone should design a matched-current causal history gate. It
should ask whether behavior changes when the current observation is held fixed
but recurrent history is reset, delayed, or replaced by a wrong matched history.

## Next Milestone

```text
experiments/manifests/m1215-paper-route-causal-history-gate-design.json
```

M1215 should pre-register:

```text
matched-current ambiguity requirements
normal/reset/delayed/wrong-history interventions
current-tiled/current-response controls
action and terminal-margin degradation thresholds
failure taxonomy for no-history-signal outcomes
implementation route using existing history-intervention tools where possible
```
