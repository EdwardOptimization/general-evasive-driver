# M2996 Engineering Controller Route A Actor-Head Delta Nonzero Residual Validation Contract Materialization Preflight

## Summary

- status pass: `True`
- gate matrix pass: `True`
- required artifacts present: `True`
- validation contract rows: `43`
- residual-head wrapper rows: `3`
- parent comparison rows: `3`
- success behavior retention rows: `13`
- stale exclusion rows: `11`
- actor input exclusions: `14`
- checkpoint side-effect guards: `12`
- target quality validated: `False`
- validation run: `False`
- ranking run: `False`
- checkpoint mutated: `False`
- next blocker: `m2997-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m2997-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-result-audit.json`

## Artifact Binding

```text
artifact: runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/candidate_residual_head_artifact.npz
artifact exists: True
linear weight shape: 72x3
linear bias shape: 3
observation/action: 72/3
residual limit: 0.07999999821186066
success guard required abs max: 0.0010000000474974513
success retention residual abs max: 0.00034158502239733934
```

## Boundary

M2996 materializes validation contracts only. It preserves actor observation
`72` and action `3`, keeps
target labels and provenance actor-invisible, keeps stale rows excluded, keeps
parent and candidate artifacts read-only, and keeps `target_quality_validated:
false`.

M2996 does not run validation, rank candidates, select a winner, mutate or
promote checkpoints, run private holdout or performance measurement, or claim
repair success, driver performance, paper evidence, current-sim verdict,
high-fidelity validation, finite-window-vs-GRU evidence, full-driver
completion, or self-ID evidence.
