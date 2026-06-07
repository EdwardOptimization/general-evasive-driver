# M3018 Engineering Controller Route A Post-Residual-Stop New Source Failure Localization Materialization Preflight

## Summary

- status: completed
- result class: `new_source_failure_localization_materialization_preflight_complete`
- source specs: 16/16
- scheduled workload rows: 32/32
- episode rows localized: 32/32
- failure rows preserved: 0/0
- failure localization rows: 32
- profile/source aggregate rows: 32
- diagnostic counts: {'success': 3, 'collision': 5, 'off_track': 23, 'speed_too_low': 2}
- termination counts: {'': 3, 'obstacle_collision': 4, 'off_track': 23, 'speed_too_low': 2}
- failure families: {'collision_clearance_failure': 5, 'offtrack_high_severity_recovery_failure': 5, 'offtrack_recovery_failure': 17, 'speed_floor_context': 2, 'success_context': 3}
- primary failure modes: {'collision_or_obstacle_collision_termination': 5, 'diagnostic_success': 3, 'off_track': 17, 'off_track_high_severity': 5, 'speed_too_low': 2}
- gate matrix pass: True
- required artifacts present: True

## Boundary

M3018 reanalyzes existing M3015 diagnostic rows only. It does not rerun environments, train, rank, promote, mutate checkpoints, tune profiles, validate, select a repair target, or claim performance.

Rejected claims:

```text
repair target selection, validation result, repair success, driver performance, current-sim verdict, paper evidence, high-fidelity validation readiness or result, finite-window-vs-GRU conclusion, full ideal driver completion, level3 self-identification, controller/profile ranking, winner selection, checkpoint mutation, checkpoint promotion, profile tuning, training, replay, or PPO
```

## Interpretation

The materialized rows preserve the 32-row denominator and expose profile/source-localized failure families for M3019 audit. These rows remain diagnostic accounting artifacts only, not repair-success, validation, current-sim verdict, paper, high-fidelity, full-driver, finite-window-vs-GRU, ranking, promotion, or self-ID evidence.

## Next

- next blocker: `m3019-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3019-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-result-audit.json`
