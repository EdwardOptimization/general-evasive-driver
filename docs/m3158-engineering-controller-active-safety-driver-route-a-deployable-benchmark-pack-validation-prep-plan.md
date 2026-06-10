# M3158 Route A Deployable Benchmark Pack Validation Prep Plan

## Summary

- status: completed
- decision: `route_to_m3159_validation_spec_materialization_preflight`
- source audit: `docs/m3157-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-result-audit.md`
- source benchmark pack: `runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_materialization_preflight/summary.json`
- selected next route: M3159 validation specification materialization preflight.

## Scope

M3158 defines the validation surface for the accepted M3156 Route A deployable
benchmark pack. It does not execute validation, run a simulator, replay a
rollout, tune a policy, rank drivers, promote a checkpoint, or claim driver
performance.

The plan keeps the engineering Route A objective separate from self-ID and GRU
evidence. The only driver under this validation-prep scope is the deployable
M3105/M3103 active-safety reflex incumbent exposed through:

```text
ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]
```

## Required Validation Denominators

M3159 must materialize these denominator specifications:

- `contract_probe_surface`: actor-visible obs72 input, direct action3 output,
  finite and bounded action probes, no hidden/oracle actor inputs, no TTC actor
  inputs, no runtime base policy, no checkpoint model, no recurrent hidden
  state.
- `m3105_full_fresh_current_sim_denominator`: 64 M3105 full-fresh rows from the
  M3084 fresh denominator, preserving 57 success, 5 collision, 2 offtrack, and
  0 speed-too-low rows as the incumbent baseline.
- `known_residual_failure_taxonomy`: 7 explicit residual blockers from M3156,
  including 5 collision and 2 offtrack blockers with source measurement ids,
  fresh panel ids, axis ids, task families, seeds, clearance, sideslip, lateral
  RMSE, speed, and return fields.
- `m3153_negative_replay_diagnostic`: 21 fixed-variant comparison rows with 0
  action-channel-sensitive comparisons. This is diagnostic evidence only and
  must not be treated as repair impossibility or validation proof.
- `future_high_fidelity_parity_hook`: a non-executed placeholder requiring any
  later high-fidelity route to preserve obs72/action3 parity, actuator latency,
  status taxonomy, and no hidden actor inputs before making high-fidelity
  claims.

## Same-Case Comparison Rules

Any future validation execution that uses the M3156 pack must preserve these
comparison rules:

- compare on identical scenario rows, seeds, task families, and binding roles;
- report the M3105 incumbent and any candidate on the same denominator;
- report success, collision, offtrack, speed-too-low, clearance margin,
  high-sideslip fraction, lateral RMSE, recovery status, return, speed, action
  clip fraction, and raw/final action bounds;
- include a row-level known-failure table for all seven residual blockers;
- preserve exact source ids for blocker rows so failures cannot be averaged
  away by aggregate success;
- report runtime contract and inference-cost rows before any deployment claim;
- keep current-sim, high-fidelity, robustness, and paper/self-ID claims in
  separate gate tiers.

## Go/No-Go Gates

M3159 must materialize gate specifications for:

- contract shape: obs72 input and action3 `[steer, throttle, brake]` output;
- finite bounded direct actions for contract probes;
- no hidden oracle, TTC, reference trajectory, precomputed success/progress,
  runtime base policy, checkpoint model, or recurrent hidden-state actor input;
- complete M3105 64-row denominator accounting;
- explicit 5 collision and 2 offtrack blocker disclosure;
- explicit 21-row M3153 negative replay diagnostic disclosure with 0
  action-channel-sensitive rows;
- future same-case validation comparison against M3105 before any candidate
  can claim improvement;
- no validation-result, driver-performance, current-sim verdict, robustness,
  repair-success, high-fidelity, paper, full-driver, feasibility-proof, ranking,
  promotion, or self-ID claim in M3158 or M3159.

## M3159 Required Artifacts

M3159 should write:

- `validation_denominator_rows.csv`
- `validation_gate_spec_rows.csv`
- `validation_reporting_artifact_rows.csv`
- `validation_claim_boundary_rows.csv`
- `gate_matrix.csv`
- `summary.json`
- `docs/m3159-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-validation-spec-materialization-preflight.md`
- follow-up manifest for M3160 result audit

## Boundary

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, feasibility proof, or level3 self-identification
```

M3158 is complete if this plan is present, reviewed, and routed to M3159 without
executing validation or weakening the obs72/action3 direct-action contract.
