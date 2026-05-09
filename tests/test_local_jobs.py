import pytest

import bdutils


def test_jobs_task_values_set_get(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)

    # Test setting a task value
    assert bdutils.jobs.taskValues.set("my_key", "my_value") is True

    # Test getting the same task value (default task key is 'local-task')
    assert bdutils.jobs.taskValues.get("local-task", "my_key") == "my_value"


def test_jobs_task_values_get_not_found(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)

    # Test getting a non-existent task
    with pytest.raises(ValueError) as excinfo:
        bdutils.jobs.taskValues.get("non-existent-task", "key")
    assert "Task 'non-existent-task' not found." in str(excinfo.value)

    # Test getting a non-existent key in an existing task
    bdutils.jobs.taskValues.set("existing_key", "val")
    with pytest.raises(ValueError) as excinfo:
        bdutils.jobs.taskValues.get("local-task", "non-existent-key")
    assert "Key 'non-existent-key' not found for task 'local-task'." in str(excinfo.value)


def test_jobs_task_values_get_defaults(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)

    # Test debugValue when task is missing
    assert bdutils.jobs.taskValues.get("missing-task", "key", debugValue="debug") == "debug"

    # Test default when task exists but key is missing
    bdutils.jobs.taskValues.set("some_key", "some_val")
    assert bdutils.jobs.taskValues.get("local-task", "missing-key", default="default_val") == "default_val"


def test_jobs_help():
    # Verify help() exists
    assert hasattr(bdutils.jobs, "help")
    assert hasattr(bdutils.jobs.taskValues, "help")
    # Should not crash
    bdutils.jobs.help()
    bdutils.jobs.taskValues.help()
