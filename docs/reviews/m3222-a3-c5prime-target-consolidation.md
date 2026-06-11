# M3222 Review: A3 C5-prime Target Consolidation

Status: accepted as an auxiliary target-consolidation measurement.

## Findings

No blocking issues found in the A3 artifact.

The preregistration existed before the full run, quick mode passed the runtime
gates, and the full run used the fresh A3 seed base `20260814`. The managed
run completed with exit code 0 and wrote the expected summary and episode-row
artifacts.

The full summary reports all four preregistered target cells:
`S0/T_limit`, `S1/T_limit`, `S2/T_limit`, and `S3/T_limit`. Each cell reports
the unfiltered paired `oracle_solved - v4_pertuned_success` structural gap and
paired CI95 readout required by the manifest.

The target-confirmation rule is met: `S1/T_limit`, `S2/T_limit`, and
`S3/T_limit` clear the frozen +0.15 effect-size bar with paired CI95 lower
bound > 0. `S0/T_limit` is positive with CI excluding 0, but does not qualify
because its gap is +0.1389.

The result is correctly scoped. It confirms the C5-prime target for CP-1
review, but it does not admit Track C training and does not override the M3221
normalization/preview blocker for future population or high-speed training.

## Decision

Accept M3222 as complete. Mark A3 DONE and keep Track C BLOCKED on CP-1.
The next independent OPEN roadmap item is B1 unless the PI redirects at CP-1.

## Checks

- `make research-validate` in pending state
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5_reflex_degradation.py --c5prime-consolidation --quick`
- `scripts/run_managed.sh m3222-a3-c5prime-target-consolidation-rerun -- env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5_reflex_degradation.py --c5prime-consolidation`
