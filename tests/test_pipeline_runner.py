
import subprocess
from unittest.mock import Mock, call, patch

import pytest

from run_pipeline import run_stage


def create_monitor():
    monitor = Mock()
    monitor.start_stage.return_value = {
        "stage_name": "Test Stage"
    }
    return monitor


@patch("run_pipeline.subprocess.run")
def test_stage_retries_after_failure_and_then_succeeds(mock_run):
    """A failed first attempt should be retried."""

    mock_run.side_effect = [
        subprocess.CalledProcessError(1, ["test"]),
        None,
    ]

    monitor = create_monitor()

    with patch("run_pipeline.time.sleep") as mock_sleep:
        elapsed = run_stage(
            stage_name="Test Stage",
            script_name="generate_data.py",
            monitor=monitor,
            retries=2,
            retry_delay_seconds=1,
        )

    assert elapsed >= 0
    assert mock_run.call_count == 2

    mock_sleep.assert_called_once_with(1)

    monitor.complete_stage.assert_called_once()
    monitor.fail_stage.assert_not_called()


@patch("run_pipeline.subprocess.run")
def test_stage_fails_after_all_attempts(mock_run):
    """The stage should fail after exhausting all attempts."""

    error = subprocess.CalledProcessError(
        1,
        ["test"],
    )

    mock_run.side_effect = error

    monitor = create_monitor()

    with patch("run_pipeline.time.sleep"):
        with pytest.raises(subprocess.CalledProcessError):
            run_stage(
                stage_name="Test Stage",
                script_name="generate_data.py",
                monitor=monitor,
                retries=2,
                retry_delay_seconds=0,
            )

    assert mock_run.call_count == 3

    monitor.fail_stage.assert_called_once()
    monitor.complete_stage.assert_not_called()


@patch("run_pipeline.subprocess.run")
def test_stage_runs_once_when_retries_are_disabled(mock_run):
    """Zero retries should mean exactly one execution attempt."""

    mock_run.side_effect = subprocess.CalledProcessError(
        1,
        ["test"],
    )

    monitor = create_monitor()

    with pytest.raises(subprocess.CalledProcessError):
        run_stage(
            stage_name="Test Stage",
            script_name="generate_data.py",
            monitor=monitor,
            retries=0,
            retry_delay_seconds=0,
        )

    assert mock_run.call_count == 1
    monitor.fail_stage.assert_called_once()
