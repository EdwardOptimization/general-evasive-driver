# Route C Chrono Dependency Unblock (2026-06-11)

## Status

- decision: `chrono_package_route_satisfied`
- scope: dependency availability record only; no high-fidelity validation,
  driver-performance, or discrepancy claim is made by this document.

## What changed

The M2638/M2883 stop condition for Route C (HF3) was
`dependency_source_unavailable`: the loop's safety constraints forbade
fetching Chrono itself and no human had supplied it. The resume condition in
both documents was "user supplies a valid local source root or an approved
package route".

On 2026-06-11 the approved package route was executed manually:

- conda env: `chrono` (dedicated, does not touch `base` or the project env)
- package: `pychrono 10.0.0` from the `projectchrono` channel — exactly the
  version pinned by M2880
- verification: `import pychrono`, `import pychrono.vehicle`, and
  `chrono.ChSystemNSC()` construction all succeed
  (`conda run -n chrono python -c "import pychrono.vehicle"`)

## Next steps (HF3/HF4, per the takeover route)

1. Implement `ChronoVehicleBackend` against the existing `DynamicsBackend`
   protocol in `src/autodrift/high_fidelity_interface.py` (603 lines, already
   piloted with 300 closed-loop steps on the repo-local four-wheel backend in
   M2490).
2. Port the obs72 feature extraction (largest work item: ego-frame road
   boundary lookahead and obstacle slot features against Chrono terrain).
3. HF4 discrepancy report: which current-sim failures reproduce or disappear
   under Chrono::Vehicle — the first true external-validity measurement for
   the project. Estimated 1-2 focused weeks.
