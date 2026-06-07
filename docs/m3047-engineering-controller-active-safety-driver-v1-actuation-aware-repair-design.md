# M3047 Active Safety Driver v1 Actuation-Aware Repair Design

## Summary

- status: completed
- decision: `continue_to_m3048_actuation_aware_residual_repair_fitting_preflight`
- parent audit: `docs/m3046-engineering-controller-active-safety-driver-v1-failure-decomposition-result-audit.md`
- next route: `m3048-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-preflight`

M3047 freezes the next repair route as a bounded offline fitting preflight for
one actuation-aware residual/reflex candidate. It does not run fitting,
training, rollout, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, paper-route evaluation, or self-ID testing.

## Repair Design

The next candidate must keep the deployable composition:

```text
input: observation vector shape 72
base action: [steer, throttle, brake] from an accepted baseline policy
raw residual: 72-to-3 residual/reflex layer
actuation-aware residual: raw residual constrained by final-action headroom
output: clipped [steer, throttle, brake]
forbidden actor inputs: hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels
```

The design blocks another M3041-style residual fit unless M3048 materializes
and applies these gates:

```text
p0 offtrack recovery: every offtrack row stays visible and weighted
p0 action saturation: candidate action_clip pressure is a separate gate from residual fitting loss
p1 collision guard: T5 collision rows remain separately guarded
p1 success preservation: parent success rows and success identity guards remain protected
p2 speed-floor guard: speed_too_low remains separately counted
p0 claim boundary: fitting loss cannot be interpreted as repair success or driver performance
```

## Actuation-Aware Constraint

M3048 must not only fit target deltas. It must constrain the candidate so the
residual does not routinely push already saturated base actions farther into
final clipping. The required repair candidate form is:

```text
raw_residual = f(obs_72)
headroom_low = action_low - base_action
headroom_high = action_high - base_action
bounded_residual = clip(raw_residual, headroom_low, headroom_high)
bounded_residual = clip(bounded_residual, -residual_limit, residual_limit)
final_action = clip(base_action + bounded_residual, action_low, action_high)
```

M3048 may materialize additional scalar gates such as action-headroom margin,
action-clip penalty, residual attenuation, or row weights, but any such gate
must be trainer-side or controller-internal only. It must not add privileged
labels to the actor observation.

## Required M3048 Outputs

M3048 should write one bounded repair fitting artifact set:

```text
actuation-aware repair config snapshot
row-preserving fitting dataset with saturation/headroom fields
loss trace with offtrack action-saturation collision and success-preservation components
candidate residual/reflex artifact with 72/action 3 runtime contract
success-preservation guard rows
action-saturation guard rows
claim-boundary rows
gate matrix
M3049 result-audit manifest
```

M3048 must fail closed if it cannot preserve all M3045 repair requirements or
if it cannot keep actor inputs within the 72-dimensional human-view contract.

## Rejected Claims

M3047 explicitly rejects:

```text
repair success
driver performance
validation result or validation readiness
current-sim verdict
checkpoint ranking
winner selection
checkpoint promotion
high-fidelity validation readiness or result
paper evidence
finite-window-vs-GRU conclusion
full ideal driver completion
level3 self-identification
```

## Next

- follow-up manifest: `experiments/manifests/m3048-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-preflight.json`
- next blocker: `m3048-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-preflight`
