import json
import sys

from autodrift.research_cycle import (
    load_queue,
    plan_next_task,
    run_next_task,
    write_queue,
)


def test_plan_next_task_selects_lowest_priority_pending_task(tmp_path):
    queue_path = tmp_path / "queue.csv"
    status_path = tmp_path / "status.json"
    status_path.write_text(
        json.dumps({"last_result": {"task_id": "previous", "status": "completed", "returncode": 0}}),
        encoding="utf-8",
    )
    queue_path.write_text(
        "\n".join(
            [
                "id,priority,status,kind,hypothesis,command,success_artifact,notes",
                "done,1,completed,benchmark,done echo,echo done,,",
                "later,30,pending,training,later echo,echo later,,",
                "next,10,pending,gate,next echo,echo next,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task = plan_next_task(queue_path=queue_path, status_path=status_path)
    status = json.loads(status_path.read_text(encoding="utf-8"))

    assert task is not None
    assert task.id == "next"
    assert status["next_task"]["id"] == "next"
    assert status["last_result"]["task_id"] == "previous"
    assert status["counts"]["pending"] == 2


def test_run_next_task_updates_queue_and_writes_log(tmp_path):
    artifact_path = tmp_path / "artifact.txt"
    queue_path = tmp_path / "queue.csv"
    status_path = tmp_path / "status.json"
    log_path = tmp_path / "research-log.md"
    command = f"{sys.executable} -c \"from pathlib import Path; Path('{artifact_path}').write_text('ok')\""
    queue_path.write_text(
        "\n".join(
            [
                "id,priority,status,kind,hypothesis,command,success_artifact,notes",
                f"smoke,5,pending,smoke,write artifact,{command},{artifact_path},",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_next_task(queue_path=queue_path, status_path=status_path, log_path=log_path, cwd=tmp_path)
    tasks = load_queue(queue_path)
    status = json.loads(status_path.read_text(encoding="utf-8"))
    log_text = log_path.read_text(encoding="utf-8")

    assert result.returncode == 0
    assert tasks[0].status == "completed"
    assert status["last_result"]["task_id"] == "smoke"
    assert status["last_result"]["status"] == "completed"
    assert "smoke" in log_text
    assert "completed" in log_text


def test_run_next_task_idle_preserves_previous_result(tmp_path):
    queue_path = tmp_path / "queue.csv"
    status_path = tmp_path / "status.json"
    log_path = tmp_path / "research-log.md"
    queue_path.write_text(
        "\n".join(
            [
                "id,priority,status,kind,hypothesis,command,success_artifact,notes",
                "done,1,completed,benchmark,done echo,echo done,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    status_path.write_text(
        json.dumps({"last_result": {"task_id": "previous", "status": "completed", "returncode": 0}}),
        encoding="utf-8",
    )

    result = run_next_task(queue_path=queue_path, status_path=status_path, log_path=log_path, cwd=tmp_path)
    status = json.loads(status_path.read_text(encoding="utf-8"))

    assert result.status == "idle"
    assert status["last_result"]["task_id"] == "previous"


def test_write_queue_round_trips_fields(tmp_path):
    queue_path = tmp_path / "queue.csv"
    source_path = tmp_path / "source.csv"
    source_path.write_text(
        "\n".join(
            [
                "id,priority,status,kind,hypothesis,command,success_artifact,notes",
                "task-a,7,blocked,gate,hypothesis,echo hi,out.json,note",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    tasks = load_queue(source_path)
    write_queue(queue_path, tasks)
    reloaded = load_queue(queue_path)
    queue_text = queue_path.read_text(encoding="utf-8")

    assert reloaded == tasks
    assert "\r" not in queue_text
