# M2880 Engineering Controller Route C HF3 Chrono Dependency Acquisition Manifest Design

## Metadata

- status: completed
- decision: `admit_m2881_chrono_source_availability_preflight`
- manifest: `experiments/manifests/m2880-engineering-controller-route-c-hf3-chrono-dependency-acquisition-manifest-design.json`
- design artifact: `docs/m2880-engineering-controller-route-c-hf3-chrono-dependency-acquisition-manifest-design.md`
- parent synthesis: `docs/m2879-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-synthesis.md`
- source blocker: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- blocker audit: `docs/m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2881-engineering-controller-route-c-hf3-chrono-source-availability-preflight.json`
- next: `m2881-engineering-controller-route-c-hf3-chrono-source-availability-preflight`

## Design Premise

M2879 closes the M2876-M2878 Route A post-package-refresh fresh diagnostic
branch as complete but weak diagnostic evidence. M2877 resolved and executed
all 11 fixed rows, but the outcome surface remained:

```text
diagnostic success/collision/off_track: 3/0/8
ordinary success denominator allowed: false
driver performance claim: false
validation readiness claim: false
high-fidelity claim: false
self-ID claim: false
```

The next useful axis is Route C/HF3 dependency handling, but only after it is
converted into a repository-local manifest. M2638/M2836 still forbid selected
platform HF3 execution unless one of the approved resume routes exists:

```text
valid local source root
approved package/import route
admitted dependency acquisition manifest
alternate backend contract
```

M2880 supplies the third route: an admitted dependency-acquisition manifest
design. It does not acquire the dependency. It defines the version, paths,
gates, failure taxonomy, actor boundaries, and claim boundaries that a later
preflight must obey.

## Selected Backend

M2880 fixes the selected backend route:

```text
backend name: chrono_vehicle
backend family: chrono_vehicle_or_equivalent_open_backend
backend package: Project Chrono / Chrono::Vehicle
selected version: 10.0.0
git tag: 10.0.0
expected commit prefix: 9faf13d
source URL: https://github.com/projectchrono/chrono.git
```

This is a fixed route selection, not a claim that this milestone checked the
remote repository or that the local source exists.

## External Path Contract

All dependency material must stay outside `general-evasive-driver`:

```text
external root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0

source root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0/source

build root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0/build

install root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0/install

logs root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0/logs

future external manifest root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0/manifests

future external probe root:
  /home/quyaonan/workspace/hf_backends/chrono/10.0.0/probes
```

M2880 does not create or mutate any of these directories.

Repository-local artifacts are limited to research docs, manifests, queue,
status, scoreboard, research log, review artifacts, and later source-availability
run outputs under `runs/`.

## Dependency Acquisition Manifest Schema

The future external dependency manifest should have this schema:

```json
{
  "backend_name": "chrono_vehicle",
  "backend_family": "chrono_vehicle_or_equivalent_open_backend",
  "chrono_version": "10.0.0",
  "chrono_git_tag": "10.0.0",
  "chrono_expected_commit_prefix": "9faf13d",
  "source_route": "manual_prefetch_or_explicitly_admitted_git_clone",
  "source_url": "https://github.com/projectchrono/chrono.git",
  "source_root": "/home/quyaonan/workspace/hf_backends/chrono/10.0.0/source",
  "build_root": "/home/quyaonan/workspace/hf_backends/chrono/10.0.0/build",
  "install_root": "/home/quyaonan/workspace/hf_backends/chrono/10.0.0/install",
  "logs_root": "/home/quyaonan/workspace/hf_backends/chrono/10.0.0/logs",
  "network_policy": {
    "agent_may_fetch_network": false,
    "manual_prefetch_required": true,
    "approved_git_clone_allowed_only_if_explicitly_enabled": false
  },
  "mutation_policy": {
    "may_mutate_hf_backends_dir": false,
    "may_mutate_general_evasive_driver_repo": false,
    "may_modify_system_packages": false,
    "may_install_python_packages": false
  },
  "required_source_files": [
    "CMakeLists.txt"
  ],
  "required_source_metadata": [
    "git rev-parse HEAD starts with 9faf13d when .git metadata is available",
    "source root is not inside general-evasive-driver"
  ],
  "required_build_tools_for_later_gates": [
    "cmake",
    "C++17-capable compiler"
  ],
  "target_modules": [
    "Chrono core",
    "Chrono::Vehicle"
  ],
  "forbidden_claims_before_reset_probe": [
    "high_fidelity_validation_passed",
    "controller_works_in_high_fidelity",
    "sim_to_real_validated",
    "finite_window_vs_gru_verdict",
    "self_id_verdict",
    "performance_improvement"
  ]
}
```

The mutation policy is false for M2881 because the next admitted task is
source availability only. A later configure/build/install manifest may relax
external `hf_backends` mutation after a source-availability audit, but it must
remain explicit and must still not mutate `general-evasive-driver` with Chrono
source, build, install, or logs.

## Gate Ladder

Route C/HF3 must proceed in this order:

```text
G0 source availability:
  read-only check of source root, CMakeLists.txt, optional git metadata, path
  boundary, and no repository pollution.

G1 configure:
  CMake configure only after G0 passes. No build if configure fails.

G2 build:
  CMake build only after G1 passes. No install if build fails.

G3 install:
  CMake install only after G2 passes. No link/import if install fails.

G4 link/import:
  minimal C++ link or package metadata probe only after G3 passes. No backend
  start if link/import fails.

G5 adapter reset:
  backend reset only after G4 passes. No policy action or rollout.

G6 manual step:
  canned manual action step only after G5 passes. No policy rollout.

G7 policy smoke:
  one-episode policy smoke only after G6 passes. No performance, ranking, paper,
  current-sim, full-driver, or self-ID claim.
```

No later gate may be skipped because an earlier gate looks likely to pass.

## Failure Taxonomy

Route C/HF3 dependency handling uses this local taxonomy:

```text
source_unavailable:
  source root missing, CMakeLists.txt missing, git metadata unavailable when
  required, wrong tag/commit, or source root inside the repo.

toolchain_missing:
  cmake missing, compiler missing, compiler too old, or C++17 unsupported.

configure_dependency_missing:
  configure fails because required dependencies or Chrono module options are
  unavailable.

build_failure:
  configure passes but compile or link fails.

install_failure:
  build passes but install fails or expected install artifacts are absent.

import_or_link_probe_failure:
  minimal include/link/import probe fails or runtime loader path is unresolved.

adapter_contract_failure:
  backend access would require forbidden actor fields or cannot preserve
  [steer, throttle, brake].

reset_failure:
  adapter reset crashes, produces non-finite telemetry, or cannot initialize a
  scenario.

step_failure:
  manual action step crashes, integration is unstable, or state becomes
  non-finite.

claim_boundary_violation:
  any source/build/reset/probe row is interpreted as validation, performance,
  paper, current-sim, high-fidelity validation, full-driver, or self-ID evidence.
```

These Route C failure labels are process taxonomy for dependency handling.
They do not replace the harness-level process-v2 failure types in milestone
manifests.

## Actor Contract Boundary

The Chrono dependency route does not change the deployed actor:

```text
observation shape: 72
action shape: 3
action mapping: [steer, throttle, brake]
actor-visible extractor: ActorView only
hidden/oracle actor input: false
dependency metadata actor visible: false
build/import/reset/validation labels actor visible: false
```

Allowed actor-visible signals remain only deployable observation:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent/history state
```

Forbidden actor-visible information remains:

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

## Claim Boundary

M2880 supports only:

```text
Route C/HF3 Chrono dependency-acquisition manifest design is now admitted.

The selected version, source URL, expected commit prefix, external paths, gate
ladder, failure taxonomy, actor boundary, and claim boundary are fixed.

M2881 source-availability preflight is admissible as a read-only follow-up.
```

M2880 rejects:

```text
source exists locally
source was fetched
source was configured
source was built
source was installed
Chrono import/link works
adapter reset works
manual step works
policy smoke works
high-fidelity validation readiness
high-fidelity validation result
driver performance
controller ranking
winner selection
checkpoint promotion
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
level3 self-identification
full ideal driver completion
```

## M2881 Admission

M2880 admits exactly one follow-up:

```text
m2881-engineering-controller-route-c-hf3-chrono-source-availability-preflight
```

M2881 must be read-only with respect to external dependency paths. It may:

```text
read docs and manifests
check whether source root exists
check whether source root is outside general-evasive-driver
check whether CMakeLists.txt exists
read git metadata if present
check cmake/compiler command availability without installing anything
write a repo-local summary under runs/m2881...
write a follow-up audit manifest if and only if the preflight completes
```

M2881 must not:

```text
create /home/quyaonan/workspace/hf_backends
clone Chrono
fetch network
install apt or pip packages
configure Chrono
build Chrono
install Chrono
import pychrono or projectchrono
run a C++ link probe
start a backend
reset
step
run policy action
roll out
validate
rank
promote
claim high-fidelity validation
```

M2881's allowed outcomes are:

```text
source_available_claim_safe:
  local source root exists, CMakeLists.txt exists, path is outside the repo,
  optional git metadata is compatible with the expected prefix, and no mutation
  was needed. This only admits a result audit; it does not admit configure until
  the audit accepts it.

source_unavailable_claim_safe:
  source root or CMakeLists.txt is missing, path is inside the repo, or metadata
  is incompatible/absent where required. Route C/HF3 remains stopped.

preflight_failed_claim_safe:
  preflight tooling fails without mutating dependencies or weakening claims.
```

## Decision

M2880 chooses:

```text
admit_m2881_chrono_source_availability_preflight
```

The branch remains process-only. No Chrono source, configure, build, install,
link/import, backend reset, manual step, policy smoke, validation, performance,
paper, current-sim, full-driver, or self-ID evidence has been produced.
