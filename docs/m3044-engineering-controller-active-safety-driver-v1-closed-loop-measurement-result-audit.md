# M3044 Active Safety Driver v1 Closed-Loop Measurement Result Audit

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m3045_failure_decomposition_materialization_preflight`
- audited milestone: `m3043-engineering-controller-active-safety-driver-v1-closed-loop-measurement-preflight`
- next route: `m3045-engineering-controller-active-safety-driver-v1-failure-decomposition-materialization-preflight`

M3044 accepts M3043 as a complete and claim-safe closed-loop measurement
artifact. It does not accept M3043 as validation, ranking, promotion,
driver-performance verdict, current-sim verdict, repair success,
high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.

## Synthesis Questions

### evidence_summary

Accepted M3043 facts:

```text
status_pass: true
gate_matrix_pass: true
scheduled measurement rows: 32
measurement episode rows: 32
measurement failure rows: 0
measurement success rows: 4
measurement collision rows: 4
measurement offtrack rows: 24
measurement speed-too-low rows: 1
all-row success rate recorded: 0.125
all-row clearance margin mean recorded: 7.361927716635305
all-row clearance margin delta mean recorded: 0.15756972004202266
all-row return delta mean recorded: -0.5880631464089019
candidate binding success rows: 0/16
parent binding success rows: 4/16
residual abs max: 0.07999999821186066
actor contract: observation 72 / action 3
residual adapter guards pass: true
actor contract guards pass: true
checkpoint side-effect guards pass: true
claim boundary guards pass: true
```

This is the first same-denominator closed-loop measurement for the M3041
residual/reflex candidate. The data are useful because they move the branch
from offline fitting loss to real current-sim rollout rows while preserving the
deployable actor boundary. The data are not sufficient to claim a deployed
driver, a repaired driver, or a validated active-safety system.

### supported_claims

Supported claims:

```text
M3043 produced the required closed-loop measurement artifacts for all 32 scheduled rows
the residual/reflex layer remained bounded at residual_abs_max 0.08
the deployable actor interface remained observation 72 to [steer throttle brake]
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs remained blocked
parent checkpoints and residual artifacts were not mutated or promoted
claim-boundary rows explicitly rejected validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver and self-ID claims
the fixed denominator now has actionable failure data for offtrack-dominant and action-saturation-aware repair analysis
```

### falsified_claims

Rejected claims:

```text
M3041 offline residual fitting alone is enough to produce broad closed-loop active-safety repair on the fixed M3043 denominator
the current M3041 residual candidate is ready for ranking promotion validation or driver-performance verdict
candidate-binding behavior is repaired by the current residual candidate
M3043 is paper evidence or self-ID evidence
M3043 establishes a finite-window-vs-GRU conclusion
M3043 establishes high-fidelity validation readiness
```

The strongest concrete negative signal is candidate-binding behavior: 0/16
candidate rows succeeded under the residual measurement, with 14 offtrack rows
and 2 collision rows. Parent-binding rows are not a promotion basis either:
4/16 succeeded, 10 were offtrack, 2 collided, and the result remains a
measurement artifact only.

### failure_taxonomy_summary

The M3043 failure surface is behavior-negative but contract-clean:

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: not observed
scenario_sampling_failure: not observed
behavior_regression: active risk because closed-loop failures remain dominant
objective_overfit: active risk because offline target fitting did not transfer broadly to closed-loop safety
proof_washout: active risk if later work optimizes only the small success or collision-delta signals
seed_fragility: unresolved because M3043 is same-denominator measurement only
```

Dominant outcome shape:

```text
off_track: 24/32
collision: 4/32
speed_too_low: 1/32
success_obstacle_pass: 4/32
candidate binding: 0/16 success, action_clip_fraction_mean 0.41243192505631066
parent binding: 4/16 success, action_clip_fraction_mean 0.0
T4: 1/16 success, 14/16 offtrack
T5: 3/16 success, 4/16 collision, 10/16 offtrack
```

This points away from more claim documents and toward a small
failure-decomposition materialization that isolates actuation saturation,
offtrack recovery, collision guard, and role/family effects before any further
candidate fitting or rollout.

### public_gate_overfit_risk

Risk is medium. The branch did not rank or promote a checkpoint and did not
optimize a policy online against public gates. It did, however, use a fixed
32-row denominator and trainer-side target tensors derived inside the same
mainline. M3045 must therefore preserve every M3043 row, including negative
candidate rows and parent rows, rather than cherry-picking the single positive
delta or the clean contract outcome.

### next_branch_decision

Decision:

```text
continue_to_m3045_failure_decomposition_materialization_preflight
```

M3045 should be a no-new-execution materialization milestone. It may read
M3043 summary, episode, metric, guard, and gate artifacts and produce
machine-checkable failure decomposition, actuation saturation, repair
requirement, claim-boundary, and M3046 audit artifacts. It must not run
rollouts, train, validate, rank, select a winner, promote or mutate
checkpoints, tune profiles, or claim repair success, driver performance,
current-sim verdict, high-fidelity validation, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.

The repair direction after M3045 should prioritize a deployable
actuation-aware reflex candidate: it must reduce offtrack and collision failure
pressure while respecting action saturation and preserving the 72/action 3
actor contract.
