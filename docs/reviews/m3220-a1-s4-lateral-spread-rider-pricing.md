# M3220 Review: A1 S4-Lateral Spread Rider Pricing

Status: accepted as an auxiliary pricing measurement.

## Findings

No blocking issues found.

The preregistration existed before the full managed run, and the script records
the new seed base, S0/S4L levels, cg/Iz instance values, paired-CI readouts, and
oracle-filtered denominators. The full run completed under
`scripts/run_managed.sh` with exit code 0.

The result is correctly negative: 0/4 cells qualify under the frozen rule.
The largest S4L prize is S4L/T-limit at +0.007 with CI95 [-0.014, 0.028], far
below the +0.15 prize threshold and without a positive lower bound.

The scope is correctly bounded. M3220 does not mutate `ActiveSafetyReflexDriver`,
does not run training, does not admit Track C, and does not make a
driver-performance or high-fidelity claim.

The main limitation is explicit and acceptable: the rider uses the current
low-fidelity `VehicleParams` path for cg shift and yaw inertia. It does not
cover load transfer, tire-curve shape, wheel lockup, wheelbase classes, or
Chrono multi-vehicle dynamics.

## Decision

Accept M3220 as complete. A1 can be marked DONE with a negative current-sim
lateral-channel verdict. The next roadmap unit is A2 unless the PI redirects.

## Checks

- `make research-validate` in pending state
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5_reflex_degradation.py --lateral-rider --quick`
- `scripts/run_managed.sh m3220-a1-s4-lateral-spread-rider -- env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5_reflex_degradation.py --lateral-rider`
