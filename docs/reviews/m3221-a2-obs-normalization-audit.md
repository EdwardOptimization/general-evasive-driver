# M3221 Review: A2 Obs-Normalization Audit

Status: accepted as an auxiliary measurement.

## Findings

No blocking issues found in the audit artifact.

The preregistration existed before the full run, and the script emits both
summary JSON and CSV tables. The full run covers 144 scripted episodes and
24,170 obs72 frames across nominal, C5-wide, and S4-proxy current-sim tiers.

The result is correctly scoped: it is not a normalization implementation and
does not admit training. It identifies a real follow-up blocker. The largest
risks are road lateral geometry scale (`road_y/20`), high-speed ego
speed/acceleration scales, and obstacle relative lateral velocity.

The recommendation is conservative: population or high-speed training remains
blocked until a separate implementation milestone changes or otherwise justifies
normalization and preview design.

## Decision

Accept M3221 as complete. Mark A2 DONE as a measurement. The next roadmap step
is A3 unless the PI chooses to insert a normalization implementation milestone
first.

## Checks

- `make research-validate` in pending state
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/obs_normalization_audit.py --quick`
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/obs_normalization_audit.py`
