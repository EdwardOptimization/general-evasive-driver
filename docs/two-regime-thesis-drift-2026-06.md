# The bounded two-regime conclusion: do not initiate drift, manage the state you have

Updated: 2026-07-10

This note supersedes the earlier claim that active countersteer uniquely
recovered 9/9 Chrono slide states. That count used the wrong action semantics
and is not admissible evidence.

## Regime A: before slip

Under assumptions A1-A8 in
`docs/preslip-reachable-set-dual-proof-theory-2026-07.md`, the force-input
differential inclusion maps every branch-labelled high-slip force history to an
ascending/peak-branch selection with the same net wrench. Therefore

`K_required-slide(T, O) subseteq K_grip(T, O)`.

The theorem is bounded to the direct-force abstraction, matched chassis and
authority, a pre-slip initial state, a static obstacle, uniform friction, common
geometry and progress constraints, and no terminal pose objective. It does not
prove steering-angle/tire-transient realization in Chrono.

M3270 independently supports this ordering on the registered finite Chrono
domain. It exhaustively replayed all 20 unique source actions across three
friction cells and eight fresh seeds per cell:

- 480/480 trajectory classifications completed;
- 60/60 exact replays passed;
- all 24/24 seeds had finite grip, required-slide, and free boundaries;
- grip minimum clearable distance `D*` was 4.0-7.5 m lower than required slide
  on every seed, giving a finite-grid grip-only witness each time;
- all 24 free optima were grip-like.

This is finite-library numerical support, not continuous detailed-model or
universal vehicle dominance.

## Regime B: after slip

For the same post-slip plant, horizon, and recovery target, exact control-set
nesting gives only the weak result

`U_baseline subset U_expanded  =>  R_baseline subseteq R_expanded`.

Strict inclusion requires a matched state in
`R_expanded \ R_baseline`. Slip alone does not create that witness.

The corrected experiments did not find strict inclusion:

- **M3271:** direct body-state injection matched `|beta|=0.8` but initialized
  rear tire slip at only `0.00136 rad`; the state was not a valid developed
  tire slide.
- **M3272:** four continuously reached Chrono branches had valid beta and rear-
  slip truth. Zero-steer throttle or uniform braking was best at every branch;
  added steering gained `0.00 s`.
- **M3273:** nine deeper, continuously reached compact-model branches across
  three friction tiers were valid slides, but baseline and expanded recovery
  were both `0/9`.

These negatives separate two real post-slip cases: moderate slides can recover
without steering-based drift management, while deeper slides can already lie
outside both tested recovery kernels.

## Invalidated earlier evidence

`scripts/audits/chrono_recovery.py` and
`scripts/audits/recovery_reachability.py` supplied normalized actions such as
`[0,0,0]` while describing them as zero physical pedals. In this repository,
normalized pedal `0` means 50% pedal; physical zero maps to normalized `-1`.
The scripts also called uniform service braking "ESC" without modeling
individual-wheel brake yaw authority. Their 3/15 and 9/9 counts must not appear
as evidence in a paper.

## Supported conclusion

The evidence supports this narrower two-regime statement:

> Before slip, do not deliberately initiate drift for collision avoidance
> within the stated theorem and finite experimental scope. After slip, manage
> the actual state with the available controls, but do not assume that steering-
> based drift control is necessary or sufficient merely because slip exists.

Equivalently, being already in slip is a necessary context for a post-slip
drift-recovery claim, not a sufficient condition for extra recovery value.

## Not supported

- strict post-slip recovery-set expansion on the current Chrono or compact-
  model panels;
- "after slip, countersteer is always the rescue";
- labeling uniform braking as production ESC;
- continuous-control, cross-vehicle, split-mu, moving-obstacle, real-car,
  promotion, or self-ID conclusions.
