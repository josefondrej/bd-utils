import pytest

import bdutils
from bdutils.exceptions import NotebookExit


def test_notebook_exit(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)

    # Test that exit() raises NotebookExit with the correct value
    with pytest.raises(NotebookExit) as excinfo:
        bdutils.notebook.exit("success")
    assert excinfo.value.value == "success"


def test_notebook_run(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)

    # Test that run() raises NotImplementedError with expected message
    with pytest.raises(NotImplementedError) as excinfo:
        bdutils.notebook.run("some/path", 60)
    assert "Local notebook.run is not implemented" in str(excinfo.value)
    assert "some/path" in str(excinfo.value)


def test_notebook_help():
    # Verify help() exists (from _HelpMixin)
    assert hasattr(bdutils.notebook, "help")
    # Calling it shouldn't crash
    bdutils.notebook.help()
