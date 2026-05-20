import numpy as np

from autodrift.tasks import CircleTrack, FigureEightTrack, make_track


def test_circle_track_reports_reference_radius():
    track = CircleTrack(radius=18.0)

    assert track.reference_radius == 18.0


def test_figure_eight_track_frame_is_finite_and_signed_curvature_changes():
    track = FigureEightTrack(radius=18.0, samples=256)
    pose = track.reset_pose(np.random.default_rng(21), speed=7.0)
    frame = track.frame(pose[0], pose[1], pose[2])

    assert track.reference_radius > 1.0
    assert np.isfinite(frame.lateral_error)
    assert np.isfinite(frame.heading_error)
    assert np.min(track.curvatures) < 0.0
    assert np.max(track.curvatures) > 0.0


def test_make_track_rejects_unknown_kind():
    try:
        make_track("unknown", radius=18.0)
    except ValueError as error:
        assert "unknown track_kind" in str(error)
    else:
        raise AssertionError("expected ValueError")
