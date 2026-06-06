# M2835 Engineering Controller Route C Selected-Platform Source Dependency Refresh Or Stop Design

## Metadata

- status: completed
- decision: `reject_refresh_keep_route_c_hf3_stopped_until_source_supplied`
- manifest: `experiments/manifests/m2835-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-design.json`
- design artifact: `docs/m2835-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-design.md`
- parent synthesis: `docs/m2834-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-branch-synthesis.md`
- source blocker: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit.json`
- next: `m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit`

## Design Premise

M2834 closed the M2831-M2833 Route C/HF0 source-only interface evidence
handoff branch and rejected another handoff artifact loop. The remaining Route
C question is whether a selected-platform source dependency refresh is
currently admissible.

M2638 defines the resume contract:

```text
source_root_route:
  source_root path explicitly provided
  source_root exists locally
  source_root contains CMakeLists.txt or an equivalent documented build entry
  source_root is not created or fetched by the preflight
  out-of-tree build root is under the milestone run directory

package_route:
  package/import path explicitly provided
  package name explicitly provided
  metadata-only import check allowed by the follow-up manifest
  no backend start reset step rollout replay validation or performance path

other allowed resume routes:
  admitted dependency acquisition manifest
  alternate backend contract
```

The current design check found no resume route:

```text
configured source root: /home/quyaonan/workspace/chrono
/home/quyaonan/workspace/chrono: missing
/home/quyaonan/workspace/chrono/CMakeLists.txt: missing
approved package route in current status or M2835 manifest: absent
dependency acquisition manifest for this route: absent
alternate high-fidelity backend contract for this route: absent
```

This was a read-only path-existence check and document search only. M2835 did
not fetch, install, import, build, probe, start a backend, reset, step, roll
out, replay, validate, train, rank, promote, mutate dependencies, or mutate a
source tree.

## Decision

M2835 rejects a selected-platform dependency refresh preflight now:

```text
read_only_dependency_refresh_admissible: false
selected_platform_hf3_execution_admissible: false
route_c_hf3_status: stopped_until_source_supplied
reason: no valid local source root, approved package route, admitted dependency
  acquisition manifest, or alternate backend contract is present
```

The next milestone is a result audit, not execution:

```text
m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit
```

M2836 must accept or reject this stop decision before the project routes to a
materially different evidence-producing branch. If M2836 accepts the decision,
the selected-platform HF3 path remains paused under M2638 until source/package
evidence is supplied.

## Evidence Preserved

M2835 preserves the completed Route C/HF0 source-only handoff evidence:

```text
M2832 status_pass: true
handoff artifact inventory rows: 17
source-only interface handoff rows: 11
actor contract guard rows: 11
blocker boundary rows: 3
claim boundary rows: 20
gate rows: 26
gate rows all pass: true
M2833 audit accepted M2832 complete and claim-safe
M2834 synthesis closed the branch and rejected another handoff loop
```

M2835 also preserves the key Route A diagnostic context:

```text
M2828 executed rows: 16
diagnostic success: 5
diagnostic collision: 1
diagnostic off_track: 10
interpretation: nonverdict diagnostic context only
```

These rows do not become validation, ranking, performance, current-sim,
high-fidelity, paper, full-driver, or self-ID evidence.

## Actor Contract Boundary

The source dependency decision does not change the deployed actor:

```text
observation shape: 72
action shape: 3
actor-visible extractor: ActorView only
hidden/oracle actor input detected: false
labels actor visible: false
diagnostics actor visible: false
selected-platform source/build/probe/reset/validation state actor visible:
  false
```

Allowed actor-visible information remains only deployable observation:

```text
ego kinematics and IMU-like response
steering throttle brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
recurrent/history state
```

Forbidden actor-visible information remains hidden dynamics, labels, and rule
answers:

```text
mu
mass
tire stiffness
brake scale
actuator tau
slip
tire force
oracle feasibility
AEB/AES/drift labels
controller mode
speed_ref
beta_target
path error
heading error
path curvature
TTC
required clearance
oracle stopping distance
reward terms
collision labels
success labels
progress labels
route labels
selected platform state
build outcome
probe outcome
reset outcome
validation outcome
blocker classification
```

## Refresh Admission Table

```text
candidate: source_root_route
required evidence: valid local source root and CMakeLists.txt or equivalent
  build entry
current evidence: /home/quyaonan/workspace/chrono missing
admitted now: false

candidate: package_route
required evidence: explicitly approved package/import path and package name,
  with metadata-only import check admitted by follow-up manifest
current evidence: no approved package route in current status or M2835 manifest
admitted now: false

candidate: dependency_acquisition_manifest
required evidence: separate manifest admitting bounded dependency acquisition
current evidence: no such active manifest in this route
admitted now: false

candidate: alternate_backend_contract
required evidence: separate high-fidelity backend contract preserving actor and
  claim boundaries
current evidence: no alternate backend contract admitted in this route
admitted now: false
```

Because all four resume candidates are false, any selected-platform refresh
preflight now would be another process artifact without changing evidence. It
would also risk weakening M2638 by treating absence of source evidence as a
refresh opportunity.

## Supported Claims

M2835 supports only:

```text
M2834 correctly changed the axis away from another HF0 handoff artifact loop.

The selected-platform HF3 path remains paused under M2638 in the current local
state.

A dependency refresh preflight is not admitted now because no source root,
approved package route, dependency acquisition manifest, or alternate backend
contract is present.

M2836 should audit this stop decision before any Route A or Route B pivot.
```

## Rejected Claims

M2835 rejects:

```text
dependency execution readiness
source-build readiness
source-build success or failure
adapter-probe readiness
adapter-probe success or failure
backend discovery
backend availability
backend start
reset feasibility
reset execution
rollout feasibility
validation readiness
validation admission
validation result
controller ranking
source-family ranking
scenario-role ranking
winner selection
checkpoint promotion
success-rate verdict
driver performance
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
level3 self-identification
full ideal driver completion
```

## Failure Taxonomy

Controlled failures and risks:

```text
contract_violation:
  controlled. Actor 72/action 3 and no hidden/oracle actor input are
  preserved.

lineage_invalid:
  controlled. M2638, M2834, and M2835 form a direct route-decision chain.

metric_artifact:
  controlled. M2832 and M2828 counts remain handoff or diagnostic context, not
  verdict metrics.

proof_washout:
  controlled. M2835 does not reinterpret source-only rows as paper or self-ID
  evidence.
```

Active failures and risks:

```text
high_fidelity_dependency:
  active. Selected-platform source/package evidence is still unavailable.

objective_overfit:
  controlled by stop. Another dependency-process artifact is rejected until
  source/package evidence exists.

behavior_regression:
  active context. M2828 remains mixed diagnostic evidence with 10 off_track
  and 1 collision rows.

scenario_sampling_failure:
  active caution. No high-fidelity validation or distribution evidence is
  produced by M2835.

self_id_gap:
  active. M2835 does not test history necessity or level3 self-identification.
```

## Next

Route to:

```text
m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit
```

M2836 must audit that M2835:

```text
kept M2638 active
rejected read-only dependency refresh under current local/source evidence
preserved actor 72/action 3 and no hidden/oracle actor input
preserved M2832 handoff evidence as handoff-only
preserved M2828 mixed outcomes as nonverdict context
made no install fetch import build probe backend reset rollout validation
training ranking performance paper high-fidelity full-driver or self-ID claim
```

If M2836 accepts the result, the selected-platform HF3 path should remain
stopped until source/package evidence is supplied, and the next route should be
a materially different Route A or Route B evidence-producing branch rather than
another Route C dependency artifact.
