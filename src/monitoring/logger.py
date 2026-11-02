
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path


class PipelineMonitor:
    """Track pipeline runs, stages, timings, metrics and failures."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.outputs_dir = self.project_root / "outputs"
        self.logs_dir = self.project_root / "logs"

        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = str(uuid.uuid4())
        self.started_at = datetime.now(timezone.utc)

        self.stages = []
        self.status = "RUNNING"
        self.metrics = {}

        self.log_path = self.logs_dir / "pipeline.log"
        self.history_path = (
            self.outputs_dir / "pipeline_run_history.json"
        )

        self.logger = logging.getLogger(
            f"customer360.{self.run_id}"
        )
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Avoid duplicate handlers.
        self.logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler = logging.FileHandler(
            self.log_path,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        self.log("Pipeline monitor initialized.")

    @staticmethod
    def timestamp():
        """Return the current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def log(self, message, level="INFO"):
        """Write a message to the pipeline log."""
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def start_stage(self, stage_name):
        """Record the start of a pipeline stage."""
        stage = {
            "stage_name": stage_name,
            "status": "RUNNING",
            "started_at": self.timestamp(),
            "completed_at": None,
            "duration_seconds": None,
            "error": None,
        }

        self.stages.append(stage)
        self.log(f"STARTED: {stage_name}")

        return stage

    def complete_stage(self, stage, duration_seconds):
        """Record successful completion of a pipeline stage."""
        stage["status"] = "SUCCESS"
        stage["completed_at"] = self.timestamp()
        stage["duration_seconds"] = round(
            duration_seconds, 3
        )

        self.log(
            f"COMPLETED: {stage['stage_name']} "
            f"in {duration_seconds:.2f} seconds"
        )

    def fail_stage(self, stage, error):
        """Record a failed pipeline stage and its error."""
        stage["status"] = "FAILED"
        stage["completed_at"] = self.timestamp()
        stage["error"] = str(error)

        self.log(
            f"FAILED: {stage['stage_name']} - {error}",
            level="ERROR",
        )

    def set_metrics(self, metrics):
        """Attach business metrics to the current pipeline run."""
        if not isinstance(metrics, dict):
            raise TypeError(
                "Pipeline metrics must be a dictionary."
            )

        self.metrics = metrics

        self.log("Pipeline business metrics attached.")

    def _load_history(self):
        """Load existing run history safely."""
        if not self.history_path.exists():
            return []

        try:
            with open(
                self.history_path,
                "r",
                encoding="utf-8",
            ) as file:
                history = json.load(file)

            if isinstance(history, list):
                return history

            self.log(
                "Existing run history is not a JSON list. "
                "Starting a new history file.",
                level="WARNING",
            )

        except (json.JSONDecodeError, OSError) as error:
            self.log(
                f"Could not read existing run history: {error}",
                level="WARNING",
            )

        return []

    def finish(self, status):
        """Finalize the pipeline run and persist its history."""
        self.status = status
        completed_at = datetime.now(timezone.utc)

        duration = (
            completed_at - self.started_at
        ).total_seconds()

        run_record = {
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "total_duration_seconds": round(duration, 3),
            "stages": self.stages,
            "metrics": self.metrics,
        }

        history = self._load_history()
        history.append(run_record)

        temporary_path = self.history_path.with_suffix(
            ".json.tmp"
        )

        try:
            with open(
                temporary_path,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    history,
                    file,
                    indent=4,
                )

            temporary_path.replace(self.history_path)

        except OSError as error:
            self.log(
                f"Could not save pipeline run history: {error}",
                level="ERROR",
            )
            raise

        self.log(
            f"PIPELINE {self.status}: "
            f"{duration:.2f} seconds"
        )

        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

        return run_record
